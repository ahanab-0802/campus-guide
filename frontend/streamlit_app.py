"""
frontend/streamlit_app.py
--------------------------
Campus Guide — Streamlit Frontend
Full dashboard for resume building, analysis, PYQ, and profile management.
Communicates with FastAPI backend via REST API calls.
"""

import streamlit as st
import requests
import json
import base64
import os
# ─── API Config ───────────────────────────────────────────────────────────────

API_BASE = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Campus Guide",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
        padding: 2rem; border-radius: 12px;
        color: white; text-align: center; margin-bottom: 2rem;
    }
    .metric-card {
        background: #00ff00; border-radius: 10px;
        padding: 1.2rem; border-left: 4px solid #2b6cb0;
    }
    .success-box {
        background: #c6f6d5; border-radius: 8px;
        padding: 1rem; border-left: 4px solid #38a169;
    }
    .warning-box {
        background: #fefcbf; border-radius: 8px;
        padding: 1rem; border-left: 4px solid #d69e2e;
    }
    .danger-box {
        background: #fed7d7; border-radius: 8px;
        padding: 1rem; border-left: 4px solid #e53e3e;
    }
    div[data-testid="stSidebar"] { background-color: #1a365d; }
    div[data-testid="stSidebar"] * { color: white !important; }
    .stButton>button {
        background-color: #2b6cb0; color: white;
        border-radius: 8px; border: none; font-weight: bold;
    }
    .stButton>button:hover { background-color: #1a365d; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
if "token"     not in st.session_state: st.session_state.token     = None
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "page"      not in st.session_state: st.session_state.page      = "login"


# ─── API Helpers ─────────────────────────────────────────────────────────────

def api_headers():
    """Return authorization headers."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_post(endpoint: str, data: dict, use_auth=True) -> requests.Response:
    headers = api_headers() if use_auth else {}
    return requests.post(f"{API_BASE}{endpoint}", json=data, headers=headers)


def api_get(endpoint: str) -> requests.Response:
    return requests.get(f"{API_BASE}{endpoint}", headers=api_headers())


def api_put(endpoint: str, data: dict) -> requests.Response:
    return requests.put(f"{API_BASE}{endpoint}", json=data, headers=api_headers())


def show_error(msg: str):
    st.markdown(f'<div class="danger-box">❌ {msg}</div>', unsafe_allow_html=True)


def show_success(msg: str):
    st.markdown(f'<div class="success-box">✅ {msg}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: LOGIN / REGISTER
# ════════════════════════════════════════════════════════════════════════════════

def render_auth_page():
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Campus Guide</h1>
        <p>AI-Powered Resume Optimization & Campus Placement Preparation</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    # ── Login ─────────────────────────────────────────────────────────────────
    with tab_login:
        st.subheader("Welcome back!")
        email    = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Login", use_container_width=True, key="btn_login"):
            if email and password:
                try:
                    res = requests.post(
                        f"{API_BASE}/auth/login",
                        json={"email": email, "password": password}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]

                        # Fetch user profile to get name
                        profile_res = requests.get(
                            f"{API_BASE}/auth/profile",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if profile_res.status_code == 200:
                            st.session_state.user_name = profile_res.json()["name"]

                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        show_error(res.json().get("detail", "Login failed."))
                except Exception as e:
                    show_error(f"Cannot connect to server: {e}")
            else:
                show_error("Please enter both email and password.")

    # ── Register ──────────────────────────────────────────────────────────────
    with tab_register:
        st.subheader("Create your account")
        col1, col2 = st.columns(2)
        with col1:
            r_name  = st.text_input("Full Name*", key="r_name")
            r_email = st.text_input("Email*", key="r_email")
            r_phone = st.text_input("Phone", key="r_phone")
            r_pwd   = st.text_input("Password*", type="password", key="r_pwd")
        with col2:
            r_college = st.text_input("College", key="r_college")
            r_year    = st.number_input("Graduation Year", 2020, 2030, 2025, key="r_year")
            r_role    = st.selectbox("Account Type", ["user", "admin"], key="r_role")

        if st.button("Create Account", use_container_width=True, key="btn_register"):
            if r_name and r_email and r_pwd:
                try:
                    res = requests.post(f"{API_BASE}/auth/register", json={
                        "name": r_name, "email": r_email, "phone": r_phone,
                        "password": r_pwd, "role": r_role,
                        "college": r_college, "graduation_year": int(r_year)
                    })
                    if res.status_code == 201:
                        show_success("Account created! Please login.")
                    else:
                        show_error(res.json().get("detail", "Registration failed."))
                except Exception as e:
                    show_error(f"Cannot connect to server: {e}")
            else:
                show_error("Name, email and password are required.")


# ════════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ════════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 🎓 Campus Guide")
        st.markdown(f"👤 **{st.session_state.user_name}**")
        st.markdown("---")

        pages = {
            "🏠 Dashboard":           "dashboard",
            "📄 Build My Resume":     "builder",
            "🔍 Analyze My Resume":   "analyzer",
            "📚 PYQ Repository":      "pyq",
            "✨ Improve My Resume":   "improve",
            "👤 Profile Management":  "profile",
        }

        for label, page_key in pages.items():
            if st.button(label, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token     = None
            st.session_state.user_name = ""
            st.session_state.page      = "login"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def render_dashboard():
    st.markdown(f"""
    <div class="main-header">
        <h1>Welcome to Campus Guide 🎓</h1>
        <h3>Hello, {st.session_state.user_name}! Let's ace your placement.</h3>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    col1, col2, col3 = st.columns(3)
    cards = [
        ("📄", "Build My Resume",    "Generate a professional PDF resume in minutes.", "builder"),
        ("🔍", "Analyze My Resume",  "Get ATS score + ML-powered shortlisting prediction.", "analyzer"),
        ("📚", "PYQ Repository",     "Practice with 1000+ placement questions.", "pyq"),
        ("✨", "Improve My Resume",  "Get NLP suggestions to improve your resume.", "improve"),
        ("📊", "Resume History",     "View your past analyses and scores.", "history"),
        ("👤", "Profile Management", "Update your details and settings.", "profile"),
    ]

    cols = [col1, col2, col3, col1, col2, col3]
    for (icon, title, desc, page), col in zip(cards, cols):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:1rem;">
                <h2>{icon}</h2>
                <h4>{title}</h4>
                <p style="color:#4a5568; font-size:0.9rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {title}", key=f"dash_{page}", use_container_width=True):
                st.session_state.page = page
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: RESUME BUILDER
# ════════════════════════════════════════════════════════════════════════════════

def render_builder():
    st.markdown("## 📄 Resume Builder")
    st.info("Fill in your details below to generate a professionally formatted PDF resume.")

    with st.form("resume_form"):
        st.subheader("Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            name     = st.text_input("Full Name*")
            email    = st.text_input("Email*")
            phone    = st.text_input("Phone*")
        with col2:
            linkedin = st.text_input("LinkedIn Username (optional)")
            github   = st.text_input("GitHub Username (optional)")

        # ── Education ─────────────────────────────────────────────────────────
        st.subheader("Education")
        n_edu = st.number_input("Number of Education Entries", 1, 4, 1)
        education = []
        for i in range(int(n_edu)):
            st.markdown(f"**Entry {i+1}**")
            c1, c2, c3, c4 = st.columns(4)
            education.append({
                "degree":      c1.text_input("Degree", key=f"deg_{i}"),
                "institution": c2.text_input("Institution", key=f"inst_{i}"),
                "year":        c3.text_input("Year", key=f"yr_{i}", value="2020-2024"),
                "cgpa":        c4.text_input("CGPA", key=f"cgpa_{i}", value="8.5"),
            })

        # ── Skills ────────────────────────────────────────────────────────────
        st.subheader("Technical Skills")
        skills_raw = st.text_area("Skills (comma-separated)", "Python, SQL, React, Docker, Machine Learning")
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        # ── Projects ──────────────────────────────────────────────────────────
        st.subheader("Projects")
        n_proj = st.number_input("Number of Projects", 1, 6, 2)
        projects = []
        for i in range(int(n_proj)):
            st.markdown(f"**Project {i+1}**")
            c1, c2, c3 = st.columns(3)
            projects.append({
                "title":        c1.text_input("Title", key=f"ptitle_{i}"),
                "description":  c2.text_input("Description", key=f"pdesc_{i}"),
                "technologies": c3.text_input("Tech Stack", key=f"ptech_{i}"),
            })

        # ── Internships ───────────────────────────────────────────────────────
        st.subheader("Internships (optional)")
        n_intern = st.number_input("Number of Internships", 0, 4, 1)
        internships = []
        for i in range(int(n_intern)):
            st.markdown(f"**Internship {i+1}**")
            c1, c2, c3, c4 = st.columns(4)
            internships.append({
                "company":     c1.text_input("Company", key=f"ic_{i}"),
                "role":        c2.text_input("Role", key=f"ir_{i}"),
                "duration":    c3.text_input("Duration", key=f"id_{i}", value="3 months"),
                "description": c4.text_input("Description", key=f"idesc_{i}"),
            })

        # ── Achievements & Certifications ─────────────────────────────────────
        st.subheader("Achievements & Certifications")
        achievements_raw    = st.text_area("Achievements (one per line)", "Won coding hackathon 2023\nDean's List 2022-23")
        certifications_raw  = st.text_area("Certifications (one per line)", "AWS Cloud Practitioner\nGoogle Data Analytics")
        achievements   = [a.strip() for a in achievements_raw.split("\n") if a.strip()]
        certifications = [c.strip() for c in certifications_raw.split("\n") if c.strip()]

        submitted = st.form_submit_button("📄 Generate PDF Resume", use_container_width=True)

    if submitted:
        if not (name and email and phone):
            show_error("Name, email, and phone are required.")
            return

        payload = {
            "name": name, "email": email, "phone": phone,
            "linkedin": linkedin, "github": github,
            "education": education, "skills": skills,
            "projects": projects, "internships": internships,
            "achievements": achievements, "certifications": certifications
        }

        with st.spinner("Generating your resume PDF..."):
            try:
                res = requests.post(
                    f"{API_BASE}/resume/build",
                    json=payload,
                    headers=api_headers()
                )
                if res.status_code == 200:
                    show_success("Resume generated successfully!")
                    st.download_button(
                        label="⬇️ Download Resume PDF",
                        data=res.content,
                        file_name=f"{name.replace(' ', '_')}_Resume.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    show_error(f"Error: {res.json().get('detail', 'Unknown error')}")
            except Exception as e:
                show_error(f"Connection error: {e}")


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: RESUME ANALYZER
# ════════════════════════════════════════════════════════════════════════════════

def render_analyzer():
    st.markdown("## 🔍 Resume Analyzer")
    st.info("Upload your resume PDF for AI-powered ATS scoring and shortlisting prediction.")

    uploaded = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])

    if uploaded and st.button("🚀 Analyze Resume", use_container_width=True):
        with st.spinner("Analyzing your resume... Running ML models..."):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
                res   = requests.post(
                    f"{API_BASE}/resume/analyze",
                    files=files,
                    headers=api_headers()
                )

                if res.status_code == 200:
                    data = res.json()
                    _display_analysis_results(data)
                else:
                    show_error(res.json().get("detail", "Analysis failed."))
            except Exception as e:
                show_error(f"Connection error: {e}")


def _display_analysis_results(data: dict):
    """Render the resume analysis results in a structured layout."""
    st.markdown("---")
    st.subheader("📊 Analysis Results")

    # ── ATS Score ─────────────────────────────────────────────────────────────
    ats = data.get("ats_score", 0)
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 ATS Score", f"{ats}/100",
                delta="Good" if ats >= 70 else ("Average" if ats >= 50 else "Needs Work"))
    col2.metric("🏷️ Shortlisted", "✅ YES" if data["shortlisted"] else "❌ NO")
    col3.metric("📊 Confidence", f"{data.get('confidence', 0)*100:.1f}%")

    # Progress bar for ATS
    st.markdown(f"**ATS Score Progress:** {ats}/100")
    st.progress(int(ats) / 100)

    ats_color = "success-box" if ats >= 70 else ("warning-box" if ats >= 50 else "danger-box")
    ats_msg   = "Excellent ATS score! You'll pass most filters." if ats >= 70 else \
                ("Decent score. Some improvements needed." if ats >= 50 else \
                 "Low ATS score. Follow suggestions below.")
    st.markdown(f'<div class="{ats_color}">{ats_msg}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Shortlisted = YES ─────────────────────────────────────────────────────
    if data.get("shortlisted"):
        st.markdown('<div class="success-box"><h3>🎉 Great news! You are likely to be shortlisted!</h3></div>',
                    unsafe_allow_html=True)
        st.markdown("### 🎯 Predictions")

        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""
        <div class="metric-card">
            <h4>💼 Job Role</h4>
            <h3 style="color:#2b6cb0;">{data.get("job_role", "N/A")}</h3>
        </div>""", unsafe_allow_html=True)
        col2.markdown(f"""
        <div class="metric-card">
            <h4>💰 Expected Salary</h4>
            <h3 style="color:#38a169;">{data.get("salary_prediction", "N/A")}</h3>
        </div>""", unsafe_allow_html=True)
        col3.markdown(f"""
        <div class="metric-card">
            <h4>🏢 Company Type</h4>
            <h3 style="color:#805ad5;">{data.get("company_type", "N/A")}</h3>
        </div>""", unsafe_allow_html=True)

    # ── Shortlisted = NO ─────────────────────────────────────────────────────
    else:
        st.markdown('<div class="danger-box"><h3>⚠️ Not likely to be shortlisted yet — but here\'s how to improve!</h3></div>',
                    unsafe_allow_html=True)

        if data.get("suggestions"):
            st.markdown("### 💡 Improvement Suggestions")
            for i, tip in enumerate(data["suggestions"], 1):
                st.markdown(f"**{i}.** {tip}")

        if data.get("missing_keywords"):
            st.markdown("### 🔑 Missing Keywords")
            cols = st.columns(min(len(data["missing_keywords"]), 4))
            for col, kw in zip(cols, data["missing_keywords"]):
                col.markdown(f'<span style="background:#fed7d7;padding:4px 10px;border-radius:15px;">{kw}</span>',
                             unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: PYQ REPOSITORY
# ════════════════════════════════════════════════════════════════════════════════

def render_pyq():
    st.markdown("## 📚 PYQ Repository — Placement Practice")

    subject_map = {
        "Quantitative Aptitude": "aptitude",
        "Data Structures & Algorithms": "dsa",
        "Object-Oriented Programming": "oop",
        "Operating Systems": "os",
        "Database Management": "dbms",
        "Computer Networks": "cn"
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        subject_label = st.selectbox("Select Subject", list(subject_map.keys()))
    with col2:
        difficulty = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"])
    with col3:
        limit = st.slider("Questions per page", 5, 50, 10)

    subject = subject_map[subject_label]
    diff_param = difficulty.lower() if difficulty != "All" else None

    if st.button("📖 Load Questions", use_container_width=True):
        url = f"{API_BASE}/pyq/{subject}?limit={limit}"
        if diff_param:
            url += f"&difficulty={diff_param}"

        try:
            res = api_get(f"/pyq/{subject}?limit={limit}" + (f"&difficulty={diff_param}" if diff_param else ""))
            if res.status_code == 200:
                questions = res.json()
                if not questions:
                    st.warning("No questions found for this filter.")
                    return

                st.markdown(f"### Showing {len(questions)} questions for **{subject_label}**")
                for i, q in enumerate(questions, 1):
                    with st.expander(f"Q{i}. {q['question'][:80]}..."):
                        st.markdown(f"**Question:** {q['question']}")

                        if q.get("options"):
                            opts = json.loads(q["options"])
                            st.markdown("**Options:**")
                            for j, opt in enumerate(opts):
                                prefix = ["A", "B", "C", "D"][j]
                                st.markdown(f"&nbsp;&nbsp;&nbsp;**{prefix}.** {opt}")

                        diff_color = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(q["difficulty"], "⚪")
                        st.markdown(f"**Difficulty:** {diff_color} {q['difficulty'].capitalize()}")

                        with st.container():
                            if st.button(f"Show Answer #{i}", key=f"ans_{q['id']}"):
                                st.success(f"✅ Answer: {q.get('answer', 'N/A')}")
                                if q.get("explanation"):
                                    st.info(f"💡 Explanation: {q['explanation']}")
            else:
                show_error(res.json().get("detail", "Failed to load questions."))
        except Exception as e:
            show_error(f"Connection error: {e}")


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: IMPROVE MY RESUME (Rule-Based Tips)
# ════════════════════════════════════════════════════════════════════════════════

def render_improve():
    st.markdown("## ✨ Improve My Resume")
    st.info("Upload your resume to get personalized NLP-based improvement suggestions.")

    uploaded = st.file_uploader("Upload Resume PDF", type=["pdf"], key="improve_upload")

    if uploaded and st.button("🔍 Get Improvement Tips", use_container_width=True):
        with st.spinner("Analyzing resume for improvements..."):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
                res   = requests.post(
                    f"{API_BASE}/resume/analyze",
                    files=files,
                    headers=api_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    st.markdown("### 📋 Resume Improvement Report")

                    # ATS Score summary
                    ats = data.get("ats_score", 0)
                    st.metric("Current ATS Score", f"{ats}/100")
                    st.progress(int(ats) / 100)

                    # Suggestions
                    suggestions = data.get("suggestions", [])
                    if suggestions:
                        st.markdown("### 💡 Personalized Suggestions")
                        for i, tip in enumerate(suggestions, 1):
                            st.markdown(f"""
                            <div class="metric-card" style="margin-bottom:8px;">
                                <b>{i}.</b> {tip}
                            </div>""", unsafe_allow_html=True)
                    else:
                        show_success("Your resume looks great! Only minor improvements needed.")

                    if data.get("missing_keywords"):
                        st.markdown("### 🔑 Add These Keywords")
                        st.write(", ".join(data["missing_keywords"]))

                else:
                    show_error(res.json().get("detail", "Failed to analyze."))
            except Exception as e:
                show_error(f"Connection error: {e}")

    # ── Static Tips ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📘 General Resume Tips")
    general_tips = [
        ("📏 Keep it 1 Page",          "For freshers, keep your resume to one page with relevant content."),
        ("🔢 Quantify Impact",          "Use numbers: '40% faster', '10K users', '3 projects deployed'."),
        ("🎯 Tailor for Each Job",      "Customize your resume keywords for each job description."),
        ("💼 ATS-Friendly Format",      "Use standard section headers. Avoid tables, graphics, and images."),
        ("🔗 Add Links",               "Include GitHub and LinkedIn profile URLs."),
        ("⚡ Use Action Verbs",         "Start bullets with: Developed, Designed, Optimized, Led, Built."),
        ("📚 Certifications Matter",   "AWS, Google, Meta certifications significantly boost your profile."),
        ("🧹 Proofread Everything",    "Spelling/grammar errors are automatic rejections at many companies."),
    ]
    cols = st.columns(2)
    for i, (title, tip) in enumerate(general_tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:10px;">
                <b>{title}</b><br><small>{tip}</small>
            </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: PROFILE MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════════

def render_profile():
    st.markdown("## 👤 Profile Management")

    # ── Fetch current profile ─────────────────────────────────────────────────
    try:
        res  = api_get("/auth/profile")
        if res.status_code != 200:
            show_error("Could not load profile.")
            return
        prof = res.json()
    except Exception as e:
        show_error(f"Connection error: {e}")
        return

    # ── Display current values ────────────────────────────────────────────────
    st.markdown("### Current Profile")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {prof['name']}")
        st.markdown(f"**Email:** {prof['email']}")
        st.markdown(f"**Phone:** {prof.get('phone', '—')}")
    with col2:
        st.markdown(f"**Role:** {prof['role']}")
        st.markdown(f"**College:** {prof.get('college', '—')}")
        st.markdown(f"**Graduation Year:** {prof.get('graduation_year', '—')}")

    st.markdown("---")
    st.markdown("### Update Profile")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name    = st.text_input("Name",    value=prof.get("name", ""))
            new_phone   = st.text_input("Phone",   value=prof.get("phone", "") or "")
            new_college = st.text_input("College", value=prof.get("college", "") or "")
        with col2:
            new_year    = st.number_input("Graduation Year", 2020, 2030,
                                          value=prof.get("graduation_year") or 2025)
            new_pwd     = st.text_input("New Password (leave blank to keep)", type="password")

        if st.form_submit_button("💾 Save Changes", use_container_width=True):
            update_data = {
                "name":            new_name,
                "phone":           new_phone,
                "college":         new_college,
                "graduation_year": int(new_year),
            }
            if new_pwd:
                update_data["password"] = new_pwd

            try:
                upd_res = api_put("/auth/profile/update", update_data)
                if upd_res.status_code == 200:
                    show_success("Profile updated successfully!")
                    st.session_state.user_name = upd_res.json()["name"]
                    st.rerun()
                else:
                    show_error(upd_res.json().get("detail", "Update failed."))
            except Exception as e:
                show_error(f"Connection error: {e}")


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE: RESUME HISTORY
# ════════════════════════════════════════════════════════════════════════════════

def render_history():
    st.markdown("## 📊 Resume Analysis History")
    try:
        res = api_get("/resume/history")
        if res.status_code == 200:
            history = res.json()
            if not history:
                st.info("No resume analyses yet. Go to 'Analyze My Resume' to get started.")
                return

            for r in history:
                status = "✅ Shortlisted" if r.get("shortlisted") else "❌ Not Shortlisted"
                with st.expander(f"📄 {r.get('filename', 'Resume')} — ATS: {r.get('ats_score', 0)}/100 | {status}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("ATS Score",  f"{r.get('ats_score', 0)}/100")
                    col2.metric("Job Role",   r.get("job_role") or "—")
                    col3.metric("Salary",     r.get("salary")   or "—")
                    st.caption(f"Analyzed on: {r.get('uploaded_at', 'Unknown')}")
        else:
            show_error("Could not fetch history.")
    except Exception as e:
        show_error(f"Connection error: {e}")


# ════════════════════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ════════════════════════════════════════════════════════════════════════════════

def main():
    # Not logged in → show auth page
    if not st.session_state.token:
        render_auth_page()
        return

    # Logged in → show sidebar + route to page
    render_sidebar()

    page_router = {
        "dashboard": render_dashboard,
        "builder":   render_builder,
        "analyzer":  render_analyzer,
        "pyq":       render_pyq,
        "improve":   render_improve,
        "profile":   render_profile,
        "history":   render_history,
    }

    page_fn = page_router.get(st.session_state.page, render_dashboard)
    page_fn()


if __name__ == "__main__":
    main()