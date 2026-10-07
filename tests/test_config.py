import pytest

from agentic_analytics_copilot.config import Settings


def test_settings_reads_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/db")
    monkeypatch.setenv("FRED_API_KEY", "test-key")

    settings = Settings()

    assert settings.database_url == "postgresql+psycopg://u:p@localhost:5432/db"


def test_settings_reads_fred_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/db")
    monkeypatch.setenv("FRED_API_KEY", "abc123")

    settings = Settings()

    assert settings.fred_api_key == "abc123"


def test_settings_reads_sec_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "Copilot me@example.com")

    assert Settings().sec_user_agent == "Copilot me@example.com"
