"""Bulk-load parsed loan records into Postgres, deduped on primary key.

Loads via COPY into an unconstrained temp staging table, then a single
set-based INSERT ... ON CONFLICT DO NOTHING from staging into the real table.
Parameterized multi-row INSERTs (even batched) ran at ~1000 rows/sec on this
dataset's performance file, because SQLAlchemy pays a Python-level
type-coercion cost per bound value; COPY does that work in psycopg's C-level
protocol instead, which loaded the same 1.46M-row file in under 40 seconds.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Engine, text

from agentic_analytics_copilot.loans.models import Base
from agentic_analytics_copilot.loans.schema import (
    ORIGINATION_FIELDS,
    PERFORMANCE_FIELDS,
    LoanOrigination,
    LoanPerformance,
)


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def _copy_upsert(
    engine: Engine,
    table_name: str,
    fields: list[str],
    rows: list[tuple[Any, ...]],  # Any: heterogeneous column values (str/int/float/date/None)
    index_elements: list[str],
) -> int:
    if not rows:
        return 0
    staging = f"_staging_{table_name}"
    columns = ",".join(fields)
    conflict_target = ",".join(index_elements)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE TEMP TABLE {staging} (LIKE {table_name}) ON COMMIT DROP"))
        assert conn.connection.dbapi_connection is not None
        # psycopg3's COPY support isn't part of SQLAlchemy's generic DBAPI stubs.
        raw_conn: Any = conn.connection.dbapi_connection
        with raw_conn.cursor() as cur, cur.copy(f"COPY {staging} ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(row)
        result = conn.execute(
            text(
                f"INSERT INTO {table_name} SELECT * FROM {staging} "
                f"ON CONFLICT ({conflict_target}) DO NOTHING "
                f"RETURNING {index_elements[0]}"
            )
        )
        return len(result.fetchall())


def load_originations(engine: Engine, records: Sequence[LoanOrigination]) -> int:
    rows = [tuple(getattr(r, f) for f in ORIGINATION_FIELDS) for r in records]
    return _copy_upsert(engine, "loans", ORIGINATION_FIELDS, rows, ["loan_sequence_number"])


def load_performance(engine: Engine, records: Sequence[LoanPerformance]) -> int:
    rows = [tuple(getattr(r, f) for f in PERFORMANCE_FIELDS) for r in records]
    return _copy_upsert(
        engine,
        "loan_performance",
        PERFORMANCE_FIELDS,
        rows,
        ["loan_sequence_number", "monthly_reporting_period"],
    )
