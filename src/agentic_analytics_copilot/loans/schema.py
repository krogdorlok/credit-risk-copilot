"""Pydantic models for Freddie Mac Single-Family Loan-Level Dataset records.

Field order and names follow the Standard Dataset Release 47 layout (effective
July 2026): 31 origination fields, 35 performance fields. Verified against
Freddie Mac's "SFLLD Disclosure Changes Effective July 2026" document and
against the actual sample files, not just the general user guide (which
predates Release 47 and is missing three of the performance fields).
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _blank_to_none(value: object) -> object | None:
    return value or None


def _parse_yyyymm(value: object) -> object:
    if not value:
        return None
    text = str(value)
    return date(int(text[:4]), int(text[4:6]), 1)


BlankToNone = BeforeValidator(_blank_to_none)
YearMonth = Annotated[date, BeforeValidator(_parse_yyyymm)]
OptYearMonth = Annotated[date | None, BeforeValidator(_parse_yyyymm)]
OptStr = Annotated[str | None, BlankToNone]
OptInt = Annotated[int | None, BlankToNone]
OptFloat = Annotated[float | None, BlankToNone]


class LoanOrigination(BaseModel):
    credit_score: int
    first_payment_date: YearMonth
    first_time_homebuyer_indicator: str
    maturity_date: YearMonth
    msa: OptInt
    mi_percentage: int
    number_of_units: int
    occupancy_status: str
    original_cltv: int
    original_dti: int
    original_upb: int
    original_ltv: int
    original_interest_rate: float
    channel: str
    prepayment_penalty_indicator: str
    amortization_type: str
    property_state: str
    property_type: str
    postal_code: str
    loan_sequence_number: str
    loan_purpose: str
    original_loan_term: int
    number_of_borrowers: int
    seller_name: str
    super_conforming_flag: str
    pre_harp_loan_sequence_number: OptStr
    special_eligibility_program: OptStr
    harp_indicator: str
    property_valuation_method: OptInt
    interest_only_indicator: str
    vantage_score: OptInt


class LoanPerformance(BaseModel):
    loan_sequence_number: str
    monthly_reporting_period: YearMonth
    current_actual_upb: float
    current_loan_delinquency_status: str
    loan_age: int
    # Documented as required (Numeric, length 3), but a handful of real
    # records ship it blank - observed in ~0.0002% of rows across the
    # 2016-2026 sample files.
    remaining_months_to_legal_maturity: OptInt
    defect_settlement_date: OptYearMonth
    modification_flag: OptStr
    zero_balance_code: OptStr
    zero_balance_effective_date: OptYearMonth
    current_interest_rate: float
    current_non_interest_bearing_upb: OptFloat
    ddlpi: OptYearMonth
    mi_recoveries: OptFloat
    net_sales_proceeds: OptStr
    non_mi_recoveries: OptFloat
    total_expenses: OptFloat
    legal_costs: OptFloat
    maintenance_and_preservation_costs: OptFloat
    taxes_and_insurance: OptFloat
    miscellaneous_expenses: OptFloat
    actual_loss: OptFloat
    cumulative_modification_costs: OptFloat
    interest_rate_step_indicator: OptStr
    payment_deferral_flag: OptStr
    eltv: OptInt
    zero_balance_removal_upb: OptFloat
    delinquent_accrued_interest: OptFloat
    delinquency_due_to_disaster: OptStr
    borrower_assistance_plan: OptStr
    current_period_modification_costs: OptFloat
    current_interest_bearing_upb: OptFloat
    mi_cancellation_indicator: OptStr
    servicer_name: OptStr
    bankruptcy_cramdown_costs: OptFloat


ORIGINATION_FIELDS = list(LoanOrigination.model_fields)
PERFORMANCE_FIELDS = list(LoanPerformance.model_fields)
