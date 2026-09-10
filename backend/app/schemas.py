from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResumeCreate(BaseModel):
    raw_text: str = Field(min_length=20, max_length=200_000)
    file_name: str = Field(default="pasted-resume.txt", max_length=255)


class MatchOut(BaseModel):
    role: str
    score: float
    readiness: float
    strengths: list[str]
    gaps: list[str]


class ResumeOut(BaseModel):
    id: int
    file_name: str
    skills: list[str]
    matches: list[MatchOut]


class RoadmapCreate(BaseModel):
    resume_id: int
    role_slug: str


class RoadmapItemOut(BaseModel):
    id: int
    position: int
    phase: str
    focus: str
    description: str
    project_outcome: str
    completed: bool
    completed_at: datetime | None


class RoadmapOut(BaseModel):
    id: int
    role_slug: str
    status: str
    items: list[RoadmapItemOut]
