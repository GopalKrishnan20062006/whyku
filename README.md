# Whyku

Whyku is a local Sudoku tutoring proof of concept. The Python engine calculates candidates, detects conflicts, and validates naked and hidden singles from the current grid. FastAPI validates every submitted board and returns the deduction evidence. React renders the board and five-stage hint ladder. At the reasoning stage, Gemini can select only approved explanation clause IDs; the backend validates those IDs and renders the explanation from server-approved facts. A deterministic template works without an API key or network access.

## Requirements

- Python 3.12 or newer
- Node.js 22.12 or newer and npm
- A modern desktop browser

## Run locally in template mode

Start the backend in PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:EXPLANATION_PROVIDER = "template"
uvicorn app.main:app --reload
```

Start the frontend in a second PowerShell terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`. The frontend proxies `/api` to FastAPI at `http://127.0.0.1:8000`.

## Optional Gemini explanations

The template mode above is offline and needs no credentials. To enable Gemini, copy `backend/.env.example` to `backend/.env` and set `GEMINI_API_KEY` there. The backend reads the optional `GEMINI_MODEL` and `EXPLANATION_TIMEOUT_SECONDS` settings from that file. Never put the key in frontend files or commit `.env`.

## Checks

Run backend tests from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run frontend tests and a production build from `frontend/`:

```powershell
npm test -- --run
npm run build
```

Automated tests use mocked providers and do not call Gemini.

## Project notes

The planning documents and build checklist are in [`devpost/`](devpost/). The offline code map is [`devpost/app-map.html`](devpost/app-map.html). The app uses in-memory game state; reloading resets the selected puzzle.
