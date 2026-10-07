from collections.abc import Callable

import httpx
import pytest

from agentic_analytics_copilot.sec.client import EdgarApiError, EdgarClient
from agentic_analytics_copilot.sec.schema import Filing

USER_AGENT = "Test Copilot test@example.com"

RECENT = {
    "accessionNumber": ["0001-26-000001", "0001-25-000002", "0001-25-000003"],
    "form": ["10-K", "10-Q", "10-K/A"],
    "reportDate": ["2025-12-31", "2025-09-30", "2024-12-31"],
    "primaryDocument": ["abc-20251231.htm", "abc-20250930.htm", "abc-20241231a.htm"],
}
OLDER_PAGE = {
    "accessionNumber": ["0001-18-000004", "0001-16-000005"],
    "form": ["10-K", "10-K"],
    "reportDate": ["2017-12-31", "2015-12-31"],
    "primaryDocument": ["abc-2017.htm", "abc-2015.htm"],
}
SUBMISSIONS = {
    "filings": {
        "recent": RECENT,
        "files": [
            {"name": "CIK0000000123-submissions-001.json", "filingTo": "2019-03-01"},
            {"name": "CIK0000000123-submissions-002.json", "filingTo": "2015-06-01"},
        ],
    }
}
INDEX_WITH_EX13 = (
    '<table><tr><td scope="row">1</td><td scope="row">FORM 10-K</td>'
    '<td scope="row"><a href="/x/abc-10k.htm">abc-10k.htm</a></td>'
    '<td scope="row">10-K</td></tr>'
    '<tr><td scope="row">6</td><td scope="row">EXHIBIT 13</td>'
    '<td scope="row"><a href="/ix?doc=/x/abc-ar.htm">abc-ar.htm</a> &nbsp;iXBRL</td>'
    '<td scope="row">EX-13</td></tr></table>'
)
FILING = Filing(
    cik=123,
    accession_number="0001-26-000001",
    period_of_report="2025-12-31",
    primary_document="abc-20251231.htm",
)


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> EdgarClient:
    return EdgarClient(
        user_agent=USER_AGENT,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )


def test_list_10k_filings_merges_older_pages_and_filters_by_form_and_year() -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.path)
        if request.url.path == "/submissions/CIK0000000123.json":
            return httpx.Response(200, json=SUBMISSIONS)
        if request.url.path == "/submissions/CIK0000000123-submissions-001.json":
            return httpx.Response(200, json=OLDER_PAGE)
        raise AssertionError(f"unexpected request {request.url}")

    filings = _client(handler).list_10k_filings(cik=123, first_fiscal_year=2016)

    assert [f.fiscal_year for f in filings] == [2025, 2017]
    assert filings[0].accession_number == "0001-26-000001"
    assert filings[1].primary_document == "abc-2017.htm"
    assert "/submissions/CIK0000000123-submissions-002.json" not in requested


def test_every_request_sends_user_agent() -> None:
    agents: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        agents.append(request.headers["User-Agent"])
        return httpx.Response(200, json={"filings": {"recent": RECENT, "files": []}})

    _client(handler).list_10k_filings(cik=123, first_fiscal_year=2016)

    assert agents == [USER_AGENT]


def test_fetch_document_uses_archive_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://www.sec.gov/Archives/edgar/data/123/000126000001/abc-20251231.htm"
        )
        return httpx.Response(200, text="<html>10-K</html>")

    assert _client(handler).fetch_document(FILING, "abc-20251231.htm") == "<html>10-K</html>"


def test_find_annual_report_returns_ex13_document() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/Archives/edgar/data/123/000126000001/0001-26-000001-index.htm"
        )
        return httpx.Response(200, text=INDEX_WITH_EX13)

    assert _client(handler).find_annual_report(FILING) == "abc-ar.htm"


def test_find_annual_report_returns_none_without_ex13() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<table><tr><td>10-K</td></tr></table>")

    assert _client(handler).find_annual_report(FILING) is None


def test_retries_on_429_then_succeeds() -> None:
    calls = {"count": 0}
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, text="ok")

    client = EdgarClient(
        user_agent=USER_AGENT,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=sleeps.append,
    )

    assert client.fetch_document(FILING, "abc-20251231.htm") == "ok"
    assert calls["count"] == 2
    assert 2.0 in sleeps


def test_raises_edgar_api_error_on_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    with pytest.raises(EdgarApiError):
        _client(handler).fetch_document(FILING, "missing.htm")
