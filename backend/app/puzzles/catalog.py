"""Curated puzzles and their backend-only known solutions."""

from dataclasses import dataclass

from app.sudoku.models import Grid
from app.sudoku.validation import normalize_grid


def _grid(rows: tuple[str, ...]) -> Grid:
    return normalize_grid([[int(value) for value in row] for row in rows])


SOLUTION = _grid(
    (
        "534678912", "672195348", "198342567", "859761423", "426853791",
        "713924856", "961537284", "287419635", "345286179",
    )
)


@dataclass(frozen=True)
class Puzzle:
    puzzle_id: str
    name: str
    level: str
    techniques: tuple[str, ...]
    initial_grid: Grid
    solution: Grid


_SINGLES = ("Naked singles", "Hidden singles")
PUZZLES: tuple[Puzzle, ...] = (
    Puzzle(
        "whyku-01", "Quick Start", "Gentle", _SINGLES,
        _grid(("534070000", "600195048", "098002067", "809060423", "400853701", "703024856", "960037284", "200419635", "040086179")),
        SOLUTION,
    ),
    Puzzle(
        "whyku-02", "A Little More Space", "Easy", _SINGLES,
        _grid(("534670900", "600195000", "098000560", "809760403", "400803001", "703920856", "061000280", "087419035", "300280179")),
        SOLUTION,
    ),
    Puzzle(
        "whyku-03", "Steady Steps", "Easy", _SINGLES,
        _grid(("530670910", "600195000", "198300560", "809060003", "400803701", "703020006", "060030280", "080419035", "000080079")),
        SOLUTION,
    ),
    Puzzle(
        "whyku-04", "Look Across the Unit", "Intermediate", _SINGLES,
        _grid(("530070900", "670195000", "098002060", "800060403", "400853001", "700020006", "060000280", "000419005", "000086079")),
        SOLUTION,
    ),
    Puzzle(
        "whyku-05", "Classic Practice", "Intermediate", _SINGLES,
        _grid(("530070000", "600195000", "098000060", "800060003", "400803001", "700020006", "060000280", "000419005", "000080079")),
        SOLUTION,
    ),
)
PUZZLE_BY_ID = {puzzle.puzzle_id: puzzle for puzzle in PUZZLES}
