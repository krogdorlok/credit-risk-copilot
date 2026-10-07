import json
from pathlib import Path

import httpx

from agentic_analytics_copilot.sec.client import EdgarClient
from agentic_analytics_copilot.sec.companies import COMPANIES
from agentic_analytics_copilot.sec.ingest import ingest_company
from agentic_analytics_copilot.sec.schema import Company, SectionName, TenK

FILLER = "Credit losses rose as mortgage rates increased. " * 60

STANDARD_10K = (
    f"<h2>Item 1. Business</h2><p>BUSINESS {FILLER}</p>"
    f"<h2>Item 1A. Risk Factors</h2><p>RISK {FILLER}</p>"
    f"<h2>Item 7. Management's Discussion and Analysis</h2><p>MDNA {FILLER}</p>"
    f"<h2>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</h2>"
    f"<p>MARKET {FILLER}</p>"
    "<h2>Item 8. Financial Statements and Supplementary Data</h2>"
)
STUB_10K = (
    f"<h2>ITEM 1. BUSINESS</h2><p>BUSINESS {FILLER}</p>"
    "<h2>ITEM 1A. RISK FACTORS</h2><p>Can be found in the Annual Report.</p>"
    "<h2>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</h2>"
    "<p>Can be found in the Annual Report under Financial Review.</p>"
    "<h2>ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA</h2>"
)
ANNUAL_REPORT = (
    f"<h2>Financial Review</h2><p>AR_MDNA {FILLER}</p>"
    f"<h2>Risk Factors</h2><p>AR_RISK {FILLER}</p>"
    "<h2>Controls and Procedures</h2>"
)
SUBMISSIONS = {
    "filings": {
        "recent": {
            "accessionNumber": ["0001-26-000001", "0001-25-000002"],
            "form": ["10-K", "10-K"],
            "reportDate": ["2025-12-31", "2024-12-31"],
            "primaryDocument": ["std-2025.htm", "stub-2024.htm"],
        },
        "files": [],
    }
}
INDEX_2024 = (
    '<tr><td scope="row"><a href="/x/ar-2024.htm">ar-2024.htm</a></td>'
    '<td scope="row">EX-13</td></tr>'
)
COMPANY = Company(ticker="ABC", cik=123, extra_titles={"mdna": [r"financial review"]})


def _fake_edgar(requests: list[str]) -> httpx.Client:
    base = "/Archives/edgar/data/123"
    routes: dict[str, object] = {
        "/submissions/CIK0000000123.json": SUBMISSIONS,
        f"{base}/000126000001/std-2025.htm": STANDARD_10K,
        f"{base}/000125000002/stub-2024.htm": STUB_10K,
        f"{base}/000125000002/0001-25-000002-index.htm": INDEX_2024,
        f"{base}/000125000002/ar-2024.htm": ANNUAL_REPORT,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        body = routes[request.url.path]
        if isinstance(body, str):
            return httpx.Response(200, text=body)
        return httpx.Response(200, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_ingest_writes_sections_and_fills_stub_from_annual_report(tmp_path: Path) -> None:
    requests: list[str] = []
    client = EdgarClient(
        user_agent="t t@example.com", http_client=_fake_edgar(requests), sleep=lambda _: None
    )

    written = ingest_company(client, COMPANY, tmp_path)

    assert sorted(p.name for p in written) == ["2024.json", "2025.json"]

    standard = TenK.model_validate(json.loads((tmp_path / "ABC" / "2025.json").read_text()))
    assert standard.fiscal_year == 2025
    expected: list[tuple[SectionName, str]] = [
        ("business", "BUSINESS"),
        ("risk_factors", "RISK"),
        ("mdna", "MDNA"),
        ("market_risk", "MARKET"),
    ]
    for name, marker in expected:
        section = standard.sections[name]
        assert section is not None
        assert section.text.startswith(marker)
        assert section.url.endswith("/000126000001/std-2025.htm")

    stub = TenK.model_validate(json.loads((tmp_path / "ABC" / "2024.json").read_text()))
    business, risk, mdna = (stub.sections[n] for n in ("business", "risk_factors", "mdna"))
    assert business is not None and business.url.endswith("/stub-2024.htm")
    assert risk is not None and risk.text.startswith("AR_RISK")
    assert mdna is not None and mdna.text.startswith("AR_MDNA")
    assert mdna.url.endswith("/000125000002/ar-2024.htm")
    assert stub.sections["market_risk"] is None


def test_ingest_rerun_skips_filings_already_on_disk(tmp_path: Path) -> None:
    requests: list[str] = []
    client = EdgarClient(
        user_agent="t t@example.com", http_client=_fake_edgar(requests), sleep=lambda _: None
    )
    ingest_company(client, COMPANY, tmp_path)
    requests.clear()

    written = ingest_company(client, COMPANY, tmp_path)

    assert written == []
    assert requests == ["/submissions/CIK0000000123.json"]


def test_company_set_has_unique_tickers_and_ciks() -> None:
    assert [c.ticker for c in COMPANIES] == [
        "FMCC",
        "FNMA",
        "RKT",
        "UWMC",
        "COOP",
        "PFSI",
        "JPM",
        "WFC",
    ]
    assert len({c.cik for c in COMPANIES}) == len(COMPANIES)


def test_ingest_skips_filings_before_company_first_fiscal_year(tmp_path: Path) -> None:
    client = EdgarClient(
        user_agent="t t@example.com", http_client=_fake_edgar([]), sleep=lambda _: None
    )
    company = COMPANY.model_copy(update={"first_fiscal_year": 2025})

    written = ingest_company(client, company, tmp_path)

    assert [p.name for p in written] == ["2025.json"]
