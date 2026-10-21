"""Gemini adapter constrained to selecting the approved clause IDs."""

import json
from collections.abc import Sequence

from app.config import Settings
from .renderer import ApprovedClause


class GeminiProvider:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def select_clause_ids(
        self,
        *,
        facts: dict[str, object],
        clauses: Sequence[ApprovedClause],
    ) -> list[str]:
        if not self._settings.gemini_api_key:
            raise RuntimeError("Gemini API key is not configured")

        from google import genai
        from google.genai import types

        clause_ids = [clause.clause_id for clause in clauses]
        response_schema = {
            "type": "object",
            "properties": {
                "clause_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": clause_ids},
                    "minItems": len(clause_ids),
                    "maxItems": len(clause_ids),
                }
            },
            "required": ["clause_ids"],
            "additionalProperties": False,
        }
        prompt = json.dumps(
            {
                "task": "Choose and order every approved explanation clause. Return clause IDs only.",
                "deduction_facts": facts,
                "approved_clauses": [
                    {"id": clause.clause_id, "purpose": clause.selection_description}
                    for clause in clauses
                ],
            },
            separators=(",", ":"),
        )
        client = genai.Client(
            api_key=self._settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=int(self._settings.explanation_timeout_seconds * 1000),
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
        try:
            response = await client.aio.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
            if not response.text:
                raise ValueError("Gemini returned no structured content")
            payload = json.loads(response.text)
            if not isinstance(payload, dict) or set(payload) != {"clause_ids"}:
                raise ValueError("Gemini returned an unexpected response shape")
            selected = payload["clause_ids"]
            if not isinstance(selected, list) or not all(isinstance(value, str) for value in selected):
                raise ValueError("Gemini clause selections must be strings")
            return selected
        finally:
            await client.aio.aclose()
