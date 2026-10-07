"""Client for SEC EDGAR: list a company's 10-K filings and download their documents.

SEC requires a User-Agent naming the requester with a contact email, and allows
at most 10 requests per second, so every request is followed by a short pause.
A company's newest filings are inline in its submissions JSON; older ones sit in
extra pages, and only pages reaching back to the first fiscal year are fetched
(heavy filers like JPM have 70+ pages, mostly structured-note filings).
"""

import re
import time
from collections.abc import Callable
from typing import Any

import httpx

from agentic_analytics_copilot.retry import get_with_retry
from agentic_analytics_copilot.sec.schema import Filing

SUBMISSIONS_URL = "https://data.sec.gov/submissions/{name}"
REQUEST_INTERVAL_SECONDS = 0.15
ANNUAL_REPORT_ROW = re.compile(r'>([^<>"]+\.htm)</a>(?:(?!</tr>).)*?>\s*EX-13\s*<', re.S)


class EdgarApiError(Exception):
    pass


class EdgarClient:
    def __init__(
        self,
        user_agent: str,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = http_client or httpx.Client(timeout=60.0)
        self._http.headers["User-Agent"] = user_agent
        self._sleep = sleep

    def _get(self, url: str) -> httpx.Response:
        response = get_with_retry(self._http, url, EdgarApiError, self._sleep)
        self._sleep(REQUEST_INTERVAL_SECONDS)
        return response

    def list_10k_filings(self, cik: int, first_fiscal_year: int) -> list[Filing]:
        submissions = self._get(SUBMISSIONS_URL.format(name=f"CIK{cik:010d}.json")).json()
        pages = [submissions["filings"]["recent"]]
        for page in submissions["filings"]["files"]:
            if page["filingTo"] >= f"{first_fiscal_year}-01-01":
                pages.append(self._get(SUBMISSIONS_URL.format(name=page["name"])).json())

        filings = [f for page in pages for f in _ten_ks(cik, page)]
        return sorted(
            (f for f in filings if f.fiscal_year >= first_fiscal_year),
            key=lambda f: f.period_of_report,
            reverse=True,
        )

    def fetch_document(self, filing: Filing, document: str) -> str:
        return self._get(filing.document_url(document)).text

    def find_annual_report(self, filing: Filing) -> str | None:
        index = self.fetch_document(filing, f"{filing.accession_number}-index.htm")
        match = ANNUAL_REPORT_ROW.search(index)
        return match.group(1) if match else None


def _ten_ks(cik: int, page: dict[str, list[Any]]) -> list[Filing]:  # Any: EDGAR column values
    return [
        Filing(
            cik=cik,
            accession_number=page["accessionNumber"][i],
            period_of_report=page["reportDate"][i],
            primary_document=page["primaryDocument"][i],
        )
        for i, form in enumerate(page["form"])
        if form == "10-K"
    ]
