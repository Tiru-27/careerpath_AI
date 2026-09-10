from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Resume, Roadmap, RoadmapItem, User
from app.schemas import RoadmapCreate, RoadmapItemOut, RoadmapOut
from app.services.catalog import ROLES, roadmap_steps

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


def roadmap_response(roadmap: Roadmap, db: Session) -> RoadmapOut:
    items = list(db.scalars(select(RoadmapItem).where(RoadmapItem.roadmap_id == roadmap.id).order_by(RoadmapItem.position)))
    return RoadmapOut(id=roadmap.id, role_slug=roadmap.role_slug, status=roadmap.status, items=[RoadmapItemOut.model_validate(item, from_attributes=True) for item in items])


@router.post("", response_model=RoadmapOut, status_code=status.HTTP_201_CREATED)
def create_roadmap(payload: RoadmapCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.role_slug not in ROLES:
        raise HTTPException(status_code=422, detail="Unknown role")
    resume = db.scalar(select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == user.id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    roadmap = Roadmap(user_id=user.id, resume_id=resume.id, role_slug=payload.role_slug)
    db.add(roadmap)
    db.flush()
    for position, (phase, focus, description, project) in enumerate(roadmap_steps(payload.role_slug), 1):
        db.add(RoadmapItem(roadmap_id=roadmap.id, position=position, phase=phase, focus=focus, description=description, project_outcome=project))
    db.commit()
    db.refresh(roadmap)
    return roadmap_response(roadmap, db)


@router.patch("/{roadmap_id}/items/{item_id}/complete", response_model=RoadmapItemOut)
def complete_item(roadmap_id: int, item_id: int, completed: bool = True, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmap = db.scalar(select(Roadmap).where(Roadmap.id == roadmap_id, Roadmap.user_id == user.id))
    item = db.scalar(select(RoadmapItem).where(RoadmapItem.id == item_id, RoadmapItem.roadmap_id == roadmap_id)) if roadmap else None
    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    item.completed, item.completed_at = completed, datetime.utcnow() if completed else None
    db.commit()
    db.refresh(item)
    return RoadmapItemOut.model_validate(item, from_attributes=True)
