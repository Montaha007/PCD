# PCD

PCD is a full‑stack wellness application that helps users log daily habits and wellbeing signals (sleep, lifestyle, mood) and get AI‑assisted insights and recommendations.

It combines a Django REST API (authentication + data logging) with optional AI services (ML predictions, retrieval‑augmented analysis, and agent‑style wellness summaries) and a modern web UI.

## What this project does

- **Accounts & profiles**: Register/login with JWT and manage basic profile preferences.
- **Sleep tracking**: Create sleep logs and receive an insomnia‑risk signal and confidence score.
- **Lifestyle tracking**: Log daily habits (workout, caffeine, screen time, etc.) and get a sleep‑related prediction.
- **Mood journaling**: Save journal entries and generate an AI summary + predicted mood label.
- **Audio therapy recommendations**: Get brainwave/frequency recommendations (used by the UI to generate sound client‑side).
- **Daily wellness analysis (agent pipeline)**: Produce a personalized “what’s going on + what to do next” style plan and cache a daily snapshot.

## Tech stack (high level)

- **Backend**: Django 5 + Django REST Framework
- **Auth**: JWT (SimpleJWT)
- **Data**: PostgreSQL (default dev configuration)
- **AI/ML (optional)**:
  - Classical ML models (scikit‑learn / CatBoost)
  - Vector search via **Qdrant**
  - Knowledge graph connectivity via **Neo4j**
  - LLM inference via **Groq**
  - Remote embeddings via **Hugging Face Inference API**
- **Frontends**:
  - `frontend/`: React + Vite SPA
  - `next-app/`: Next.js app (template included)

## Repository structure

- `mysite/` — Django project settings + root URLs
- `accounts/`, `profiles/`, `sleeplog/`, `lifestyle/`, `mood/`, `audio/` — domain apps
- `ai/` — AI service layer (pipelines, retrieval, agent orchestration)
- `frontend/` — React/Vite client
- `next-app/` — Next.js client (optional / alternative)

## Quick start (local)

### 1) Backend (Django)

Prereqs: Python 3.11+ recommended, PostgreSQL running locally.

```bash
# from repo root
python -m venv .venv
# activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```


### 2) Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

### 3) (Optional) Next.js app

```bash
cd next-app
npm install
npm run dev
```

## Configuration (environment variables)

Create a `.env` file in the repo root for AI integrations. Most core CRUD endpoints work without these, but AI endpoints will require the relevant services.

Common variables:

- `QDRANT_URL`, `QDRANT_API_KEY`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- `GROQ_API_KEY`
- `HF_API_KEY`

Model paths (optional overrides):

- `SLEEP_CLASSIFIER_PATH`, `SLEEP_SCALER_PATH`
- `LIFESTYLE_MODEL_PATH`, `LIFESTYLE_SCALER_PATH`

## Notes

- This repository is currently configured for development (for example: permissive CORS and `DEBUG=True`). Review settings before deploying.
- Audio recommendations are data‑driven; the backend returns frequency targets, and the client generates audio.

## Contact / ownership

If you’re reviewing this project and have questions about the AI pipeline, data model, or UI flows, open an issue or reach out to the repository owner.
