from agentic_analytics_copilot.sec.parser import extract_sections
from agentic_analytics_copilot.sec.schema import SectionName


def _filler(marker: str) -> str:
    return f"<p>{marker} " + "Credit losses rose as mortgage rates increased. " * 60 + "</p>"


def _doc(*blocks: str) -> str:
    return "<html><body>" + "".join(blocks) + "</body></html>"


TABLE_OF_CONTENTS = (
    "<div>Item 1. Business</div><div>1</div>"
    "<div>Item 1A. Risk Factors</div><div>9</div>"
    "<div>Item 7. Management's Discussion and Analysis</div><div>40</div>"
    "<div>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</div><div>70</div>"
)


def test_extracts_standard_item_sections_and_skips_table_of_contents() -> None:
    html = _doc(
        TABLE_OF_CONTENTS,
        "<h2>Item 1. Business</h2>",
        _filler("BUSINESS_TEXT"),
        "<h2>Item 1A. Risk Factors</h2>",
        _filler("RISK_TEXT"),
        "<h2>Item 2. Properties</h2>",
        _filler("PROPERTIES_TEXT"),
        "<h2>Item 7. Management’s Discussion and Analysis of Financial Condition</h2>",
        _filler("MDNA_TEXT"),
        "<h2>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</h2>",
        _filler("MARKET_TEXT"),
        "<h2>Item 8. Financial Statements and Supplementary Data</h2>",
        _filler("FINANCIALS_TEXT"),
    )

    sections = extract_sections(html)

    expected: list[tuple[SectionName, str]] = [
        ("business", "BUSINESS_TEXT"),
        ("risk_factors", "RISK_TEXT"),
        ("mdna", "MDNA_TEXT"),
        ("market_risk", "MARKET_TEXT"),
    ]
    for name, marker in expected:
        text = sections[name]
        assert text is not None
        assert text.startswith(marker)
        assert "PROPERTIES_TEXT" not in text
        assert "FINANCIALS_TEXT" not in text


def test_item_number_and_title_on_separate_lines() -> None:
    html = _doc(
        "<div>Item 1.</div><div>Business</div>",
        _filler("BUSINESS_TEXT"),
        "<div>Item 1A.</div><div>Risk Factors</div>",
        _filler("RISK_TEXT"),
    )

    sections = extract_sections(html)

    assert sections["business"] is not None
    assert sections["business"].startswith("BUSINESS_TEXT")
    assert "RISK_TEXT" not in sections["business"]


def test_missing_section_returns_none() -> None:
    html = _doc("<h2>Item 1. Business</h2>", _filler("BUSINESS_TEXT"))

    sections = extract_sections(html)

    assert sections["business"] is not None
    assert sections["risk_factors"] is None
    assert sections["mdna"] is None
    assert sections["market_risk"] is None


def test_cross_reference_stub_is_treated_as_missing() -> None:
    html = _doc(
        "<div>ITEM 7.</div><div>MANAGEMENT’S DISCUSSION AND ANALYSIS</div>",
        "<p>Information in response to this Item 7 can be found in the Annual Report under "
        "Financial Review. That information is incorporated into this item by reference.</p>",
        "<div>ITEM 8.</div><div>FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA</div>",
        _filler("FINANCIALS_TEXT"),
    )

    assert extract_sections(html)["mdna"] is None


def test_lowercase_prose_line_is_not_a_heading() -> None:
    html = _doc(
        "<h2>Item 1. Business</h2>",
        _filler("BUSINESS_TEXT"),
        "<p>risk factors.</p>",
        _filler("STILL_BUSINESS"),
    )

    business = extract_sections(html)["business"]

    assert business is not None
    assert "STILL_BUSINESS" in business


def test_running_page_headers_do_not_split_section() -> None:
    html = _doc(
        "<h2>Management's Discussion and Analysis</h2>",
        _filler("MDNA_PAGE_ONE"),
        "<div>Management's Discussion and Analysis</div>",
        _filler("MDNA_PAGE_TWO"),
        "<h2>Risk Factors</h2>",
        _filler("RISK_TEXT"),
    )

    mdna = extract_sections(html)["mdna"]

    assert mdna is not None
    assert "MDNA_PAGE_ONE" in mdna
    assert "MDNA_PAGE_TWO" in mdna
    assert "RISK_TEXT" not in mdna


def test_company_title_override() -> None:
    html = _doc(
        "<h2>Financial Review</h2>", _filler("MDNA_TEXT"), "<h2>Risk Factors</h2>", _filler("R")
    )

    assert extract_sections(html)["mdna"] is None
    mdna = extract_sections(html, {"mdna": [r"financial review"]})["mdna"]
    assert mdna is not None
    assert mdna.startswith("MDNA_TEXT")


def test_skips_hidden_xbrl_header_scripts_and_page_numbers() -> None:
    html = _doc(
        "<ix:header>HIDDEN_XBRL</ix:header><script>var x = 1;</script>",
        "<h2>Item 1. Business</h2>",
        _filler("BUSINESS_TEXT"),
        "<div>45</div>",
        _filler("MORE"),
    )

    business = extract_sections(html)["business"]

    assert business is not None
    assert "HIDDEN_XBRL" not in business
    assert "var x" not in business
    assert "\n45\n" not in business


def test_heading_with_footnote_marker() -> None:
    html = _doc("<h2>Financial Review1</h2>", _filler("MDNA_TEXT"), "<h2>Risk Factors</h2>")

    mdna = extract_sections(html, {"mdna": [r"financial review"]})["mdna"]

    assert mdna is not None
    assert mdna.startswith("MDNA_TEXT")
