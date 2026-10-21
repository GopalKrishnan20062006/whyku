"""Typed, immutable values shared by the pure Sudoku engine."""

from dataclasses import dataclass
from typing import Literal, TypeAlias

Cell: TypeAlias = tuple[int, int]
Grid: TypeAlias = tuple[tuple[int, ...], ...]
Candidates: TypeAlias = tuple[tuple[tuple[int, ...], ...], ...]
UnitKind: TypeAlias = Literal["row", "column", "box"]
Technique: TypeAlias = Literal["naked_single", "hidden_single"]


@dataclass(frozen=True)
class Unit:
    kind: UnitKind
    index: int


@dataclass(frozen=True)
class Conflict:
    cell: Cell
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Blocker:
    cell: Cell
    digit: int
    shared_units: tuple[UnitKind, ...]


@dataclass(frozen=True)
class PositionElimination:
    cell: Cell
    blockers: tuple[Blocker, ...]


@dataclass(frozen=True)
class Deduction:
    technique: Technique
    target: Cell
    digit: int
    unit: Unit | None
    candidate_digits: tuple[int, ...]
    eligible_cells: tuple[Cell, ...]
    blockers: tuple[Blocker, ...]
    excluded_positions: tuple[PositionElimination, ...]


@dataclass(frozen=True)
class Analysis:
    candidates: Candidates
    conflicts: tuple[Conflict, ...]
    mismatches: tuple[Cell, ...]
    is_full: bool
    is_solved: bool
    deduction: Deduction | None
    hint_block_reason: str | None
