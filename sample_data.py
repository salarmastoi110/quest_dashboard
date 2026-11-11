"""
sample_data.py
--------------
Two simple jobs:
  1. FACULTIES  -> the list of QUEST faculties and their departments (edit here to change them).
  2. make_sample() -> creates made-up student records, used when no file has been uploaded.
"""
import numpy as np
import pandas as pd

# Faculty name -> list of its departments (taken from quest.edu.pk)
FACULTIES = {
    "Faculty of Computer Engineering": [
        "Computer Systems Engineering", "Artificial Intelligence", "Software Engineering"],
    "Faculty of Electrical and Electronic Engineering": [
        "Electrical Engineering", "Electrical (Automation & Control Engineering)",
        "Electronic Engineering", "Telecommunication Engineering", "Biomedical Engineering"],
    "Faculty of Civil and Mechanical Engineering": [
        "Civil Engineering", "Mechanical Engineering",
        "Building and Architectural Engineering", "Industrial and Manufacturing Engineering"],
    "Faculty of Environmental Engineering": [
        "Environment Engineering", "Energy Systems Engineering", "Chemical Engineering"],
    "Faculty of Science": [
        "Data Science", "Computer Science", "Information Technology", "Mathematics and Statistics",
        "Basic Science and Related Studies", "English (Language and Literature)", "Physics",
        "Cyber Security", "Chemistry"],
    "Faculty of Technology": [
        "Food Engineering Technology", "Civil Engineering Technology"],
}

# Reverse lookup: department name -> its faculty (used when an uploaded file has no faculty column)
DEPT_TO_FACULTY = {dept.lower(): fac for fac, depts in FACULTIES.items() for dept in depts}

FIRST_NAMES = ["Ali", "Ahmed", "Sana", "Hina", "Bilal", "Fatima", "Usman", "Zain", "Ayesha",
               "Imran", "Noor", "Hamza", "Sara", "Kashif", "Mehwish", "Asif", "Rabia", "Farhan"]
LAST_NAMES = ["Memon", "Shaikh", "Bhutto", "Soomro", "Jatoi", "Khoso", "Abro", "Chandio",
              "Rind", "Leghari", "Mangi", "Kalhoro"]


def make_sample(per_dept: int = 40, seed: int = 7) -> pd.DataFrame:
    """Create `per_dept` made-up students for every department."""
    rng = np.random.default_rng(seed)          # fixed seed = same data every time
    rows, counter = [], 1
    for faculty, departments in FACULTIES.items():
        for department in departments:
            dept_level = rng.uniform(2.3, 3.0)  # some departments score higher than others
            for _ in range(per_dept):
                semester = int(rng.integers(1, 9))
                gpa = dept_level + rng.normal(0, 0.6) + (semester - 4) * 0.03
                gpa = float(np.clip(gpa, 0.8, 4.0))
                # Students with better GPA usually attend more; noise keeps it realistic
                attendance = float(np.clip(62 + gpa * 7 + rng.normal(0, 10), 40, 100))
                rows.append({
                    "id": f"22{counter:04d}",
                    "name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                    "faculty": faculty,
                    "department": department,
                    "semester": semester,
                    "gpa": round(gpa, 2),
                    "attendance": round(attendance),
                })
                counter += 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Run `python sample_data.py` to re-create sample_students.csv
    make_sample(per_dept=6).to_csv("sample_students.csv", index=False)
    print("sample_students.csv written")
