"""JSON contracts at the FastAPI boundary."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictInt

from app.sudoku.models import Technique, UnitKind

Cell = tuple[int, int]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BoardRequest(StrictModel):
    puzzle_id: str
    grid: list[list[StrictInt]]


class PuzzleSummary(StrictModel):
    puzzle_id: str
    name: str
    level: str
    techniques: list[str]


class ConflictResponse(StrictModel):
    cell: Cell
    reasons: list[str]


class AnalysisResponse(StrictModel):
    candidates: list[list[list[int]]]
    rule_conflicts: list[ConflictResponse]
    solution_mismatch_cells: list[Cell]
    is_full: bool
    is_solved: bool
    hints_enabled: bool
    hint_block_reason: str | None


class PuzzleResponse(PuzzleSummary):
    grid: list[list[int]]
    analysis: AnalysisResponse


class UnitResponse(StrictModel):
    kind: UnitKind
    index: int


class BlockerResponse(StrictModel):
    cell: Cell
    digit: int
    shared_units: list[UnitKind]


class PositionEliminationResponse(StrictModel):
    cell: Cell
    blockers: list[BlockerResponse]


class DeductionResponse(StrictModel):
    technique: Technique
    target: Cell
    digit: int
    unit: UnitResponse | None
    candidate_digits: list[int]
    eligible_cells: list[Cell]
    blockers: list[BlockerResponse]
    excluded_positions: list[PositionEliminationResponse]


HintStatus = Literal[
    "available",
    "rule_conflict",
    "solution_mismatch",
    "completed",
    "no_supported_single",
]


class HintResponse(StrictModel):
    status: HintStatus
    message: str | None
    deduction: DeductionResponse | None
    analysis: AnalysisResponse


class ExplanationResponse(StrictModel):
    status: HintStatus
    message: str | None
    deduction: DeductionResponse | None
    explanation: str | None
    source: Literal["gemini", "template"] | None
    clause_ids: list[str]
