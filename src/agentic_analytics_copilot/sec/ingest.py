"""Download, parse, and save each 10-K as data/sec/{ticker}/{fiscal_year}.json.

A filing already on disk is skipped, so reruns only fetch what is new. If the
10-K itself is missing a section (a cross-reference stub), the filing's Annual
Report exhibit (EX-13), when it has one, fills the gaps.
"""

from pathlib import Path

from agentic_analytics_copilot.sec.client import EdgarClient
from agentic_analytics_copilot.sec.parser import extract_sections
from agentic_analytics_copilot.sec.schema import (
    SECTION_NAMES,
    Company,
    Filing,
    Section,
    SectionName,
    TenK,
)


def _parse(
    client: EdgarClient, company: Company, filing: Filing, document: str
) -> dict[SectionName, Section | None]:
    url = filing.document_url(document)
    texts = extract_sections(client.fetch_document(filing, document), company.extra_titles)
    return {
        name: None if text is None else Section(text=text, url=url) for name, text in texts.items()
    }


def ingest_company(client: EdgarClient, company: Company, out_dir: Path) -> list[Path]:
    written = []
    for filing in client.list_10k_filings(company.cik, company.first_fiscal_year):
        path = out_dir / company.ticker / f"{filing.fiscal_year}.json"
        if path.exists():
            continue

        sections = _parse(client, company, filing, filing.primary_document)
        if any(sections[name] is None for name in SECTION_NAMES):
            annual_report = client.find_annual_report(filing)
            if annual_report is not None:
                exhibit = _parse(client, company, filing, annual_report)
                sections = {name: sections[name] or exhibit[name] for name in SECTION_NAMES}

        ten_k = TenK(
            ticker=company.ticker,
            cik=company.cik,
            fiscal_year=filing.fiscal_year,
            accession_number=filing.accession_number,
            sections=sections,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ten_k.model_dump_json(indent=1))
        written.append(path)
    return written
