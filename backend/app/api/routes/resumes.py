from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import CareerMatch, Resume, SkillProfile, User
from app.schemas import MatchOut, ResumeCreate, ResumeOut
from app.services.catalog import detect_skills
from app.services.matching import rank_roles

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
def create_resume(payload: ResumeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    skills = detect_skills(payload.raw_text)
    if not skills:
        raise HTTPException(status_code=422, detail="No supported skills found. Add clearer skills or use the manual fallback.")
    resume = Resume(user_id=user.id, raw_text=payload.raw_text, file_name=payload.file_name)
    db.add(resume)
    db.flush()
    for skill in skills:
        db.add(SkillProfile(resume_id=resume.id, skill_name=skill))
    matches = rank_roles(skills)
    for match in matches:
        db.add(CareerMatch(resume_id=resume.id, role_slug=match["role"], score=match["score"], readiness=match["readiness"], explanation={"strengths": match["strengths"], "gaps": match["gaps"]}))
    db.commit()
    return ResumeOut(id=resume.id, file_name=resume.file_name, skills=skills, matches=[MatchOut(**match) for match in matches])


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    skills = list(db.scalars(select(SkillProfile.skill_name).where(SkillProfile.resume_id == resume.id)))
    records = list(db.scalars(select(CareerMatch).where(CareerMatch.resume_id == resume.id)))
    matches = [MatchOut(role=record.role_slug, score=record.score, readiness=record.readiness, strengths=record.explanation.get("strengths", []), gaps=record.explanation.get("gaps", [])) for record in sorted(records, key=lambda item: item.score, reverse=True)]
    return ResumeOut(id=resume.id, file_name=resume.file_name, skills=skills, matches=matches)
