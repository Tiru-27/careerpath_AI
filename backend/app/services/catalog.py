import re

ROLES = {
    "data-analyst": {"title": "Data Analyst", "skills": {"Python": .75, "SQL": .90, "Excel": .80, "Statistics": .75, "Power BI": .70, "Tableau": .55}, "keywords": ["python", "sql", "excel", "statistics", "power bi", "tableau", "data analysis", "dashboard", "analytics"]},
    "full-stack-developer": {"title": "Full-Stack Developer", "skills": {"HTML/CSS": .75, "JavaScript": .85, "React": .75, "Node.js": .75, "SQL": .65, "Git": .70}, "keywords": ["html", "css", "javascript", "react", "node", "sql", "git", "web development", "api"]},
    "ml-engineer": {"title": "ML Engineer", "skills": {"Python": .85, "SQL": .55, "Machine Learning": .90, "Statistics": .80, "Git": .65, "APIs": .60}, "keywords": ["python", "machine learning", "ml", "statistics", "sql", "git", "api", "tensorflow", "pytorch"]},
    "business-analyst": {"title": "Business Analyst", "skills": {"Excel": .80, "SQL": .65, "Communication": .80, "Statistics": .55, "Power BI": .65, "Business Analysis": .85}, "keywords": ["excel", "sql", "communication", "statistics", "power bi", "business analysis", "requirements", "stakeholder", "dashboard"]},
    "devops-engineer": {"title": "DevOps Engineer", "skills": {"Linux": .75, "Git": .80, "Docker": .80, "Cloud": .75, "CI/CD": .80, "Python": .55}, "keywords": ["linux", "git", "docker", "cloud", "ci/cd", "cicd", "python", "aws", "azure", "devops"]},
}

ALIASES = {"python":"Python", "sql":"SQL", "mysql":"SQL", "postgresql":"SQL", "excel":"Excel", "power bi":"Power BI", "powerbi":"Power BI", "tableau":"Tableau", "javascript":"JavaScript", "js":"JavaScript", "html":"HTML/CSS", "css":"HTML/CSS", "react":"React", "reactjs":"React", "node":"Node.js", "node.js":"Node.js", "nodejs":"Node.js", "git":"Git", "github":"Git", "linux":"Linux", "docker":"Docker", "cloud":"Cloud", "aws":"Cloud", "azure":"Cloud", "ci/cd":"CI/CD", "cicd":"CI/CD", "machine learning":"Machine Learning", "ml":"Machine Learning", "statistics":"Statistics", "communication":"Communication", "business analysis":"Business Analysis", "api":"APIs", "apis":"APIs"}


def detect_skills(text: str) -> list[str]:
    return sorted({skill for alias, skill in ALIASES.items() if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text.lower())})


def roadmap_steps(role_slug: str) -> list[tuple[str, str, str, str]]:
    role = ROLES[role_slug]
    skills = list(role["skills"])
    return [
        ("Build foundations", " + ".join(skills[:2]), f"Build a practical foundation in {skills[0]} and {skills[1]}.", f"Create a small project demonstrating {skills[0]} and {skills[1]}."),
        ("Build depth", skills[2], f"Practise {skills[2]} through focused exercises and feedback.", f"Publish a focused {skills[2]} case study."),
        ("Apply", skills[3], f"Use {skills[3]} to solve a realistic problem.", "Document the problem, decisions and outcome."),
        ("Prove", "Portfolio project", "Combine your core skills in one inspectable project.", "Publish a README, demo and project evidence."),
        ("Prepare", "Interview readiness", "Practise role-specific technical and behavioural questions.", "Complete two mock interviews and improve your resume."),
        ("Launch", "Applications", "Tailor applications using your strongest evidence.", "Apply to targeted internships or entry-level roles."),
    ]
