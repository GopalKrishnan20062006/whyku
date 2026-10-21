"""Clause selection, independent validation, and deterministic fallback."""

import asyncio
from collections.abc import Sequence

from app.sudoku.models import Deduction
from .protocol import ExplanationProvider
from .renderer import (
    ApprovedClause,
    RenderedExplanation,
    approved_clauses,
    deduction_facts,
    render_clauses,
    template_explanation,
)


class ExplanationService:
    def __init__(self, provider: ExplanationProvider | None, timeout_seconds: float = 8.0):
        self._provider = provider
        self._timeout_seconds = timeout_seconds

    async def explain(self, deduction: Deduction) -> RenderedExplanation:
        clauses = approved_clauses(deduction)
        if self._provider is None:
            return template_explanation(deduction)
        try:
            selected = await asyncio.wait_for(
                self._provider.select_clause_ids(
                    facts=deduction_facts(deduction),
                    clauses=clauses,
                ),
                timeout=self._timeout_seconds,
            )
            ordered_ids = _validate_selection(selected, clauses)
            return render_clauses(deduction, ordered_ids, source="ai")
        except Exception:
            return template_explanation(deduction)


def _validate_selection(
    selected: Sequence[str],
    clauses: Sequence[ApprovedClause],
) -> tuple[str, ...]:
    if not isinstance(selected, (list, tuple)):
        raise ValueError("Provider must return a list of approved IDs")
    allowed = {clause.clause_id for clause in clauses}
    if len(selected) != len(allowed) or len(set(selected)) != len(selected) or set(selected) != allowed:
        raise ValueError("Provider selection must be a permutation of the approved IDs")
    return tuple(selected)
