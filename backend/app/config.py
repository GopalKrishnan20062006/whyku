"""Environment-backed configuration. Secrets are loaded only by the backend."""

from dataclasses import dataclass
import math
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    explanation_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    explanation_timeout_seconds: float = 8.0

    @classmethod
    def from_environment(cls) -> "Settings":
        try:
            timeout = float(os.getenv("EXPLANATION_TIMEOUT_SECONDS", "8"))
            if timeout <= 0 or not math.isfinite(timeout):
                timeout = 8.0
        except ValueError:
            timeout = 8.0
        return cls(
            explanation_provider=os.getenv("EXPLANATION_PROVIDER", "gemini").strip().lower(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip(),
            explanation_timeout_seconds=timeout,
        )
