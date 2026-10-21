"""Clause selection, independent validation, and deterministic fallback."""

import asyncio
import logging
import re
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

logger = logging.getLogger(__name__)


class ExplanationService:
    def __init__(
        self,
        provider: ExplanationProvider | None,
        timeout_seconds: float = 8.0,
        sensitive_values: tuple[str, ...] = (),
    ):
        self._provider = provider
        self._timeout_seconds = timeout_seconds
        self._sensitive_values = tuple(value for value in sensitive_values if value)

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
            return render_clauses(deduction, ordered_ids, source="gemini")
        except Exception as error:
            logger.warning(
                "Explanation provider failed (%s): %s; using template fallback",
                type(error).__name__,
                _sanitized_message(error, self._sensitive_values),
            )
            return template_explanation(deduction)


def _sanitized_message(error: Exception, sensitive_values: tuple[str, ...]) -> str:
    message = str(error)
    for secret in sensitive_values:
        message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"(?i)AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", message)
    message = re.sub(
        r"(?i)(x-goog-api-key|authorization|api[_ -]?key)\s*[:=]\s*[^,\s}\]]+",
        r"\1=[REDACTED]",
        message,
    )
    message = re.sub(r"(?i)headers?\s*[:=]\s*\{[^}]*\}", "headers=[REDACTED]", message)
    message = re.sub(r"https?://\S+", "[URL]", message)
    message = " ".join(message.split())
    return message[:500] or "provider request failed without an error message"


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
