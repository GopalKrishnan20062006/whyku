"""Sudoku-rule candidate calculation and conflict detection."""

from collections import defaultdict

from .models import Candidates, Conflict, Grid
from .units import all_units, cells_for_unit, units_for_cell


def calculate_candidates(grid: Grid) -> Candidates:
    result: list[tuple[tuple[int, ...], ...]] = []
    for row in range(9):
        candidate_row: list[tuple[int, ...]] = []
        for column in range(9):
            if grid[row][column] != 0:
                candidate_row.append(())
                continue
            unavailable = {
                grid[peer_row][peer_column]
                for unit in units_for_cell((row, column))
                for peer_row, peer_column in cells_for_unit(unit)
                if grid[peer_row][peer_column] != 0
            }
            candidate_row.append(tuple(digit for digit in range(1, 10) if digit not in unavailable))
        result.append(tuple(candidate_row))
    return tuple(result)


def find_conflicts(grid: Grid, candidates: Candidates) -> tuple[Conflict, ...]:
    reasons: dict[tuple[int, int], set[str]] = defaultdict(set)
    for unit in all_units():
        seen: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for cell in cells_for_unit(unit):
            digit = grid[cell[0]][cell[1]]
            if digit:
                seen[digit].append(cell)
        for duplicate_cells in seen.values():
            if len(duplicate_cells) > 1:
                for cell in duplicate_cells:
                    reasons[cell].add(f"duplicate_{unit.kind}")

    for row in range(9):
        for column in range(9):
            if grid[row][column] == 0 and not candidates[row][column]:
                reasons[(row, column)].add("no_candidates")

    return tuple(
        Conflict(cell, tuple(sorted(cell_reasons)))
        for cell, cell_reasons in sorted(reasons.items())
    )
