from pathlib import Path

import pytest
from sqlalchemy import delete, select

from agentic_analytics_copilot.db import get_engine
from agentic_analytics_copilot.loans.loader import (
    create_tables,
    load_originations,
    load_performance,
)
from agentic_analytics_copilot.loans.models import LoanOriginationRow, LoanPerformanceRow
from agentic_analytics_copilot.loans.parser import parse_origination_file, parse_performance_file

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def engine():  # type: ignore[no-untyped-def]
    engine = get_engine()
    try:
        with engine.connect():
            pass
    except Exception:
        pytest.skip("Postgres not reachable")
    create_tables(engine)
    yield engine
    with engine.begin() as conn:
        conn.execute(
            delete(LoanPerformanceRow).where(LoanPerformanceRow.loan_sequence_number.like("TEST%"))
        )
        conn.execute(
            delete(LoanOriginationRow).where(LoanOriginationRow.loan_sequence_number.like("TEST%"))
        )


def test_load_originations_dedups_on_rerun(engine) -> None:  # type: ignore[no-untyped-def]
    records = parse_origination_file(FIXTURES / "sample_orig.txt").records

    first_count = load_originations(engine, records)
    second_count = load_originations(engine, records)

    assert first_count == len(records)
    assert second_count == 0

    with engine.connect() as conn:
        rows = conn.execute(
            select(LoanOriginationRow).where(LoanOriginationRow.loan_sequence_number.like("TEST%"))
        ).all()
    assert len(rows) == len(records)


def test_load_performance_dedups_on_rerun(engine) -> None:  # type: ignore[no-untyped-def]
    load_originations(engine, parse_origination_file(FIXTURES / "sample_orig.txt").records)
    records = parse_performance_file(FIXTURES / "sample_perf.txt").records

    first_count = load_performance(engine, records)
    second_count = load_performance(engine, records)

    assert first_count == len(records)
    assert second_count == 0
