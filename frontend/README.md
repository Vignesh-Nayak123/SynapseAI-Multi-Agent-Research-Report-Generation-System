# Multi-Agent Research System Frontend

A lightweight Vite + React interface that talks to the FastAPI backend exposed at `/research`. Use it to submit research prompts, monitor workflow progress, and review the generated draft plus cited sources.

## Getting Started

```bash
cd frontend
cp .env.example .env        # optionally adjust VITE_API_BASE_URL
npm install                 # already done in the repo, but run after clean clones
npm run dev                 # launches Vite on http://localhost:5173
```

Ensure the FastAPI server is running locally (default `uvicorn run:app --reload` via `python run.py`). The frontend expects the backend at the URL set in `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

## Features

- Topic textarea + depth slider to collect `ResearchRequest` payloads.
- Visual status (loading, success, error) for the long-running multi-agent workflow.
- Draft viewer using a pre-formatted block plus an ordered list of returned sources.
- CORS-friendly backend integration (configured in `src/api.py`).

## Production build

```bash
npm run build      # outputs to frontend/dist
npm run preview    # smoke-test the static bundle locally
```

Serve the `dist/` folder behind any static host (Netlify, Vercel, etc.) and proxy `/research` calls to the FastAPI service.
