import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()   # reads agent/.env

llm = init_chat_model(
    "groq:openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)
