import pytest
from sqlalchemy import text

from agentic_analytics_copilot.db import get_engine


def test_engine_connects_to_postgres() -> None:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception:
        pytest.skip("Postgres not reachable")
