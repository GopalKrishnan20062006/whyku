---
doc: spec
status: approved
---
# Whyku — Technical Spec

## How This Works, In Plain Language

The browser shows the Sudoku board and keeps the selected puzzle, entries, selected cell, and hint step in memory only while the page is open. Whenever the grid changes, React sends it to the Python backend. The Python Sudoku engine checks the board and returns legal candidates, rule conflicts, solution-mismatch warnings, and completion status. When allowed, it also finds and validates a next deduction. React displays these results; it does not calculate candidates or choose moves.

When a player reaches the reasoning step, FastAPI builds a short list of approved explanation clauses from the verified deduction. Gemini can select and arrange only those clause IDs. FastAPI checks every ID and renders the explanation from server-approved facts. If Gemini is missing, over quota, slow, or returns invalid IDs, FastAPI uses a template that works without the network. The solver is separate from Gemini, and automated tests use a mock provider, so neither logic correctness nor tests depend on an external service.

The app has two local parts: React/Vite for the interactive board, and Python/FastAPI for trusted Sudoku logic and explanation rendering. This keeps the important boundary explicit without adding accounts, a database, Docker, or deployment.

## The Core Journey Through the System

1. **Open Whyku:** Vite serves React. React requests puzzle metadata and the default puzzle. FastAPI returns the initial board and backend-computed candidates, never the solution.
2. **Select a puzzle:** React requests the selected puzzle by ID. FastAPI returns its initial board and candidates. React immediately discards the previous game and resets selection and hint progress.
3. **Enter or erase:** React updates the visible cell, keeps it selected, and submits the new grid to FastAPI. The backend validates dimensions, values, and givens; recomputes candidates from Sudoku rules; detects rule conflicts; checks player entries against the known solution; and checks completion. React ignores late responses for older grid states.
4. **Request a hint:** React sends puzzle ID and current grid. FastAPI validates it again. A rule conflict or any solution mismatch blocks hint generation. Otherwise, the engine finds a supported single and validates its evidence record without using the solution to choose the move.
5. **Reveal the ladder:** React shows the five stages from the same backend record, with technique-specific evidence. It masks the target digit until Reveal.
6. **Explain the reasoning:** At the Reasoning stage, React asks FastAPI for an explanation using the puzzle ID and current grid. FastAPI rechecks the state and recomputes the deduction. It sends Gemini only verified facts and approved clauses. Gemini returns clause IDs, not prose; FastAPI validates the list and renders the final text. Any failure returns the deterministic template and a source label.
7. **Apply the move:** The player enters the revealed digit. React clears stale hint evidence, keeps the cell selected, and requests fresh analysis. Only a full grid that matches the solution is marked solved.

PRD refs: **prd.md > The Core Journey**, **Screens and Layout**, **Features and Behavior**, and **States and Boundaries**.

~~~mermaid
flowchart LR
  UI[React board] -->|current grid| API[FastAPI]
  API --> Engine[Python Sudoku engine]
  Engine -->|analysis or verified deduction| API
  API -->|approved facts and clauses| Gemini[Gemini adapter]
  Gemini -->|clause IDs only| API
  API -->|validated server-rendered text or template| UI
~~~

## Stack

- **Frontend:** React and Vite, chosen by the learner for the interactive grid and fast local development. Use JavaScript/JSX, matching the learner's stated experience; use Node.js 22.12+ to satisfy current Vite and Vitest requirements. [React](https://react.dev/learn), [Vite setup and requirements](https://vite.dev/guide/), [Vitest 5 requirements](https://vitest.dev/guide/migration/).
- **Styling:** Tailwind CSS through the official Vite plugin, as chosen by the learner. [Tailwind + Vite](https://tailwindcss.com/docs/installation/using-vite).
- **Backend:** Python 3.12+ and FastAPI. Python keeps the solver independently testable; FastAPI supplies typed JSON request validation. [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/), [Python virtual environments](https://docs.python.org/3/tutorial/venv.html).
- **Gemini adapter:** Google's maintained google-genai Python SDK and Gemini Developer API. Configurable model ID defaults to gemini-3.5-flash-lite; current Google docs confirm that exact stable ID supports structured outputs. [Model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [structured-output support](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [Python SDK](https://ai.google.dev/gemini-api/docs/libraries).
- **Tests:** pytest, FastAPI TestClient + httpx, Vitest, and React Testing Library. Every provider test injects a mock; automated tests make no network calls. [pytest](https://pytest.org/en/latest/getting-started.html), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Vitest](https://vitest.dev/guide/).
- **Dependency versions:** Use current compatible stable releases during the first build slice, then commit frontend/package-lock.json and pin Python dependencies in backend/requirements.txt. This avoids inventing versions before the fresh project is scaffolded while keeping later installs repeatable.

## Where It Runs and How Someone Tries It

Run locally as two development processes. Deployment is out of scope; a local recording is sufficient. The hackathon submission still needs a short demo video and a public GitHub repository.

Requirements: desktop OS, Python 3.12+, Node.js 22.12+, npm, and a modern browser. The template fallback works offline without an API key. Live Gemini explanations need a key in backend/.env. Free-tier quotas vary by account/model and may change; check AI Studio usage before recording. The learner accepted the free-tier data terms for payloads containing only puzzle deduction facts and approved clause IDs.

From the repository root, start the backend in one PowerShell terminal:

~~~powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Put GEMINI_API_KEY in backend/.env for live explanations.
uvicorn app.main:app --reload
~~~

Start the frontend in a second terminal:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Open the URL printed by Vite (normally http://localhost:5173). FastAPI interactive docs are at http://127.0.0.1:8000/docs. Configure Vite to proxy /api to the backend so the browser uses one local origin.

Run backend tests with pytest from backend/; run frontend tests with npm test -- --run from frontend/. These commands use mocks and make no external calls.

For the short demo, open a curated puzzle, request a real supported hint, show its evidence and AI/template badge, enter the digit, and show candidates updating. For fallback, use a test-only or demo-only provider failure switch; do not fake the deduction itself.

## Look and Feel

Carry forward **prd.md > Look and Feel**: warm off-white background, dark ink-like digits, subtle lines, and restrained accent colors. Use soft blue for relevant units, amber for the target, muted/crossed marks for eliminated candidates, and a distinct style for hidden-single candidate positions. Distinguish givens from player entries. Keep hints closed until requested; place hint content beside the board on wide screens and below it on narrow screens. Tailwind styles the React interface and does not affect backend behavior.

## Components

### Puzzle Catalog

Backend-owned static data for about five puzzle IDs, names, difficulty/technique labels, initial grids, and known solutions. Puzzle list and load responses never include solutions. The public repository will contain this proof-of-concept data; solution values are not treated as secrets and digit concealment is for spoiler control. Curated data is validated in tests for a unique solution and a path using supported singles.

Implements **prd.md > Screens and Layout**, **Puzzle selection and board entry**, and **What We're Building**.

### Sudoku Engine

Pure Python rules and deduction logic. It validates board shape/values and givens; computes candidates; detects duplicate and zero-candidate conflicts; finds naked/hidden singles in rows, columns, and boxes; creates and checks deduction records; compares entries to the known solution; and checks completion.

Move selection uses Sudoku candidates only. The known solution is used only for mismatch warnings and solved-state checks, never to choose a hint. A record is valid only if it can be recomputed from the current grid: a naked single has one candidate in its cell; a hidden single has one possible position for its digit in its stated unit. Naked evidence records every peer blocker accounting for all eliminated digits. Hidden evidence records the unit, the one eligible cell, and each other empty position with its digit-matching blocker cells. The backend recomputes and validates these records; records are generated server-side and never trusted from the client.

Selection order is stable: naked singles first in row-major order, then hidden singles in rows, columns, and boxes, with digits ascending within each unit. Contradictions, malformed grids, and zero-candidate cells never produce a hint. Rule conflicts and solution mismatches remain distinct statuses.

The engine must never return a deduction unless it can independently recompute and validate that deduction from the submitted current grid. Tests cover naked and hidden singles in rows, columns, and boxes, including cases where several candidates are eliminated before one remains. Evidence and target coordinates must match the recomputed record exactly.

Implements **prd.md > Puzzle selection and board entry**, **Progressive hints and visual evidence**, and **No supported single, contradiction, and completion**.

### FastAPI Routes

FastAPI is the trust boundary. It rejects malformed grids, unknown puzzle IDs, altered givens, and client-supplied solution/candidate/deduction data. Expected domain states (conflict, mismatch, no supported single, solved) use typed responses; malformed bodies return 422 and unknown puzzle IDs return 404.

Suggested routes:

| Route | Request | Response |
|---|---|---|
| GET /api/puzzles | none | IDs, names, difficulty/technique labels |
| GET /api/puzzles/{id} | puzzle ID | initial grid and computed candidates, no solution |
| POST /api/analysis | puzzle ID and current 9×9 grid | candidates, rule conflicts, mismatch cell coordinates, completion, hint-allowed status |
| POST /api/hints | puzzle ID and current grid | verified deduction/evidence or blocked/no-supported-single status |
| POST /api/hints/explanation | puzzle ID and current grid | rendered explanation, source label and evidence metadata |

For hints and explanations, FastAPI revalidates the current state and recomputes the deduction; it never accepts a deduction record from React as authority. A solution mismatch keeps candidate analysis active but blocks hints and provider calls. Return mismatch cell coordinates only, never the correct digit. A rule conflict is reported separately.

Implements **prd.md > Progressive hints and visual evidence** and **States and Boundaries**.

### Explanation Service and Clause Renderer

An async provider interface accepts verified deduction facts and an approved clause catalog, returning clause IDs only. The server builds the catalog and controls all facts; model selections must be allowed for the current deduction, unique, and within a small maximum. The renderer maps approved IDs to server-authored sentence fragments and inserts verified values. It does not display arbitrary model prose.

The service calls a provider only at the Reasoning level after fresh server validation. It rejects missing, unknown, repeated, or otherwise invalid clause selections. Any missing key, service error/quota, timeout, refusal, parse/schema problem, or invalid selection produces a server-rendered template and source=template. A valid selection produces server-rendered wording and source=ai. The template requires no network or provider package.

Implements **prd.md > Progressive hints and visual evidence** and **Product Decisions**.

### Gemini Provider Adapter

Use google-genai with a structured-output schema whose enum values are only approved clause IDs for the current deduction. Configure the SDK request timeout to the environment value in milliseconds and disable retry attempts so a quota error immediately takes the fallback path. Config:

~~~text
EXPLANATION_PROVIDER=gemini
GEMINI_API_KEY=             # secret; backend/.env only
GEMINI_MODEL=gemini-3.5-flash-lite
EXPLANATION_TIMEOUT_SECONDS=8
~~~

Commit `backend/.env.example` with these variable names and safe sample defaults, leaving `GEMINI_API_KEY` blank or clearly marked as a local secret placeholder. Document that developers copy it to `backend/.env` and add their own key there. Never commit `.env`, real keys, or other secret values; the repository `.gitignore` excludes `.env` and `.env.*` while allowing `.env.example`.

The provider sees only the minimum deduction facts and allowed clauses needed for selection—not the full puzzle, solution grid, or player history. FastAPI applies an 8-second deadline. Quota/service failure, unavailability, timeout, or output rejection immediately uses the template. The provider is replaceable by configuration and another adapter; solver and UI imports never reference Gemini.

For the Google GenAI Python SDK, call models.generate_content with the configured model, a single prompt containing the allowed clause IDs and short descriptions, and a JSON response schema whose clauses field is an array of strings restricted to that request's allow-list. Use GEMINI_API_KEY for API-key authentication. The API method is POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent; request contents and generationConfig.responseMimeType="application/json" plus generationConfig.responseSchema carry the prompt and schema. Consume the response text only as structured clause IDs; never display it directly. [GenerateContent API reference](https://ai.google.dev/api/generate-content), [SDK timeout and retry options](https://googleapis.github.io/python-genai/genai.html).

Implements **prd.md > Product Decisions** and **States and Boundaries**.

### React App and API Client

The app state holds puzzle ID, current 9×9 grid, selected cell, warning-display setting, latest backend analysis, current hint record and level, pending request IDs, and explanation-source status. It exists only in React memory. Puzzle switch resets board, selection, hint progress, and warnings to the selected puzzle's initial values. Reload returns to the default puzzle.

The API client handles /api requests and domain responses. Every grid update submits a new board analysis; increment a local request sequence and ignore any response older than the newest submitted grid. While the newest response is pending, show a subtle updating status and do not present stale evidence as current. Clear hint evidence on every grid change. Keep the entered cell selected and provide mouse/arrow movement.

Implements **prd.md > The Core Journey**, **Screens and Layout**, **Puzzle selection and board entry**, and **States and Boundaries**.

### Board, Controls, and Hint Ladder

Board components render digits and candidate marks from backend results; they do not compute candidates or deductions. Given cells are not editable. Keyboard 1–9 and number-pad input enter into the selected editable cell without moving selection; erase clears it. The hint panel reveals Nudge, Area, Technique, Reasoning, and Reveal from the same deduction record and draws evidence strictly from its fields. The digit stays hidden until Reveal. Show the explanation-source label returned by the API.

Implements **prd.md > Screens and Layout** and **Features and Behavior**.

## Data Model

No database, browser storage, accounts, or backend game sessions. The browser keeps active play in React memory. The backend holds a read-only curated puzzle catalog.

- **Puzzle record (backend):** ID, display name, difficulty/technique tags, initial 81-cell grid, known 81-cell solution. Solutions are never included in client responses.
- **Board request:** puzzle ID and 9×9 integer grid (0 for empty). Server checks dimensions, digit range, puzzle ID, and givens.
- **Analysis response:** candidate digits for cells, rule-conflict cells/reasons, solution-mismatch coordinates, completion state, and whether/why hints are enabled. Never return the expected answer for a mismatching cell.
- **Deduction record:** technique, target cell/digit, unit, supporting candidates/positions or eliminations, and display evidence. Produced and validated by Python; held by React only for the current hint; never accepted back as trusted data.
- **Approved explanation data:** server-generated facts and clause allow-list for a deduction; returned provider clause IDs; server-rendered text; source (ai or template). No free-form model prose reaches the UI.
- **Configuration:** provider, model, timeout, and key from backend environment. No secret is sent to the browser.

Each entry/erase updates React's grid and triggers backend analysis. Switching puzzles resets it; reload returns to default. No progress is saved.

## File Structure

~~~text
whyku/
├── frontend/
│   ├── index.html
│   ├── package.json                 # scripts and frontend dependencies
│   ├── package-lock.json            # exact npm dependency tree
│   ├── vite.config.js               # React/Tailwind and /api proxy
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                  # in-memory app state and journey
│       ├── api/client.js            # API requests/domain responses
│       ├── components/
│       │   ├── SudokuBoard.jsx
│       │   ├── PuzzlePicker.jsx
│       │   ├── NumberPad.jsx
│       │   ├── HintPanel.jsx
│       │   └── StatusMessage.jsx
│       ├── styles.css
│       └── test/                    # Vitest + React Testing Library
├── backend/
│   ├── .env                         # local secret/config; gitignored
│   ├── .env.example                 # secret-free sample; committed
│   ├── requirements.txt             # pinned backend dependencies
│   ├── app/
│   │   ├── main.py                  # FastAPI app and route wiring
│   │   ├── schemas.py               # Pydantic request/response types
│   │   ├── config.py                # env config and defaults
│   │   ├── puzzles/
│   │   │   ├── catalog.py           # curated boards and solutions
│   │   │   └── validation.py        # curated puzzle checks
│   │   ├── sudoku/
│   │   │   ├── candidates.py
│   │   │   ├── singles.py
│   │   │   ├── records.py
│   │   │   └── completion.py
│   │   ├── explanations/
│   │   │   ├── protocol.py          # provider interface
│   │   │   ├── gemini.py            # Gemini adapter
│   │   │   ├── clauses.py           # approved facts/clauses
│   │   │   ├── renderer.py          # server text and template
│   │   │   └── service.py           # timeout/validation/fallback
│   │   ├── routes/
│   │   │   ├── puzzles.py
│   │   │   ├── analysis.py
│   │   │   └── hints.py
│   │   └── tests/
│   │       ├── test_candidates.py
│   │       ├── test_singles.py
│   │       ├── test_records.py
│   │       ├── test_api.py
│   │       └── test_explanations.py
├── devpost/
│   ├── scope.md
│   ├── prd.md
│   └── spec.md
├── .gitignore                       # ignores .env and learner profile
└── README.md                        # setup, tests and demo instructions
~~~

## Verification Plan

- **Python engine tests:** candidate calculation and rule conflicts; naked and hidden singles in rows, columns, and boxes; multiple-candidate-elimination evidence; record validation by recomputation; zero-candidate contradictions; solved/full-incorrect distinction; curated puzzle uniqueness and supported-technique progression. Assert no deduction is returned unless its target and evidence are independently supported by the current grid.
- **Mismatch tests separate from rule conflicts:** a locally legal wrong digit with no row/column/box duplicate is still flagged; candidates continue to update; hints are blocked; the provider mock has zero calls. Correcting or erasing the digit re-enables hints.
- **FastAPI tests:** malformed shape/range, unknown puzzle, given overwrite, client attempts to submit trusted fields, expected domain statuses, no-supported-single, and no solution digits in responses. Use TestClient/httpx.
- **Explanation-service tests with fake providers only:** valid IDs render server text with AI source; unknown/duplicate/unapproved IDs are rejected; timeout, quota/provider exception, missing key, refusal, and malformed response all yield template source and preserve the same verified deduction.
- **React/Vitest tests with mocked API:** selected cell remains selected after entry; keyboard/number-pad behavior; givens locked; candidates/conflicts/mismatches render server results; hint clears on grid changes; stale responses ignored; mismatch disables hints and displays the required message; AI/template badge; solved state only for full correct grid.
- **No automated test imports or calls the live Gemini adapter.** Live API connectivity may be tried manually during build only if configured; fallback and test paths remain network-independent.

## Build Sequence

Build and verify one slice before starting the next. Keep the implementation in this order:

1. **Solver and tests:** scaffold the Python backend and implement server-side candidates, conflicts, mismatch status, naked/hidden singles, evidence records, and completion checks. Run pytest tests for row/column/box deductions, including multi-elimination and unsupported-record rejection cases.
2. **API:** expose puzzle loading and validated analysis/hint endpoints over the tested engine. Use pytest/TestClient to verify malformed or forged input rejection, mismatch versus rule-conflict behavior, and no solution leakage.
3. **Playable grid:** scaffold React/Vite in JavaScript/JSX and wire puzzle selection, entry/erase, backend candidate/conflict status, immediate analysis, and stale-response suppression. Verify with Vitest and hands-on browser review.
4. **Hints and explanations:** add the five-step evidence ladder and approved-clause renderer/provider fallback, then complete the remaining backend and frontend behaviors. Verify with pytest and Vitest using mock providers only; no API key or network access is needed for the automated suite.

Each slice is reviewed and its stated tests pass before work proceeds to the next. Do not implement the whole application in one pass.

## External Services and Dependencies

### Gemini Developer API

- **Call:** Google GenAI Python SDK, models.generate_content; underlying request is POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent.
- **Configuration:** GEMINI_API_KEY for API-key auth; GEMINI_MODEL defaults to gemini-3.5-flash-lite; EXPLANATION_TIMEOUT_SECONDS defaults to 8. The key stays in backend/.env, which Git ignores.
- **Input:** one current deduction's verified facts plus approved clause IDs/descriptions and brief style direction. Do not send the full grid, solution, player history, or personal data.
- **Output:** JSON containing an ordered list of clause IDs. Schema restricts values to the server-provided allow-list. FastAPI independently checks the result, then renders approved text; it never displays raw model output.
- **Failure/latency:** SDK timeout is set to 8 seconds and retries are disabled. Missing model/key, quota (including 429), service/network error, timeout, refusal, invalid JSON, or disallowed clause ID returns the offline template immediately.
- **Quota and price:** Google's current pricing lists free text input/output for this model, but exact per-project RPM/TPM/RPD limits vary by model and account and can change; check AI Studio for the active project before the demo. The free tier may use submitted data to improve Google products, which the learner accepted for minimal puzzle facts and clause IDs. [Model details](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [GenerateContent request/response](https://ai.google.dev/api/generate-content), [structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [pricing and data-use note](https://ai.google.dev/gemini-api/docs/pricing.md), [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits?authuser=2), [Python SDK retry/timeout options](https://googleapis.github.io/python-genai/genai.html).

No other runtime external service. npm and Python package registries are used only when installing dependencies. The offline template has no network dependency.

## Important Failure Modes

- **Invalid/forged board:** FastAPI rejects it; React keeps current board and shows a recoverable message.
- **Rule conflict or solution mismatch:** Backend identifies cells and blocks hints. Mismatch does not stop candidate updates; it stops provider calls.
- **No supported single:** Show the singles-only message and entry/puzzle options; do not call a provider.
- **Gemini missing, over quota, unavailable, timed out, or invalid:** Immediately return the deterministic server template with source=template.
- **Late response for an older grid:** React ignores it by request sequence.

## What Was Simplified and Why

- Static curated puzzles instead of generator/database — keeps attention on supported deductions.
- In-memory state instead of persistence/accounts — reload resets, as chosen.
- Local two-process run instead of Docker/deployment — keeps demo setup simple.
- One Gemini adapter behind an interface instead of multiple providers — replacement stays possible without building extras now.
- Clause selection plus server rendering instead of unrestricted prose — AI influences presentation but cannot introduce facts.
- Mock provider in all automated tests — tests remain deterministic and quota-free.

## Decisions and Open Issues

- **Learner choices:** React + Vite, Tailwind CSS, Python + FastAPI, Gemini initial provider, pytest + Vitest, one repository with separate frontend/backend directories, local demo, no Docker/deployment/database/accounts/persistence.
- **Learner choices:** Current cell remains selected after input; puzzle switch resets immediately; reload restores default; Python is the sole Sudoku logic source; backend validates all submitted grids; stale analysis responses are ignored.
- **Learner choices:** Use Gemini model ID gemini-3.5-flash-lite after checking current official docs; configure provider/model/timeout by environment; default timeout 8 seconds; offline template on missing model/key, quota/service failure, timeout, or invalid output; tests never use live provider.
- **Learner choices:** Candidates continue updating during a solution mismatch, but hints and provider calls are blocked until correction/erase; flag without revealing the answer and test independently from rule conflicts.
- **Learner choice:** Free-tier requests contain only puzzle facts and approved clause IDs; learner accepted Google's current free-tier data-use terms.
- **Implementation decision:** Server owns candidates and every trusted status/deduction, avoiding duplicated Sudoku logic at the cost of one local request per edit.
- **Implementation decision:** Use JavaScript/JSX rather than adding TypeScript for this small proof of concept; the learner reported JavaScript/React experience and the Python API already validates incoming/outgoing data.
- **Implementation decision:** Frontend request sequence numbers prevent late responses replacing newer analysis.
- **Learning moment:** The learner identified that valid JSON or structured claims do not guarantee truthful free-form prose. The agreed interface lets Gemini select only approved clause IDs; FastAPI renders from verified facts.
- **Build-time check:** Inspect current account-specific Gemini quota in AI Studio before the demo. Quota changes affect availability, not architecture; failures use the offline template.

No product-defining questions remain open for the proof of concept.
