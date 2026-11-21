import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from typing_extensions import TypedDict

from fastmcp.client import Client
from langchain.mcp import MCPAdapter
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from llm import llm

load_dotenv()


# ============================================================
# Settings (agent/.env)
# ============================================================

MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
FASTMCP_KEY = os.getenv("FASTMCP_KEY")          # empty = server needs no key
DB_PATH = "memory.db"                           # SQLite file: chats survive restarts

# Where the tools live. With a key we use a Client, without a key a plain URL.
server = Client(MCP_URL, auth=FASTMCP_KEY) if FASTMCP_KEY else MCP_URL


# ============================================================
# System prompt
# ============================================================

SYSTEM_PROMPT = """
You are a GPA and CGPA assistant for a PUCIT BS(CS) student.
Your job is to help the student with:
 semester GPA
 CGPA
 projected CGPA
 required GPA for a target CGPA
 semester course information
 remaining credit hours
 saving GPA reports

IMPORTANT RULES:

1. Every GPA or CGPA calculation must be performed using the
   appropriate calculation tool.
   Never perform the arithmetic yourself.

2. Never invent or assume:
   - marks
   - grade points
   - credit hours
   - current CGPA
   - completed credit hours
   - semester number

   If information is missing, ask the student for it.

3. Ask only one or two missing things at a time.
   Do not ask the student for a long list of information at once.

4. MD-001 and MD-002 are non-credit pass/fail courses.
   They must not be included in GPA calculations.

5. Quran Translation courses are credit-bearing courses.
   Each Quran Translation course has 0.5 credit hours.

6. If the required GPA for a target CGPA is greater than 4.0,
   clearly explain that the target is not achievable within
   that remaining-credit-hour horizon.

7. If a target is not achievable within the current horizon,
   use the available remaining-credit-hour information to help
   the student consider a wider horizon.

8. Do not save a report automatically.
   Offer to save a report only after producing a meaningful result,
   such as a semester GPA, projected CGPA, or target-GPA plan.

9. When using a tool, provide the tool with the exact information
   required by its parameters.

10. Give the final answer in simple and understandable language.

11. When the student gives their current semester and asks whether
    they can achieve a target CGPA, ALWAYS call
    get_remaining_credit_hours first.

12. NEVER calculate remaining credit hours yourself.
    NEVER ask the student for remaining credit hours if the
    current semester is provided.

13. After getting the remaining credit hours, use the returned
    value as future_credit_hours for required_gpa_for_target.

14. If completed credit hours are required but not provided,
    ask the student only for their completed credit hours.

15. Example:
    Student: "I am in 7th semester having 3.71 CGPA, achieve 3.8"

    Required tool sequence:
    1. get_remaining_credit_hours(7)
    2. Ask for completed credit hours if not already known.
    3. required_gpa_for_target(...)
    4. Explain whether the target is achievable.

16. You remember this student's earlier messages. If the student
    already told you their CGPA, semester, completed credit hours or
    marks earlier in this conversation, use them. Do not ask again.

17. If a tool returns an error saying it failed or the server could
    not be reached, tell the student the calculation tools are not
    available right now and to try again later. Never guess the result.
"""


# ============================================================
# Graph state
# ============================================================

class State(TypedDict):
    # add_messages = the reducer: new messages are added to the END of the list
    messages: Annotated[list, add_messages]


# ============================================================
# Task 6: when the tool server is down
# ============================================================

NO_ANSWER = (
    "Error: this tool call got no answer because the MCP tool server "
    "was not reachable. Tell the student the calculation tools are not "
    "available right now. Do not guess the result."
)


def tool_error_message(error: Exception) -> str:
    """ToolNode calls this when a tool raises, so the model is TOLD instead of the chat crashing."""
    return (
        f"Error: the tool failed or the MCP tool server could not be reached "
        f"({type(error).__name__}: {error}). Tell the student the calculation "
        f"tools are not available right now. Do not guess the result."
    )


def missing_tool_answers(messages) -> list[ToolMessage]:
    """For every tool call in the history that has no ToolMessage, make an error ToolMessage."""
    answered = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    missing = []
    for m in messages:
        if isinstance(m, AIMessage):
            for call in m.tool_calls:
                if call["id"] not in answered:
                    missing.append(
                        ToolMessage(
                            content=NO_ANSWER,
                            tool_call_id=call["id"],
                            name=call["name"],
                            status="error",
                        )
                    )
    return missing


def fix_dangling_tool_calls(messages) -> list:
    """Copy of the history where each unanswered tool call is followed by its error answer."""
    answered = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    fixed = []
    for m in messages:
        fixed.append(m)
        if isinstance(m, AIMessage):
            for call in m.tool_calls:
                if call["id"] not in answered:
                    fixed.append(
                        ToolMessage(
                            content=NO_ANSWER,
                            tool_call_id=call["id"],
                            name=call["name"],
                            status="error",
                        )
                    )
    return fixed


async def heal_thread(app, config):
    """Repair the SAVED chat: write an error answer for any tool call that never got one."""
    state = await app.aget_state(config)
    missing = missing_tool_answers(state.values.get("messages", []))
    if missing:
        await app.aupdate_state(config, {"messages": missing}, as_node="tools")
        print("(Repaired a tool call that never got an answer in the saved chat.)")


# ============================================================
# Build the graph (Lab 6 style): agent node <-> tools node
# ============================================================

def build_app(tools, memory):
    model_with_tools = llm.bind_tools(tools)

    async def call_model(state: State):
        # Safety net: never send a history with an unanswered tool call to the API
        messages = fix_dangling_tool_calls(state["messages"])
        response = await model_with_tools.ainvoke(
            [SystemMessage(content=SYSTEM_PROMPT)] + messages
        )
        return {"messages": [response]}

    builder = StateGraph(State)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=tool_error_message))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)   # tool calls? -> "tools", else END
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=memory)


# ============================================================
# Task 3: Memory helpers
# ============================================================

async def list_threads(memory) -> list[str]:
    """Names (thread ids) of every chat saved in the SQLite file."""
    names = []
    async for checkpoint in memory.alist(None):
        name = checkpoint.config["configurable"]["thread_id"]
        if name not in names:
            names.append(name)
    return names


def text_of(content) -> str:
    """Message content is a string, or a list of parts for some models."""
    if isinstance(content, str):
        return content
    return "".join(
        part.get("text", "") for part in content if isinstance(part, dict)
    )


def short(text, limit: int = 150) -> str:
    text = str(text).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


async def show_history(app, config):
    """Print everything saved for this person (/history)."""
    state = await app.aget_state(config)
    messages = state.values.get("messages", [])

    if not messages:
        print("(No saved messages yet.)\n")
        return

    print("\n------ Saved chat ------")
    for message in messages:
        if isinstance(message, HumanMessage):
            print(f"You: {text_of(message.content)}")
        elif isinstance(message, AIMessage):
            for call in message.tool_calls:
                print(f"   [tool call] {call['name']}({call['args']})")
            if text_of(message.content):
                print(f"Agent: {text_of(message.content)}")
        elif isinstance(message, ToolMessage):
            print(f"   [tool result] {message.name}: {short(message.content)}")
    print("------------------------\n")


async def ask(prompt: str) -> str:
    """input() would freeze the async program, so run it in a thread."""
    return (await asyncio.to_thread(input, prompt)).strip()


async def choose_person(memory) -> str:
    """Print the saved chats, then ask who is chatting. The name is the thread_id."""
    threads = await list_threads(memory)
    if threads:
        print("Saved chats: " + ", ".join(threads))
    else:
        print("No saved chats yet.")

    name = ""
    while not name:
        name = await ask("Who is chatting? (type a name): ")
    return name


# ============================================================
# Task 4: Streaming
# ============================================================

async def stream_reply(app, user_input: str, config):
    """Send ONE new message; the saved history is loaded by the checkpointer."""
    inputs = {"messages": [HumanMessage(content=user_input)]}
    typing = False        # are we in the middle of printing the answer?

    async for chunk in app.astream(
        inputs,
        config,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        if chunk["type"] == "messages":
            token, metadata = chunk["data"]          # one piece of the model's answer
            node = metadata["langgraph_node"]        # which node produced it
            text = text_of(token.content)
            if node == "agent" and text:
                if not typing:
                    print("\nAgent: ", end="", flush=True)
                    typing = True
                print(text, end="", flush=True)

        else:                                        # "updates"
            for node, update in chunk["data"].items():
                if not isinstance(update, dict):
                    continue
                for message in update.get("messages", []):
                    if node == "agent" and message.tool_calls:
                        for call in message.tool_calls:
                            print(f"\n  [calling tool] {call['name']}({call['args']}) ...")
                        typing = False
                    elif node == "tools":
                        print(f"  [tool answered] {message.name}: {short(message.content)}")

    print("\n")


# ============================================================
# Main
# ============================================================

HELP = (
    "Commands:  /history  show saved chat   |  /switch  change person\n"
    "           /forget   delete my chat    |  /help    show this  |  exit"
)


async def main():
    print("========================================")
    print("       PUCIT GPA & CGPA Assistant")
    print("========================================")

    # connect, list the tools, disconnect (each later tool call opens its own connection)
    try:
        tools = await MCPAdapter(server).list_tools()
    except Exception as error:
        print(f"Could not reach the MCP server at {MCP_URL}.")
        print(f"({type(error).__name__}: {error})")
        print("Start it with:  cd server && python server.py")
        return

    print("Tools from the server: " + ", ".join(tool.name for tool in tools) + "\n")

    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as memory:
        app = build_app(tools, memory)

        name = await choose_person(memory)
        config = {"configurable": {"thread_id": name}}
        await heal_thread(app, config)
        print(f"\nHello {name}!  {HELP}\n")

        while True:
            user_input = await ask(f"{name}: ")

            if not user_input:
                print("Agent: Please enter something.\n")
                continue

            command = user_input.lower()

            if command in ["exit", "quit", "/exit", "/quit"]:
                print("\nAgent: Goodbye! 👋")
                break

            if command == "/help":
                print(HELP + "\n")

            elif command == "/history":
                await show_history(app, config)

            elif command == "/switch":
                name = await choose_person(memory)
                config = {"configurable": {"thread_id": name}}
                await heal_thread(app, config)
                print(f"\nHello {name}!\n")

            elif command == "/forget":
                await memory.adelete_thread(name)
                print(f"Deleted everything saved for {name}. Starting fresh.\n")

            else:
                try:
                    await stream_reply(app, user_input, config)
                except Exception as error:
                    print(f"\n\nSomething went wrong: {type(error).__name__}: {error}")
                    print("Please try again in a moment.\n")
                    # a half-finished run may have left a tool call without an answer
                    try:
                        await heal_thread(app, config)
                    except Exception:
                        pass


if __name__ == "__main__":
    asyncio.run(main())
