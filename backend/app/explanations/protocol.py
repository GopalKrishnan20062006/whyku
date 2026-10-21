"""Provider contract: select clause IDs only; never write user-facing claims."""

from collections.abc import Sequence
from typing import Protocol

from .renderer import ApprovedClause


class ExplanationProvider(Protocol):
    async def select_clause_ids(
        self,
        *,
        facts: dict[str, object],
        clauses: Sequence[ApprovedClause],
    ) -> list[str]: ...
