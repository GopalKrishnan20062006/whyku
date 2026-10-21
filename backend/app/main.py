"""FastAPI app factory and HTTP trust boundary for Whyku."""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException

from app.config import Settings
from app.explanations.gemini import GeminiProvider
from app.explanations.protocol import ExplanationProvider
from app.explanations.service import ExplanationService
from app.puzzles.catalog import PUZZLE_BY_ID, PUZZLES, Puzzle
from app.schemas import (
    AnalysisResponse,
    BoardRequest,
    ConflictResponse,
    DeductionResponse,
    ExplanationResponse,
    HintResponse,
    PuzzleResponse,
    PuzzleSummary,
)
from app.sudoku.engine import analyze_grid
from app.sudoku.models import Analysis

_UNSET = object()


def create_app(
    *,
    provider: ExplanationProvider | None | object = _UNSET,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings.from_environment()
    if provider is _UNSET:
        selected_provider: ExplanationProvider | None = (
            GeminiProvider(settings) if settings.explanation_provider == "gemini" else None
        )
    else:
        selected_provider = provider  # type: ignore[assignment]

    app = FastAPI(title="Whyku API", version="0.1.0")
    app.state.explanation_service = ExplanationService(
        selected_provider,
        timeout_seconds=settings.explanation_timeout_seconds,
        sensitive_values=(settings.gemini_api_key,),
    )

    @app.get("/api/puzzles", response_model=list[PuzzleSummary])
    def list_puzzles() -> list[PuzzleSummary]:
        return [_summary(puzzle) for puzzle in PUZZLES]

    @app.get("/api/puzzles/{puzzle_id}", response_model=PuzzleResponse)
    def load_puzzle(puzzle_id: str) -> PuzzleResponse:
        puzzle = _get_puzzle(puzzle_id)
        result = _analyze(puzzle, puzzle.initial_grid)
        return PuzzleResponse(
            **_summary(puzzle).model_dump(),
            grid=puzzle.initial_grid,
            analysis=_analysis_response(result),
        )

    @app.post("/api/analysis", response_model=AnalysisResponse)
    def analyze_board(request: BoardRequest) -> AnalysisResponse:
        puzzle = _get_puzzle(request.puzzle_id)
        return _analysis_response(_analyze(puzzle, request.grid))

    @app.post("/api/hints", response_model=HintResponse)
    def get_hint(request: BoardRequest) -> HintResponse:
        puzzle = _get_puzzle(request.puzzle_id)
        result = _analyze(puzzle, request.grid)
        status, message = _hint_status(result)
        return HintResponse(
            status=status,
            message=message,
            deduction=_deduction_response(result),
            analysis=_analysis_response(result),
        )

    @app.post("/api/hints/explanation", response_model=ExplanationResponse)
    async def explain_hint(request: BoardRequest) -> ExplanationResponse:
        puzzle = _get_puzzle(request.puzzle_id)
        result = _analyze(puzzle, request.grid)
        status, message = _hint_status(result)
        if result.deduction is None:
            return ExplanationResponse(
                status=status,
                message=message,
                deduction=None,
                explanation=None,
                source=None,
                clause_ids=[],
            )

        rendered = await app.state.explanation_service.explain(result.deduction)
        return ExplanationResponse(
            status="available",
            message=None,
            deduction=_deduction_response(result),
            explanation=rendered.text,
            source=rendered.source,
            clause_ids=list(rendered.clause_ids),
        )

    return app


def _summary(puzzle: Puzzle) -> PuzzleSummary:
    return PuzzleSummary(
        puzzle_id=puzzle.puzzle_id,
        name=puzzle.name,
        level=puzzle.level,
        techniques=list(puzzle.techniques),
    )


def _get_puzzle(puzzle_id: str) -> Puzzle:
    puzzle = PUZZLE_BY_ID.get(puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail="Unknown puzzle ID")
    return puzzle


def _analyze(puzzle: Puzzle, grid) -> Analysis:
    try:
        return analyze_grid(grid, puzzle.initial_grid, puzzle.solution)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _analysis_response(result: Analysis) -> AnalysisResponse:
    return AnalysisResponse(
        candidates=result.candidates,
        rule_conflicts=[ConflictResponse.model_validate(asdict(item)) for item in result.conflicts],
        solution_mismatch_cells=result.mismatches,
        is_full=result.is_full,
        is_solved=result.is_solved,
        hints_enabled=result.deduction is not None,
        hint_block_reason=result.hint_block_reason,
    )


def _deduction_response(result: Analysis) -> DeductionResponse | None:
    return DeductionResponse.model_validate(asdict(result.deduction)) if result.deduction else None


def _hint_status(result: Analysis) -> tuple[str, str | None]:
    reason = result.hint_block_reason
    if reason == "rule_conflict":
        return reason, "Resolve the Sudoku rule conflict before requesting a hint."
    if reason == "solution_mismatch":
        return reason, "Correct or erase the flagged entry before requesting a hint."
    if reason == "completed":
        return reason, "Puzzle solved. You worked it out!"
    if reason == "no_supported_single":
        return reason, "No naked or hidden single is available right now."
    return "available", None


app = create_app()
