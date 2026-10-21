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
  Commit: `Build verified Sudoku engine`

- [ ] **2. API validates grids and returns safe hints/explanations**
  Becomes usable: A local API loads curated puzzles, returns trusted analysis and hint states, and can render a verified explanation or offline fallback.
  Why now: The API makes the solver's guarantees an explicit boundary before the browser consumes them.
  PRD ref: `prd.md > The Core Journey`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components` (FastAPI Routes), `spec.md > Data Model`, `spec.md > Verification Plan`
  Build: Add schemas, curated puzzle data, puzzle/analysis/hint/explanation routes, backend validation of dimensions, values, puzzle IDs and givens, and server-side candidate recomputation. Add the mock provider, configurable Gemini adapter, approved clause validation/rendering, and deterministic offline fallback. Ensure mismatch blocks hints/provider calls without revealing solution digits.
  Verify (mechanical): From `backend/`, run `pytest`; TestClient/service cases cover malformed/forged boards, rule conflict versus mismatch, no solution leakage, no supported single, verified endpoint evidence, valid/invalid clause selections, provider timeout/quota/unavailable fallback, and prove tests use mocks without network calls.
  Learner check: Call the local API for a clean board, then a locally legal but solution-wrong entry; inspect that candidates remain available while hints are blocked. Inspect a mocked explanation failure and confirm the returned fallback is server-rendered.
  Commit: `Expose validated API and explanation service`

- [ ] **3. Playable board uses backend analysis**
  Becomes usable: The browser displays curated Sudoku puzzles and supports selection, keyboard/mouse entry, erase, candidates, and backend status updates.
  Why now: It gives the tested backend a real interactive surface while preserving Python as the only Sudoku logic source.
  PRD ref: `prd.md > The Core Journey`, `prd.md > Screens and Layout`, `prd.md > Features and Behavior`
  Spec ref: `spec.md > Look and Feel`, `spec.md > Components` (Frontend App and Board, Controls, and Hint Ladder), `spec.md > File Structure`
  Build: Scaffold React/Vite in JavaScript/JSX with Tailwind; add board, selector, controls, selected-cell behavior, keyboard and mouse entry/erase, API client, immediate backend analysis, visible candidates/conflict indicators/statuses, and request-sequence handling for stale responses.
  Verify (mechanical): Run `npm test -- --run` from `frontend/`; Vitest covers givens locked, entry/erase, selection retention, backend candidate rendering, mismatch warnings, and stale responses. Start both local dev processes and confirm the board loads.
  Learner check: Open the board, switch puzzles, enter and erase a digit, and confirm the selected cell stays put while candidate marks update.
  Commit: `Build playable backend-driven grid`

- [ ] **4. Evidence ladder and end-to-end demo**
  Becomes usable: A player can reveal the five hint levels, inspect technique-specific evidence, and receive verified AI wording or a labeled offline template in the completed demo flow.
  Why now: With the solver, API/explanation service, and playable grid reviewed, the ladder can render deduction evidence without deciding or inventing moves.
  PRD ref: `prd.md > Features and Behavior`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components` (Explanation Service and Clause Renderer, Gemini Provider Adapter, Frontend App and Board), `spec.md > Verification Plan`, `spec.md > External Services and Dependencies`
  Build: Add Nudge/Area/Technique/Reasoning/Reveal, naked/hidden-single evidence displays, target masking, hint blocking for mismatch/conflict states, fallback labeling, and end-to-end wiring. Keep all factual explanation content server-rendered from approved clauses. Mock provider in all automated tests.
  Verify (mechanical): Run the full backend `pytest` and frontend `npm test -- --run` suites; cover all five stages, hidden target digit before Reveal, approved/invalid clause IDs, timeout/quota/unavailable-model fallback, no test network calls, mismatch hint blocking, AI/template source labels, and candidate refresh after applying a move. Manually inspect the end-to-end demo flow with the offline template.
  Learner check: Play the demo path: request a hint, inspect its evidence through Reasoning, observe the template fallback label, reveal and enter the digit; confirm fresh analysis replaces old highlights.
  Commit: `Add verified hint ladder and explanations`

## Hands-on Checkpoints

- [ ] Slice 1 engine evidence reviewed before its commit and before starting the API slice.
- [ ] Slice 2 API behavior reviewed before its commit and before starting the React slice.
- [ ] Early usable board explored after slice 3; feedback can shape the hint interaction.
- [ ] Slice 4 hint and fallback behavior reviewed before its commit and final review.
- [ ] Final kick-the-tires exploration and feedback completed.

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/answered/declined/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [record after build]
Route and stops: [record after build]
Edit outcome: [record after build]
Reflection: [offered/answered/declined/already covered]
Activity mode: [record after build]

## Revisions

- Added complete hidden-single position blockers and documented deterministic naked/hidden selection order after slice review identified missing proof detail; expanded regression tests and confirmed the solver suite passes.
