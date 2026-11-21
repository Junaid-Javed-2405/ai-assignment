import os

# ============================================================
# Semester Credit Hours
# ============================================================

SEMESTER_CREDIT_HOURS = {
    1: 15.5,
    2: 15.5,
    3: 16.5,
    4: 16.5,
    5: 18.5,
    6: 18.5,
    7: 18.5,
    8: 14.5,
}


# ============================================================
# Semester Courses Detail
# ============================================================

SEMESTER_COURSES = {

    # Semester 1
    1: [
        ("MS-251", "Probability & Statistics", 3.0),
        ("GE-160", "Applications of ICT", 3.0),
        ("GE-169", "Applied Physics", 3.0),
        ("GE-167", "Discrete Structures", 3.0),
        ("HQ-001", "Quran Translation - I", 0.5),
        ("GE-190", "Functional English", 3.0),
    ],

    # Semester 2
    2: [
        ("CC-112", "Programming Fundamentals", 3.0),
        ("CC-112-L", "Programming Fundamentals Lab", 1.0),
        ("CC-110", "Digital Logic Design", 2.0),
        ("CC-110-L", "Digital Logic Design Lab", 1.0),
        ("MS-252", "Linear Algebra", 3.0),
        ("GE-191", "Expository Writing", 3.0),
        ("GE-163", "Islamic Studies", 2.0),
        ("HQ-002", "Quran Translation - II", 0.5),
    ],

    # Semester 3
    3: [
        ("CC-211", "Object Oriented Programming", 3.0),
        ("CC-211-L", "Object Oriented Programming Lab", 1.0),
        ("CC-215", "Database Systems", 3.0),
        ("CC-215-L", "Database Systems Lab", 1.0),
        ("CC-210", "Computer Organization & Assembly Language", 3.0),
        ("GE-162", "Calculus & Analytical Geometry", 3.0),
        ("GE-192", "Introduction to Management", 2.0),
        ("HQ-003", "Quran Translation - III", 0.5),
    ],

    # Semester 4
    4: [
        ("CC-213", "Data Structures", 3.0),
        ("CC-213-L", "Data Structures Lab", 1.0),
        ("CC-312", "Information Security", 3.0),
        ("CC-214", "Computer Networks", 3.0),
        ("CC-212", "Software Engineering", 3.0),
        ("DC-220", "Advanced Database Management Systems", 3.0),
        ("HQ-004", "Quran Translation - IV", 0.5),
    ],

    # Semester 5
    5: [
        ("CC-313", "Analysis of Algorithms", 3.0),
        ("CC-310", "Artificial Intelligence", 3.0),
        ("DC-320", "Theory of Automata and Formal Languages", 3.0),
        ("DC-321", "Human Computer Interaction", 3.0),
        ("DC-322", "Computer Architecture", 3.0),
        ("EC-330", "Web Technologies / Elective", 3.0),
        ("HQ-005", "Quran Translation - V", 0.5),
    ],

    # Semester 6
    6: [
        ("CC-311", "Operating Systems", 3.0),
        ("EC-333", "Mobile Application Development / Elective", 3.0),
        ("EC-324", "Software Construction & Development / Elective", 3.0),
        ("EC-335", "Machine Learning / Elective", 3.0),
        ("EC-334", "Game Design and Development / Elective", 3.0),
        ("MS-253", "Multivariable Calculus", 3.0),
        ("HQ-006", "Quran Translation - VI", 0.5),
    ],

    # Semester 7
    7: [
        ("CC-411", "Final Year Project - I", 2.0),
        ("DC-328", "Parallel & Distributed Computing", 3.0),
        ("EC-345", "Computer Vision / Elective", 3.0),
        ("EC-425", "Software Quality Engineering / Elective", 3.0),
        ("MS-254", "Technical and Business Writing", 3.0),
        ("GE-263", "Entrepreneurship", 2.0),
        ("GE-262", "Professional Practices", 2.0),
        ("HQ-007", "Quran Translation - VII", 0.5),
    ],

    # Semester 8
    8: [
        ("CC-412", "Final Year Project - II", 4.0),
        ("DC-421", "Compiler Construction", 3.0),
        ("UE-272", "Introduction to Marketing", 3.0),
        ("GE-168", "Ideology and Constitution of Pakistan", 2.0),
        ("GE-363", "Civics and Community Engagement", 2.0),
        ("HQ-008", "Quran Translation - VIII", 0.5),
    ],
}

# Folder where save_report writes its files (on the machine running the server)
REPORTS_DIR = "reports"


# ============================================================
# Tool 1: Convert Marks to Grade Points
# ============================================================

def marks_to_grade_points(marks: float) -> float | str:
    """
    Convert numerical marks (0-100) into grade points on the 4.0 scale.

    Parameters:
        marks (float): Marks obtained by the student. Valid range is 0 to 100.

    Returns:
        float: Grade points according to the grading scale.
        str: Error message if marks are outside 0-100.
    """

    if marks < 0 or marks > 100:
        return "Error: Marks must be between 0 and 100."

    if marks >= 85:
        return 4.0

    if marks >= 80:
        return 3.7

    if marks >= 75:
        return 3.3

    if marks >= 70:
        return 3.0

    if marks >= 65:
        return 2.7

    if marks >= 61:
        return 2.3

    if marks >= 58:
        return 2.0

    if marks >= 55:
        return 1.7

    if marks >= 50:
        return 1.0

    return 0.0


# ============================================================
# Tool 2: Calculate Semester GPA
# ============================================================

def calculate_semester_gpa(
    grade_points: list[float],
    credit_hours: list[float]
) -> float | str:
    """
    Calculate the GPA of a semester using grade points and
    the corresponding credit hours of each course.

    Parameters:
        grade_points (list[float]):
            Grade points obtained in each course.

        credit_hours (list[float]):
            Credit hours of the corresponding courses (same order).

    Returns:
        float: Semester GPA rounded to two decimal places.
        str: Error message if input lists are invalid.
    """

    if len(grade_points) != len(credit_hours):
        return "Error: Number of grade points must be equal to the number of credit hours."

    if len(grade_points) == 0:
        return "Error: At least one course is required."

    if any(ch <= 0 for ch in credit_hours):
        return "Error: Credit hours must be greater than 0."

    total_quality_points = sum(
        gp * ch
        for gp, ch in zip(grade_points, credit_hours)
    )

    total_credit_hours = sum(credit_hours)

    gpa = total_quality_points / total_credit_hours

    return round(gpa, 2)


# ============================================================
# Tool 3: Calculate New CGPA
# ============================================================

def calculate_new_cgpa(
    current_cgpa: float,
    completed_credit_hours: float,
    semester_gpa: float,
    semester_credit_hours: float
) -> float | str:
    """
    Calculate the new cumulative GPA (CGPA) after completing
    a new semester.

    Parameters:
        current_cgpa (float):
            Student's current cumulative GPA.

        completed_credit_hours (float):
            Credit hours completed before the new semester.

        semester_gpa (float):
            GPA obtained in the new semester.

        semester_credit_hours (float):
            Credit hours of the new semester.

    Returns:
        float: New CGPA rounded to two decimal places.
        str: Error message if any input is invalid.
    """

    if current_cgpa < 0 or current_cgpa > 4:
        return "Error: Current CGPA should be between 0.0 and 4.0."

    if semester_gpa < 0 or semester_gpa > 4:
        return "Error: Semester GPA should be between 0.0 and 4.0."

    if completed_credit_hours <= 0:
        return "Error: Completed credit hours must be greater than 0."

    if semester_credit_hours <= 0:
        return "Error: Semester credit hours must be greater than 0."

    new_cgpa = (
        (current_cgpa * completed_credit_hours)
        + (semester_gpa * semester_credit_hours)
    ) / (
        completed_credit_hours + semester_credit_hours
    )

    return round(new_cgpa, 2)


# ============================================================
# Tool 4: Calculate Required GPA for Target CGPA
# ============================================================

def required_gpa_for_target(
    current_cgpa: float,
    completed_credit_hours: float,
    target_cgpa: float,
    future_credit_hours: float
) -> float | str:
    """
    Calculate the GPA required in the remaining semesters to
    achieve a desired target CGPA. A result above 4.0 means the
    target is not achievable in that many remaining credit hours.

    Parameters:
        current_cgpa (float):
            Student's current cumulative GPA.

        completed_credit_hours (float):
            Total credit hours completed so far.

        target_cgpa (float):
            Desired final CGPA.

        future_credit_hours (float):
            Total credit hours remaining.

    Returns:
        float: Required future GPA rounded to two decimal places.
        str: Error message if any input is invalid.
    """

    if current_cgpa < 0 or current_cgpa > 4:
        return "Error: Current CGPA must be between 0.0 and 4.0."

    if target_cgpa < 0 or target_cgpa > 4:
        return "Error: Target CGPA must be between 0.0 and 4.0."

    if completed_credit_hours <= 0:
        return "Error: Completed credit hours must be greater than 0."

    if future_credit_hours <= 0:
        return "Error: Future credit hours must be greater than 0."

    total_credit_hours = (
        completed_credit_hours + future_credit_hours
    )

    required_gpa = (
        (target_cgpa * total_credit_hours)
        - (current_cgpa * completed_credit_hours)
    ) / future_credit_hours

    return round(required_gpa, 2)


# ============================================================
# Tool 5: Get Semester Courses
# ============================================================

def get_semester_courses(semester: int) -> list[dict] | str:
    """
    Return the courses of a semester (1 to 8) of the PUCIT BS(CS) program.

    Parameters:
        semester (int):
            Semester number from 1 to 8.

    Returns:
        list: One entry per course with its code, name and credit hours.
        str: Error message if semester is invalid.
    """

    if semester < 1 or semester > 8:
        return "Error: Semester must be between 1 and 8."

    return [
        {"code": code, "name": name, "credit_hours": credits}
        for code, name, credits in SEMESTER_COURSES[semester]
    ]


# ============================================================
# Tool 6: Get Remaining Credit Hours
# ============================================================

def get_remaining_credit_hours(current_semester: int) -> float | str:
    """
    Calculate the total credit hours of all semesters that come
    AFTER the given current semester.

    Parameters:
        current_semester (int):
            Student's current semester from 1 to 8.

    Returns:
        float: Total remaining credit hours.
        str: Error message if semester number is invalid.
    """

    if current_semester < 1 or current_semester > 8:
        return "Error: Semester must be between 1 and 8."

    remaining_credit_hours = sum(
        credits
        for semester, credits in SEMESTER_CREDIT_HOURS.items()
        if semester > current_semester
    )

    return remaining_credit_hours


# ============================================================
# Tool 7: Save Report
# ============================================================

def save_report(
    report_text: str,
    filename: str = "gpa_report.txt"
) -> str:
    """
    Save a GPA report as a text file inside the server's 'reports' folder.

    Parameters:
        report_text (str):
            Text content of the GPA report.

        filename (str):
            Name of the file (no folders). Default is 'gpa_report.txt'.

    Returns:
        str: Success message if the report is saved successfully.
        str: Error message if the report cannot be saved.
    """

    if not report_text.strip():
        return "Error: Report cannot be empty."

    # Keep only the file name so nobody can write outside REPORTS_DIR
    filename = os.path.basename(filename.strip()) or "gpa_report.txt"
    if not filename.endswith(".txt"):
        filename += ".txt"

    try:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        path = os.path.join(REPORTS_DIR, filename)

        with open(path, "w", encoding="utf-8") as file:
            file.write(report_text)

        return f"Report saved successfully as {path}."

    except Exception as error:
        return f"Error: Could not save report. {error}"
