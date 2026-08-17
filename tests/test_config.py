import pytest

from agentic_analytics_copilot.config import Settings


def test_settings_reads_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/db")

    settings = Settings()

    assert settings.database_url == "postgresql+psycopg://u:p@localhost:5432/db"
