from pathlib import Path

from agentic_analytics_copilot.loans.parser import parse_origination_file, parse_performance_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_origination_file_row_count_and_errors() -> None:
    result = parse_origination_file(FIXTURES / "sample_orig.txt")

    assert len(result.records) == 2
    assert len(result.errors) == 2


def test_parse_origination_file_schema_validation() -> None:
    result = parse_origination_file(FIXTURES / "sample_orig.txt")

    loan = result.records[0]
    assert loan.loan_sequence_number == "TEST0000001"
    assert loan.credit_score == 720
    assert loan.first_payment_date.isoformat() == "2023-01-01"
    assert loan.msa == 19100
    assert loan.pre_harp_loan_sequence_number is None


def test_parse_origination_file_malformed_rows_reported() -> None:
    result = parse_origination_file(FIXTURES / "sample_orig.txt")

    assert "line 3" in result.errors[0]
    assert "line 4" in result.errors[1]


def test_parse_performance_file_row_count_and_schema() -> None:
    result = parse_performance_file(FIXTURES / "sample_perf.txt")

    assert len(result.records) == 3
    assert len(result.errors) == 1

    perf = result.records[0]
    assert perf.loan_sequence_number == "TEST0000001"
    assert perf.current_actual_upb == 250000.00
    assert perf.zero_balance_code is None
    assert perf.ddlpi is None
