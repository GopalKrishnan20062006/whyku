---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. Solver proves singles from the current grid**
  Becomes usable: A runnable Python engine returns candidates, conflicts, mismatch status, completion status, and only independently verified naked or hidden single records.
  Why now: The deterministic engine is Whyku's unique kernel and highest correctness risk; independent pytest evidence can validate it before UI or AI work.
  PRD ref: `prd.md > Features and Behavior`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components` (Sudoku Engine), `spec.md > Verification Plan`
  Build: Scaffold backend Python environment and engine modules; implement candidate calculation, rule-conflict and solution-mismatch separation, naked/hidden singles across rows, columns, and boxes, verified evidence records, and completion checks.
  Verify (mechanical): From `backend/`, run `pytest`; include row/column/box cases, multiple eliminations, unsupported-deduction rejection, locally legal solution mismatch, and rule conflict cases.
  Learner check: Inspect the pytest results and one deduction fixture; confirm the recorded target and evidence match what the current grid proves.
  Commit: `191c602317220a32ba39c78303c08500db6f88f1` (`Build verified Sudoku engine`)

- [x] **2. API validates grids and returns safe hints/explanations**
  Becomes usable: A local API loads curated puzzles, returns trusted analysis and hint states, and can render a verified explanation or offline fallback.
  Why now: The API makes the solver's guarantees an explicit boundary before the browser consumes them.
  PRD ref: `prd.md > The Core Journey`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components` (FastAPI Routes), `spec.md > Data Model`, `spec.md > Verification Plan`
  Build: Add schemas, curated puzzle data, puzzle/analysis/hint/explanation routes, backend validation of dimensions, values, puzzle IDs and givens, and server-side candidate recomputation. Add the mock provider, configurable Gemini adapter, approved clause validation/rendering, and deterministic offline fallback. Ensure mismatch blocks hints/provider calls without revealing solution digits.
  Verify (mechanical): From `backend/`, run `pytest`; TestClient/service cases cover malformed/forged boards, rule conflict versus mismatch, no solution leakage, no supported single, verified endpoint evidence, valid/invalid clause selections, provider timeout/quota/unavailable fallback, and prove tests use mocks without network calls.
  Learner check: Verified live template-mode API responses for a clean board, a locally legal but solution-wrong entry, blocked hints, malformed-grid rejection, and recovery after erasure. Template explanation was server-rendered; mismatch response exposed only coordinates.
  Commit: `7ff4f7fdd18a7f24e1bb96b02596968f5ed03006` (`Expose validated API and explanation service`)

- [x] **3. Playable board uses backend analysis**
  Becomes usable: The browser displays curated Sudoku puzzles and supports selection, keyboard/mouse entry, erase, candidates, and backend status updates.
  Why now: It gives the tested backend a real interactive surface while preserving Python as the only Sudoku logic source.
  PRD ref: `prd.md > The Core Journey`, `prd.md > Screens and Layout`, `prd.md > Features and Behavior`
  Spec ref: `spec.md > Look and Feel`, `spec.md > Components` (Frontend App and Board, Controls, and Hint Ladder), `spec.md > File Structure`
  Build: Scaffold React/Vite in JavaScript/JSX with Tailwind; add board, selector, controls, selected-cell behavior, keyboard and mouse entry/erase, API client, immediate backend analysis, visible candidates/conflict indicators/statuses, and request-sequence handling for stale responses.
  Verify (mechanical): Run `npm test -- --run` from `frontend/`; Vitest covers givens locked, entry/erase, selection retention, backend candidate rendering, mismatch warnings, and stale responses. Start both local dev processes and confirm the board loads.
  Learner check: Learner confirmed the browser review passed: puzzle switching resets entries, keyboard and number-pad entry retain selection, candidates refresh after erasure, mismatches are flagged and block hints without revealing answers, givens stay locked, and cell/unit highlights are clear.
  Commit: `d633a73fb027594c6195504e346297ecc1a9d03c` (`Build playable backend-driven grid`)

- [x] **4. Evidence ladder and end-to-end demo**
  Becomes usable: A player can reveal the five hint levels, inspect technique-specific evidence, and receive verified AI wording or a labeled offline template in the completed demo flow.
  Why now: With the solver, API/explanation service, and playable grid reviewed, the ladder can render deduction evidence without deciding or inventing moves.
  PRD ref: `prd.md > Features and Behavior`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components` (Explanation Service and Clause Renderer, Gemini Provider Adapter, Frontend App and Board), `spec.md > Verification Plan`, `spec.md > External Services and Dependencies`
  Build: Add Nudge/Area/Technique/Reasoning/Reveal, naked/hidden-single evidence displays, target masking, hint blocking for mismatch/conflict states, fallback labeling, and end-to-end wiring. Keep all factual explanation content server-rendered from approved clauses. Mock provider in all automated tests.
  Verify (mechanical): Run the full backend `pytest` and frontend `npm test -- --run` suites; cover all five stages, hidden target digit before Reveal, approved/invalid clause IDs, timeout/quota/unavailable-model fallback, no test network calls, mismatch hint blocking, AI/template source labels, and candidate refresh after applying a move. Manually inspect the end-to-end demo flow with the offline template.
  Learner check: Completed in Chrome against the local backend in template mode. Played a real naked-single record through all five levels; Reasoning showed the Offline template label and blocker evidence, Reveal showed R1C4 = 6, applying it cleared the prior hint, and the refreshed grid produced another hint.
  Commit: `2be64bc4c10c089be7f1e1fe6608b9a811928b04` (`Add verified hint ladder and explanations`)

## Hands-on Checkpoints

- [x] Slice 1 engine evidence reviewed before its commit and before starting the API slice.
- [x] Slice 2 API behavior reviewed before its commit and before starting the React slice.
- [x] Early usable board explored after slice 3; learner approved the board during browser review.
- [x] Slice 4 hint and fallback behavior reviewed before its commit and final review.
- [x] Final kick-the-tires review completed; learner confirmed ready as-is and requested no additional changes.

## Final Review

- [x] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [x] Learning activity complete — focused alternative, prior practice connected, or brief recap
- [x] Optional edit and transfer reflection addressed — offered/answered/declined/not applicable as appropriate
- [x] `devpost/app-map.html` generated from finished code, checked in Chrome, and shown, including a project-grounded practice to reuse

Activity and evidence: Focused evidence recap connected the learner's stated trust boundary to the implementation and checks: engine tests verify deductions from the current grid, API tests cover mismatch blocking and provider fallback, frontend tests render the returned record, and the Chrome flow showed evidence and a refreshed hint after entry.
Route and stops: Reference route (not an interactive code tour) in `devpost/app-map.html`: `frontend/src/App.jsx` → `frontend/src/api.js` → `backend/app/main.py` → `backend/app/sudoku/engine.py` / `singles.py` → `backend/app/explanations/service.py`.
Edit outcome: Not applicable; the focused evidence recap needed no code edit.
Reflection: Already covered by the learner's planning decisions about solver truth, backend validation, and approved explanation clauses; final review reiterated explanation trust, hint clarity, and mismatch edge cases. No additional transfer question was needed.
Activity mode: Focused evidence recap for an experienced plan-first learner.

## Revisions

- Slice 3 browser review was reported passed by the learner and approved. Six Vitest checks pass, the Vite production build succeeds, and the local Vite proxy served all five puzzles and backend candidates.
- Slice 4 verification: backend `.venv\Scripts\python.exe -m pytest` passed (34 tests, 1 recorded Starlette/httpx deprecation warning); frontend `npm test -- --run` passed (8 tests); `npm run build` passed. Automated tests use mocks. The live Chrome flow used `EXPLANATION_PROVIDER=template`; API logs show the analysis, hint, and explanation requests without Gemini network calls. Mismatch blocking/recovery was also rechecked in the browser. `git diff --check` passed.
- Final repository check: all four slice commits are present (`191c602`, `7ff4f7f`, `d633a73`, `2be64bc`). The tracked tree had no uncommitted changes before completion docs; unrelated untracked `.agents/`, `.claude/`, `agent/`, and `skills-lock.json` remain untouched. `backend/.env` does not exist and is ignored; no API-key pattern was found in tracked files or reachable Git history. `devpost/learner-profile.md` is not tracked. `devpost/app-map.html` was opened in Chrome and reviewed; its code reference is snapshot `2be64bc`.
- Final review: learner confirmed "Ready as-is" and requested no changes. The Starlette/httpx deprecation remains documented for follow-up.
- Slice 2 manual API checks passed in template mode; `pytest` passed (34 tests). Recorded Starlette deprecation warning: TestClient currently uses httpx; investigate the recommended `httpx2` migration during cleanup rather than suppressing it.
- Added complete hidden-single position blockers and documented deterministic naked/hidden selection order after slice review identified missing proof detail; expanded regression tests and confirmed the solver suite passes.
