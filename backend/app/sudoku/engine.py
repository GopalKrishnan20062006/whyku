"""Pure deterministic analysis; known solutions never choose deductions."""

from collections.abc import Sequence

from .candidates import calculate_candidates, find_conflicts
from .models import Analysis, Deduction, Grid
from .singles import find_singles, validate_deduction
from .validation import normalize_grid, validate_givens, validate_solution


def analyze_grid(
    current: Sequence[Sequence[int]],
    givens: Sequence[Sequence[int]],
    solution: Sequence[Sequence[int]],
) -> Analysis:
    grid: Grid = normalize_grid(current, name="grid")
    initial = normalize_grid(givens, name="givens")
    known_solution = normalize_grid(solution, name="solution")
    validate_givens(grid, initial)
    validate_solution(known_solution)
    for row in range(9):
        for column in range(9):
            if initial[row][column] and initial[row][column] != known_solution[row][column]:
                raise ValueError("givens do not match the supplied solution")

    candidates = calculate_candidates(grid)
    conflicts = find_conflicts(grid, candidates)
    mismatches = tuple(
        (row, column)
        for row in range(9)
        for column in range(9)
        if initial[row][column] == 0
        and grid[row][column] != 0
        and grid[row][column] != known_solution[row][column]
    )
    is_full = all(digit != 0 for row in grid for digit in row)
    is_solved = is_full and grid == known_solution

    hint_block_reason = None
    if conflicts:
        hint_block_reason = "rule_conflict"
    elif mismatches:
        hint_block_reason = "solution_mismatch"
    elif is_solved:
        hint_block_reason = "completed"

    deduction = None if hint_block_reason else select_next_deduction(grid)
    if not hint_block_reason and deduction is None:
        hint_block_reason = "no_supported_single"
    return Analysis(
        candidates=candidates,
        conflicts=conflicts,
        mismatches=mismatches,
        is_full=is_full,
        is_solved=is_solved,
        deduction=deduction,
        hint_block_reason=hint_block_reason,
    )


def select_next_deduction(current: Sequence[Sequence[int]]) -> Deduction | None:
    """Select deterministically from Sudoku rules only; no solution is accepted here.

    Naked singles are ordered by row and column. Hidden singles follow by rows,
    columns, then boxes, with ascending digits within each unit.
    """
    grid = normalize_grid(current, name="grid")
    candidates = calculate_candidates(grid)
    if find_conflicts(grid, candidates):
        return None
    return next(
        (item for item in find_singles(grid, candidates) if validate_deduction(grid, item)),
        None,
    )
