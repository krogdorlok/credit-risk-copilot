import os
from collections.abc import Iterator

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, text

from agentic_analytics_copilot.db import get_engine
from agentic_analytics_copilot.loans.loader import create_tables


class DbTestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_database_url: str


TEST_DATABASE_URL = DbTestSettings().test_database_url
if not TEST_DATABASE_URL.endswith("_test"):
    raise RuntimeError(f"TEST_DATABASE_URL must end in _test, got {TEST_DATABASE_URL}")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = get_engine()
    create_tables(engine)
    yield engine
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE loans, loan_performance"))
