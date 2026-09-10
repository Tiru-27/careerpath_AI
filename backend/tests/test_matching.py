from app.services.catalog import detect_skills
from app.services.matching import rank_roles


def test_detect_skills_normalises_aliases():
    assert detect_skills("I use Python, PostgreSQL and PowerBI") == ["Power BI", "Python", "SQL"]


def test_data_profile_prefers_data_analyst():
    results = rank_roles(["Python", "SQL", "Excel", "Statistics", "Power BI"])
    assert results[0]["role"] == "data-analyst"
    assert results[0]["readiness"] > 50
