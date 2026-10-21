from app.config import Settings


def test_default_model_and_timeout_are_available_without_api_key(monkeypatch):
    monkeypatch.delenv("EXPLANATION_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("EXPLANATION_TIMEOUT_SECONDS", raising=False)

    settings = Settings.from_environment()

    assert settings.explanation_provider == "gemini"
    assert settings.gemini_api_key == ""
    assert settings.gemini_model == "gemini-3.5-flash-lite"
    assert settings.explanation_timeout_seconds == 8


def test_model_and_timeout_are_environment_configurable(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "a-configured-model")
    monkeypatch.setenv("EXPLANATION_TIMEOUT_SECONDS", "2.5")

    settings = Settings.from_environment()

    assert settings.gemini_model == "a-configured-model"
    assert settings.explanation_timeout_seconds == 2.5


def test_invalid_timeout_uses_eight_second_default(monkeypatch):
    monkeypatch.setenv("EXPLANATION_TIMEOUT_SECONDS", "inf")
    assert Settings.from_environment().explanation_timeout_seconds == 8
