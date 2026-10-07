"""Fetch and parse every 10-K for the fixed company set into data/sec/."""

from pathlib import Path

from agentic_analytics_copilot.config import Settings
from agentic_analytics_copilot.sec.client import EdgarClient
from agentic_analytics_copilot.sec.companies import COMPANIES
from agentic_analytics_copilot.sec.ingest import ingest_company
from agentic_analytics_copilot.sec.schema import TenK

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sec"


def main() -> None:
    client = EdgarClient(user_agent=Settings().sec_user_agent)
    for company in COMPANIES:
        for path in ingest_company(client, company, OUT_DIR):
            ten_k = TenK.model_validate_json(path.read_text())
            missing = [name for name, section in ten_k.sections.items() if section is None]
            print(f"{company.ticker} FY{ten_k.fiscal_year}: missing {missing or 'none'}")


if __name__ == "__main__":
    main()
