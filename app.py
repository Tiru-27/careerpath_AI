import re
from datetime import date

import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


st.set_page_config(page_title="CareerPath AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

CAREERS = {
    "Data Analyst": {
        "tagline": "Turn data into clear decisions.",
        "skills": {"Python": .75, "SQL": .90, "Excel": .80, "Statistics": .75, "Power BI": .70, "Tableau": .55},
        "keywords": ["python", "sql", "excel", "statistics", "power bi", "tableau", "data analysis", "dashboard", "analytics"],
        "roadmap": [("Build foundations", "Excel + Statistics", "Learn formulas, pivot tables, descriptive statistics and data storytelling.", "Analyse a sales dataset in Excel."), ("Query with confidence", "SQL", "Master SELECT, JOIN, GROUP BY, subqueries and window functions.", "Answer ten business questions with SQL."), ("Visualise insight", "Power BI", "Create a clean, interactive KPI dashboard.", "Publish a sales-performance dashboard."), ("Analyse with Python", "Python for data", "Use Pandas, NumPy and exploratory data analysis.", "Explore a public dataset in a notebook."), ("Prove your work", "Portfolio", "Package two end-to-end analysis projects with clear business stories.", "Publish two case studies on GitHub."), ("Launch", "Interview + applications", "Practise SQL, case-study and behavioural interviews.", "Tailor your resume and apply to internships.")],
    },
    "Full-Stack Developer": {
        "tagline": "Build useful digital products end to end.",
        "skills": {"HTML/CSS": .75, "JavaScript": .85, "React": .75, "Node.js": .75, "SQL": .65, "Git": .70},
        "keywords": ["html", "css", "javascript", "react", "node", "sql", "git", "web development", "api"],
        "roadmap": [("Build foundations", "HTML/CSS + Git", "Create responsive layouts and use Git confidently.", "Ship a portfolio website."), ("Make it interactive", "JavaScript", "Learn DOM, events, async code and modern JavaScript.", "Build a task manager."), ("Build interfaces", "React", "Learn components, state, hooks and routing.", "Create a React dashboard."), ("Build APIs", "Node.js + APIs", "Create REST endpoints and validation.", "Build a small API."), ("Connect + deploy", "SQL + deployment", "Persist application data and deploy safely.", "Deploy a full-stack app."), ("Launch", "Capstone + interview", "Polish one production-style project and practise interviews.", "Present your capstone."),],
    },
    "ML Engineer": {
        "tagline": "Create practical models from real-world data.",
        "skills": {"Python": .85, "SQL": .55, "Machine Learning": .90, "Statistics": .80, "Git": .65, "APIs": .60},
        "keywords": ["python", "machine learning", "ml", "statistics", "sql", "git", "api", "tensorflow", "pytorch"],
        "roadmap": [("Build foundations", "Python + Statistics", "Strengthen Python, probability and hypothesis testing.", "Analyse a real dataset."), ("Learn models", "Machine Learning", "Learn regression, classification and evaluation.", "Train a prediction model."), ("Improve models", "Feature engineering", "Practise clean features and validation.", "Enter a Kaggle-style project."), ("Make it usable", "Model deployment", "Serve a trained model through an API.", "Deploy a prediction API."), ("Work professionally", "MLOps", "Track experiments and version your work.", "Document an experiment."), ("Launch", "Capstone + interview", "Complete one end-to-end ML project.", "Present your model story.")],
    },
    "Business Analyst": {
        "tagline": "Connect business needs with better solutions.",
        "skills": {"Excel": .80, "SQL": .65, "Communication": .80, "Statistics": .55, "Power BI": .65, "Business Analysis": .85},
        "keywords": ["excel", "sql", "communication", "statistics", "power bi", "business analysis", "requirements", "stakeholder", "dashboard"],
        "roadmap": [("Build foundations", "Excel + business analysis", "Practise requirements and spreadsheet analysis.", "Document a process improvement."), ("Query with confidence", "SQL", "Learn SQL for reporting and analysis.", "Build a reporting query set."), ("Visualise insight", "Power BI", "Build a KPI dashboard for stakeholders.", "Create an executive dashboard."), ("Think in cases", "Case studies", "Frame problems and recommend actions.", "Solve two business cases."), ("Prove your work", "Portfolio", "Document dashboards and cases clearly.", "Publish a case-study portfolio."), ("Launch", "Interview + applications", "Practise stakeholder and case interviews.", "Apply to analyst roles.")],
    },
    "DevOps Engineer": {
        "tagline": "Make software delivery reliable and repeatable.",
        "skills": {"Linux": .75, "Git": .80, "Docker": .80, "Cloud": .75, "CI/CD": .80, "Python": .55},
        "keywords": ["linux", "git", "docker", "cloud", "ci/cd", "cicd", "python", "aws", "azure", "devops"],
        "roadmap": [("Build foundations", "Linux + Git", "Learn shell basics and reliable version control.", "Version a small project."), ("Package apps", "Docker", "Containerise a simple application.", "Create a Docker image."), ("Automate delivery", "CI/CD", "Create an automated build and test pipeline.", "Set up GitHub Actions."), ("Deploy", "Cloud", "Deploy an app to a cloud platform.", "Deploy a container."), ("Observe", "Monitoring", "Learn logging, metrics and alerts.", "Add basic monitoring."), ("Launch", "DevOps capstone", "Build a complete deployment pipeline.", "Present your pipeline.")],
    },
}

ALIASES = {"python":"Python", "sql":"SQL", "mysql":"SQL", "postgresql":"SQL", "excel":"Excel", "power bi":"Power BI", "powerbi":"Power BI", "tableau":"Tableau", "javascript":"JavaScript", "js":"JavaScript", "html":"HTML/CSS", "css":"HTML/CSS", "react":"React", "reactjs":"React", "node":"Node.js", "node.js":"Node.js", "nodejs":"Node.js", "git":"Git", "github":"Git", "linux":"Linux", "docker":"Docker", "cloud":"Cloud", "aws":"Cloud", "azure":"Cloud", "ci/cd":"CI/CD", "cicd":"CI/CD", "machine learning":"Machine Learning", "ml":"Machine Learning", "statistics":"Statistics", "communication":"Communication", "business analysis":"Business Analysis", "api":"APIs", "apis":"APIs"}

# Short evidence-based questions used to validate skills mentioned in a resume.
# This is intentionally a knowledge check, not an identity or proctoring system.
QUESTION_BANK = {
    "Python": ("Which Python collection stores key–value pairs?", ["List", "Dictionary", "Tuple", "Set"], "Dictionary", "A dictionary maps a key to a value."),
    "SQL": ("Which SQL clause combines rows from two related tables?", ["JOIN", "GROUP BY", "ORDER BY", "WHERE"], "JOIN", "JOIN combines related rows using a shared field."),
    "Excel": ("Which Excel feature summarises a large table by category?", ["PivotTable", "Freeze Panes", "Find", "Merge Cells"], "PivotTable", "PivotTables group and aggregate data quickly."),
    "Statistics": ("Which measure is least affected by a single extreme value?", ["Mean", "Median", "Range", "Variance"], "Median", "The median is robust to outliers."),
    "Power BI": ("What is the primary purpose of a Power BI dashboard?", ["Visualise and monitor key metrics", "Write Python code", "Store PDFs", "Edit database rows"], "Visualise and monitor key metrics", "Dashboards communicate key metrics and insights visually."),
    "Tableau": ("In Tableau, what is a worksheet used for?", ["Building an individual visualisation", "Writing SQL only", "Installing software", "Sending emails"], "Building an individual visualisation", "Worksheets are the building blocks for Tableau views and dashboards."),
    "HTML/CSS": ("Which technology controls the visual layout and styling of a web page?", ["CSS", "SQL", "Git", "Docker"], "CSS", "CSS controls presentation, layout and responsive styling."),
    "JavaScript": ("Which JavaScript keyword creates a block-scoped variable that can be reassigned?", ["let", "const", "class", "import"], "let", "let is block-scoped and can be reassigned."),
    "React": ("What does React primarily use to describe a UI?", ["Components", "Spreadsheets", "Containers", "SQL joins"], "Components", "React applications are composed from reusable UI components."),
    "Node.js": ("Node.js is mainly used to run JavaScript where?", ["On the server", "Only in Excel", "Only in a browser tab", "Inside Power BI"], "On the server", "Node.js lets JavaScript run outside the browser, commonly for servers and APIs."),
    "Git": ("Which Git command records staged changes in local history?", ["git commit", "git clone", "git status", "git branch"], "git commit", "git commit saves staged changes as a local history point."),
    "Machine Learning": ("What is the usual purpose of a train/test split?", ["Evaluate generalisation on unseen data", "Make the dataset larger", "Remove all features", "Encrypt a model"], "Evaluate generalisation on unseen data", "A held-out test set estimates performance on unseen examples."),
    "APIs": ("What does a REST API commonly exchange with a client?", ["Structured data over HTTP", "Only image files", "Keyboard shortcuts", "Spreadsheet formulas"], "Structured data over HTTP", "REST APIs expose resources through HTTP requests and structured responses."),
    "Communication": ("What is the best first step when explaining an insight to a stakeholder?", ["Adapt the message to their decision and context", "Use maximum jargon", "Show every raw row", "Avoid a conclusion"], "Adapt the message to their decision and context", "Effective communication starts with the audience and the decision they need to make."),
    "Business Analysis": ("A business requirement mainly describes what?", ["The business outcome or need", "Only the database schema", "A programming language", "A colour palette"], "The business outcome or need", "Requirements explain the need and value before a technical solution is chosen."),
    "Linux": ("Which Linux command lists files in the current folder?", ["ls", "cd", "pwd", "mkdir"], "ls", "ls lists directory contents."),
    "Docker": ("What is a Docker image?", ["A reusable blueprint for a container", "A cloud bill", "A Git branch", "A database query"], "A reusable blueprint for a container", "Images package an application and its dependencies to create containers."),
    "Cloud": ("A key benefit of cloud computing is what?", ["On-demand scalable resources", "No internet required", "No cost ever", "Only local storage"], "On-demand scalable resources", "Cloud services can scale resources up or down as demand changes."),
    "CI/CD": ("What is the purpose of continuous integration?", ["Frequently merge and automatically test changes", "Avoid using version control", "Manually deploy every file", "Replace all documentation"], "Frequently merge and automatically test changes", "CI catches integration issues early through frequent automated checks."),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
:root { --ink:#172033; --muted:#68738a; --brand:#4f46e5; --aqua:#0ea5a4; --paper:#f7f8fc; --line:#e7eaf2; }
.stApp { background: var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif; }
h1,h2,h3 { font-family:'Plus Jakarta Sans',sans-serif !important; letter-spacing:-.03em; color:var(--ink); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#171d35,#272c52); }
[data-testid="stSidebar"] * { color:#f6f7ff !important; }
[data-testid="stSidebar"] .stTextInput input { background:#30385f !important; border-color:#4d588a !important; }
.hero { background:radial-gradient(circle at 85% 0,#7775ff 0,transparent 32%),linear-gradient(115deg,#151a35,#30388a); border-radius:24px; padding:2rem 2.2rem; color:#fff; margin:0 0 1.4rem; box-shadow:0 14px 35px rgba(37,44,99,.20); }
.hero h1,.hero p { color:#fff !important; margin:0; }.hero h1 { font-size:2.15rem !important; }.hero p { opacity:.8; margin-top:.45rem; font-size:1.02rem; }
.eyebrow { color:#aeefff !important; font-size:.72rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
.card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.25rem; min-height:110px; box-shadow:0 5px 16px rgba(23,32,51,.035); }
.metric-label { color:var(--muted); font-size:.76rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }.metric-value { color:var(--ink); font:800 1.6rem 'Plus Jakarta Sans'; margin:.25rem 0; }.metric-note { color:#788399; font-size:.82rem; }
.chip { display:inline-block; margin:0 .38rem .42rem 0; padding:.36rem .66rem; border-radius:999px; font-size:.82rem; font-weight:700; }.chip.have { background:#dcfce7; color:#157a42; }.chip.gap { background:#fff0ed; color:#bd4b35; }.chip.neutral { background:#eef2ff; color:#4f46e5; }
.role-card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.2rem; margin-bottom:.8rem; }.role-card.top { border:2px solid #7775ff; box-shadow:0 10px 24px rgba(79,70,229,.10); }.score { color:#4f46e5; font:800 1.55rem 'Plus Jakarta Sans'; float:right; }
.roadmap { border-left:3px solid #817df4; padding-left:1.25rem; margin:.2rem 0 .3rem .65rem; }.roadmap-card { position:relative; background:#fff; border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; margin:0 0 1rem; }.roadmap-card:before { content:''; position:absolute; width:13px; height:13px; background:#6962e9; border-radius:50%; left:-1.72rem; top:1.25rem; border:4px solid var(--paper); }.month { color:#4f46e5; font-weight:800; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }.small { color:var(--muted); font-size:.9rem; }
/* Streamlit renders buttons differently across releases: style each path explicitly. */
.stButton>button, .stDownloadButton>button { background:linear-gradient(135deg,#625bf6,#4338ca) !important; color:#fff !important; border:1px solid #5b54e6 !important; border-radius:11px !important; font-weight:800 !important; padding:.58rem 1rem !important; box-shadow:0 6px 14px rgba(79,70,229,.17); transition:transform .15s ease,box-shadow .15s ease; }
.stButton>button:hover, .stDownloadButton>button:hover { color:#fff !important; transform:translateY(-1px); box-shadow:0 9px 18px rgba(79,70,229,.24); }
.stButton>button[kind="secondary"], [data-testid="stBaseButton-secondary"] { background:#fff !important; color:#4f46e5 !important; border:1px solid #d9d8ff !important; box-shadow:none !important; }
div[data-testid="stFileUploader"] button { background:#eef2ff !important; color:#4f46e5 !important; border:1px solid #d9d8ff !important; box-shadow:none !important; }
[data-testid="stProgressBar"]>div>div { background:linear-gradient(90deg,#4f46e5,#14b8a6); } [data-testid="stTabs"] button { font-weight:750 !important; color:#5b657b !important; }
.momentum-map { display:grid; grid-template-columns:1fr 1fr 1fr; gap:.55rem; margin:1rem 0 1.4rem; }.momentum-step { border-radius:16px; padding:1rem; background:#fff; border:1px solid var(--line); }.momentum-step b { display:block; font-family:'Plus Jakarta Sans'; font-size:1rem; margin:.3rem 0; }.momentum-step.active { background:linear-gradient(145deg,#5350d9,#25296d); border-color:#5350d9; }.momentum-step.active,.momentum-step.active * { color:#fff !important; }.momentum-step .eyebrow { color:#4f46e5 !important; }.momentum-step.active .eyebrow { color:#b8f7ee !important; }
@media(max-width:700px) { .hero { padding:1.5rem; }.hero h1 { font-size:1.65rem !important; }.momentum-map { grid-template-columns:1fr; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def init_state():
    defaults = {"skills": [], "scores": [], "selected_career": None, "profile": {}, "analysed": False, "completed": set(), "mock_result": None, "resume_received": False, "pending_skills": [], "pending_scores": [], "show_mock": False}
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

def extract_pdf_text(file):
    return "\n".join(page.extract_text() or "" for page in PdfReader(file).pages)

def detect_skills(text):
    return sorted({skill for alias, skill in ALIASES.items() if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text.lower())})

def calculate_scores(skills):
    student_text = " ".join(skills) or "student"
    results = []
    for career, data in CAREERS.items():
        required = set(data["skills"])
        direct = len(set(skills) & required) / len(required)
        matrix = TfidfVectorizer().fit_transform([student_text, " ".join(data["keywords"])])
        semantic = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        results.append((career, round((.7 * direct + .3 * semantic) * 100)))
    return sorted(results, key=lambda item: item[1], reverse=True)

def gap_data(career):
    required = list(CAREERS[career]["skills"])
    have = [skill for skill in required if skill in st.session_state.skills]
    gaps = [skill for skill in required if skill not in st.session_state.skills]
    readiness = round(100 * len(have) / len(required))
    return required, have, gaps, readiness

def hero(title, subtitle):
    st.markdown(f"<section class='hero'><div class='eyebrow'>CareerPath AI · Student career copilot</div><h1>{title}</h1><p>{subtitle}</p></section>", unsafe_allow_html=True)

def chips(items, kind="neutral"):
    return "".join(f"<span class='chip {kind}'>{item}</span>" for item in items) or "<span class='small'>Nothing to show yet.</span>"

def show_empty(title, message):
    st.info(f"**{title}** — {message}")

def assessment_questions(career):
    """Prioritise skill claims detected in the resume, then fill from the chosen role."""
    role_skills = [skill for skill in CAREERS[career]["skills"] if skill in QUESTION_BANK]
    source_skills = st.session_state.skills if st.session_state.analysed else st.session_state.pending_skills
    claimed = [skill for skill in role_skills if skill in source_skills]
    remaining = [skill for skill in role_skills if skill not in claimed]
    chosen = (claimed + remaining)[:6]
    return [(skill, QUESTION_BANK[skill]) for skill in chosen]

@st.dialog("🧪 Resume Skill Check")
def resume_mock_dialog():
    """Modal gate shown immediately after a resume is received."""
    career = st.session_state.selected_career
    questions = assessment_questions(career)
    st.markdown(f"**Before we analyse your career fit, answer these {len(questions)} questions.** They check the skills detected from your resume for the likely role: **{career}**.")
    st.caption("No answer is selected for you. Complete every question to continue.")
    with st.form("resume_mock_assessment"):
        answers = {}
        for number, (skill, (question, options, correct, explanation)) in enumerate(questions, 1):
            st.markdown(f"**{number}. {question}**")
            st.caption(f"Resume skill being checked: {skill}")
            answers[skill] = st.radio("Choose one answer", options, index=None, key=f"mock_{career}_{skill}", label_visibility="collapsed")
        submitted = st.form_submit_button("Verify skills & unlock my analysis →", type="primary", use_container_width=True)
    if submitted:
        if any(answer is None for answer in answers.values()):
            st.warning("Please choose one answer for every question before continuing.")
        else:
            correct_count = sum(answers[skill] == question[2] for skill, question in questions)
            percentage = round(correct_count / len(questions) * 100)
            st.session_state.mock_result = {"career": career, "score": percentage, "correct": correct_count, "total": len(questions), "answers": answers}
            st.session_state.skills = st.session_state.pending_skills
            st.session_state.scores = st.session_state.pending_scores
            st.session_state.analysed = True
            st.session_state.show_mock = False
            st.rerun()

init_state()

with st.sidebar:
    st.markdown("## 🎯 CareerPath AI")
    st.caption("Your path from potential to placement.")
    st.divider()
    st.markdown("**STUDENT PROFILE**")
    name = st.text_input("Name", value=st.session_state.profile.get("name", ""), placeholder="e.g. Priya Sharma")
    education = st.text_input("Program / year", value=st.session_state.profile.get("education", ""), placeholder="B.Tech CSE · 3rd year")
    goal = st.selectbox("Career goal", ["Explore my options", *CAREERS.keys()], index=None, placeholder="Choose a goal (optional)")
    st.session_state.profile = {"name": name, "education": education, "goal": goal}
    st.divider()
    st.markdown("**DEMO STORY**")
    st.caption("Resume → skills → best role → gap → roadmap → readiness")
    if st.session_state.analysed:
        st.success(f"Analysis ready · {len(st.session_state.skills)} skills found")
    else:
        st.caption("Start from Analyze to unlock your personalised dashboard.")

tabs = st.tabs(["✨ Analyze", "🎯 Career Match", "📊 Skill Gap", "🗺️ Roadmap", "🧪 Mock Test", "🚀 Progress"])

with tabs[0]:
    hero("Turn your profile into a career plan.", "Upload a resume or add skills. CareerPath makes your strongest next move visible in minutes.")
    left, right = st.columns([1.08, .92], gap="large")
    with left:
        st.markdown("### Start with what you have")
        uploaded = st.file_uploader("Upload your resume", type=["pdf"], help="PDF text is analysed locally in this prototype.")
        manual = st.text_area("Or paste your skills / resume text", placeholder="Example: Python, SQL, Excel, Power BI, Statistics, Git", height=150)
        if st.button("Check resume & begin mock test →", type="primary", use_container_width=True):
            try:
                pdf_text = extract_pdf_text(uploaded) if uploaded else ""
                text = f"{pdf_text}\n{manual}"
                found = detect_skills(text)
                if not found:
                    st.error("We could not recognise a supported skill yet. Try adding skills such as Python, SQL, Excel, Power BI or Git.")
                else:
                    # Hold career results until the resume skill check is submitted.
                    st.session_state.pending_skills = found
                    st.session_state.pending_scores = calculate_scores(found)
                    st.session_state.selected_career = st.session_state.pending_scores[0][0]
                    st.session_state.resume_received = True
                    st.session_state.mock_result = None
                    st.session_state.analysed = False
                    st.session_state.show_mock = True
                    # A new resume must always start with blank quiz answers.
                    for state_key in [key for key in st.session_state if key.startswith("mock_")]:
                        del st.session_state[state_key]
                    st.rerun()
            except Exception as exc:
                st.error(f"We could not read that PDF. Please try another text-based PDF or paste your skills. ({exc})")
    with right:
        st.markdown("### What you’ll get")
        st.markdown("<div class='card'><div class='metric-label'>1 · Career direction</div><div class='metric-note'>Explainable role matches, not a black box.</div><br><div class='metric-label'>2 · Skill-gap clarity</div><div class='metric-note'>Know exactly what to keep and what to learn next.</div><br><div class='metric-label'>3 · Six-month momentum</div><div class='metric-note'>A practical roadmap with portfolio outcomes.</div></div>", unsafe_allow_html=True)
    if st.session_state.resume_received and not st.session_state.analysed:
        st.success("Resume received. Your skill check is ready in the **🧪 Mock Test** tab. Complete it to unlock career analysis.")
        st.markdown("### Skills selected for verification")
        st.markdown(chips(st.session_state.pending_skills, "neutral"), unsafe_allow_html=True)
    elif st.session_state.analysed:
        st.markdown("### Skills detected and verified")
        st.markdown(chips(st.session_state.skills, "have"), unsafe_allow_html=True)

with tabs[1]:
    hero("Your best-fit career directions.", "Each match combines the skills you have with role-specific keywords. Select a role to personalise the rest of your plan.")
    if not st.session_state.analysed:
        show_empty("Your recommendations will appear here", "Analyse a resume or add skills on the Analyze tab first.")
    else:
        cols = st.columns(4)
        top_role, top_score = st.session_state.scores[0]
        for col, label, value, note in [(cols[0], "Skills detected", len(st.session_state.skills), "from your profile"), (cols[1], "Top match", f"{top_score}%", top_role), (cols[2], "Roles explored", len(CAREERS), "curated career paths"), (cols[3], "Plan length", "6 months", "personalised next steps")]:
            with col: st.markdown(f"<div class='card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)
        st.markdown("### Ranked for your profile")
        for index, (career, score) in enumerate(st.session_state.scores[:3], 1):
            active = "top" if career == st.session_state.selected_career else ""
            st.markdown(f"<div class='role-card {active}'><span class='score'>{score}%</span><div class='eyebrow'>#{index} CAREER MATCH</div><h3>{career}</h3><p class='small'>{CAREERS[career]['tagline']}</p></div>", unsafe_allow_html=True)
            if st.button(f"Use {career} as my target", key=f"target_{career}", type="primary" if career == st.session_state.selected_career else "secondary"):
                st.session_state.selected_career = career
                st.rerun()

with tabs[2]:
    hero("Make your next skill move obvious.", "A transparent comparison between your current strengths and the capabilities your target role requires.")
    if not st.session_state.analysed:
        show_empty("Your skill-gap report will appear here", "Complete your analysis first to compare your profile with a target role.")
    else:
        career = st.session_state.selected_career
        required, have, gaps, readiness = gap_data(career)
        a, b, c = st.columns([.9, 1.1, 1.1], gap="large")
        with a:
            st.markdown(f"<div class='card'><div class='metric-label'>{career}</div><div class='metric-value'>{readiness}%</div><div class='metric-note'>role readiness today</div></div>", unsafe_allow_html=True)
            st.progress(readiness / 100)
            st.caption(f"{len(have)} of {len(required)} role skills already in your profile")
        with b:
            st.markdown("#### ✅ Strengths to leverage")
            st.markdown(chips(have, "have"), unsafe_allow_html=True)
            st.caption("Keep demonstrating these in projects, your resume and interviews.")
        with c:
            st.markdown("#### 🔥 Priority to build")
            st.markdown(chips(gaps, "gap"), unsafe_allow_html=True)
            st.caption("Your roadmap is focused around the highest-impact gaps.")
        next_move = gaps[0] if gaps else "a portfolio case study"
        st.markdown(f"""<div class='momentum-map'>
            <div class='momentum-step'><div class='eyebrow'>01 · Your edge</div><b>{len(have)} skills ready</b><span class='small'>Use these strengths in your next project.</span></div>
            <div class='momentum-step active'><div class='eyebrow'>02 · Next best move</div><b>Build {next_move}</b><span class='small'>The clearest step toward {career}.</span></div>
            <div class='momentum-step'><div class='eyebrow'>03 · Destination</div><b>{career}</b><span class='small'>Reach application-ready confidence.</span></div>
        </div>""", unsafe_allow_html=True)
        st.markdown("### Skill-by-skill view")
        for skill in required:
            status = "✓ Ready" if skill in have else "→ Build next"
            colour = "#15803d" if skill in have else "#c2410c"
            st.markdown(f"<div class='card' style='min-height:auto;padding:.75rem 1rem;margin-bottom:.45rem'><b>{skill}</b><span style='float:right;color:{colour};font-weight:700'>{status}</span></div>", unsafe_allow_html=True)
        report = f"CareerPath AI Skill Report\nGenerated: {date.today()}\n\nTarget role: {career}\nReadiness: {readiness}%\n\nStrengths: {', '.join(have) or 'None'}\nPriority gaps: {', '.join(gaps) or 'None'}\n\nNext step: Follow the personalised six-month roadmap."
        st.download_button("Download skill-gap report", report, file_name=f"careerpath_{career.lower().replace(' ', '_')}_report.txt", mime="text/plain")

with tabs[3]:
    hero("Your personalised six-month roadmap.", "Each month turns a career goal into one focused learning outcome and one proof-of-work project.")
    if not st.session_state.analysed:
        show_empty("Your roadmap will appear here", "Analyse your profile first. It takes less than a minute.")
    else:
        career = st.session_state.selected_career
        _, _, gaps, readiness = gap_data(career)
        st.markdown(f"<div class='card'><div class='metric-label'>Target role · {career}</div><div class='metric-value'>From {readiness}% to application-ready</div><div class='metric-note'>Your priority skills: {', '.join(gaps[:3]) if gaps else 'Keep building your portfolio and interview confidence.'}</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='roadmap'>", unsafe_allow_html=True)
        for number, (phase, focus, detail, project) in enumerate(CAREERS[career]["roadmap"], 1):
            done = number in st.session_state.completed
            mark = "✅ Completed" if done else "Next milestone"
            st.markdown(f"<div class='roadmap-card'><div class='month'>Month {number} · {phase}</div><h3>{focus}</h3><p class='small'>{detail}</p><p><b>Proof of work:</b> {project}</p><span class='chip {'have' if done else 'neutral'}'>{mark}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[4]:
    hero("Evidence behind your resume.", "Your skill check opens automatically after a resume is submitted. Here you can review the result and use it to improve your preparation.")
    if not st.session_state.resume_received:
        show_empty("Your mock test will appear here", "Upload a resume or add skills on Analyze. A skill-check popup starts before career analysis.")
    elif not st.session_state.analysed:
        st.info("Your Resume Skill Check is open. Complete the popup to unlock your analysis.")
    else:
        result = st.session_state.mock_result
        career = st.session_state.selected_career
        questions = assessment_questions(career)
        if result and result["career"] == career:
            score = result["score"]
            if score >= 80:
                label, message, kind = "Resume skills verified", "Strong evidence that your claimed core skills are ready to discuss in an interview.", "have"
            elif score >= 50:
                label, message, kind = "Partially verified", "You have a good base. Review the missed concepts before adding strong proficiency claims to your resume.", "neutral"
            else:
                label, message, kind = "Needs strengthening", "Use the roadmap to rebuild the foundations before presenting these skills as strengths.", "gap"
            left, right = st.columns([.85, 1.15], gap="large")
            with left:
                st.markdown(f"<div class='card'><div class='metric-label'>Verification score</div><div class='metric-value'>{score}%</div><div class='metric-note'>{result['correct']} / {result['total']} correct</div></div>", unsafe_allow_html=True)
                st.progress(score / 100)
            with right:
                st.markdown(f"#### <span class='chip {kind}'>{label}</span>", unsafe_allow_html=True)
                st.write(message)
                with st.expander("Review answers and explanations"):
                    for skill, (_, _, correct, explanation) in questions:
                        selected = result["answers"][skill]
                        icon = "✅" if selected == correct else "❌"
                        st.markdown(f"{icon} **{skill}:** Correct answer — **{correct}**. {explanation}")

with tabs[5]:
    hero("Build momentum. Become internship ready.", "Track visible progress through your roadmap and the final actions that turn learning into opportunities.")
    if not st.session_state.analysed:
        show_empty("Your progress tracker will appear here", "Analyse your profile first to unlock a role-specific roadmap.")
    else:
        career = st.session_state.selected_career
        roadmap = CAREERS[career]["roadmap"]
        st.markdown("### Roadmap completion")
        for number, (_, focus, _, _) in enumerate(roadmap, 1):
            checked = st.checkbox(f"Month {number} — {focus}", value=number in st.session_state.completed, key=f"complete_{career}_{number}")
            if checked: st.session_state.completed.add(number)
            else: st.session_state.completed.discard(number)
        project_count = st.slider("Portfolio projects completed", 0, 4, 0)
        resume_ready = st.checkbox("Resume updated for my target role")
        github_ready = st.checkbox("GitHub / portfolio is updated")
        interview_ready = st.checkbox("Completed a mock interview")
        progress = (len(st.session_state.completed) + min(project_count, 2) + int(resume_ready) + int(github_ready) + int(interview_ready)) / 11
        percent = round(progress * 100)
        left, right = st.columns([1, 1])
        with left:
            st.markdown(f"<div class='card'><div class='metric-label'>Internship readiness</div><div class='metric-value'>{percent}%</div><div class='metric-note'>{'Ready to start applying 🚀' if percent >= 75 else 'Keep building — your next milestone is clear.'}</div></div>", unsafe_allow_html=True)
            st.progress(progress)
        with right:
            st.markdown("#### Final readiness checklist")
            st.markdown(chips(["Roadmap momentum", "Portfolio proof", "Targeted resume", "Public profile", "Interview practice"], "neutral"), unsafe_allow_html=True)
            st.caption("Aim for 75%+ before a focused internship application sprint.")

# Kept at the end of the script so the modal overlays the fully rendered app.
if st.session_state.resume_received and not st.session_state.analysed and st.session_state.show_mock:
    resume_mock_dialog()
