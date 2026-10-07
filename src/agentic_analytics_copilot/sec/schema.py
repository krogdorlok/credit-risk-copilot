"""Pydantic models for SEC EDGAR 10-K filings and their extracted sections."""

from datetime import date
from typing import Literal, get_args

from pydantic import BaseModel

SectionName = Literal["business", "risk_factors", "mdna", "market_risk"]
SECTION_NAMES: tuple[SectionName, ...] = get_args(SectionName)


class Company(BaseModel):
    ticker: str
    cik: int
    first_fiscal_year: int = 2016
    extra_titles: dict[SectionName, list[str]] = {}


class Filing(BaseModel):
    cik: int
    accession_number: str
    period_of_report: date
    primary_document: str

    @property
    def fiscal_year(self) -> int:
        return self.period_of_report.year

    def document_url(self, document: str) -> str:
        folder = self.accession_number.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{folder}/{document}"


class Section(BaseModel):
    text: str
    url: str


class TenK(BaseModel):
    ticker: str
    cik: int
    fiscal_year: int
    accession_number: str
    sections: dict[SectionName, Section | None]
