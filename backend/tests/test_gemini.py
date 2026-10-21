import asyncio
import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.config import Settings
from app.explanations.gemini import GeminiProvider
from app.explanations.renderer import approved_clauses, deduction_facts
from app.explanations.service import ExplanationService
from app.puzzles.catalog import PUZZLES
from app.sudoku.engine import analyze_grid


def _deduction():
    puzzle = PUZZLES[0]
    result = analyze_grid(puzzle.initial_grid, puzzle.initial_grid, puzzle.solution)
    assert result.deduction is not None
    return result.deduction


def _install_fake_genai(monkeypatch, response_text=None, failure=None):
    clients = []

    class FakeModels:
        async def generate_content(self, *, model, contents, config):
            self.model = model
            self.contents = contents
            self.config = config
            if failure:
                raise RuntimeError(failure)
            return SimpleNamespace(text=response_text)

    class FakeClient:
        def __init__(self, *, api_key, http_options):
            self.models = FakeModels()
            self.aio = SimpleNamespace(models=self.models, aclose=self._aclose)
            self.api_key = api_key
            self.http_options = http_options
            clients.append(self)

        async def _aclose(self):
            return None

    fake_types = SimpleNamespace(
        HttpOptions=lambda **kwargs: kwargs,
        HttpRetryOptions=lambda **kwargs: kwargs,
        GenerateContentConfig=lambda **kwargs: kwargs,
    )
    fake_genai = ModuleType("google.genai")
    fake_genai.Client = FakeClient
    fake_google = ModuleType("google")
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    return clients


def test_gemini_schema_omits_rejected_field_and_accepts_approved_ids(monkeypatch):
    deduction = _deduction()
    clauses = approved_clauses(deduction)
    expected_ids = [clause.clause_id for clause in reversed(clauses)]
    clients = _install_fake_genai(monkeypatch, json.dumps({"clause_ids": expected_ids}))
    provider = GeminiProvider(Settings(gemini_api_key="test-key", explanation_timeout_seconds=8))

    selected = asyncio.run(
        provider.select_clause_ids(facts=deduction_facts(deduction), clauses=clauses)
    )

    schema = clients[0].models.config["response_schema"]
    assert selected == expected_ids
    assert "additionalProperties" not in schema
    assert set(schema) == {"type", "properties", "required"}
    assert clients[0].http_options["timeout"] == 10_000


@pytest.mark.parametrize(
    "response_text",
    [
        "not json",
        '{"clause_ids": [], "extra": "claim"}',
        '{"unexpected": []}',
        '{"clause_ids": "not-an-array"}',
    ],
)
def test_gemini_provider_rejects_malformed_structured_output(monkeypatch, response_text):
    deduction = _deduction()
    clauses = approved_clauses(deduction)
    _install_fake_genai(monkeypatch, response_text)
    provider = GeminiProvider(Settings(gemini_api_key="test-key"))

    with pytest.raises((ValueError, json.JSONDecodeError)):
        asyncio.run(provider.select_clause_ids(facts=deduction_facts(deduction), clauses=clauses))


def test_schema_rejection_logs_safe_diagnostic_and_uses_template(monkeypatch, caplog):
    deduction = _deduction()
    clauses = approved_clauses(deduction)
    _install_fake_genai(
        monkeypatch,
        failure="Unknown name additional_properties; x-goog-api-key=test-key",
    )
    settings = Settings(gemini_api_key="test-key")
    service = ExplanationService(
        GeminiProvider(settings), sensitive_values=(settings.gemini_api_key,)
    )

    rendered = asyncio.run(service.explain(deduction))

    assert rendered.source == "template"
    assert len(rendered.clause_ids) == len(clauses)
    assert "RuntimeError" in caplog.text
    assert "Unknown name additional_properties" in caplog.text
    assert "test-key" not in caplog.text
    assert "x-goog-api-key=[REDACTED]" in caplog.text
