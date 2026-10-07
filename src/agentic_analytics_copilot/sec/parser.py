"""Extract Item 1, 1A, 7, and 7A text from 10-K HTML.

A heading is a short line that matches a section's Item number or its standard
title. Title-only headings must start uppercase so prose lines like "business."
are not mistaken for one, and may carry a trailing footnote marker ("Financial
Review1"). Each heading's span runs until the next heading of a
different section or an end marker (any other Item, Financial Statements, ...).
Filings repeat headings in the table of contents, in cross-reference stubs, and
as running page headers, so for each section the candidate with the longest span
wins, and a winner under MIN_SECTION_CHARS counts as missing: that is a stub
pointing elsewhere (e.g. "can be found in the Annual Report"), not real content.

Filers that fold a section into another (GSEs and large banks put Item 7A inside
MD&A) come back with that section missing; its text is still in MD&A. Companies
whose titles differ from the standard ones pass extra title patterns.
"""

import re
from collections.abc import Mapping, Sequence
from html.parser import HTMLParser

from agentic_analytics_copilot.sec.schema import SECTION_NAMES, SectionName

MIN_SECTION_CHARS = 2000
MAX_HEADING_CHARS = 120

BLOCK_TAGS = {"p", "div", "br", "tr", "td", "li", "table", "h1", "h2", "h3", "h4", "h5", "h6"}
SKIP_TAGS = {"script", "style", "head", "ix:header"}

TITLES: dict[SectionName, list[str]] = {
    "business": [r"item\s*1\b\.?(\s*business)?", r"business"],
    "risk_factors": [r"item\s*1a\b\.?(\s*risk factors)?", r"risk factors"],
    "mdna": [
        r"item\s*7\b\.?(\s*management's discussion.*)?",
        r"management's discussion and analysis.*",
    ],
    "market_risk": [
        r"item\s*7a\b\.?(\s*quantitative.*)?",
        r"quantitative and qualitative disclosures? about market risk.*",
    ],
}
END_MARKERS = [
    r"item\s*\d{1,2}[a-c]?\b.*",
    r"financial statements and supplementary data.*",
    r"controls and procedures.*",
    r"report of independent registered public accounting firm.*",
    r"management's report on internal control.*",
]
END = "_end"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def _lines(html: str) -> list[str]:
    extractor = _TextExtractor()
    extractor.feed(html)
    lines = []
    for raw in "".join(extractor.parts).splitlines():
        line = re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()
        if line and not line.isdigit():
            lines.append(line)
    merged = []
    i = 0
    while i < len(lines):
        if re.fullmatch(r"(?i)item\s*\d{1,2}[a-c]?\.?", lines[i]) and i + 1 < len(lines):
            merged.append(f"{lines[i]} {lines[i + 1]}")
            i += 2
        else:
            merged.append(lines[i])
            i += 1
    return merged


def _label(line: str, titles: Mapping[SectionName, Sequence[str]]) -> str | None:
    if len(line) > MAX_HEADING_CHARS:
        return None
    text = line.lower().replace("’", "'").rstrip(".: ")
    if not text.startswith("item"):
        if not line[0].isupper():
            return None
        text = text.rstrip("0123456789").rstrip(".: ")
    for name in SECTION_NAMES:
        if any(re.fullmatch(p, text) for p in titles[name]):
            return name
    if any(re.fullmatch(p, text) for p in END_MARKERS):
        return END
    return None


def extract_sections(
    html: str, extra_titles: Mapping[SectionName, Sequence[str]] | None = None
) -> dict[SectionName, str | None]:
    extra = extra_titles or {}
    titles = {name: [*extra.get(name, []), *TITLES[name]] for name in SECTION_NAMES}
    lines = _lines(html)
    labels = [_label(line, titles) for line in lines]

    sections: dict[SectionName, str | None] = {}
    for name in SECTION_NAMES:
        best = ""
        for start, label in enumerate(labels):
            if label != name:
                continue
            end = start + 1
            while end < len(lines) and labels[end] in (None, name):
                end += 1
            body = "\n".join(lines[start + 1 : end])
            if len(body) > len(best):
                best = body
        sections[name] = best if len(best) >= MIN_SECTION_CHARS else None
    return sections
