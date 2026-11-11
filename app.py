"""
QUEST Nawabshah - Student Performance Dashboard
Built by Salaar Mastoi

How this file is organised (read it top to bottom):
  1. SETTINGS        - colours and the pass / attendance rules (change numbers here)
  2. DATA HELPERS    - read the file, clean it, work out each student's attendance status
  3. SMALL HELPERS   - tiny functions that draw cards and style charts
  4. TAB FUNCTIONS   - one function per tab on the page
  5. MAIN PAGE       - sidebar filters, top banner, tabs and footer
"""
import base64
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from sample_data import DEPT_TO_FACULTY, FACULTIES, make_sample

# =====================================================================
# 1. SETTINGS
# =====================================================================
NAVY, ORANGE, RED, GREEN, TEAL = "#0a3a71", "#f99410", "#c0392b", "#1e8449", "#0e9aa7"

PASS_GPA = 2.0                 # GPA below this = failing
ELIGIBLE_ATT = 75              # 75% or more                -> eligible for paper
CONDONATION_ATT = 60           # from 60% up to below 75%   -> condonation needed
                               # below 60%                  -> not eligible for paper

# The three attendance groups (these exact words appear in tables and charts)
ELIGIBLE = "Eligible for paper"
CONDONATION = "Needs condonation"
NOT_ELIGIBLE = "Not eligible for paper"
STATUS_ORDER = [ELIGIBLE, CONDONATION, NOT_ELIGIBLE]
STATUS_COLORS = {ELIGIBLE: GREEN, CONDONATION: ORANGE, NOT_ELIGIBLE: RED}

# One colour for each faculty
FAC_COLORS = dict(zip(FACULTIES, [NAVY, ORANGE, GREEN, TEAL, "#7a4b9a", "#8d6e63"]))
FAC_COLORS["Other"] = "#6c757d"

# Columns an uploaded file must have, and the friendly names shown in tables
REQUIRED = ["id", "name", "department", "semester", "gpa", "attendance"]
COLUMN_LABELS = {"id": "Student ID", "name": "Student Name", "faculty": "Faculty",
                 "department": "Department", "semester": "Semester", "gpa": "GPA",
                 "attendance": "Attendance %", "attendance_status": "Attendance Status"}

ROOT = Path(__file__).parent
st.set_page_config(page_title="QUEST Student Performance Dashboard", page_icon="🎓", layout="wide")


# =====================================================================
# 2. DATA HELPERS
# =====================================================================
def attendance_status(attendance: pd.Series) -> pd.Series:
    """Turn attendance % into one of the three groups using the rules above."""
    groups = pd.cut(attendance,
                    bins=[-float("inf"), CONDONATION_ATT, ELIGIBLE_ATT, float("inf")],
                    labels=[NOT_ELIGIBLE, CONDONATION, ELIGIBLE],
                    right=False)            # right=False -> 75 itself counts as Eligible, 60 as Condonation
    return groups.astype(str)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Fix data types, drop incomplete rows, find the faculty and add the attendance status."""
    df = df.copy()
    for col in ["gpa", "attendance", "semester"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["gpa", "attendance", "semester", "department"])
    df["semester"] = df["semester"].astype(int)
    df["department"] = df["department"].astype(str).str.strip()
    if "faculty" not in df.columns:         # no faculty column? guess it from the department name
        df["faculty"] = df["department"].str.lower().map(DEPT_TO_FACULTY)
    df["faculty"] = df["faculty"].fillna("Other")
    df["attendance_status"] = attendance_status(df["attendance"])
    return df


@st.cache_data
def default_data() -> pd.DataFrame:
    """Built-in student records, used until the user uploads their own file."""
    return clean_data(make_sample())


def read_uploaded_file(upload):
    """Read the uploaded CSV/Excel. If column names differ, let the user match them."""
    raw = pd.read_csv(upload) if upload.name.lower().endswith(".csv") else pd.read_excel(upload)
    lower_names = {c.lower().strip(): c for c in raw.columns}

    # Case 1: all required columns found -> use the file directly
    if all(r in lower_names for r in REQUIRED):
        keep = REQUIRED + (["faculty"] if "faculty" in lower_names else [])
        return clean_data(raw.rename(columns={lower_names[k]: k for k in keep})[keep])

    # Case 2: names differ -> show drop-downs so the user can match each column
    st.sidebar.warning("Your column names are different. Please match them:")
    options, chosen = list(raw.columns), {}
    for needed in REQUIRED:
        guess = options.index(lower_names[needed]) if needed in lower_names else 0
        chosen[needed] = st.sidebar.selectbox(COLUMN_LABELS[needed], options, index=guess, key=f"map_{needed}")
    if st.sidebar.button("Apply column matching", type="primary"):
        renamed = raw.rename(columns={v: k for k, v in chosen.items()})[REQUIRED]
        st.session_state["matched_data"] = clean_data(renamed)
        st.session_state["matched_name"] = upload.name
    if "matched_data" in st.session_state:
        return st.session_state["matched_data"], st.session_state["matched_name"]
    return None


def load_data():
    """Sidebar upload box. Returns (dataframe, name of the data source)."""
    st.sidebar.markdown('<div class="sb">QUEST Nawabshah<small>Student Performance Dashboard</small></div>',
                        unsafe_allow_html=True)
    st.sidebar.subheader("Student Data")
    upload = st.sidebar.file_uploader("Upload your file (CSV or Excel)", type=["csv", "xlsx"])
    df, source = default_data(), "Default student data"
    if upload is not None:
        result = read_uploaded_file(upload)
        if isinstance(result, pd.DataFrame):
            df, source = result, upload.name
        elif result is not None:
            df, source = result
    st.sidebar.download_button("Download blank CSV template", make_sample(per_dept=1).head(8).to_csv(index=False),
                               "students_template.csv", "text/csv")
    return df, source


# =====================================================================
# 3. SMALL HELPERS (cards, chart style, tables)
# =====================================================================
def kpi_cards(cards):
    """Show a row of number cards. Each card = (title, big value, small text, colour)."""
    html = "".join(f'<div class="kpi" style="--c:{c}"><div class="l">{t}</div>'
                   f'<div class="v">{v}</div><div class="s">{s}</div></div>' for t, v, s, c in cards)
    st.markdown(f'<div class="kgrid">{html}</div>', unsafe_allow_html=True)


def section_title(text):
    st.markdown(f'<div class="sec">{text}</div>', unsafe_allow_html=True)


def rules_box():
    """The three attendance rules, shown as coloured boxes."""
    st.markdown(
        '<div class="rules">'
        f'<div class="rule" style="--c:{GREEN}"><b>✅ {ELIGIBLE}</b><span>Attendance {ELIGIBLE_ATT}% or more</span></div>'
        f'<div class="rule" style="--c:{ORANGE}"><b>📝 {CONDONATION}</b><span>Attendance from {CONDONATION_ATT}% up to {ELIGIBLE_ATT - 1}%</span></div>'
        f'<div class="rule" style="--c:{RED}"><b>⛔ {NOT_ELIGIBLE}</b><span>Attendance below {CONDONATION_ATT}%</span></div>'
        '</div>', unsafe_allow_html=True)


def style_chart(fig, height=360):
    """Give every chart the same clean look."""
    fig.update_layout(height=height, plot_bgcolor="#fff", paper_bgcolor="#fff",
                      margin=dict(l=10, r=10, t=50, b=10), font=dict(color="#1b2430"),
                      title_font=dict(size=15, color=NAVY), legend_title=None)
    fig.update_xaxes(gridcolor="#eef1f5")
    fig.update_yaxes(gridcolor="#eef1f5")
    return fig


def show_chart(fig, height=360):
    st.plotly_chart(style_chart(fig, height), width="stretch")


def short_faculty(series: pd.Series) -> pd.Series:
    """'Faculty of Science' -> 'Science' (shorter labels on charts)."""
    return series.str.replace("Faculty of ", "", regex=False)


def show_table(df: pd.DataFrame, height=420):
    """Show a student table with friendly column names and progress bars."""
    show = df[[c for c in COLUMN_LABELS if c in df.columns]].rename(columns=COLUMN_LABELS)
    st.dataframe(show, width="stretch", hide_index=True, height=height, column_config={
        "GPA": st.column_config.ProgressColumn("GPA", min_value=0, max_value=4, format="%.2f"),
        "Attendance %": st.column_config.ProgressColumn("Attendance %", min_value=0, max_value=100, format="%d"),
        "Semester": st.column_config.NumberColumn("Semester", format="%d")})


def department_card(name, z, color):
    """One small card for a department (used in the Faculties tab)."""
    def bar(label, value_text, percent):
        return (f'<div class="br"><span>{label}</span><b>{value_text}</b></div>'
                f'<div class="mt"><i style="width:{max(0, min(percent, 100)):.0f}%"></i></div>')

    avg_gpa, avg_att = z.gpa.mean(), z.attendance.mean()
    pass_rate = (z.gpa >= PASS_GPA).mean() * 100
    not_eligible = int((z.attendance_status == NOT_ELIGIBLE).sum())
    condonation = int((z.attendance_status == CONDONATION).sum())
    warn = "bad" if not_eligible else ""
    return (f'<div class="dc" style="--c:{color}"><div class="dn">{escape(name)}</div>'
            f'<div class="ds">{len(z)} students</div>'
            + bar("Average GPA", f"{avg_gpa:.2f}", avg_gpa / 4 * 100)
            + bar("Average attendance", f"{avg_att:.0f}%", avg_att)
            + bar("Pass rate", f"{pass_rate:.0f}%", pass_rate)
            + f'<div class="dr {warn}">⛔ {not_eligible} not eligible · 📝 {condonation} condonation</div></div>')


def download(label, df, filename):
    st.download_button(label, df.to_csv(index=False), filename, "text/csv")


# =====================================================================
# 4. TAB FUNCTIONS  (each one draws one tab)
# =====================================================================
def tab_overview(f, by_dept):
    """Tab 1: key numbers and the main charts."""
    not_eligible = int((f.attendance_status == NOT_ELIGIBLE).sum())
    condonation = int((f.attendance_status == CONDONATION).sum())
    kpi_cards([
        ("Total Students", f"{len(f):,}", f"in {f.faculty.nunique()} faculties", NAVY),
        ("Average GPA", f"{f.gpa.mean():.2f}", "out of 4.00", ORANGE),
        ("Average Attendance", f"{f.attendance.mean():.0f}%", f"{ELIGIBLE_ATT}% needed for paper", TEAL),
        ("Pass Rate", f"{(f.gpa >= PASS_GPA).mean() * 100:.0f}%", f"students with GPA {PASS_GPA} or more", GREEN),
        ("Needs Condonation", f"{condonation:,}", f"attendance {CONDONATION_ATT}% – {ELIGIBLE_ATT - 1}%", ORANGE),
        ("Not Eligible for Paper", f"{not_eligible:,}", f"attendance below {CONDONATION_ATT}%", RED)])

    best, worst = by_dept.loc[by_dept.gpa.idxmax()], by_dept.loc[by_dept.gpa.idxmin()]
    st.markdown(f'<div class="ins">💡 <b>Quick insight:</b> The department with the highest average GPA is '
                f'<b>{escape(best.department)}</b> ({best.gpa:.2f}). The lowest is '
                f'<b>{escape(worst.department)}</b> ({worst.gpa:.2f}).</div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    # Chart 1: average GPA of each faculty
    fac = f.groupby("faculty", as_index=False).agg(gpa=("gpa", "mean"))
    fac["Faculty"] = short_faculty(fac.faculty)
    fig = px.bar(fac, x="Faculty", y="gpa", color="faculty", color_discrete_map=FAC_COLORS,
                 range_y=[0, 4], text=fac.gpa.round(2), title="Average GPA of each faculty")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Average GPA")
    with left:
        show_chart(fig)
    # Chart 2: how GPA changes from semester to semester
    trend = f.groupby(["semester", "faculty"], as_index=False)["gpa"].mean()
    fig = px.line(trend, x="semester", y="gpa", color="faculty", markers=True,
                  color_discrete_map=FAC_COLORS, range_y=[0, 4], title="GPA from semester to semester")
    fig.update_layout(legend=dict(orientation="h", y=-0.25), xaxis=dict(dtick=1, title="Semester"),
                      yaxis_title="Average GPA")
    with right:
        show_chart(fig)

    left, right = st.columns([3, 2])
    # Chart 3: every department ranked by GPA
    ranked = by_dept.sort_values("gpa")
    fig = px.bar(ranked, x="gpa", y="department", orientation="h", color="faculty",
                 color_discrete_map=FAC_COLORS, range_x=[0, 4], title="Departments ranked by average GPA")
    fig.update_layout(showlegend=False, yaxis_title=None, xaxis_title="Average GPA")
    with left:
        show_chart(fig, max(380, 24 * len(ranked) + 90))
    # Chart 4: how many students have each GPA
    fig = px.histogram(f, x="gpa", nbins=18, title="How many students have each GPA")
    fig.update_traces(marker_color=NAVY)
    fig.add_vline(x=PASS_GPA, line_dash="dash", line_color=RED, annotation_text="Pass line")
    fig.update_layout(xaxis_title="GPA", yaxis_title="Number of students")
    with right:
        show_chart(fig, 380)

    # Chart 5: does better attendance mean better GPA?
    fig = px.scatter(f, x="attendance", y="gpa", color="faculty", color_discrete_map=FAC_COLORS,
                     hover_data=["name", "department"], opacity=.7, title="Attendance vs GPA (each dot is a student)")
    fig.add_vline(x=CONDONATION_ATT, line_dash="dot", line_color=RED)
    fig.add_vline(x=ELIGIBLE_ATT, line_dash="dot", line_color=GREEN)
    fig.update_layout(legend=dict(orientation="h", y=-0.2), xaxis_title="Attendance %", yaxis_title="GPA")
    show_chart(fig, 420)


def tab_more_charts(f, by_dept):
    """Tab 2: extra charts and graphs."""
    # ---------- Attendance charts ----------
    section_title("Attendance")
    left, right = st.columns(2)
    counts = f.attendance_status.value_counts().reindex(STATUS_ORDER, fill_value=0).reset_index()
    counts.columns = ["Status", "Students"]
    fig = px.pie(counts, names="Status", values="Students", hole=.55, color="Status",
                 color_discrete_map=STATUS_COLORS, title="Students by attendance status")
    fig.update_traces(textinfo="label+percent+value")
    fig.update_layout(showlegend=False)
    with left:
        show_chart(fig, 400)

    fig = px.histogram(f, x="attendance", nbins=25, title="How many students have each attendance %")
    fig.update_traces(marker_color=TEAL)
    fig.add_vline(x=CONDONATION_ATT, line_dash="dash", line_color=RED, annotation_text=f"{CONDONATION_ATT}%")
    fig.add_vline(x=ELIGIBLE_ATT, line_dash="dash", line_color=GREEN, annotation_text=f"{ELIGIBLE_ATT}%")
    fig.update_layout(xaxis_title="Attendance %", yaxis_title="Number of students")
    with right:
        show_chart(fig, 400)

    left, right = st.columns(2)
    fig = px.histogram(f.assign(Faculty=short_faculty(f.faculty)), x="Faculty", color="attendance_status",
                       barnorm="percent", text_auto=".0f", color_discrete_map=STATUS_COLORS,
                       category_orders={"attendance_status": STATUS_ORDER},
                       title="Attendance status of each faculty (%)")
    fig.update_layout(yaxis_title="% of students", xaxis_title=None, legend=dict(orientation="h", y=-0.25))
    with left:
        show_chart(fig, 400)

    by_sem = f.groupby("semester", as_index=False).agg(att=("attendance", "mean"))
    fig = px.bar(by_sem, x="semester", y="att", text=by_sem.att.round(0), title="Average attendance of each semester")
    fig.update_traces(marker_color=NAVY, texttemplate="%{text}%")
    fig.add_hline(y=ELIGIBLE_ATT, line_dash="dash", line_color=GREEN, annotation_text=f"{ELIGIBLE_ATT}% needed")
    fig.update_layout(xaxis=dict(dtick=1, title="Semester"), yaxis=dict(title="Average attendance %", range=[0, 100]))
    with right:
        show_chart(fig, 400)

    # ---------- GPA charts ----------
    section_title("GPA and results")
    left, right = st.columns(2)
    fig = px.box(f.assign(Faculty=short_faculty(f.faculty)), x="Faculty", y="gpa", color="faculty",
                 color_discrete_map=FAC_COLORS, title="GPA spread inside each faculty")
    fig.add_hline(y=PASS_GPA, line_dash="dash", line_color=RED)
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="GPA")
    with left:
        show_chart(fig, 400)

    bands = pd.cut(f.gpa, bins=[0, 2.0, 2.5, 3.0, 3.5, 4.01], right=False,
                   labels=["Below 2.0 (fail)", "2.0 – 2.49", "2.5 – 2.99", "3.0 – 3.49", "3.5 – 4.0"])
    bands = bands.value_counts().sort_index().reset_index()
    bands.columns = ["GPA range", "Students"]
    fig = px.bar(bands, x="GPA range", y="Students", text="Students", title="Students in each GPA range")
    fig.update_traces(marker_color=[RED, ORANGE, TEAL, NAVY, GREEN])
    with right:
        show_chart(fig, 400)

    left, right = st.columns(2)
    per_sem = f.groupby("semester", as_index=False).agg(students=("id", "count"))
    fig = px.bar(per_sem, x="semester", y="students", text="students", title="Number of students in each semester")
    fig.update_traces(marker_color=ORANGE)
    fig.update_layout(xaxis=dict(dtick=1, title="Semester"), yaxis_title="Students")
    with left:
        show_chart(fig, 380)

    top = f.nlargest(10, "gpa").assign(label=lambda d: d.name + " (" + d.id.astype(str) + ")")
    fig = px.bar(top.sort_values("gpa"), x="gpa", y="label", orientation="h", text="gpa",
                 range_x=[0, 4.3], title="Top 10 students by GPA")
    fig.update_traces(marker_color=GREEN)
    fig.update_layout(yaxis_title=None, xaxis_title="GPA")
    with right:
        show_chart(fig, 380)

    # ---------- Department comparison ----------
    section_title("Department comparison")
    summary = f.groupby("department", as_index=False).agg(
        gpa=("gpa", "mean"), attendance=("attendance", "mean"), students=("id", "count"))
    summary["faculty"] = summary.department.map(f.drop_duplicates("department").set_index("department").faculty)
    fig = px.scatter(summary, x="attendance", y="gpa", size="students", color="faculty",
                     color_discrete_map=FAC_COLORS, hover_name="department", size_max=32,
                     title="Departments: average attendance vs average GPA (bigger bubble = more students)")
    fig.update_layout(legend=dict(orientation="h", y=-0.2), xaxis_title="Average attendance %",
                      yaxis_title="Average GPA")
    show_chart(fig, 460)

    grid = f.pivot_table(index="department", columns="semester", values="gpa", aggfunc="mean")
    fig = px.imshow(grid, aspect="auto", text_auto=".1f", color_continuous_scale="Blues",
                    title="Average GPA of each department in each semester (darker = higher)")
    fig.update_layout(xaxis_title="Semester", yaxis_title=None, coloraxis_colorbar_title="GPA")
    show_chart(fig, max(420, 26 * len(grid) + 100))


def tab_attendance(f):
    """Tab 3: who is eligible, who needs condonation and who cannot sit the paper."""
    section_title("Attendance rules")
    rules_box()
    n_ok, n_con, n_no = (int((f.attendance_status == s).sum()) for s in STATUS_ORDER)
    n_low_gpa = int((f.gpa < PASS_GPA).sum())
    kpi_cards([("Eligible for Paper", f"{n_ok:,}", f"{n_ok / len(f) * 100:.0f}% of students", GREEN),
               ("Needs Condonation", f"{n_con:,}", f"{n_con / len(f) * 100:.0f}% of students", ORANGE),
               ("Not Eligible for Paper", f"{n_no:,}", f"{n_no / len(f) * 100:.0f}% of students", RED),
               ("Low GPA", f"{n_low_gpa:,}", f"GPA below {PASS_GPA}", NAVY)])

    # Chart: departments with the most students who cannot sit / need condonation
    dept_status = f.groupby(["department", "attendance_status"]).size().reset_index(name="Students")
    problem = dept_status[dept_status.attendance_status != ELIGIBLE].groupby("department").Students.sum()
    worst = problem.sort_values().tail(12).index
    fig = px.bar(dept_status[dept_status.department.isin(worst) & (dept_status.attendance_status != ELIGIBLE)],
                 x="Students", y="department", color="attendance_status", orientation="h",
                 color_discrete_map=STATUS_COLORS, category_orders={"department": list(worst)},
                 title="Departments with the most attendance problems (top 12)")
    fig.update_layout(yaxis_title=None, legend=dict(orientation="h", y=-0.2))
    show_chart(fig, 460)

    # Lists of students
    section_title("Student lists")
    lists = st.tabs([f"⛔ {NOT_ELIGIBLE} ({n_no})", f"📝 {CONDONATION} ({n_con})", f"📉 Low GPA ({n_low_gpa})"])
    groups = [(f[f.attendance_status == NOT_ELIGIBLE].sort_values("attendance"), "not_eligible_students.csv"),
              (f[f.attendance_status == CONDONATION].sort_values("attendance"), "condonation_students.csv"),
              (f[f.gpa < PASS_GPA].sort_values("gpa"), "low_gpa_students.csv")]
    for box, (data, filename) in zip(lists, groups):
        with box:
            if data.empty:
                st.success("No students in this group for the current selection.")
            else:
                show_table(data)
                download("Download this list", data, filename)


def tab_faculties(f, faculties):
    """Tab 4: each faculty with a card for every department."""
    st.caption("Departments are grouped under their faculty. Each faculty has its own colour.")
    for fac in faculties:
        z = f[f.faculty == fac]
        if z.empty:
            continue
        color = FAC_COLORS[fac]
        cards = "".join(department_card(d, z[z.department == d], color) for d in sorted(z.department.unique()))
        st.markdown(f'<div class="fh" style="--c:{color}"><span>{escape(fac)}</span>'
                    f'<small>Average GPA {z.gpa.mean():.2f} · {len(z)} students · {z.department.nunique()} departments</small></div>'
                    f'<div class="fb"><div class="dgrid">{cards}</div></div>', unsafe_allow_html=True)


def tab_students(f):
    """Tab 5: searchable list of all students."""
    query = st.text_input("🔎 Search by name, ID or department")
    shown = f
    if query:
        match = (f.name.str.contains(query, case=False) | f.id.astype(str).str.contains(query)
                 | f.department.str.contains(query, case=False))
        shown = f[match]
    st.caption(f"{len(shown)} students found")
    show_table(shown.sort_values("gpa", ascending=False), height=520)
    download("Download this list", shown, "students_list.csv")


def tab_evaluation():
    """Tab 6: lets you test how easy the dashboard is to use (task test + SUS score)."""
    section_title("Task test: how easy and accurate is the dashboard?")
    st.caption("Give a teacher a task, for example “Which department has the lowest average GPA?”. "
               "Write down the time taken and whether the answer was correct.")
    st.session_state.setdefault("tasks", [])
    with st.form("task_form", clear_on_submit=True):
        a, b, c = st.columns([3, 1, 1])
        task = a.text_input("Task given to the teacher")
        seconds = b.number_input("Time taken (seconds)", min_value=0.0, step=1.0)
        correct = c.checkbox("Answer was correct")
        if st.form_submit_button("Save result", type="primary") and task:
            st.session_state["tasks"].append({"Task": task, "Seconds": seconds, "Correct": correct})
    if st.session_state["tasks"]:
        results = pd.DataFrame(st.session_state["tasks"])
        st.dataframe(results, width="stretch", hide_index=True)
        m1, m2 = st.columns(2)
        m1.metric("Accuracy", f"{results.Correct.mean() * 100:.0f}%")
        m2.metric("Average time", f"{results.Seconds.mean():.1f} sec")
        download("Download task results", results, "task_results.csv")

    section_title("SUS questionnaire (System Usability Scale)")
    st.caption("Move each slider: 1 = strongly disagree, 5 = strongly agree")
    questions = ["I would like to use this dashboard frequently",
                 "The dashboard is unnecessarily complex",
                 "The dashboard is easy to use",
                 "I would need technical support to use it",
                 "The functions are well integrated",
                 "There is too much inconsistency",
                 "Most teachers would learn it quickly",
                 "The dashboard is cumbersome to use",
                 "I felt confident using it",
                 "I needed to learn a lot before using it"]
    answers = [st.slider(f"{i + 1}. {q}", 1, 5, 3, key=f"sus{i}") for i, q in enumerate(questions)]
    if st.button("Calculate SUS score", type="primary"):
        # Odd questions (1,3,5..) score answer-1; even questions score 5-answer. Total x 2.5 = score out of 100.
        score = sum((a - 1) if i % 2 == 0 else (5 - a) for i, a in enumerate(answers)) * 2.5
        st.success(f"SUS score: {score:.1f} / 100 ({'above' if score > 68 else 'below'} the average of 68)")


# =====================================================================
# 5. MAIN PAGE
# =====================================================================
def apply_style(show_background: bool):
    """Load style.css and put the campus photo in the banner / background."""
    photo = ROOT / "assets" / "campus.jpg"
    hero = base64.b64encode(photo.read_bytes()).decode() if photo.exists() else ""
    background = ("background:linear-gradient(rgba(255,255,255,.90),rgba(255,255,255,.95)),var(--hero) center top/cover no-repeat fixed;"
                  if show_background else "background:#fff;")
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css.replace('__HERO__', hero).replace('__BG__', background)}</style>", unsafe_allow_html=True)


# ----- Sidebar: data + filters -----
df, source = load_data()

st.sidebar.subheader("Filters")
faculties = [x for x in list(FACULTIES) + ["Other"] if x in df.faculty.unique()]
sel_faculty = st.sidebar.multiselect("Faculty", faculties, default=faculties)
dept_options = sorted(df[df.faculty.isin(sel_faculty)].department.unique())
sel_dept = st.sidebar.multiselect("Department", dept_options, default=dept_options)
sem_min, sem_max = int(df.semester.min()), int(df.semester.max())
sel_sem = st.sidebar.slider("Semester range", sem_min, sem_max, (sem_min, sem_max)) if sem_min < sem_max else (sem_min, sem_max)
sel_status = st.sidebar.multiselect("Attendance status", STATUS_ORDER, default=STATUS_ORDER)

st.sidebar.subheader("Appearance")
apply_style(st.sidebar.toggle("Campus photo background", value=True))

# Keep only the students that match every filter
f = df[df.faculty.isin(sel_faculty) & df.department.isin(sel_dept)
       & df.semester.between(*sel_sem) & df.attendance_status.isin(sel_status)]

# ----- Top banner -----
st.markdown(f"""<div class="hero"><span class="tag">Student Performance Dashboard</span>
<h1>Quaid-e-Awam University of Engineering, Science &amp; Technology</h1>
<p>Nawabshah, Sindh, Pakistan · Academic Performance Dashboard</p>
<div class="chips"><span class="chip">Data: {escape(source)}</span><span class="chip">{len(f):,} students</span>
<span class="chip">{f.department.nunique()} departments</span><span class="chip">Semesters {sel_sem[0]}–{sel_sem[1]}</span></div></div>""",
            unsafe_allow_html=True)

with st.expander("ℹ️ How to read this dashboard (click to open)"):
    st.markdown(f"""
- **GPA** is out of 4.00. A student with GPA below **{PASS_GPA}** is counted as failing.
- **Attendance rules** decide who can sit the paper:
""")
    rules_box()
    st.markdown("- Use the **filters on the left** to look at one faculty, department or semester.\n"
                "- Every list has a **Download** button, so you can save it as an Excel-readable CSV file.")

# ----- Tabs -----
tabs = st.tabs(["📊 Overview", "📈 More Charts", "📝 Attendance & Eligibility",
                "🏛️ Faculties & Departments", "🎓 Students", "🧪 Teacher Evaluation"])

if f.empty:
    for tab in tabs[:5]:
        with tab:
            st.info("No students match the selected filters. Please change the filters on the left.")
else:
    by_dept = f.groupby(["faculty", "department"], as_index=False).agg(gpa=("gpa", "mean"))
    with tabs[0]:
        tab_overview(f, by_dept)
    with tabs[1]:
        tab_more_charts(f, by_dept)
    with tabs[2]:
        tab_attendance(f)
    with tabs[3]:
        tab_faculties(f, faculties)
    with tabs[4]:
        tab_students(f)
with tabs[5]:
    tab_evaluation()

# ----- Footer -----
st.markdown('<div class="built">Built by <b>Salaar Mastoi</b></div>', unsafe_allow_html=True)
