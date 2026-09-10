from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import auth, resumes, roadmaps
from app.core.config import settings
from app.db.session import engine
from app.models import Base

app = FastAPI(title=settings.app_name, version="0.1.0", description="Persistent backend for CareerPulse.")
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(resumes.router, prefix="/api/v1")
app.include_router(roadmaps.router, prefix="/api/v1")


@app.on_event("startup")
def create_local_tables() -> None:
    """Convenient for local/offline demos. Production must run Alembic migrations."""
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable") from exc
    return {"status": "ok", "mode": "offline-demo" if settings.database_url.startswith("sqlite") else "database"}
