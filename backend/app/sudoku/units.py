"""Canonical row, column, and box definitions."""

from .models import Cell, Unit, UnitKind


def cells_for_unit(unit: Unit) -> tuple[Cell, ...]:
    if not 0 <= unit.index < 9:
        raise ValueError("unit index must be from 0 to 8")
    if unit.kind == "row":
        return tuple((unit.index, column) for column in range(9))
    if unit.kind == "column":
        return tuple((row, unit.index) for row in range(9))
    if unit.kind == "box":
        start_row = (unit.index // 3) * 3
        start_column = (unit.index % 3) * 3
        return tuple(
            (row, column)
            for row in range(start_row, start_row + 3)
            for column in range(start_column, start_column + 3)
        )
    raise ValueError(f"unknown unit kind: {unit.kind}")


def all_units() -> tuple[Unit, ...]:
    return tuple(Unit(kind, index) for kind in ("row", "column", "box") for index in range(9))


def units_for_cell(cell: Cell) -> tuple[Unit, Unit, Unit]:
    row, column = cell
    return (
        Unit("row", row),
        Unit("column", column),
        Unit("box", (row // 3) * 3 + column // 3),
    )


def shared_unit_kinds(first: Cell, second: Cell) -> tuple[UnitKind, ...]:
    return tuple(
        unit.kind
        for unit in units_for_cell(first)
        if second in cells_for_unit(unit)
    )
