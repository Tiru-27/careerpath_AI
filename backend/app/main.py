from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, resumes, roadmaps
from app.core.config import settings
from app.db.session import engine
from app.models import Base

app = FastAPI(title=settings.app_name, version="0.1.0", description="Persistent backend for CareerPath AI.")
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
    return {"status": "ok", "mode": "offline-demo" if settings.database_url.startswith("sqlite") else "database"}
