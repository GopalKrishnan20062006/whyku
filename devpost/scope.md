---
doc: scope
status: approved
---
# Whyku

A Sudoku tutor that helps players understand a correct next move by showing the deduction evidence behind it.

## The Unique Kernel
A deterministic engine chooses and validates the Sudoku deduction; AI only explains that verified record. The player can inspect the highlighted cells and candidates that support the move, so the prose is never the source of truth.

## Who It's For
Beginner and intermediate Sudoku players who know the basic rules but get stuck and want to improve their reasoning, not just finish a puzzle. Instead of taking an unexplained answer, they can ask for a hint and inspect why the move works.

## The Core Loop
The player opens a curated puzzle, solves in the grid, and asks for help when stuck. Whyku finds a supported single, reveals progressively more of the hint, and highlights the row, column, box, or candidate cells relevant to the deduction. The player enters the digit and continues, with the aim of recognizing the technique next time.

## Inspiration & Identity
The experience should feel like a patient tutor that makes its reasoning inspectable. Prioritize a clear, polished hint interaction and visible evidence over breadth of Sudoku features. No specific visual reference was provided.

## Why This Matters to the Learner
The project demonstrates that AI can make a deterministic system easier to understand without being trusted to determine the truth. The learner wants to practice turning this product idea into a reliable technical plan, defining component interfaces, small verifiable slices, and tests that catch subtle logic errors.

## What "Working" Looks Like
A one-minute demo shows one real puzzle state in a playable grid. The player requests a hint; the engine returns a valid naked or hidden single, and Whyku progressively reveals the clue and technique while highlighting the supporting area and candidates. An explanation is tied to the verified deduction record, with a deterministic template available if AI output fails verification or times out. The player enters the digit and continues. The visible evidence must support the move independently of the AI prose; the deduction must come from the actual puzzle state, not a hardcoded demonstration.

## The POC Boundary
- A playable 9×9 Sudoku grid with keyboard and mouse input.
- A deterministic solver limited to naked singles and hidden singles in rows, columns, and boxes.
- A progressive hint ladder, from a gentle nudge through evidence and technique to the digit and explanation.
- Visible cell and candidate evidence for the selected deduction.
- AI-generated explanations checked against the deduction record, with a deterministic template fallback on failed verification or timeout.
- About five curated puzzles with unique solutions, selected to be solvable using the supported techniques. Correctness and visible deduction evidence take priority over puzzle count.

## Later
- A broader puzzle collection and a puzzle generator.
- Additional solving techniques.
- A separate tutorial library.

## Explicitly Cut
- Accounts and leaderboards: they do not help prove the hinting and reasoning experience.
- Advanced solving techniques: they would expand solver and test scope before the core deductions are established.

