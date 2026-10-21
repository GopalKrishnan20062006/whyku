---
doc: prd
status: approved
---
# Whyku — Product Requirements

A board-first Sudoku tutor for beginner and intermediate players that shows the evidence behind a verified next move.
Source: `scope.md > The Unique Kernel`, `Who It's For`, and `The Core Loop`.

## The Core Journey

1. The player opens Whyku directly to a playable Sudoku board with one curated puzzle selected. They can choose among about five puzzles, with difficulty or required technique indicated.
2. They select an empty cell and enter digits with the keyboard or number pad. Givens are locked; player entries can be edited or erased. Candidate marks update as entries change.
3. When stuck, they select **Get Hint**. The deterministic engine returns a supported naked or hidden single with a deduction record and its visual evidence.
4. The player steps through as much of the five-level hint as they want. Evidence stays visible on the board; the target digit stays concealed until Reveal.
5. At Reveal, they can enter the digit or return to solving. The old highlights clear after the entry, and Whyku requests a fresh deduction from the updated grid.
6. The journey is successful when the player can inspect a valid deduction on the actual puzzle state, see why the move follows from Sudoku rules independently of the AI prose, and enter it to continue.

## Screens and Layout

### Puzzle board (only primary screen)

- **Top bar:** Whyku name/logo and the short tagline “Understand every move.”
- **Puzzle selector:** A dropdown or compact set of choices for the curated puzzles; indicate difficulty or required technique.
- **Board:** A large centered 9×9 grid. Given digits are visually distinct and locked; player-entered digits are editable. Candidate marks are on by default.
- **Entry controls:** Number pad, erase, and a prominent **Get Hint** action.
- **Status area:** “Solve at your own pace. Ask for a hint when you get stuck.” Replace this with applicable warning, hint status, or completion feedback.
- **Hint presentation:** Hint text and controls appear only after requested. The grid remains visible and holds the evidence highlights while the hint is open.

## Look and Feel

A thoughtfully designed digital puzzle notebook: warm off-white background, dark ink-like digits, subtle grid lines, and restrained accent colors for selection and hint evidence. Keep the solving board calm and focused; do not present hints before requested. Use consistent colors and shapes to distinguish the selected cell, relevant unit, target cell, candidate positions, and eliminated candidates.

## Features and Behavior

### Puzzle selection and board entry

- Open directly to the board, with a curated puzzle ready to play.
- Let the player choose among about five curated puzzles. Show difficulty or required technique with each choice.
- Support selection by mouse and number entry through either keyboard digits 1–9 or the on-screen number pad.
- Selecting a cell clearly marks it and softly highlights its row, column, and 3×3 box. Given cells cannot be edited; player-entered digits can.
- After a digit is entered, keep the current cell selected. Do not move focus automatically. The player can select another cell with the mouse or arrow keys; a number key enters that digit into the selected editable cell. Given cells cannot be overwritten.
- Recalculate candidates in affected empty cells in the entered digit's row, column, and box. Remove candidates made illegal by that entry. If any cell has no legal candidates, flag a contradiction.
- Keep rule legality separate from solution correctness. Rule-based candidates come only from Sudoku constraints. An optional immediate mistake-warning toggle is enabled by default and may flag a locally legal digit that disagrees with the selected puzzle's solution; do not reveal the right digit. A rule violation and a solution mismatch receive subtle visual warnings and remain editable or erasable. Continue candidate calculation during a solution mismatch, but disable hint generation until all mismatching entries are corrected or erased. Show: “Correct or erase the flagged entry before requesting a hint.” Never send a deduction to the explanation provider while a mismatch remains.
- Erasing an editable digit restores affected candidates immediately. Candidate marks update immediately after every entry or erasure. If the grid changes while a hint is open, clear its stale evidence; any new hint must be requested from the updated grid. Do not silently continue a contradictory grid as though it were valid.

### Progressive hints and visual evidence

Every level comes from the same engine-verified deduction record. The engine records candidate and unit-position evidence; the interface renders those records instead of independently guessing which cells support the move. The player may reveal the next level, return to the puzzle, or dismiss the hint at each stage. Keep evidence highlights on the board while the hint remains open.

1. **Nudge:** A gentle clue, such as “There’s a cell in this box with only one possible digit.” Show no coordinates or digit.
2. **Area:** Highlight the relevant row, column, or box. Do not identify the exact cell or digit.
3. **Technique:** Name the technique and unit (for example, “Hidden single in box 5”) and highlight the relevant evidence cells. The target digit remains hidden.
   - **Naked single:** Outline the target cell; softly shade its row, column, and box; show its candidates with all but the surviving candidate visibly eliminated or crossed out. Mask the surviving digit.
   - **Hidden single:** Highlight the relevant unit and all empty cells in it where the target digit remains a legal candidate. Distinguish the target cell from the other candidate cells, while masking the digit itself, including its candidate marks.
4. **Reasoning:** Show the complete candidate evidence and why the move must go in that cell; keep the digit hidden.
   - **Naked single:** Keep the target outlined; show the digits already present in its row, column, and box that rule out other candidates; mark eliminated candidates unavailable. Explain that every other candidate is ruled out by those existing digits.
   - **Hidden single:** Keep the unit highlighted; show the target digit as a masked candidate in each relevant empty cell and distinguish the sole eligible cell. Explain that this digit has only one possible position in the unit, even if that cell has other candidates.
   - Show an AI explanation derived from the verified record only if it passes the explanation check. If generation times out or the explanation fails verification, show the deterministic template for the same record.
5. **Reveal:** Highlight the target cell and show the digit. Offer an explicit action to enter it into the grid.

When the player changes the grid, clear stale evidence highlights. A fresh deduction is requested from the updated grid when the player asks for another hint. Returning to the puzzle keeps the current hint evidence visible while that hint remains open; dismissing the hint clears its evidence. The next hint request is based on the current board.

### No supported single, contradiction, and completion

- If the engine finds no supported single, leave the grid unchanged and say: “No naked or hidden single is available right now.” Explain that Whyku supports singles only and the puzzle may need a more advanced technique. Offer review of entries or another curated puzzle. Do not call the explanation model without a verified deduction record.
- If an entry violates Sudoku rules or creates a contradiction, identify the relevant conflicting cells and explain that the grid needs correction before a reliable hint can be provided. Do not send a contradictory state to the explanation model or reveal the solution. Keep player entries editable/erasable.
- If a player entry is locally legal but disagrees with the known solution, keep updating candidates and detecting ordinary rule conflicts, but flag the mismatching entry without showing the correct digit. Disable hint generation until every mismatching entry is corrected or erased and show: “Correct or erase the flagged entry before requesting a hint.” Never send a deduction to the explanation provider while a mismatch remains. Test this separately from rule conflicts, including an incorrect digit that creates no row, column, or box duplicate.
- A puzzle is solved only when every cell is filled and the grid matches its solution. Show “Puzzle solved. You worked it out!”, disable or hide **Get Hint**, and offer **Play another puzzle**.
- A full but incorrect grid is never success. Highlight conflicting entries and let the player correct them.

## States and Boundaries

- **Initial:** A curated puzzle is loaded directly in the board; candidates are visible by default and the hint is closed.
- **Normal solving:** Selection, entry, erasure, candidate updates, and optional mistake warnings operate on the current board.
- **Hint open:** Current level and corresponding engine evidence appear; player may advance, return, or dismiss. Target digit is concealed before Reveal.
- **No supported single:** State the engine limitation and offer entry review or puzzle selection; no generated explanation.
- **Contradiction:** Flag the relevant cells and block reliable hinting until correction; do not explain a contradictory record as valid.
- **Solution mismatch:** Continue candidate updates and rule-conflict detection, flag mismatching entries without revealing their correct digits, and block hint/provider calls until corrected or erased. Explain: “Correct or erase the flagged entry before requesting a hint.” This is distinct from a Sudoku rule conflict.
- **Solved:** Show success only for a full grid matching the solution, then offer another puzzle.
- **Full but incorrect:** No success state; flag conflicting entries and allow correction.
- **Persistence:** Not specified for this proof of concept; the active puzzle and entries are not promised to survive closing/reloading.

## Product Decisions

- Keep the player in control of how much help is revealed; each of five levels can be followed by another reveal, return to the puzzle, or dismissal.
- Never expose the target digit before Reveal, and never let AI choose the deduction. Both choices protect learning and trust.
- Show actual deduction evidence from the engine record; use a deterministic template when AI explanation is unavailable or unverified.
- Separate local Sudoku legality from correctness against the puzzle solution, with immediate mistake warnings enabled by default but not revealing the answer.
- Block hints and provider calls on a known-solution mismatch even when the entry is locally legal, while allowing candidate updates to continue.
- Prioritize correctness and inspectable evidence over puzzle count or technique breadth.
- Visual direction is a warm, restrained puzzle notebook, not a generic AI chat interface.

## What We're Building

One board-first screen; curated puzzle selection; mouse and keyboard entry; editable player digits and locked givens; rule-based candidate marks; default-on solution mistake warnings; naked and hidden singles in rows, columns, and boxes; five progressive hint levels with technique-specific evidence; verified AI explanations and deterministic fallback; truthful no-single, contradiction, solved, and full-but-incorrect states; and a one-minute demonstrable solving moment.

## Deferred From the POC

- More puzzles or puzzle generation, because curated puzzles are enough to demonstrate the loop and can be selected for supported techniques.
- Additional solving techniques, because correctness and tests for singles come first.
- A separate tutorial library, because the hint ladder teaches within the solving moment.
- Accounts, progress sync, and leaderboards, because they do not prove the deduction and explanation experience.

## Possible Later Enhancements

Expand the puzzle collection and supported techniques after the existing deduction evidence is reliable. A separate tutorial library could build on the techniques learners encounter in hints.

## Non-Goals

- Generating puzzles or guaranteeing arbitrary puzzles can be solved by the supported engine.
- Explaining or hinting with techniques beyond naked and hidden singles.
- Automatically revealing the solution when an entry is wrong or when no supported single exists.
- Accounts, online synchronization, leaderboards, or a separate tutorial experience.

## Open Questions


- **Can be decided in `4-spec`:** The exact verification rule for AI prose against the deduction record, timeout duration, and service behavior are technical decisions; preserve the required deterministic fallback and never trust unverified prose.
- **Can be decided in `4-spec`:** The exact local mechanism for puzzle solution checking and mistake-warning toggle placement, as long as warnings do not reveal the correct digit and candidate legality remains independent.



