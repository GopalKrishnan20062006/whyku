"""Input validation for Sudoku grids and immutable puzzle givens."""

from collections.abc import Sequence

from .models import Grid


def normalize_grid(value: Sequence[Sequence[int]], *, name: str = "grid") -> Grid:
    if not isinstance(value, (list, tuple)) or len(value) != 9:
        raise ValueError(f"{name} must contain exactly 9 rows")

    rows: list[tuple[int, ...]] = []
    for row_index, row in enumerate(value):
        if not isinstance(row, (list, tuple)) or len(row) != 9:
            raise ValueError(f"{name} row {row_index} must contain exactly 9 values")
        normalized: list[int] = []
        for column_index, digit in enumerate(row):
            if isinstance(digit, bool) or not isinstance(digit, int) or not 0 <= digit <= 9:
                raise ValueError(
                    f"{name} cell ({row_index}, {column_index}) must be an integer from 0 to 9"
                )
            normalized.append(digit)
        rows.append(tuple(normalized))
    return tuple(rows)


def validate_givens(grid: Grid, givens: Grid) -> None:
    for row in range(9):
        for column in range(9):
            given = givens[row][column]
            if given and grid[row][column] != given:
                raise ValueError(f"given cell ({row}, {column}) cannot be changed")


def validate_solution(solution: Grid) -> None:
    """Reject a malformed or invalid known solution before using it for status checks."""
    from .units import all_units

    if any(value == 0 for row in solution for value in row):
        raise ValueError("solution must be a complete grid")
    for unit in all_units():
        values = {solution[row][column] for row, column in unit_cells(unit)}
        if values != set(range(1, 10)):
            raise ValueError(f"solution has invalid digits in {unit.kind} {unit.index + 1}")


def unit_cells(unit):
    from .units import cells_for_unit

    return cells_for_unit(unit)
