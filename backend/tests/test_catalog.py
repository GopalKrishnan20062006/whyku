"""Prove every curated board is unique and progresses with supported singles."""

from app.puzzles.catalog import PUZZLES
from app.sudoku.candidates import calculate_candidates, find_conflicts
from app.sudoku.engine import analyze_grid
from app.sudoku.validation import normalize_grid


def _count_solutions(grid, limit=2):
    candidates = calculate_candidates(grid)
    if find_conflicts(grid, candidates):
        return 0
    empties = [
        (len(candidates[row][column]), row, column)
        for row in range(9)
        for column in range(9)
        if grid[row][column] == 0
    ]
    if not empties:
        return 1
    count, row, column = min(empties)
    if count == 0:
        return 0
    solutions = 0
    for digit in candidates[row][column]:
        next_grid = [list(values) for values in grid]
        next_grid[row][column] = digit
        solutions += _count_solutions(normalize_grid(next_grid), limit - solutions)
        if solutions >= limit:
            return solutions
    return solutions


def test_five_puzzles_match_their_solution_and_have_unique_solutions():
    assert len(PUZZLES) == 5
    assert len({puzzle.puzzle_id for puzzle in PUZZLES}) == 5
    for puzzle in PUZZLES:
        for row in range(9):
            for column in range(9):
                if puzzle.initial_grid[row][column]:
                    assert puzzle.initial_grid[row][column] == puzzle.solution[row][column]
        assert _count_solutions(puzzle.initial_grid) == 1


def test_every_curated_puzzle_can_be_completed_using_supported_singles():
    for puzzle in PUZZLES:
        grid = puzzle.initial_grid
        for _ in range(81):
            result = analyze_grid(grid, puzzle.initial_grid, puzzle.solution)
            if result.is_solved:
                break
            assert result.hint_block_reason is None
            assert result.deduction is not None
            rows = [list(values) for values in grid]
            row, column = result.deduction.target
            rows[row][column] = result.deduction.digit
            grid = normalize_grid(rows)
        else:
            raise AssertionError(f"{puzzle.puzzle_id} did not solve in 81 steps")
        assert result.is_solved
