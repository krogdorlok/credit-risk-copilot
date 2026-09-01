"""SQLAlchemy table definitions for loan origination and performance data.

Column names and nullability mirror the Pydantic models in schema.py, which
are the source of truth for the Freddie Mac SFLLD Release 47 field layout.
"""

from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LoanOriginationRow(Base):
    __tablename__ = "loans"

    loan_sequence_number: Mapped[str] = mapped_column(primary_key=True)
    credit_score: Mapped[int] = mapped_column()
    first_payment_date: Mapped[date] = mapped_column()
    first_time_homebuyer_indicator: Mapped[str] = mapped_column()
    maturity_date: Mapped[date] = mapped_column()
    msa: Mapped[int | None] = mapped_column()
    mi_percentage: Mapped[int] = mapped_column()
    number_of_units: Mapped[int] = mapped_column()
    occupancy_status: Mapped[str] = mapped_column()
    original_cltv: Mapped[int] = mapped_column()
    original_dti: Mapped[int] = mapped_column()
    original_upb: Mapped[int] = mapped_column()
    original_ltv: Mapped[int] = mapped_column()
    original_interest_rate: Mapped[float] = mapped_column()
    channel: Mapped[str] = mapped_column()
    prepayment_penalty_indicator: Mapped[str] = mapped_column()
    amortization_type: Mapped[str] = mapped_column()
    property_state: Mapped[str] = mapped_column()
    property_type: Mapped[str] = mapped_column()
    postal_code: Mapped[str] = mapped_column()
    loan_purpose: Mapped[str] = mapped_column()
    original_loan_term: Mapped[int] = mapped_column()
    number_of_borrowers: Mapped[int] = mapped_column()
    seller_name: Mapped[str] = mapped_column()
    super_conforming_flag: Mapped[str] = mapped_column()
    pre_harp_loan_sequence_number: Mapped[str | None] = mapped_column()
    special_eligibility_program: Mapped[str | None] = mapped_column()
    harp_indicator: Mapped[str] = mapped_column()
    property_valuation_method: Mapped[int | None] = mapped_column()
    interest_only_indicator: Mapped[str] = mapped_column()
    vantage_score: Mapped[int | None] = mapped_column()


class LoanPerformanceRow(Base):
    __tablename__ = "loan_performance"

    loan_sequence_number: Mapped[str] = mapped_column(
        ForeignKey("loans.loan_sequence_number"), primary_key=True
    )
    monthly_reporting_period: Mapped[date] = mapped_column(primary_key=True)
    current_actual_upb: Mapped[float] = mapped_column()
    current_loan_delinquency_status: Mapped[str] = mapped_column()
    loan_age: Mapped[int] = mapped_column()
    remaining_months_to_legal_maturity: Mapped[int | None] = mapped_column()
    defect_settlement_date: Mapped[date | None] = mapped_column()
    modification_flag: Mapped[str | None] = mapped_column()
    zero_balance_code: Mapped[str | None] = mapped_column()
    zero_balance_effective_date: Mapped[date | None] = mapped_column()
    current_interest_rate: Mapped[float] = mapped_column()
    current_non_interest_bearing_upb: Mapped[float | None] = mapped_column()
    ddlpi: Mapped[date | None] = mapped_column()
    mi_recoveries: Mapped[float | None] = mapped_column()
    net_sales_proceeds: Mapped[str | None] = mapped_column()
    non_mi_recoveries: Mapped[float | None] = mapped_column()
    total_expenses: Mapped[float | None] = mapped_column()
    legal_costs: Mapped[float | None] = mapped_column()
    maintenance_and_preservation_costs: Mapped[float | None] = mapped_column()
    taxes_and_insurance: Mapped[float | None] = mapped_column()
    miscellaneous_expenses: Mapped[float | None] = mapped_column()
    actual_loss: Mapped[float | None] = mapped_column()
    cumulative_modification_costs: Mapped[float | None] = mapped_column()
    interest_rate_step_indicator: Mapped[str | None] = mapped_column()
    payment_deferral_flag: Mapped[str | None] = mapped_column()
    eltv: Mapped[int | None] = mapped_column()
    zero_balance_removal_upb: Mapped[float | None] = mapped_column()
    delinquent_accrued_interest: Mapped[float | None] = mapped_column()
    delinquency_due_to_disaster: Mapped[str | None] = mapped_column()
    borrower_assistance_plan: Mapped[str | None] = mapped_column()
    current_period_modification_costs: Mapped[float | None] = mapped_column()
    current_interest_bearing_upb: Mapped[float | None] = mapped_column()
    mi_cancellation_indicator: Mapped[str | None] = mapped_column()
    servicer_name: Mapped[str | None] = mapped_column()
    bankruptcy_cramdown_costs: Mapped[float | None] = mapped_column()
