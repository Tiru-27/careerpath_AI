from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.catalog import ROLES


def rank_roles(skills: list[str]) -> list[dict]:
    student_text = " ".join(skills) or "student"
    results = []
    for slug, role in ROLES.items():
        required = set(role["skills"])
        have = sorted(set(skills) & required)
        gaps = sorted(required - set(skills))
        direct = len(have) / len(required)
        matrix = TfidfVectorizer().fit_transform([student_text, " ".join(role["keywords"])])
        semantic = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        results.append({"role": slug, "score": round((.7 * direct + .3 * semantic) * 100), "readiness": round(direct * 100), "strengths": have, "gaps": gaps})
    return sorted(results, key=lambda item: item["score"], reverse=True)
