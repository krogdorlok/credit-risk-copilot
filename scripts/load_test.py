"""Fire concurrent analytical queries through the app engine and report latency per query type."""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text

from agentic_analytics_copilot.db import get_engine

USERS = 100

QUERIES = {
    "heavy": "select monthly_reporting_period, avg((current_loan_delinquency_status <> '00')::int) "
    "from loan_performance where monthly_reporting_period between '2022-01-01' and '2022-12-01' "
    "group by 1",
    "medium": "select property_state, count(*), avg(credit_score), avg(original_ltv) "
    "from loans group by 1",
    "light": "select * from loan_performance where loan_sequence_number = :id",
}

engine = get_engine()
with engine.connect() as conn:
    loan_id = conn.execute(text("select loan_sequence_number from loans limit 1")).scalar_one()

kinds = list(QUERIES)


def user(i: int) -> tuple[str, float, str | None]:
    kind = kinds[i % 3]
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text(QUERIES[kind]), {"id": loan_id}).fetchall()
        return kind, time.perf_counter() - start, None
    except Exception as exc:
        return kind, time.perf_counter() - start, type(exc).__name__


wall = time.perf_counter()
with ThreadPoolExecutor(USERS) as pool:
    results = list(pool.map(user, range(USERS)))
wall = time.perf_counter() - wall

print(f"{USERS} concurrent users, pool_size={engine.pool.size()}, wall time {wall:.1f}s\n")
for kind in kinds:
    ok = sorted(t for k, t, e in results if k == kind and e is None)
    errs = [e for k, _, e in results if k == kind and e]
    line = f"{kind:6} ok={len(ok):3} errors={len(errs):3}"
    if ok:
        p95 = ok[int(len(ok) * 0.95) - 1] if len(ok) > 1 else ok[0]
        line += f"  p50={statistics.median(ok):6.1f}s  p95={p95:6.1f}s  max={ok[-1]:6.1f}s"
    if errs:
        line += f"  ({', '.join(sorted(set(errs)))})"
    print(line)
