"""Server-owned facts and text. Provider output changes ordering only."""

from dataclasses import dataclass

from app.sudoku.models import Deduction


@dataclass(frozen=True)
class ApprovedClause:
    clause_id: str
    selection_description: str


@dataclass(frozen=True)
class RenderedExplanation:
    text: str
    source: str
    clause_ids: tuple[str, ...]


def approved_clauses(deduction: Deduction) -> tuple[ApprovedClause, ...]:
    if deduction.technique == "naked_single":
        return (
            ApprovedClause("naked.cell_has_one_candidate", "Describe the target cell's one remaining candidate."),
            ApprovedClause("naked.peers_rule_out_others", "Explain that row, column, and box values eliminate all other candidates."),
        )
    return (
        ApprovedClause("hidden.unit_has_one_position", "Describe that the target digit has one position in the relevant unit."),
        ApprovedClause("hidden.other_positions_blocked", "Explain that every other empty position in that unit is blocked."),
    )


def deduction_facts(deduction: Deduction) -> dict[str, object]:
    facts: dict[str, object] = {
        "technique": deduction.technique,
        "target_cell": {"row": deduction.target[0] + 1, "column": deduction.target[1] + 1},
    }
    if deduction.technique == "naked_single":
        facts["remaining_candidate_count"] = len(deduction.candidate_digits)
        facts["eliminated_candidate_count"] = len({blocker.digit for blocker in deduction.blockers})
    else:
        assert deduction.unit is not None
        facts["unit"] = {"kind": deduction.unit.kind, "number": deduction.unit.index + 1}
        facts["eligible_position_count"] = len(deduction.eligible_cells)
        facts["excluded_empty_position_count"] = len(deduction.excluded_positions)
    return facts


def render_clauses(deduction: Deduction, clause_ids: tuple[str, ...], *, source: str) -> RenderedExplanation:
    if deduction.technique == "naked_single":
        text_by_id = {
            "naked.cell_has_one_candidate": "This cell has only one remaining candidate.",
            "naked.peers_rule_out_others": (
                "Every other digit is ruled out by values already in its row, column, or box."
            ),
        }
    else:
        assert deduction.unit is not None
        unit_name = {"row": "row", "column": "column", "box": "box"}[deduction.unit.kind]
        text_by_id = {
            "hidden.unit_has_one_position": (
                f"In {unit_name} {deduction.unit.index + 1}, the target digit has only one legal position."
            ),
            "hidden.other_positions_blocked": (
                f"Every other empty cell in that {unit_name} is blocked from holding that digit "
                "by a value in its row, column, or box."
            ),
        }
    return RenderedExplanation(
        text=" ".join(text_by_id[clause_id] for clause_id in clause_ids),
        source=source,
        clause_ids=clause_ids,
    )


def template_explanation(deduction: Deduction) -> RenderedExplanation:
    all_ids = tuple(clause.clause_id for clause in approved_clauses(deduction))
    return render_clauses(deduction, all_ids, source="template")
