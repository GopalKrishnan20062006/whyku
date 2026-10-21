from app.config import Settings
from app.main import create_app
from app.puzzles.catalog import PUZZLES
from fastapi.testclient import TestClient


class RecordingProvider:
    def __init__(self, mode="valid"):
        self.mode = mode
        self.calls = 0
        self.facts = None

    async def select_clause_ids(self, *, facts, clauses):
        self.calls += 1
        self.facts = facts
        ids = [clause.clause_id for clause in clauses]
        if self.mode == "valid":
            return list(reversed(ids))
        if self.mode == "unknown":
            return [ids[0], "made_up_claim"]
        if self.mode == "duplicate":
            return [ids[0], ids[0]]
        if self.mode == "partial":
            return [ids[0]]
        if self.mode == "freeform":
            return "This cell must contain 8."
        if self.mode == "quota":
            raise RuntimeError("provider quota exceeded")
        if self.mode == "unavailable":
            raise RuntimeError("model unavailable")
        if self.mode == "missing_key":
            raise RuntimeError("Gemini API key is not configured")
        if self.mode == "secret_failure":
            raise RuntimeError("quota denied key=test-secret-123 headers={'x-goog-api-key': 'test-secret-123'}")
        if self.mode == "slow":
            import asyncio
            await asyncio.sleep(0.1)
            return ids
        raise AssertionError(f"unexpected test mode: {self.mode}")


_DEFAULT_PROVIDER = object()


def _client(provider=_DEFAULT_PROVIDER, timeout=8):
    if provider is _DEFAULT_PROVIDER:
        provider = RecordingProvider()
    return TestClient(create_app(provider=provider, settings=Settings(explanation_timeout_seconds=timeout)))


def _payload(puzzle=PUZZLES[-1]):
    return {"puzzle_id": puzzle.puzzle_id, "grid": [list(row) for row in puzzle.initial_grid]}


def test_puzzle_catalog_and_load_never_expose_solution():
    with _client() as client:
        catalog = client.get("/api/puzzles")
        loaded = client.get(f"/api/puzzles/{PUZZLES[0].puzzle_id}")

    assert catalog.status_code == 200
    assert len(catalog.json()) == 5
    assert loaded.status_code == 200
    assert len(loaded.json()["grid"]) == 9
    assert "solution" not in loaded.json()
    assert "solution" not in loaded.json()["analysis"]


def test_unknown_puzzle_returns_404():
    with _client() as client:
        response = client.get("/api/puzzles/not-a-puzzle")
    assert response.status_code == 404


def test_backend_rejects_malformed_and_client_supplied_trusted_fields():
    body = _payload()
    body["grid"] = [[0] * 8 for _ in range(9)]
    with _client() as client:
        malformed = client.post("/api/analysis", json=body)
        forged = client.post(
            "/api/analysis",
            json={**_payload(), "solution": PUZZLES[-1].solution, "candidates": []},
        )
        boolean_digit = _payload()
        boolean_digit["grid"][0][0] = True
        strict_value = client.post("/api/analysis", json=boolean_digit)
    assert malformed.status_code == 422
    assert forged.status_code == 422
    assert strict_value.status_code == 422


def test_given_overwrite_is_rejected():
    body = _payload()
    body["grid"][0][0] = 9
    with _client() as client:
        response = client.post("/api/analysis", json=body)
    assert response.status_code == 422
    assert "cannot be changed" in response.json()["detail"]


def test_analysis_recomputes_candidates_and_returns_no_solution_values():
    body = _payload()
    with _client() as client:
        response = client.post("/api/analysis", json=body)

    assert response.status_code == 200
    data = response.json()
    assert len(data["candidates"]) == 9
    assert data["candidates"][0][0] == []
    assert data["rule_conflicts"] == []
    assert data["solution_mismatch_cells"] == []
    assert "solution" not in data


def test_solution_mismatch_is_separate_from_rule_conflict_and_blocks_provider():
    provider = RecordingProvider()
    body = _payload()
    # Find a rule-legal alternative using the server engine's candidate list.
    with _client() as client:
        current_analysis = client.post("/api/analysis", json=body).json()
    wrong_entry = next(
        (row, column, digit)
        for row in range(9)
        for column in range(9)
        if body["grid"][row][column] == 0
        for digit in current_analysis["candidates"][row][column]
        if digit != PUZZLES[-1].solution[row][column]
    )
    row, column, digit = wrong_entry
    body["grid"][row][column] = digit

    with _client(provider=provider) as client:
        analysis = client.post("/api/analysis", json=body).json()
        explanation = client.post("/api/hints/explanation", json=body).json()

    assert analysis["rule_conflicts"] == []
    assert [row, column] in analysis["solution_mismatch_cells"]
    assert "solution" not in analysis
    for other_row in range(9):
        for other_column in range(9):
            if (other_row, other_column) == (row, column):
                continue
            same_unit = (
                other_row == row
                or other_column == column
                or (other_row // 3, other_column // 3) == (row // 3, column // 3)
            )
            if same_unit and body["grid"][other_row][other_column] == 0:
                assert digit not in analysis["candidates"][other_row][other_column]
    assert explanation["status"] == "solution_mismatch"
    assert explanation["source"] is None
    assert provider.calls == 0


def test_rule_conflict_blocks_hints_and_is_reported_separately():
    provider = RecordingProvider()
    body = _payload()
    body["grid"][0][2] = body["grid"][0][0]
    with _client(provider=provider) as client:
        response = client.post("/api/hints", json=body)
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "rule_conflict"
    assert data["deduction"] is None
    assert data["analysis"]["rule_conflicts"]
    assert provider.calls == 0


def test_hint_endpoint_returns_backend_verified_deduction():
    with _client() as client:
        response = client.post("/api/hints", json=_payload())
    data = response.json()
    assert data["status"] == "available"
    assert data["deduction"]["technique"] in {"naked_single", "hidden_single"}
    assert data["deduction"]["digit"] in range(1, 10)


def test_gemini_selection_only_reorders_server_rendered_approved_clauses():
    provider = RecordingProvider()
    with _client(provider=provider) as client:
        response = client.post("/api/hints/explanation", json=_payload())
    data = response.json()

    assert data["source"] == "gemini"
    assert len(data["clause_ids"]) == 2
    assert data["explanation"] == (
        "Every other digit is ruled out by values already in its row, column, or box. "
        "This cell has only one remaining candidate."
    )
    assert isinstance(provider.facts, dict)
    assert "digit" not in provider.facts


def test_invalid_provider_selections_fall_back_to_template():
    for mode in ("unknown", "duplicate", "partial", "freeform"):
        provider = RecordingProvider(mode)
        with _client(provider=provider) as client:
            response = client.post("/api/hints/explanation", json=_payload())
        data = response.json()
        assert data["source"] == "template"
        assert len(data["clause_ids"]) == 2
        assert provider.calls == 1


def test_provider_quota_unavailable_timeout_and_missing_provider_use_offline_template():
    for provider, timeout in (
        (RecordingProvider("quota"), 8),
        (RecordingProvider("unavailable"), 8),
        (RecordingProvider("slow"), 0.01),
        (RecordingProvider("missing_key"), 8),
    ):
        with _client(provider=provider, timeout=timeout) as client:
            response = client.post("/api/hints/explanation", json=_payload())
        assert response.json()["source"] == "template"


def test_provider_failure_is_logged_safely_and_falls_back(caplog):
    from app.config import Settings
    from app.main import create_app

    provider = RecordingProvider("secret_failure")
    app = create_app(provider=provider, settings=Settings(gemini_api_key="test-secret-123"))
    with TestClient(app) as client:
        response = client.post("/api/hints/explanation", json=_payload())

    assert response.status_code == 200
    assert response.json()["source"] == "template"
    logs = caplog.text
    assert "RuntimeError" in logs
    assert "quota denied" in logs
    assert "test-secret-123" not in logs
    assert "headers=[REDACTED]" in logs
