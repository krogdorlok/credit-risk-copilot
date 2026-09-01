"""Load every downloaded Freddie Mac sample-dataset year (data/sample_*.zip) into Postgres."""

import zipfile
from pathlib import Path

from agentic_analytics_copilot.db import get_engine
from agentic_analytics_copilot.loans.loader import (
    create_tables,
    load_originations,
    load_performance,
)
from agentic_analytics_copilot.loans.parser import parse_origination_file, parse_performance_file

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"


def main() -> None:
    engine = get_engine()
    create_tables(engine)

    for zip_path in sorted(DATA_DIR.glob("sample_*.zip")):
        year = zip_path.stem.removeprefix("sample_")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(RAW_DIR)

        orig = parse_origination_file(RAW_DIR / f"sample_orig_{year}.txt")
        perf = parse_performance_file(RAW_DIR / f"sample_perf_{year}.txt")

        orig_loaded = load_originations(engine, orig.records)
        perf_loaded = load_performance(engine, perf.records)

        print(
            f"{year}: origination {orig_loaded}/{len(orig.records)} loaded "
            f"({len(orig.errors)} errors), performance {perf_loaded}/{len(perf.records)} loaded "
            f"({len(perf.errors)} errors)"
        )


if __name__ == "__main__":
    main()
