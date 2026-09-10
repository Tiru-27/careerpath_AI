import os
import re
from datetime import date
from urllib.parse import quote_plus

import requests
import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


st.set_page_config(page_title="CareerPulse", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

API_BASE_URL = os.getenv("CAREERPATH_API_URL", "http://localhost:8000/api/v1").rstrip("/")
MAX_RESUME_BYTES = 10 * 1024 * 1024
MAX_RESUME_PAGES = 25

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

LEARNING_RESOURCES = {
    "Excel": {"title": "Excel for Beginners", "channel": "freeCodeCamp.org", "video_id": "Vl0H-qTclOg", "description": "Build the spreadsheet foundations used in analysis and reporting."},
    "Statistics": {"title": "Statistics for Data Science", "channel": "freeCodeCamp.org", "video_id": "xxpc-HPKN28", "description": "Review the statistics concepts behind evidence-led decisions."},
    "SQL": {"title": "SQL Full Course for Beginners", "channel": "freeCodeCamp.org", "video_id": "HXV3zeQKqGY", "description": "Practise queries, joins and aggregations for real datasets."},
    "Power BI": {"title": "Power BI Full Course", "channel": "Simplilearn", "video_id": "AGrl-H87pRU", "description": "Learn the dashboard and reporting workflow for business metrics."},
    "Python": {"title": "Python for Beginners", "channel": "freeCodeCamp.org", "video_id": "rfscVS0vtbw", "description": "Strengthen Python fundamentals before working with data or models."},
    "HTML/CSS": {"title": "HTML and CSS Full Course", "channel": "SuperSimpleDev", "video_id": "G3e-cpL7ofc", "description": "Create responsive page structure and styling for web projects."},
    "Git": {"title": "Git and GitHub for Beginners", "channel": "Kunal Kushwaha", "video_id": "RGOj5yH7evk", "description": "Build reliable version-control habits and publish your work."},
    "JavaScript": {"title": "JavaScript Algorithms and Data Structures", "channel": "freeCodeCamp.org", "video_id": "PkZNo7MFNFg", "description": "Learn the language fundamentals needed for interactive interfaces."},
    "React": {"title": "React Course for Beginners", "channel": "freeCodeCamp.org", "video_id": "bMknfKXIFA8", "description": "Understand components, state and the foundations of React apps."},
    "Node.js": {"title": "Node.js and Express Full Course", "channel": "freeCodeCamp.org", "video_id": "Oe421EPjeBE", "description": "Build server-side JavaScript services and API foundations."},
    "Machine Learning": {"title": "Machine Learning for Everybody", "channel": "freeCodeCamp.org", "video_id": "i_LwzRVP7bg", "description": "Learn the model-building workflow from data to evaluation."},
    "Docker": {"title": "Docker Tutorial for Beginners", "channel": "TechWorld with Nana", "video_id": "fqMOX6JJhGo", "description": "Package applications consistently for development and deployment."},
    "Linux": {"title": "Linux for Beginners", "channel": "freeCodeCamp.org", "video_id": "sWbUDq4S6Y8", "description": "Practise the command-line foundations used in delivery work."},
    "Cloud": {"title": "AWS Cloud Practitioner Full Course", "channel": "freeCodeCamp.org", "video_id": "SOTamWNgDKc", "description": "Build a practical baseline in cloud concepts and services."},
    "CI/CD": {"title": "GitHub Actions CI/CD Tutorial", "channel": "TechWorld with Nana", "video_id": "R8_veQiYBjI", "description": "Automate testing and delivery with a modern CI/CD workflow."},
    "APIs": {"title": "REST API Tutorial", "channel": "Web Dev Simplified", "video_id": "qbLc5a9jdXo", "description": "Understand how clients and services exchange structured data."},
}

ALIASES = {"python":"Python", "sql":"SQL", "mysql":"SQL", "postgresql":"SQL", "excel":"Excel", "power bi":"Power BI", "powerbi":"Power BI", "tableau":"Tableau", "javascript":"JavaScript", "js":"JavaScript", "html":"HTML/CSS", "css":"HTML/CSS", "react":"React", "reactjs":"React", "node":"Node.js", "node.js":"Node.js", "nodejs":"Node.js", "git":"Git", "github":"Git", "linux":"Linux", "docker":"Docker", "cloud":"Cloud", "aws":"Cloud", "azure":"Cloud", "ci/cd":"CI/CD", "cicd":"CI/CD", "machine learning":"Machine Learning", "ml":"Machine Learning", "statistics":"Statistics", "communication":"Communication", "business analysis":"Business Analysis", "api":"APIs", "apis":"APIs"}

# Curated student-facing guidance.  Certification details are deliberately limited
# to information published by the provider; an empty/variable price is not guessed.
CAREER_GUIDE = {
    "Data Analyst": {
        "overview": "Data analysts turn data into evidence for business decisions, using queries, spreadsheets and clear visual stories.",
        "tools": ["Excel", "SQL", "Power BI", "Tableau", "Python"],
        "interviews": ["Explain one dashboard decision", "Practise SQL joins and aggregations", "Tell a concise data-to-recommendation story"],
        "certifications": [
            {"name": "Google Data Analytics Certificate", "provider": "Google Career Certificates", "level": "Foundational", "prerequisites": "No experience or degree required; Google notes high-school-level maths is sufficient.", "time": "About 3–6 months (Google estimates about 240 hours).", "cost": "US/Canada: US$49/month after a 7-day trial; local pricing may differ.", "link": "https://grow.google/certificates/data-analytics/", "skills": ["Spreadsheets", "SQL", "Tableau", "R", "data cleaning", "data storytelling"], "why": "A structured entry point with a shareable case study for an early portfolio."},
            {"name": "Microsoft Certified: Power BI Data Analyst Associate (PL-300)", "provider": "Microsoft", "level": "Associate", "prerequisites": "Practical Power Query and DAX proficiency is expected by the exam audience profile.", "time": "Microsoft does not prescribe a preparation duration; use its study guide and practice assessment to plan your study.", "cost": "Listed at US$165; the proctored-exam price varies by country/region.", "link": "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/", "skills": ["Data preparation", "data modelling", "DAX", "visualisation", "Power BI security"], "why": "Useful when a role specifically uses Power BI and you can demonstrate dashboard work alongside it."},
        ],
    },
    "Full-Stack Developer": {
        "overview": "Full-stack developers build and maintain user-facing applications, APIs and the data layer that connects them.",
        "tools": ["HTML/CSS", "JavaScript", "React", "Node.js", "SQL", "Git"],
        "interviews": ["Build and explain a small feature", "Practise JavaScript and API fundamentals", "Walk through trade-offs in a deployed project"],
        "certifications": [
            {"name": "Meta Front-End Developer Professional Certificate", "provider": "Meta on Coursera", "level": "Beginner", "prerequisites": "No degree or prior experience required.", "time": "Coursera lists 7 months at 6 hours/week; it is self-paced.", "cost": "See Coursera enrolment options; the provider page does not give one universal price.", "link": "https://www.coursera.org/professional-certificates/meta-front-end-developer", "skills": ["HTML", "CSS", "JavaScript", "React", "responsive layouts", "portfolio projects"], "why": "Useful for building a visible front-end foundation; pair it with an API and database project for full-stack evidence."},
            {"name": "AWS Certified Cloud Practitioner", "provider": "Amazon Web Services", "level": "Foundational", "prerequisites": "AWS positions it as a starting point, including for people with no prior IT or cloud experience.", "time": "AWS provides an exam-prep plan but does not state one required study duration.", "cost": "US$100 exam fee; foreign-exchange and local details are on AWS pricing pages.", "link": "https://aws.amazon.com/certification/certified-cloud-practitioner/", "skills": ["Cloud concepts", "AWS services", "security", "pricing", "support"], "why": "Helpful for understanding the cloud vocabulary behind deployment; it does not replace software projects."},
        ],
    },
    "ML Engineer": {
        "overview": "ML engineers turn data and models into dependable software systems that can be evaluated, deployed and maintained.",
        "tools": ["Python", "SQL", "scikit-learn", "Git", "APIs", "experiment tracking"],
        "interviews": ["Explain validation and leakage", "Defend a model metric", "Discuss how you would deploy and monitor a model"],
        "certifications": [
            {"name": "Google Advanced Data Analytics Certificate", "provider": "Google Career Certificates", "level": "Advanced", "prerequisites": "Foundational data-analytics knowledge is assumed; Google suggests its Data Analytics Certificate for newcomers.", "time": "3–6 months, according to Google.", "cost": "Check the enrolment page for current local pricing; no single global price is published on the overview page.", "link": "https://grow.google/certificates/data-analytics/?advanced=", "skills": ["Python", "Jupyter Notebook", "statistics", "regression", "machine learning", "Tableau"], "why": "A guided bridge from analysis into modelling; an end-to-end deployment project should still be your central proof of engineering ability."},
            {"name": "Microsoft Certified: Azure AI Fundamentals (AI-900)", "provider": "Microsoft", "level": "Fundamentals", "prerequisites": "No formal prerequisite is listed; it is a fundamentals credential.", "time": "Microsoft does not prescribe a preparation duration; use the official learning resources and practice assessment.", "cost": "Listed at US$99; the proctored-exam price varies by country/region.", "link": "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-fundamentals/", "skills": ["AI concepts", "responsible AI", "Azure AI services", "generative AI basics"], "why": "Useful for cloud-AI vocabulary, but it is introductory rather than evidence of production ML engineering."},
        ],
    },
    "Business Analyst": {
        "overview": "Business analysts clarify needs, align stakeholders and turn evidence into requirements and recommendations.",
        "tools": ["Excel", "SQL", "Power BI", "requirements documents", "process maps", "presentations"],
        "interviews": ["Structure a vague business problem", "Explain a stakeholder trade-off", "Present a concise requirements or dashboard case"],
        "certifications": [
            {"name": "Entry Certificate in Business Analysis (ECBA)", "provider": "International Institute of Business Analysis (IIBA)", "level": "Entry", "prerequisites": "No specific eligibility requirements; candidates must agree to IIBA's code and certification terms.", "time": "IIBA does not publish a standard preparation duration; its Learning Journey and practice exam can guide a personal study plan.", "cost": "Up to US$395 including membership, exam and practice exam; IIBA lists student prices from US$315, region-dependent.", "link": "https://www.iiba.org/business-analysis-certifications/ecba/", "skills": ["Business analysis foundations", "requirements", "stakeholder communication", "business analysis practices"], "why": "A role-aligned entry credential; use a process-improvement or requirements case study to make it concrete."},
        ],
    },
    "DevOps Engineer": {
        "overview": "DevOps engineers improve the reliability and repeatability of software delivery through automation, infrastructure and observability.",
        "tools": ["Linux", "Git", "Docker", "CI/CD", "cloud platforms", "monitoring"],
        "interviews": ["Explain a CI/CD pipeline", "Debug a deployment scenario", "Discuss logging, metrics and safe rollback"],
        "certifications": [
            {"name": "AWS Certified Cloud Practitioner", "provider": "Amazon Web Services", "level": "Foundational", "prerequisites": "AWS positions it as a starting point, including for people with no prior IT or cloud experience.", "time": "AWS provides an exam-prep plan but does not state one required study duration.", "cost": "US$100 exam fee; foreign-exchange and local details are on AWS pricing pages.", "link": "https://aws.amazon.com/certification/certified-cloud-practitioner/", "skills": ["Cloud concepts", "AWS services", "security", "pricing", "support"], "why": "A sensible cloud baseline before deeper platform credentials; a working pipeline and containerised deployment matter more for a DevOps portfolio."},
        ],
    },
}

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
.guide-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; margin:.55rem 0; }.guide-card h4 { margin:.1rem 0 .4rem; }.guide-label { color:var(--muted); font-weight:800; font-size:.74rem; letter-spacing:.06em; text-transform:uppercase; }.notice { border-left:4px solid #0ea5a4; background:#ecfeff; border-radius:0 12px 12px 0; padding:.8rem 1rem; color:#155e75; font-size:.9rem; }
/* Streamlit renders buttons differently across releases: style each path explicitly. */
.stButton>button, .stDownloadButton>button { background:linear-gradient(135deg,#625bf6,#4338ca) !important; color:#fff !important; border:1px solid #5b54e6 !important; border-radius:11px !important; font-weight:800 !important; padding:.58rem 1rem !important; box-shadow:0 6px 14px rgba(79,70,229,.17); transition:transform .15s ease,box-shadow .15s ease; }
.stButton>button:hover, .stDownloadButton>button:hover { color:#fff !important; transform:translateY(-1px); box-shadow:0 9px 18px rgba(79,70,229,.24); }
.stButton>button[kind="secondary"], [data-testid="stBaseButton-secondary"] { background:#fff !important; color:#4f46e5 !important; border:1px solid #d9d8ff !important; box-shadow:none !important; }
div[data-testid="stFileUploader"] button { background:#eef2ff !important; color:#4f46e5 !important; border:1px solid #d9d8ff !important; box-shadow:none !important; }
[data-testid="stProgressBar"]>div>div { background:linear-gradient(90deg,#4f46e5,#14b8a6); } [data-testid="stTabs"] [role="tablist"] { gap:.45rem; border-bottom:1px solid #e7eaf2; } [data-testid="stTabs"] button { min-height:4.35rem !important; padding:.55rem .7rem .65rem !important; border-radius:12px 12px 0 0 !important; color:#4d5870 !important; font-weight:900 !important; transition:background .15s ease,color .15s ease,transform .15s ease; } [data-testid="stTabs"] button:hover { background:#eef2ff !important; color:#4f46e5 !important; transform:translateY(-1px); } [data-testid="stTabs"] button p { display:block !important; white-space:normal !important; text-align:center !important; line-height:1.35 !important; font-weight:900 !important; color:inherit !important; } [data-testid="stTabs"] button[aria-selected="true"] { background:#eef2ff !important; color:#4f46e5 !important; box-shadow:inset 0 -3px 0 #4f46e5; } [data-testid="stTabs"] button:nth-child(7), [data-testid="stTabs"] button:nth-child(7) p { color:#4f46e5 !important; }
.momentum-map { display:grid; grid-template-columns:1fr 1fr 1fr; gap:.55rem; margin:1rem 0 1.4rem; }.momentum-step { border-radius:16px; padding:1rem; background:#fff; border:1px solid var(--line); }.momentum-step b { display:block; font-family:'Plus Jakarta Sans'; font-size:1rem; margin:.3rem 0; }.momentum-step.active { background:linear-gradient(145deg,#5350d9,#25296d); border-color:#5350d9; }.momentum-step.active,.momentum-step.active * { color:#fff !important; }.momentum-step .eyebrow { color:#4f46e5 !important; }.momentum-step.active .eyebrow { color:#b8f7ee !important; }
.login-shell { max-width:1040px; margin:7vh auto 0; padding:2.6rem; background:linear-gradient(135deg,#151a35 0%,#30388a 58%,#4f46e5 100%); border-radius:28px; box-shadow:0 24px 60px rgba(37,44,99,.18); }
.login-brand { color:#fff; padding:1.6rem 2rem; background:linear-gradient(145deg,#202753,#4f46e5); border-radius:22px; min-height:360px; }.login-brand h1 { color:#fff !important; font-size:2.6rem !important; line-height:1.08; margin:.8rem 0 1rem; font-weight:800 !important; }.login-brand p { color:#e5e9ff; max-width:390px; font-size:1rem; line-height:1.65; font-weight:600; }.login-brand .eyebrow { color:#b8f7ee !important; font-weight:800; }.login-point { display:flex; gap:.7rem; align-items:flex-start; color:#f2f5ff; margin:1.1rem 0; font-size:.9rem; font-weight:600; }.login-point b { display:block; color:#fff; margin-bottom:.15rem; font-weight:800; }.login-point span { color:#d6dcf7; font-weight:600; }.login-mark { display:inline-grid; place-items:center; width:2.8rem; height:2.8rem; border-radius:13px; background:#fff; color:#4f46e5; font-size:1.35rem; box-shadow:0 10px 22px rgba(0,0,0,.14); }
.login-card { background:#fff; border-radius:20px; padding:1.7rem 1.8rem .9rem; }.login-card h2 { margin:.2rem 0 .35rem; font-size:1.45rem !important; }.login-card p { color:var(--muted); margin-top:0; }.login-card [data-testid="stForm"] { border:0; padding:0; }.login-card [data-testid="stFormSubmitButton"] button { min-height:2.8rem; }.login-demo { color:#788399; font-size:.78rem; text-align:center; margin-top:.8rem; }
.login-card-header { padding:.2rem .2rem .45rem; }.login-card-header h2 { margin:.25rem 0 .35rem !important; font-size:1.45rem !important; }.login-card-header p { color:var(--muted); margin:0; font-weight:600; }
div[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid #e2e6f1 !important; border-radius:22px !important; background:rgba(255,255,255,.88) !important; box-shadow:0 18px 42px rgba(35,44,86,.09) !important; padding:.6rem !important; }
div[data-testid="stForm"] div[data-testid="stTextInput"] > div, div[data-testid="stForm"] [data-baseweb="input"] { position:relative; background:#fff !important; border:1px solid #dfe3ee !important; border-radius:10px !important; overflow:hidden; } div[data-testid="stForm"] div[data-testid="stTextInput"] input, div[data-testid="stForm"] [data-baseweb="input"] input { width:100% !important; min-width:0 !important; flex:1 1 auto !important; background:#fff !important; color:var(--ink) !important; border:0 !important; box-shadow:none !important; font-weight:600 !important; padding-right:3rem !important; } div[data-testid="stForm"] div[data-testid="stTextInput"] input::placeholder, div[data-testid="stForm"] [data-baseweb="input"] input::placeholder { color:#7a8498 !important; opacity:1 !important; font-weight:600 !important; } div[data-testid="stForm"] div[data-testid="stTextInput"] button, div[data-testid="stForm"] [data-baseweb="input"] button { position:absolute !important; right:0 !important; top:0 !important; height:100% !important; flex:0 0 2.75rem !important; width:2.75rem !important; min-width:2.75rem !important; padding:0 !important; background:#fff !important; color:#68738a !important; border:0 !important; box-shadow:none !important; } .stForm label { color:var(--ink) !important; font-weight:800 !important; } div[data-testid="stFormSubmitButton"] button { background:linear-gradient(135deg,#625bf6,#4338ca) !important; color:#fff !important; border:1px solid #5b54e6 !important; font-weight:800 !important; letter-spacing:.01em; }
.auth-mode { display:flex; gap:.75rem; align-items:center; margin:1.1rem 0 .8rem; }.auth-mode-icon { display:grid; place-items:center; width:2rem; height:2rem; border-radius:9px; background:#eef2ff; color:#4f46e5; font-weight:800; }.auth-mode b { display:block; color:var(--ink); font-size:.95rem; font-weight:800; }.auth-mode span:last-child { display:block; color:#5f6b82; font-size:.78rem; margin-top:.15rem; font-weight:600; }.auth-note { display:flex; gap:.5rem; align-items:center; padding:.7rem .8rem; margin-top:1rem; border:1px solid #e6e8f2; border-radius:10px; color:#5f6b82; font-size:.76rem; background:#fafbfe; font-weight:600; }.auth-note strong { color:#4f46e5; }.auth-help { color:#5f6b82; font-size:.78rem; margin:.2rem 0 1rem; font-weight:600; }
@media(max-width:700px) { .hero { padding:1.5rem; }.hero h1 { font-size:1.65rem !important; }.momentum-map { grid-template-columns:1fr; }.login-shell { margin:1rem auto 0; padding:1.2rem; border-radius:20px; }.login-brand { padding:1rem .3rem 1.3rem; }.login-brand h1 { font-size:2rem !important; }.login-card { padding:1.35rem 1.1rem .8rem; } }

/* Shared product UI layer: keeps every existing page in one visual system. */
:root { --ink:#18233d; --muted:#66728a; --brand:#5146e5; --brand-deep:#242052; --aqua:#0ca6a6; --paper:#f6f8fc; --line:#e4e9f3; --soft:#eef2ff; --shadow:0 12px 30px rgba(35,44,86,.07); --shadow-hover:0 18px 38px rgba(53,63,122,.12); }
.stApp { background:radial-gradient(circle at 8% 4%,rgba(112,124,255,.13),transparent 25rem),radial-gradient(circle at 94% 38%,rgba(20,184,166,.08),transparent 22rem),linear-gradient(180deg,#fbfcff 0%,#f5f7fb 100%); }
section.main > div { max-width:1500px; padding-top:1.1rem; }
h1,h2,h3,h4 { color:var(--ink) !important; font-weight:800 !important; }
h2 { margin-top:1.65rem !important; } h3 { margin-top:1.25rem !important; } h4 { margin-top:.8rem !important; }
p,li,.stMarkdown { color:#354159; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#171c36 0%,#252957 100%); border-right:1px solid rgba(255,255,255,.08); box-shadow:8px 0 32px rgba(25,31,72,.10); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#dce3ff !important; }
[data-testid="stSidebar"] .stTextInput input { background:#303866 !important; border:1px solid #505b91 !important; color:#fff !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] div { color:#fff !important; }
.hero { position:relative; overflow:hidden; background:linear-gradient(125deg,#171b3a 0%,#303887 60%,#5146e5 100%); border:1px solid rgba(255,255,255,.10); border-radius:22px; padding:2.15rem 2.35rem; margin:0 0 1.65rem; box-shadow:0 18px 38px rgba(38,45,103,.18); }
.hero:after { content:''; position:absolute; width:17rem; height:17rem; right:-5rem; top:-8rem; border:1px solid rgba(184,247,238,.28); border-radius:50%; box-shadow:0 0 0 2.2rem rgba(184,247,238,.05),0 0 0 4.4rem rgba(184,247,238,.035); }
.hero h1 { position:relative; z-index:1; max-width:850px; font-size:clamp(1.75rem,3vw,2.55rem) !important; line-height:1.12; }
.hero p { position:relative; z-index:1; max-width:760px; color:#d9e0ff !important; font-weight:600; line-height:1.6; }
.eyebrow { position:relative; z-index:1; font-weight:900 !important; }
.card,.role-card,.roadmap-card,.guide-card { background:rgba(255,255,255,.92); border:1px solid var(--line); border-radius:14px; box-shadow:var(--shadow); transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; }
.card:hover,.role-card:hover,.guide-card:hover { transform:translateY(-2px); box-shadow:var(--shadow-hover); border-color:#d4d9f5; }
.card { padding:1.2rem 1.3rem; min-height:112px; }
.metric-label,.guide-label { color:#77839a; font-weight:900; letter-spacing:.08em; }
.metric-value { color:var(--ink); font-size:1.75rem; }
.metric-note,.small { color:#66728a; line-height:1.5; }
.role-card { padding:1.25rem 1.35rem; margin-bottom:.9rem; }
.role-card.top { border:2px solid #7c78ee; background:linear-gradient(145deg,#fff,#f6f5ff); box-shadow:0 14px 30px rgba(81,70,229,.12); }
.score { color:var(--brand); font-size:1.7rem; }
.chip { border:1px solid transparent; font-weight:800; }
.chip.have { background:#e5f9ee; border-color:#c6efd9; color:#147a48; }.chip.gap { background:#fff0ec; border-color:#ffd8cf; color:#ba4a35; }.chip.neutral { background:#eef1ff; border-color:#dfe2ff; color:#4d47c7; }
.roadmap { border-left:3px solid #817cf0; padding-left:1.35rem; margin:1rem 0 .5rem .7rem; }
.roadmap-card { padding:1.15rem 1.25rem; margin-bottom:1.1rem; }
.roadmap-card:before { background:#5b54e6; box-shadow:0 0 0 5px rgba(91,84,230,.10); }
.month { color:var(--brand); font-weight:900; }
.notice { background:#effcfc; border:1px solid #c9eeee; border-left:4px solid var(--aqua); color:#155e75; box-shadow:none; }
.momentum-map { gap:.8rem; }.momentum-step { border:1px solid var(--line); box-shadow:var(--shadow); }.momentum-step.active { background:linear-gradient(145deg,#5751df,#25295f); box-shadow:0 14px 28px rgba(57,57,153,.18); }
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"] button { min-height:2.75rem; border-radius:10px !important; font-weight:900 !important; letter-spacing:.01em; }
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible,input:focus-visible { outline:3px solid rgba(20,184,166,.28) !important; outline-offset:2px; }
div[data-testid="stFileUploader"] { padding:1rem; background:linear-gradient(145deg,#fafbff,#f3f5ff); border:1px dashed #aaa9e9; border-radius:14px; }
div[data-testid="stTextArea"] textarea,div[data-testid="stTextInput"] input { border-radius:10px !important; border-color:#dce2ee !important; background:#fff !important; }
div[data-testid="stTextArea"] textarea:focus,div[data-testid="stTextInput"] input:focus { border-color:#817cf0 !important; box-shadow:0 0 0 3px rgba(81,70,229,.10) !important; }
[data-testid="stTabs"] [role="tablist"] { padding:.35rem .7rem; background:rgba(255,255,255,.72); border:1px solid var(--line); border-radius:15px; box-shadow:0 8px 22px rgba(35,44,86,.05); overflow-x:auto; scrollbar-width:thin; gap:1.65rem !important; }
[data-testid="stTabs"] [role="tablist"] { justify-content:flex-start !important; }
[data-testid="stTabs"] button { min-width:118px !important; min-height:4.4rem !important; margin:0 !important; padding-left:1.15rem !important; padding-right:1.15rem !important; border-radius:11px !important; }
[data-testid="stTabs"] [role="tablist"] > button + button { margin-left:1.4rem !important; }
[data-testid="stTabs"] button[aria-selected="true"] { background:linear-gradient(145deg,#eef0ff,#e2e5ff) !important; box-shadow:inset 0 -3px 0 var(--brand),0 4px 12px rgba(81,70,229,.08) !important; }
[data-testid="stExpander"] { border:1px solid var(--line) !important; border-radius:12px !important; background:rgba(255,255,255,.75) !important; overflow:hidden; }
[data-testid="stExpander"] summary { font-weight:800 !important; color:var(--ink) !important; }
[data-testid="stProgressBar"] { background:#e9edf5; border-radius:99px; overflow:hidden; }
[data-testid="stProgressBar"]>div>div { border-radius:99px; }
[data-testid="stCheckbox"] label,[data-testid="stSlider"] label,[data-testid="stRadio"] label { font-weight:700 !important; color:var(--ink) !important; }
[data-testid="stDialog"] { border:1px solid #dfe3f4 !important; border-radius:20px !important; box-shadow:0 24px 70px rgba(27,35,83,.25) !important; background:#fbfcff !important; }
[data-testid="stDialog"] [data-testid="stForm"] { padding:1rem !important; border:1px solid #e5e8f3 !important; border-radius:15px !important; background:#fff !important; }
[data-testid="stDialog"] [data-testid="stRadio"] > div { gap:.55rem !important; }
[data-testid="stDialog"] [data-testid="stRadio"] label { padding:.7rem .85rem !important; border:1px solid #e1e5f0 !important; border-radius:10px !important; background:#fbfcff !important; transition:background .15s ease,border-color .15s ease,transform .15s ease; }
[data-testid="stDialog"] [data-testid="stRadio"] label:hover { background:#eef1ff !important; border-color:#aaa8ed !important; transform:translateY(-1px); }
[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button { margin-top:.8rem; min-height:3rem; }
[data-testid="stDialog"] [data-testid="stCaptionContainer"] { color:#68738a !important; font-weight:600 !important; }
[data-testid="stProgressBar"] { min-height:.55rem; }
.learning-heading { margin:.95rem 0 .65rem; color:#4f46e5; font-size:.78rem; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
.learning-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.75rem; margin-bottom:.35rem; }
.learning-card { overflow:hidden; background:#fbfcff; border:1px solid #e2e6f2; border-radius:12px; box-shadow:0 5px 14px rgba(35,44,86,.04); }
.learning-card img { display:block; width:100%; aspect-ratio:16/9; object-fit:cover; background:#eef1ff; }.learning-body { padding:.75rem .8rem .85rem; }.learning-title { color:var(--ink); font-weight:800; font-size:.9rem; line-height:1.3; }.learning-channel { color:#68738a; font-size:.72rem; font-weight:800; margin:.2rem 0 .45rem; }.learning-description { color:#5d6a82; font-size:.77rem; line-height:1.45; min-height:2.2rem; }.learning-link { display:inline-block; margin-top:.55rem; color:#4f46e5 !important; font-size:.78rem; font-weight:900; text-decoration:none; }.learning-link:hover { text-decoration:underline; }
.mock-summary { display:grid; grid-template-columns:1.25fr repeat(3,1fr); gap:.75rem; margin:.2rem 0 1rem; }.mock-score-card,.mock-stat-card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; box-shadow:var(--shadow); }.mock-score-card { background:linear-gradient(135deg,#eef0ff,#f8f8ff); border-color:#d9d9ff; }.mock-label { color:#737f97; font-size:.72rem; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }.mock-score { color:#4f46e5; font:800 2.25rem 'Plus Jakarta Sans'; line-height:1.1; margin:.25rem 0; }.mock-stat-value { color:var(--ink); font:800 1.45rem 'Plus Jakarta Sans'; margin:.25rem 0; }.mock-stat-note { color:#68738a; font-size:.78rem; }.mock-result-note { color:#58657d; font-size:.85rem; line-height:1.45; }.question-review { padding:.85rem 1rem; margin:.55rem 0; background:#fff; border:1px solid var(--line); border-left:4px solid #d5dbea; border-radius:0 12px 12px 0; }.question-review.correct { border-left-color:#17a66a; }.question-review.incorrect { border-left-color:#dd654d; }.question-review-title { color:var(--ink); font-weight:800; }.question-review-answer { color:#68738a; font-size:.82rem; margin-top:.25rem; }.question-review-state { float:right; font-size:.75rem; font-weight:900; }.question-review-state.correct { color:#15803d; }.question-review-state.incorrect { color:#c2410c; }
@media(max-width:900px) { section.main > div { padding-left:.8rem; padding-right:.8rem; }.hero { padding:1.55rem 1.35rem; }.card,.role-card,.roadmap-card,.guide-card { border-radius:12px; }.momentum-map { grid-template-columns:1fr; } }
@media(max-width:700px) { .learning-grid,.mock-summary { grid-template-columns:1fr; }.mock-score-card { min-height:auto; } }

/* Final presentation layer: one calm, consistent system across the existing app. */
:root { --ink:#17233f; --muted:#64718a; --brand:#5146e5; --brand-2:#756df3; --aqua:#0eaaa5; --paper:#f7f9fd; --line:#e2e7f1; --surface:#ffffff; --radius-lg:18px; --radius-md:12px; --shadow-soft:0 10px 28px rgba(35,44,86,.065); }
html,body { background:#f7f9fd !important; }
.stApp { background:radial-gradient(700px 360px at 4% -4%,rgba(111,119,245,.12),transparent 70%),radial-gradient(620px 360px at 98% 42%,rgba(14,170,165,.075),transparent 70%),linear-gradient(180deg,#fbfcff 0%,#f5f7fb 100%) !important; }
section.main > div { width:100%; max-width:1480px; padding:1.25rem clamp(.75rem,2.5vw,2.25rem) 3rem; }
h1,h2,h3,h4 { color:var(--ink) !important; font-family:'Plus Jakarta Sans',sans-serif !important; font-weight:800 !important; letter-spacing:-.025em !important; }
h1 { line-height:1.12 !important; } h2 { margin:1.45rem 0 .7rem !important; } h3 { margin:1.1rem 0 .5rem !important; } h4 { margin:.8rem 0 .35rem !important; }
p,li { color:#394761; line-height:1.55; }
.hero { min-height:150px; display:flex; flex-direction:column; justify-content:center; padding:2rem clamp(1.3rem,3vw,2.5rem); margin-bottom:1.7rem; border-radius:var(--radius-lg); background:linear-gradient(120deg,#171c3d 0%,#303987 58%,#5146e5 100%); box-shadow:0 18px 38px rgba(39,47,107,.17); }
.hero:after { width:20rem; height:20rem; right:-7rem; top:-10rem; }
.hero h1 { font-size:clamp(1.8rem,3vw,2.55rem) !important; max-width:900px; }
.hero p { max-width:760px; margin:.5rem 0 0 !important; color:#dce3ff !important; opacity:1; font-weight:600; }
.eyebrow { font-size:.7rem !important; font-weight:900 !important; letter-spacing:.13em !important; }
.card,.role-card,.roadmap-card,.guide-card,.mock-score-card,.mock-stat-card { border-radius:var(--radius-md); border:1px solid var(--line); box-shadow:var(--shadow-soft); }
.card,.role-card,.roadmap-card,.guide-card { background:rgba(255,255,255,.95); }
.card { padding:1.2rem 1.3rem; min-height:112px; }.role-card { padding:1.25rem 1.35rem; }.roadmap-card { padding:1.2rem 1.3rem; }.guide-card { padding:1.05rem 1.2rem; }
.card:hover,.role-card:hover,.guide-card:hover { border-color:#cfd5f4; box-shadow:0 16px 34px rgba(53,63,122,.11); transform:translateY(-2px); transition:all .18s ease; }
.metric-label,.guide-label,.mock-label { color:#78849b; font-weight:900 !important; letter-spacing:.08em; }
.metric-value { color:var(--ink); font-size:1.75rem; }.metric-note,.small { color:#64718a; }
.chip { padding:.38rem .72rem; border-radius:999px; font-weight:800; }
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"] button { min-height:2.8rem !important; padding:.62rem 1.05rem !important; border-radius:10px !important; font-weight:900 !important; box-shadow:0 6px 14px rgba(79,70,229,.14) !important; }
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stFormSubmitButton"] button:hover { transform:translateY(-1px); box-shadow:0 10px 20px rgba(79,70,229,.2) !important; }
[data-testid="stTabs"] [role="tablist"] { display:flex !important; align-items:stretch !important; justify-content:flex-start !important; gap:1rem !important; padding:.45rem .6rem !important; margin-bottom:1.35rem; overflow-x:auto !important; border:1px solid #e0e5f0 !important; border-radius:16px !important; background:rgba(255,255,255,.78) !important; box-shadow:0 8px 22px rgba(35,44,86,.05) !important; }
[data-testid="stTabs"] [role="tab"] { flex:0 0 auto !important; min-width:120px !important; min-height:4.55rem !important; margin:0 !important; padding:.65rem .85rem !important; display:flex !important; align-items:center !important; justify-content:center !important; border-radius:11px !important; color:#536078 !important; }
[data-testid="stTabs"] [role="tab"] + [role="tab"] { margin-left:0 !important; }
[data-testid="stTabs"] [role="tab"] p { display:flex !important; flex-direction:column !important; align-items:center !important; justify-content:center !important; gap:.38rem !important; line-height:1.1 !important; white-space:normal !important; text-align:center !important; color:inherit !important; font-size:.78rem !important; font-weight:900 !important; }
[data-testid="stTabs"] [role="tab"] p strong { display:block !important; order:0 !important; color:inherit !important; font-weight:900 !important; }
[data-testid="stTabs"] [role="tab"] p > :last-child { display:block !important; order:1 !important; font-size:1.12rem !important; line-height:1 !important; }
[data-testid="stTabs"] [role="tab"]:hover { background:#f0f2ff !important; color:var(--brand) !important; transform:translateY(-1px); }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:linear-gradient(145deg,#eef0ff,#e3e5ff) !important; color:var(--brand) !important; box-shadow:inset 0 -3px 0 var(--brand),0 5px 14px rgba(81,70,229,.09) !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#171c38,#252957) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#dce3ff !important; }
[data-testid="stSidebar"] input,[data-testid="stSidebar"] [data-baseweb="select"] { background:#303866 !important; border-color:#535f97 !important; color:#fff !important; }
[data-testid="stExpander"] { border:1px solid var(--line) !important; border-radius:var(--radius-md) !important; background:rgba(255,255,255,.8) !important; }
[data-testid="stExpander"] summary { padding:.8rem 1rem !important; color:var(--ink) !important; font-weight:800 !important; }
div[data-testid="stFileUploader"] { padding:1rem !important; border:1px dashed #aaa9e9 !important; border-radius:var(--radius-md) !important; background:linear-gradient(145deg,#fcfcff,#f3f5ff) !important; }
div[data-testid="stTextArea"] textarea,div[data-testid="stTextInput"] input { min-height:2.8rem; border-radius:10px !important; border-color:#dce2ee !important; }
[data-testid="stProgressBar"] { min-height:.55rem; border-radius:99px; overflow:hidden; background:#e9edf5; }
[data-testid="stProgressBar"]>div>div { border-radius:99px; }

/* Auth surface: native Streamlit blocks stay inside one restrained product card. */
div[data-testid="stVerticalBlockBorderWrapper"] { width:100% !important; padding:1.45rem !important; border:1px solid #e0e5f1 !important; border-radius:22px !important; background:rgba(255,255,255,.92) !important; box-shadow:0 20px 48px rgba(35,44,86,.1) !important; }
.login-brand { min-height:420px; padding:2rem 2.2rem; border-radius:20px; background:linear-gradient(145deg,#1b2149,#4f46e5); box-shadow:0 18px 36px rgba(46,51,130,.18); }
.login-brand h1 { margin:.85rem 0 1rem; font-size:clamp(2rem,3.5vw,2.75rem) !important; }
.login-brand p { color:#e2e7ff; max-width:410px; }
.login-point { margin:1.35rem 0; }
.login-card-header { padding:.1rem .2rem .65rem; }.login-card-header h2 { font-size:1.5rem !important; margin:.3rem 0 .35rem !important; }.login-card-header p { color:var(--muted); font-weight:600; }
.auth-mode { margin:1rem 0 .7rem; }.auth-help { margin-bottom:.9rem; }
div[data-testid="stForm"] div[data-testid="stTextInput"] > div,div[data-testid="stForm"] [data-baseweb="input"] { min-height:2.8rem; border:1px solid #dce2ee !important; border-radius:10px !important; background:#fff !important; }
div[data-testid="stForm"] [data-baseweb="input"] input { min-width:0 !important; padding-right:3.2rem !important; background:#fff !important; color:var(--ink) !important; }
div[data-testid="stForm"] [data-baseweb="input"] input::placeholder { color:#7a8498 !important; opacity:1 !important; }
div[data-testid="stForm"] [data-baseweb="input"] button { width:2.8rem !important; min-width:2.8rem !important; right:0 !important; background:#fff !important; color:#64718a !important; }
.auth-note { margin-top:1rem; border-color:#e2e6f1; background:#f8f9fd; }
@media(max-width:900px) { section.main > div { padding-left:.8rem; padding-right:.8rem; }.login-brand { min-height:auto; }.hero { padding:1.6rem 1.3rem; } }
@media(max-width:700px) { [data-testid="stTabs"] [role="tablist"] { gap:.55rem !important; padding:.35rem !important; } [data-testid="stTabs"] [role="tab"] { min-width:105px !important; min-height:4.35rem !important; } div[data-testid="stVerticalBlockBorderWrapper"] { padding:1rem !important; border-radius:16px !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def init_state():
    defaults = {"authenticated": False, "access_token": "", "user_email": "", "skills": [], "scores": [], "selected_career": None, "profile": {}, "analysed": False, "completed": set(), "mock_result": None, "resume_received": False, "pending_skills": [], "pending_scores": [], "show_mock": False, "raw_resume_text": ""}
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

def extract_pdf_text(file):
    if getattr(file, "size", 0) > MAX_RESUME_BYTES:
        raise ValueError("Resume files must be 10 MB or smaller.")
    reader = PdfReader(file)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF files are not supported.")
    if len(reader.pages) > MAX_RESUME_PAGES:
        raise ValueError("Resume files must contain 25 pages or fewer.")
    return "\n".join(page.extract_text() or "" for page in reader.pages)

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

def resume_coach(text, career):
    """Transparent rubric; this is preparation guidance, not an ATS prediction."""
    text = text or ""
    lower = text.lower()
    required, have, gaps, _ = gap_data(career)
    has_headline = any(word in lower for word in ["summary", "profile", "objective"])
    has_projects = any(word in lower for word in ["project", "portfolio", "github"])
    has_experience = any(word in lower for word in ["experience", "internship", "work history"])
    has_education = any(word in lower for word in ["education", "university", "college", "b.tech", "bachelor"])
    has_metrics = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:%|users|hours|days|projects|clients|records|rows)\b", lower))
    has_link = bool(re.search(r"(?:github\.com|linkedin\.com|https?://)", lower))
    alignment = round(25 * len(have) / len(required))
    sections = 5 * sum([has_headline, has_projects, has_experience, has_education])
    score = min(100, alignment + sections + (20 if has_metrics else 0) + (15 if has_link else 0) + 20)
    suggestions = []
    if not has_headline: suggestions.append(f"Add a 2–3 line summary tailored to {career}, using your strongest verified skills.")
    if not has_projects: suggestions.append("Add a Projects section with problem, action, tools, result and a portfolio/GitHub link.")
    if not has_metrics: suggestions.append("Quantify impact where truthful: dataset size, speed improvement, users, accuracy or project scope.")
    if not has_link: suggestions.append("Add one working GitHub, portfolio or LinkedIn link near your contact details.")
    if gaps: suggestions.append(f"Do not claim unbuilt skills as strengths; instead show a project plan for {', '.join(gaps[:2])}.")
    return score, suggestions, {"Summary": has_headline, "Projects": has_projects, "Experience": has_experience, "Education": has_education, "Measured impact": has_metrics, "Portfolio link": has_link}

def capstone_blueprint(career, skills, gaps):
    guide = CAREER_GUIDE[career]
    toolset = list(dict.fromkeys(skills + guide["tools"]))[:5]
    focus = ", ".join(gaps[:2]) if gaps else "your strongest role skills"
    return {
        "title": f"{career} Evidence Project",
        "problem": f"Choose a small real-world problem and demonstrate {focus} through a measurable solution.",
        "deliverables": ["One-page problem brief with assumptions", "Working project or analysis", "README explaining tools, decisions and limitations", "Two-minute demo or project walkthrough"],
        "tools": toolset,
        "success": "A reviewer can understand the problem, inspect the evidence and see your personal contribution in under five minutes.",
    }

def roadmap_learning_resources(career, focus):
    focus_lower = focus.lower()
    resources = []
    for skill, resource in LEARNING_RESOURCES.items():
        if skill.lower() in focus_lower or (skill == "Machine Learning" and "ml" in focus_lower):
            resources.append(resource)
    if resources:
        return resources[:2]
    query = quote_plus(f"{career} {focus} tutorial")
    return [{
        "title": f"{focus} learning search",
        "channel": "YouTube educational search",
        "video_id": None,
        "url": f"https://www.youtube.com/results?search_query={query}",
        "description": f"Find a focused {focus} lesson aligned to this {career} milestone.",
    }]

def mock_performance(score):
    if score >= 81:
        return "Excellent", "Strong command of the checked concepts.", "have"
    if score >= 61:
        return "Good", "A solid foundation with a few concepts to reinforce.", "have"
    if score >= 41:
        return "Developing", "Review the missed concepts before claiming strong proficiency.", "neutral"
    return "Needs improvement", "Use the roadmap to rebuild these foundations step by step.", "gap"

def hero(title, subtitle):
    st.markdown(f"<section class='hero'><div class='eyebrow'>CareerPulse · Know Your Skills. Find Your Direction.</div><h1>{title}</h1><p>{subtitle}</p></section>", unsafe_allow_html=True)

def api_error(response):
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    return detail or f"The account service returned HTTP {response.status_code}."

def authenticate(email, password):
    response = requests.post(
        f"{API_BASE_URL}/auth/token",
        data={"username": email, "password": password},
        timeout=10,
    )
    if not response.ok:
        raise ValueError(api_error(response))
    return response.json()

def register_account(email, password, display_name):
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": email, "password": password, "display_name": display_name or None},
        timeout=10,
    )
    if not response.ok:
        raise ValueError(api_error(response))
    return response.json()

def start_authenticated_session(email, token):
    st.session_state.authenticated = True
    st.session_state.access_token = token
    st.session_state.user_email = email
    st.rerun()

def render_login_page():
    left, right = st.columns([1.05, .95], gap="large", vertical_alignment="top")
    with left:
        st.markdown("""
        <div class='login-brand'>
            <div class='login-mark'>🎯</div>
            <div class='eyebrow' style='margin-top:1.2rem'>CareerPulse · Know Your Skills. Find Your Direction.</div>
            <h1>Make your next move count.</h1>
            <p>Turn your current skills into a clear, evidence-led path toward the role you want.</p>
            <div class='login-point'><b>01</b><div><b>Know your direction</b><span>See explainable career matches built around your strengths.</span></div></div>
            <div class='login-point'><b>02</b><div><b>Build with momentum</b><span>Follow a practical roadmap with visible proof of progress.</span></div></div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown("<div class='login-card-header'><div class='eyebrow' style='color:#4f46e5 !important'>Secure workspace</div><h2>Your career plan starts here</h2><p>Use your account to access your personalised workspace.</p></div>", unsafe_allow_html=True)
            sign_in, create_account = st.tabs(["↪  Sign in", "＋  Create account"])
            with sign_in:
                st.markdown("<div class='auth-mode'><span class='auth-mode-icon'>↪</span><div><b>Sign in to your workspace</b><span>Continue where you left off.</span></div></div>", unsafe_allow_html=True)
                st.markdown("<div class='auth-help'>Use the email and password connected to your CareerPulse account.</div>", unsafe_allow_html=True)
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                st.markdown("<div class='auth-note'>🔒 <span>Your account details are handled by the CareerPulse API.</span></div>", unsafe_allow_html=True)
                if submitted:
                    normalized_email = email.strip().lower()
                    if not normalized_email or not password:
                        st.warning("Enter both your email and password to sign in.")
                    else:
                        try:
                            auth = authenticate(normalized_email, password)
                            start_authenticated_session(normalized_email, auth["access_token"])
                        except requests.RequestException:
                            st.error("We could not reach the account service. Start the CareerPulse API and try again.")
                        except (ValueError, KeyError) as exc:
                            if str(exc) == "Incorrect email or password":
                                st.error("That email and password do not match an account. Use the exact password you registered, or create a new account.")
                            else:
                                st.error(str(exc))
            with create_account:
                st.markdown("<div class='auth-mode'><span class='auth-mode-icon'>＋</span><div><b>Create your career workspace</b><span>Save your progress under your own account.</span></div></div>", unsafe_allow_html=True)
                st.markdown("<div class='auth-help'>Use a valid email and choose a password with at least 8 characters.</div>", unsafe_allow_html=True)
                with st.form("register_form"):
                    display_name = st.text_input("Name", placeholder="Your name")
                    new_email = st.text_input("Email", placeholder="you@example.com")
                    new_password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                    confirm_password = st.text_input("Confirm password", type="password", placeholder="Repeat your password")
                    registered = st.form_submit_button("Create account", type="primary", use_container_width=True)
                st.markdown("<div class='auth-note'>✨ <span>One account gives you a personal starting point for your career plan.</span></div>", unsafe_allow_html=True)
                if registered:
                    normalized_email = new_email.strip().lower()
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 8:
                        st.error("Use a password with at least 8 characters.")
                    else:
                        try:
                            auth = register_account(normalized_email, new_password, display_name.strip())
                            start_authenticated_session(normalized_email, auth["access_token"])
                        except requests.RequestException:
                            st.error("We could not reach the account service. Start the CareerPulse API and try again.")
                        except (ValueError, KeyError) as exc:
                            if str(exc) == "An account already exists for this email":
                                st.info("This email already has an account. Open the **Sign in** tab and use that account instead.")
                            else:
                                st.error(str(exc))

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

if not st.session_state.authenticated:
    render_login_page()
    st.stop()

with st.sidebar:
    st.markdown("## 🎯 CareerPulse")
    st.caption(st.session_state.user_email)
    if st.button("Sign out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.access_token = ""
        st.session_state.user_email = ""
        st.rerun()
    st.divider()
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

tabs = st.tabs(["**Analyze**  \n✨", "**Career Match**  \n🎯", "**Skill Gap**  \n📊", "**Roadmap**  \n🗺️", "**Mock Test**  \n🧪", "**Progress**  \n🚀", "**Resume Coach**  \n📄", "**Portfolio Lab**  \n🧩"])

with tabs[0]:
    hero("Turn your profile into a career plan.", "Upload a resume or add skills. CareerPulse makes your strongest next move visible in minutes.")
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
                    st.session_state.raw_resume_text = text
                    st.session_state.selected_career = st.session_state.pending_scores[0][0]
                    st.session_state.resume_received = True
                    st.session_state.mock_result = None
                    st.session_state.analysed = False
                    st.session_state.show_mock = True
                    # A new resume must always start with blank quiz answers.
                    for state_key in [key for key in st.session_state if key.startswith("mock_")]:
                        del st.session_state[state_key]
                    st.rerun()
            except Exception:
                st.error("We could not read that PDF. Please try another text-based PDF or paste your skills.")
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
        selected_guide = CAREER_GUIDE[st.session_state.selected_career]
        with st.expander(f"Explore {st.session_state.selected_career} before choosing it"):
            st.write(selected_guide["overview"])
            st.markdown("**Common tools and technologies**")
            st.markdown(chips(selected_guide["tools"], "neutral"), unsafe_allow_html=True)

with tabs[2]:
    hero("Make your next skill move obvious.", "A transparent comparison between your current strengths and the capabilities your target role requires.")
    if not st.session_state.analysed:
        show_empty("Your skill-gap report will appear here", "Complete your analysis first to compare your profile with a target role.")
    else:
        career = st.session_state.selected_career
        guide = CAREER_GUIDE[career]
        required, have, gaps, readiness = gap_data(career)
        st.markdown(f"<div class='notice'><b>Career overview:</b> {guide['overview']}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
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
        report = f"CareerPulse Skill Report\nGenerated: {date.today()}\n\nTarget role: {career}\nReadiness: {readiness}%\n\nStrengths: {', '.join(have) or 'None'}\nPriority gaps: {', '.join(gaps) or 'None'}\n\nNext step: Follow the personalised six-month roadmap."
        st.download_button("Download skill-gap report", report, file_name=f"careerpath_{career.lower().replace(' ', '_')}_report.txt", mime="text/plain")

with tabs[3]:
    hero("Your personalised six-month roadmap.", "Build skills, create evidence and choose certifications only when they strengthen your story—not as a substitute for projects.")
    if not st.session_state.analysed:
        show_empty("Your roadmap will appear here", "Analyse your profile first. It takes less than a minute.")
    else:
        career = st.session_state.selected_career
        guide = CAREER_GUIDE[career]
        _, _, gaps, readiness = gap_data(career)
        st.markdown(f"<div class='card'><div class='metric-label'>Target role · {career}</div><div class='metric-value'>From {readiness}% to application-ready</div><div class='metric-note'>Your priority skills: {', '.join(gaps[:3]) if gaps else 'Keep building your portfolio and interview confidence.'}</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='roadmap'>", unsafe_allow_html=True)
        for number, (phase, focus, detail, project) in enumerate(CAREERS[career]["roadmap"], 1):
            done = number in st.session_state.completed
            mark = "✅ Completed" if done else "Next milestone"
            st.markdown(f"<div class='roadmap-card'><div class='month'>Month {number} · {phase}</div><h3>{focus}</h3><p class='small'>{detail}</p><p><b>Proof of work:</b> {project}</p><span class='chip {'have' if done else 'neutral'}'>{mark}</span></div>", unsafe_allow_html=True)
            resources = roadmap_learning_resources(career, focus)
            st.markdown("<div class='learning-heading'>Recommended learning</div><div class='learning-grid'>", unsafe_allow_html=True)
            resource_cards = []
            for resource in resources:
                watch_url = resource.get("url") or f"https://www.youtube.com/watch?v={resource['video_id']}"
                thumbnail = resource.get("thumbnail") or (f"https://img.youtube.com/vi/{resource['video_id']}/hqdefault.jpg" if resource.get("video_id") else "https://placehold.co/640x360/eef1ff/4f46e5?text=YouTube+Learning")
                resource_cards.append(f"<article class='learning-card'><img src='{thumbnail}' alt='Thumbnail for {resource['title']}'><div class='learning-body'><div class='learning-title'>{resource['title']}</div><div class='learning-channel'>{resource['channel']}</div><div class='learning-description'>{resource['description']}</div><a class='learning-link' href='{watch_url}' target='_blank' rel='noopener noreferrer'>Watch on YouTube ↗</a></div></article>")
            st.markdown("".join(resource_cards) + "</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("### Recommended certifications")
        st.markdown("<div class='notice'><b>How to use this list:</b> These are curated learning and certification options for this path. Details below come from the provider pages linked in the app. Prices, availability and objectives can change—always confirm them with the provider before paying.</div>", unsafe_allow_html=True)
        for cert in guide["certifications"]:
            with st.expander(f"{cert['name']} · {cert['level']}", expanded=False):
                st.markdown(f"<div class='guide-card'><div class='guide-label'>Provider</div><h4>{cert['provider']}</h4><p><b>Why it is useful:</b> {cert['why']}</p></div>", unsafe_allow_html=True)
                left, right = st.columns(2)
                with left:
                    st.markdown("**Level**")
                    st.write(cert["level"])
                    st.markdown("**Prerequisites**")
                    st.write(cert["prerequisites"])
                    st.markdown("**Estimated preparation time**")
                    st.write(cert["time"])
                with right:
                    st.markdown("**Approximate cost**")
                    st.write(cert["cost"])
                    st.markdown("**Skills covered**")
                    st.markdown(chips(cert["skills"], "neutral"), unsafe_allow_html=True)
                    st.link_button("Open official provider page ↗", cert["link"], use_container_width=True)
        st.markdown("### Interview preparation")
        st.caption("Use your roadmap projects as examples; certifications support, but do not replace, clear evidence of ability.")
        for prompt in guide["interviews"]:
            st.markdown(f"- {prompt}")
        st.markdown("### Progression milestones")
        milestones = [
            ("Foundation", "Understand the core tools and explain basic concepts."),
            ("Proof", "Complete the roadmap project and document what you decided and learned."),
            ("Application-ready", "Publish 2 relevant projects, tailor your resume and practise role-specific interview questions."),
        ]
        milestone_cols = st.columns(3)
        for col, (label, detail) in zip(milestone_cols, milestones):
            with col:
                st.markdown(f"<div class='guide-card'><div class='guide-label'>{label}</div><p class='small'>{detail}</p></div>", unsafe_allow_html=True)
        with st.expander("Prototype scope: what is live vs planned"):
            st.markdown("**Implemented now:** curated role data, keyword-based skill detection, explainable matching, a skill-gap view, roadmap projects, progress tracking, and the official-link certification guidance above.")
            st.markdown("**Planned / not connected:** live job-market data, provider catalogue APIs, automatic price updates, credential verification, embeddings/vector search, LLM-generated roadmaps, and a production backend.")

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
            incorrect = result["total"] - result["correct"]
            performance, performance_note, performance_kind = mock_performance(score)
            if score >= 80:
                label, message, kind = "Resume skills verified", "Strong evidence that your claimed core skills are ready to discuss in an interview.", "have"
            elif score >= 50:
                label, message, kind = "Partially verified", "You have a good base. Review the missed concepts before adding strong proficiency claims to your resume.", "neutral"
            else:
                label, message, kind = "Needs strengthening", "Use the roadmap to rebuild the foundations before presenting these skills as strengths.", "gap"
            st.markdown(f"""<div class='mock-summary'>
                <div class='mock-score-card'><div class='mock-label'>Your score</div><div class='mock-score'>{score}%</div><div class='mock-result-note'><b>{performance}</b> · {performance_note}</div></div>
                <div class='mock-stat-card'><div class='mock-label'>Correct</div><div class='mock-stat-value'>{result['correct']}</div><div class='mock-stat-note'>answers</div></div>
                <div class='mock-stat-card'><div class='mock-label'>Incorrect</div><div class='mock-stat-value'>{incorrect}</div><div class='mock-stat-note'>answers</div></div>
                <div class='mock-stat-card'><div class='mock-label'>Total</div><div class='mock-stat-value'>{result['total']}</div><div class='mock-stat-note'>questions</div></div>
            </div>""", unsafe_allow_html=True)
            st.progress(score / 100)
            st.markdown(f"#### <span class='chip {performance_kind}'>{performance}</span> <span class='chip {kind}'>{label}</span>", unsafe_allow_html=True)
            st.write(message)
            st.markdown("### Question review")
            with st.expander("Review answers and explanations", expanded=True):
                for number, (skill, (_, _, correct, explanation)) in enumerate(questions, 1):
                    selected = result["answers"][skill]
                    is_correct = selected == correct
                    state = "Correct" if is_correct else "Incorrect"
                    state_class = "correct" if is_correct else "incorrect"
                    selected_text = f"Your answer: {selected}"
                    correct_text = "" if is_correct else f" · Correct answer: {correct}"
                    st.markdown(f"<div class='question-review {state_class}'><span class='question-review-state {state_class}'>{'✓' if is_correct else '✕'} {state}</span><div class='question-review-title'>Question {number} · {skill}</div><div class='question-review-answer'>{selected_text}{correct_text}</div><div class='question-review-answer'>{explanation}</div></div>", unsafe_allow_html=True)

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

with tabs[6]:
    hero("Make your resume easier to trust.", "A transparent, role-aware checklist that turns your current resume into stronger interview evidence.")
    if not st.session_state.analysed:
        show_empty("Your resume review will appear here", "Analyse a resume first so CareerPulse can tailor the review to a target role.")
    else:
        career = st.session_state.selected_career
        score, suggestions, checks = resume_coach(st.session_state.raw_resume_text, career)
        left, right = st.columns([.78, 1.22], gap="large")
        with left:
            st.markdown(f"<div class='card'><div class='metric-label'>Resume evidence score</div><div class='metric-value'>{score}%</div><div class='metric-note'>Preparation rubric for {career}</div></div>", unsafe_allow_html=True)
            st.progress(score / 100)
            st.caption("This is not a prediction of any employer’s ATS decision.")
        with right:
            st.markdown("#### Evidence checklist")
            checklist_html = "".join(f"<span class='chip {'have' if value else 'gap'}'>{'✓' if value else '→'} {label}</span>" for label, value in checks.items())
            st.markdown(checklist_html, unsafe_allow_html=True)
            st.markdown("#### Highest-impact edits")
            for suggestion in suggestions:
                st.markdown(f"- {suggestion}")
        _, have, gaps, _ = gap_data(career)
        st.markdown("#### Role-targeted summary starter")
        strength_text = ", ".join(have[:3]) or "relevant foundation skills"
        gap_text = ", ".join(gaps[:2]) or "a portfolio project"
        st.code(f"Aspiring {career} with hands-on experience in {strength_text}. Building evidence through practical projects and currently strengthening {gap_text}.", language=None)

with tabs[7]:
    hero("Turn learning into proof of ability.", "Build one explainable capstone that gives judges, recruiters and interviewers something concrete to evaluate.")
    if not st.session_state.analysed:
        show_empty("Your capstone blueprint will appear here", "Complete your analysis first to create a role-specific project brief.")
    else:
        career = st.session_state.selected_career
        _, have, gaps, _ = gap_data(career)
        blueprint = capstone_blueprint(career, have, gaps)
        st.markdown(f"<div class='notice'><b>CareerPulse evidence engine:</b> Rather than only recommending courses, this converts the target role and your gaps into a project a reviewer can inspect.</div>", unsafe_allow_html=True)
        st.markdown(f"### {blueprint['title']}")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**Project challenge**")
            st.write(blueprint["problem"])
            st.markdown("**Suggested toolkit**")
            st.markdown(chips(blueprint["tools"], "neutral"), unsafe_allow_html=True)
        with right:
            st.markdown("**Definition of done**")
            st.write(blueprint["success"])
            st.markdown("**Evidence to publish**")
            for item in blueprint["deliverables"]:
                st.markdown(f"- {item}")
        st.markdown("#### Judge-ready project narrative")
        st.info("“CareerPulse does not stop at a score. It identifies a gap, prescribes a focused learning path, and asks the student to produce inspectable evidence before claiming readiness.”")

# Kept at the end of the script so the modal overlays the fully rendered app.
if st.session_state.resume_received and not st.session_state.analysed and st.session_state.show_mock:
    resume_mock_dialog()
