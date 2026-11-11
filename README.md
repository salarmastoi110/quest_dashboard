# QUEST Nawabshah - Student Performance Dashboard

Built by **Salaar Mastoi**

A simple dashboard that shows student GPA and attendance for all 6 faculties and 26 departments of QUEST.
Colours (navy #0a3a71, orange #f99410) are taken from quest.edu.pk.

## Attendance rules used in the dashboard
| Attendance | Result |
|---|---|
| 75% or more | Eligible for paper |
| 60% to 74% | Needs condonation |
| Below 60% | Not eligible for paper |

## What is inside the dashboard
- **Overview** - key numbers and main charts
- **More Charts** - attendance charts, GPA spread, GPA ranges, top 10 students, heatmap, department comparison
- **Attendance & Eligibility** - rules, charts and downloadable lists (not eligible / condonation / low GPA)
- **Faculties & Departments** - a card for each department
- **Students** - search and download the student list
- **Teacher Evaluation** - task test and SUS questionnaire

## How to run on your computer
```bash
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Then open http://localhost:8501

## Use your own student file
Upload a CSV or Excel file from the left sidebar. Required columns:
`id, name, department, semester, gpa, attendance`
Optional column: `faculty` (if missing, it is found automatically from the department name).
If your column names are different, the sidebar lets you match them. See `sample_students.csv` for an example.

## Project files (easy guide)
| File | What it does |
|---|---|
| `app.py` | The dashboard itself. Settings (pass GPA, attendance limits) are at the top. |
| `sample_data.py` | List of faculties/departments and the built-in sample students |
| `assets/style.css` | Colours and look of the page |
| `assets/campus.jpg` | Campus photo (replace with any JPG) |
| `sample_students.csv` | Example file format |

## To change the rules
Open `app.py` and edit these lines at the top:
```python
PASS_GPA = 2.0
ELIGIBLE_ATT = 75
CONDONATION_ATT = 60
```

## Deploy on Streamlit Community Cloud
1. Upload this whole folder to a GitHub repository (keep `assets` and `.streamlit`).
2. Open https://share.streamlit.io -> Create app.
3. Select repo, branch `main`, main file `app.py` -> Deploy.
