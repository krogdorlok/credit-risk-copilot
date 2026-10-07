"""The fixed set of 10-K filers, keyed by SEC CIK rather than ticker.

CIKs never change, while tickers get delisted (Mr. Cooper's CIK now belongs to
"Maverick Merger Sub 2, LLC" after Rocket acquired it, and SEC's ticker map no
longer lists COOP). Six of these appear as sellers or servicers in the Freddie
Mac loan data; Freddie Mac guarantees every loan, and Fannie Mae is its peer.

Filings start at FY2016 to match the loan data, except where a CIK's earlier
10-Ks belong to a pre-merger shell: COOP's CIK filed as WMIH Corp until the
2018 Nationstar merger, and UWMC's as the SPAC Gores Holdings IV until 2021.
PennyMac's 2016-2017 10-Ks sit under its pre-2018 holding company CIK and are
not included.

Freddie Mac has no "Business" heading; its Item 1 content is the Introduction.
Wells Fargo's 10-K points to its Annual Report exhibit, where MD&A is titled
"Financial Review". Mr. Cooper's FY2023-2024 filings place the Item 7A heading
mid-MD&A, so the end of MD&A (capital resources, liquidity) lands in market_risk.
"""

from agentic_analytics_copilot.sec.schema import Company

COMPANIES = [
    Company(ticker="FMCC", cik=1026214, extra_titles={"business": [r"introduction"]}),
    Company(ticker="FNMA", cik=310522),
    Company(ticker="RKT", cik=1805284),
    Company(ticker="UWMC", cik=1783398, first_fiscal_year=2021),
    Company(ticker="COOP", cik=933136, first_fiscal_year=2018),
    Company(ticker="PFSI", cik=1745916),
    Company(ticker="JPM", cik=19617),
    Company(ticker="WFC", cik=72971, extra_titles={"mdna": [r"financial review"]}),
]
