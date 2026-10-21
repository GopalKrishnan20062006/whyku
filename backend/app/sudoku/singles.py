"""Naked and hidden single discovery plus evidence recomputation."""

from .models import Blocker, Candidates, Cell, Deduction, Grid, PositionElimination, Unit
from .units import all_units, cells_for_unit, shared_unit_kinds, units_for_cell


def find_singles(grid: Grid, candidates: Candidates) -> tuple[Deduction, ...]:
    """Return all supported singles in stable order: naked row-major, then
    hidden by rows, columns, boxes; within each unit, digits ascend.
    """
    naked: list[Deduction] = []
    for row in range(9):
        for column in range(9):
            possible = candidates[row][column]
            if grid[row][column] == 0 and len(possible) == 1:
                target = (row, column)
                blockers = tuple(
                    Blocker(peer, grid[peer[0]][peer[1]], shared_unit_kinds(target, peer))
                    for peer in sorted(peer_cells(target))
                    if grid[peer[0]][peer[1]] != 0
                )
                naked.append(
                    Deduction("naked_single", target, possible[0], None, possible, (), blockers, ())
                )

    hidden: list[Deduction] = []
    for unit in all_units():
        cells = cells_for_unit(unit)
        for digit in range(1, 10):
            eligible = tuple(
                cell for cell in cells
                if grid[cell[0]][cell[1]] == 0 and digit in candidates[cell[0]][cell[1]]
            )
            if len(eligible) == 1:
                target = eligible[0]
                excluded_positions = tuple(
                    PositionElimination(cell, _blockers_for_digit(grid, cell, digit))
                    for cell in cells
                    if grid[cell[0]][cell[1]] == 0
                    and cell != target
                    and digit not in candidates[cell[0]][cell[1]]
                )
                hidden.append(
                    Deduction(
                        "hidden_single",
                        target,
                        digit,
                        unit,
                        candidates[target[0]][target[1]],
                        eligible,
                        (),
                        excluded_positions,
                    )
                )
    return tuple(naked + hidden)


def _blockers_for_digit(grid: Grid, cell: Cell, digit: int) -> tuple[Blocker, ...]:
    return tuple(
        Blocker(peer, digit, shared_unit_kinds(cell, peer))
        for peer in sorted(peer_cells(cell))
        if grid[peer[0]][peer[1]] == digit
    )


def peer_cells(cell: Cell) -> frozenset[Cell]:
    return frozenset(
        peer
        for unit in units_for_cell(cell)
        for peer in cells_for_unit(unit)
        if peer != cell
    )


def validate_deduction(grid: Grid, deduction: Deduction) -> bool:
    """Rebuild the claim from this grid; matching only its target digit is insufficient."""
    from .candidates import calculate_candidates, find_conflicts

    if (
        not isinstance(deduction.target, tuple)
        or len(deduction.target) != 2
        or any(isinstance(index, bool) or not isinstance(index, int) for index in deduction.target)
    ):
        return False
    if not (0 <= deduction.target[0] < 9 and 0 <= deduction.target[1] < 9):
        return False
    if grid[deduction.target[0]][deduction.target[1]] != 0:
        return False
    candidates = calculate_candidates(grid)
    if find_conflicts(grid, candidates):
        return False
    valid = find_singles(grid, candidates)
    return deduction in valid
