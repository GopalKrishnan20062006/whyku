from dataclasses import replace

import pytest

from app.sudoku.candidates import calculate_candidates, find_conflicts
from app.sudoku.engine import analyze_grid, select_next_deduction
from app.sudoku.models import Unit
from app.sudoku.singles import find_singles, validate_deduction
from app.sudoku.units import cells_for_unit
from app.sudoku.validation import normalize_grid, validate_givens


SOLUTION = normalize_grid(
    [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ],
    name="solution",
)
EMPTY = normalize_grid([[0] * 9 for _ in range(9)])
HIDDEN_FIXTURE = normalize_grid(
    [
        [0, 0, 0, 0, 7, 8, 9, 0, 0],
        [0, 0, 0, 1, 9, 0, 0, 0, 8],
        [1, 9, 8, 3, 4, 0, 0, 0, 0],
        [8, 0, 0, 7, 0, 1, 4, 0, 3],
        [4, 0, 6, 8, 5, 0, 0, 9, 0],
        [7, 1, 0, 0, 2, 0, 8, 0, 6],
        [9, 0, 0, 5, 3, 0, 0, 8, 4],
        [0, 8, 7, 0, 0, 9, 0, 3, 0],
        [3, 0, 0, 0, 0, 0, 0, 7, 0],
    ]
)


@pytest.mark.parametrize("target", [(0, 0), (4, 3), (8, 8)])
def test_naked_single_records_multiple_eliminations_and_all_peer_units(target):
    rows = [list(row) for row in SOLUTION]
    rows[target[0]][target[1]] = 0
    grid = normalize_grid(rows)

    candidates = calculate_candidates(grid)
    deduction = next(
        item for item in find_singles(grid, candidates)
        if item.technique == "naked_single" and item.target == target
    )

    assert deduction.candidate_digits == (SOLUTION[target[0]][target[1]],)
    assert deduction.target == target
    assert deduction.technique == "naked_single"
    eliminated = {blocker.digit for blocker in deduction.blockers}
    assert eliminated == set(range(1, 10)) - {deduction.digit}
    assert {kind for blocker in deduction.blockers for kind in blocker.shared_units} == {
        "row", "column", "box"
    }
    expected_blockers = {
        (row, column)
        for row in range(9)
        for column in range(9)
        if (row, column) != target
        and SOLUTION[row][column] != 0
        and (
            row == target[0]
            or column == target[1]
            or (row // 3, column // 3) == (target[0] // 3, target[1] // 3)
        )
    }
    assert {blocker.cell for blocker in deduction.blockers} == expected_blockers
    assert all(SOLUTION[b.cell[0]][b.cell[1]] == b.digit for b in deduction.blockers)
    assert validate_deduction(grid, deduction)


@pytest.mark.parametrize(
    ("kind", "target", "digit"),
    [
        ("row", (3, 2), 9),
        ("column", (1, 1), 7),
        ("box", (1, 1), 7),
    ],
)
def test_hidden_single_records_the_only_eligible_position(kind, target, digit):
    candidates = calculate_candidates(HIDDEN_FIXTURE)
    deduction = next(
        item for item in find_singles(HIDDEN_FIXTURE, candidates)
        if item.technique == "hidden_single"
        and item.unit == Unit(kind, {"row": 3, "column": 1, "box": 0}[kind])
        and item.target == target
        and item.digit == digit
    )

    assert len(deduction.candidate_digits) > 1
    assert deduction.eligible_cells == (target,)
    assert deduction.eligible_cells == tuple(
        cell for cell in cells_for_unit(deduction.unit)
        if HIDDEN_FIXTURE[cell[0]][cell[1]] == 0 and digit in candidates[cell[0]][cell[1]]
    )
    unit_cells = cells_for_unit(deduction.unit)
    expected_excluded = {
        cell for cell in unit_cells
        if HIDDEN_FIXTURE[cell[0]][cell[1]] == 0 and cell != target
    }
    assert {item.cell for item in deduction.excluded_positions} == expected_excluded
    for excluded in deduction.excluded_positions:
        assert excluded.blockers
        assert all(blocker.digit == digit for blocker in excluded.blockers)
        for blocker in excluded.blockers:
            assert HIDDEN_FIXTURE[blocker.cell[0]][blocker.cell[1]] == digit
            assert kind not in blocker.shared_units
            expected_shared = set()
            if excluded.cell[0] == blocker.cell[0]:
                expected_shared.add("row")
            if excluded.cell[1] == blocker.cell[1]:
                expected_shared.add("column")
            if (excluded.cell[0] // 3, excluded.cell[1] // 3) == (
                blocker.cell[0] // 3, blocker.cell[1] // 3
            ):
                expected_shared.add("box")
            assert set(blocker.shared_units) == expected_shared
    assert validate_deduction(HIDDEN_FIXTURE, deduction)
    assert not validate_deduction(
        HIDDEN_FIXTURE, replace(deduction, excluded_positions=())
    )


def test_record_with_changed_digit_or_evidence_is_rejected_by_recomputation():
    grid = tuple(
        tuple(0 if (row, column) == (0, 0) else digit for column, digit in enumerate(values))
        for row, values in enumerate(SOLUTION)
    )
    candidates = calculate_candidates(grid)
    valid = next(item for item in find_singles(grid, candidates) if item.target == (0, 0))

    assert not validate_deduction(grid, replace(valid, digit=valid.digit % 9 + 1))
    assert not validate_deduction(grid, replace(valid, blockers=()))
    assert not validate_deduction(grid, replace(valid, target=(0, 1)))


def test_same_grid_has_stable_selection_and_solution_does_not_steer_it():
    rows = [list(row) for row in SOLUTION]
    rows[4][3] = 0
    grid = normalize_grid(rows)
    alternate_solution = normalize_grid(
        [[{8: 9, 9: 8}.get(digit, digit) for digit in row] for row in SOLUTION]
    )

    first = select_next_deduction(grid)
    second = select_next_deduction(grid)
    assert first == second
    assert first is not None
    assert (first.technique, first.target, first.digit) == ("naked_single", (4, 3), 8)
    assert first.digit != alternate_solution[first.target[0]][first.target[1]]

    # The higher-level analyzer uses the reference solution only to block the
    # contradictory game state; the rule-only selector above remains unchanged.
    blocked = analyze_grid(grid, EMPTY, alternate_solution)
    assert blocked.hint_block_reason == "solution_mismatch"
    assert blocked.deduction is None


def test_next_move_order_is_naked_row_major_then_hidden_unit_order():
    rows = [list(row) for row in SOLUTION]
    rows[0][0] = 0
    rows[1][4] = 0
    grid = normalize_grid(rows)

    selected = select_next_deduction(grid)
    assert selected is not None
    assert (selected.technique, selected.target, selected.digit) == ("naked_single", (0, 0), 5)


@pytest.mark.parametrize("bad_grid", [[], [[0] * 8 for _ in range(9)], [[False] + [0] * 8] + [[0] * 9 for _ in range(8)], [[10] + [0] * 8] + [[0] * 9 for _ in range(8)]])
def test_grid_shape_and_values_are_validated(bad_grid):
    with pytest.raises(ValueError):
        analyze_grid(bad_grid, EMPTY, SOLUTION)


def test_given_cells_are_immutable():
    givens = [list(row) for row in EMPTY]
    givens[0][0] = 5
    grid = [list(row) for row in givens]
    grid[0][0] = 4
    with pytest.raises(ValueError, match="cannot be changed"):
        validate_givens(normalize_grid(grid), normalize_grid(givens))


def test_duplicate_conflict_and_zero_candidate_are_reported_separately():
    duplicate = [list(row) for row in EMPTY]
    duplicate[0][0] = duplicate[0][1] = 5
    duplicate_grid = normalize_grid(duplicate)
    duplicate_result = analyze_grid(duplicate_grid, EMPTY, SOLUTION)
    assert {(0, 0), (0, 1)} <= {conflict.cell for conflict in duplicate_result.conflicts}
    assert "duplicate_row" in next(c for c in duplicate_result.conflicts if c.cell == (0, 0)).reasons
    assert duplicate_result.hint_block_reason == "rule_conflict"

    no_candidates = [list(row) for row in EMPTY]
    no_candidates[0] = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    no_candidates[1][0:3] = [9, 3, 4]
    grid = normalize_grid(no_candidates)
    assert not calculate_candidates(grid)[0][0]
    conflict = next(c for c in find_conflicts(grid, calculate_candidates(grid)) if c.cell == (0, 0))
    assert conflict.reasons == ("no_candidates",)
    blocked = analyze_grid(grid, EMPTY, SOLUTION)
    assert blocked.hint_block_reason == "rule_conflict"
    assert blocked.deduction is None


def test_solution_mismatch_keeps_candidates_but_blocks_deductions_without_answer():
    current = [list(row) for row in EMPTY]
    current[0][0] = 1 if SOLUTION[0][0] != 1 else 2
    result = analyze_grid(normalize_grid(current), EMPTY, SOLUTION)

    assert result.mismatches == ((0, 0),)
    assert not result.conflicts
    assert result.candidates[0][1]  # Rule-based candidates continue updating.
    assert 1 not in result.candidates[0][1]  # The entered digit still removes a candidate.
    assert result.hint_block_reason == "solution_mismatch"
    assert result.deduction is None
    assert not hasattr(result, "solution")


def test_completion_requires_full_grid_matching_solution():
    solved = analyze_grid(SOLUTION, EMPTY, SOLUTION)
    assert solved.is_full and solved.is_solved
    assert solved.hint_block_reason == "completed"

    swapped = [list(row) for row in SOLUTION]
    for row in range(9):
        for column in range(9):
            swapped[row][column] = {1: 2, 2: 1}.get(swapped[row][column], swapped[row][column])
    incorrect = analyze_grid(normalize_grid(swapped), EMPTY, SOLUTION)
    assert incorrect.is_full and not incorrect.is_solved
    assert not incorrect.conflicts
    assert incorrect.mismatches
    assert incorrect.hint_block_reason == "solution_mismatch"


def test_no_supported_single_is_reported_without_inventing_a_deduction():
    result = analyze_grid(EMPTY, EMPTY, SOLUTION)

    assert not result.conflicts
    assert not result.mismatches
    assert result.deduction is None
    assert result.hint_block_reason == "no_supported_single"
