# CareerPulse — V2

A hackathon prototype for turning a student's resume and skills into career recommendations, a transparent skill-gap report, and a personalized six-month roadmap.

## What the prototype currently does

- Extracts a small, curated vocabulary of skills from pasted text or text-based PDFs.
- Produces explainable weighted career matches, a role skill-gap view, a short skill check, and a six-step roadmap.
- Includes student-facing role context: common tools, project proof-of-work, interview prompts, milestones, and curated certification guidance.
- Adds a transparent Resume Coach rubric and a Portfolio Lab that turns a student’s target role and gaps into inspectable project evidence.
- Shows official certification provider links, stated prerequisites, preparation-time guidance, skills, and prices only where a provider publishes them. Price and availability must be checked on the provider page before purchase.

## Prototype boundaries / future integrations

The app does **not** use a live job-market feed, paid-course catalogue API, verified credential service, LLM, vector database, or production-grade semantic skill model. Certification records are static curated guidance, not personalised eligibility advice or a recommendation to pay for a credential. Those integrations are future work and should be labelled as such in a demo.

## Run locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Open the local address Streamlit displays (normally `http://localhost:8501`).

## Demo flow

1. Start the backend API, then open the Streamlit app and create an account.
2. Complete the profile and upload a PDF or paste skills on **Analyze**.
3. Select the strongest role on **Career Match**.
4. Show the readiness score and priority gaps on **Skill Gap**.
5. Show the tailored six-month plan on **Roadmap**.
6. Open **Recommended certifications** in Roadmap for role-specific, official-source guidance; compare it with your project plan before deciding.
7. Mark milestones complete on **Progress** to show internship readiness updating.
8. Use **Resume Coach** to improve resume evidence and **Portfolio Lab** to create one role-specific capstone brief.

The prototype uses a curated skill vocabulary and explainable weighted matching; it does not claim to be a production AI model.

## Backend foundation — Phase 1

The repository now includes a FastAPI backend in [`backend/`](backend/) that makes the core journey persistent without changing the current Streamlit demo:

- Email/password registration and JWT authentication.
- PostgreSQL-ready tables for users, resume versions, extracted skills, career matches, roadmaps, roadmap items, and milestone completion.
- API routes for creating/retrieving resumes, generating a persisted roadmap, and marking a roadmap item complete.
- Extracted deterministic matching and role-roadmap logic in testable backend services.
- SQLite local/offline mode, PostgreSQL Docker Compose mode, Alembic schema migration, and initial matching tests.

### Run the backend offline

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API docs are then available at `http://localhost:8000/docs`. SQLite is used by default for a no-key, offline demo. For local backend settings, copy the root example into the backend working directory with `Copy-Item ..\.env.example .env`; before deployment, set `ENVIRONMENT=production` and a strong `JWT_SECRET`.

### Run with PostgreSQL

```powershell
docker compose up --build
```

This starts PostgreSQL and applies the included Alembic migration before starting the API. Database credentials are read from `.env`; use a strong password for hosted deployments.

### API flow

1. `POST /api/v1/auth/register` creates an account and returns a bearer token.
2. `POST /api/v1/resumes` stores resume text, extracts supported skills, and persists ranked matches.
3. `POST /api/v1/roadmaps` creates a persistent six-step roadmap for an owned resume.
4. `PATCH /api/v1/roadmaps/{roadmap_id}/items/{item_id}/complete` saves progress.

The Streamlit interface remains the reliable hackathon UI. Its account gate now uses the backend's authenticated endpoints, while the existing student journey remains local session state.

### Connect the Streamlit login to the backend

Run the backend in offline SQLite mode:

```powershell
cd backend
uvicorn app.main:app --reload
```

Then run Streamlit from the project root:

```powershell
streamlit run app.py
```

The app connects to `http://localhost:8000/api/v1` by default. Set `CAREERPATH_API_URL` when the API is hosted elsewhere. Account registration and login use the backend's JWT endpoints; no paid API or external service is required.

The Streamlit uploader is limited to 10 MB and 25 PDF pages. PDFs are parsed in memory and are not written to permanent application storage. The UI's analysis, roadmap progress, and mock-test state remain session-local in the current application; the backend persistence routes are available for the planned persistence migration but are not silently substituted into this existing flow.

## Deployment checklist

This project is a Streamlit application with a separate FastAPI service. Vercel is not a suitable target for the Streamlit UI because Streamlit requires a long-running Python process and WebSocket connection. Use Streamlit Community Cloud, Render, Railway, or another platform that supports persistent Streamlit processes for the UI.

### Streamlit UI

1. Deploy the repository to a Streamlit-compatible host with `app.py` as the entry point.
2. Install the root `requirements.txt`.
3. Set `CAREERPATH_API_URL` to the public backend URL ending in `/api/v1`.
4. The host should run `streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT` (or its platform equivalent).

### FastAPI backend

For a hosted PostgreSQL deployment, copy `.env.example` to `.env` or configure the same values in the platform's secret manager. Required values are:

- `ENVIRONMENT=production`
- `DATABASE_URL`
- `JWT_SECRET` with a strong random value
- `CORS_ORIGINS` containing the public Streamlit URL

For Docker Compose, also set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. Compose waits for PostgreSQL health before running the API migration. Never commit `.env` or replace secret placeholders with real credentials in tracked files.

### Resource policy

Roadmap learning videos are curated static YouTube links matched to each existing roadmap focus. They do not require a YouTube API key, so no API credential is exposed in the UI or repository. If a provider changes a video, update its entry in `LEARNING_RESOURCES` in `app.py`.

### Deployment verification

Before deploying, run these checks from the repository root:

```powershell
\.venv\Scripts\python.exe -m py_compile app.py backend\app\main.py
\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Run the UI with `streamlit run app.py` and the API with `uvicorn app.main:app --host 0.0.0.0 --port $PORT` from `backend/`. Confirm `/health` returns `status: ok` after the database is available. Docker Compose additionally requires Docker Desktop/WSL 2 on Windows and `POSTGRES_PASSWORD`, `JWT_SECRET`, and the other values documented in `.env.example`.
