"""Parse Freddie Mac SFLLD pipe-delimited text files into validated records.

Files have no header row; columns are positional (see schema.py). Malformed
rows (wrong column count, or a value that fails type validation) are skipped
and reported rather than aborting the whole file.
"""

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ValidationError

from agentic_analytics_copilot.loans.schema import (
    ORIGINATION_FIELDS,
    PERFORMANCE_FIELDS,
    LoanOrigination,
    LoanPerformance,
)


@dataclass
class ParseResult[T: BaseModel]:
    records: list[T] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _parse_lines[T: BaseModel](
    lines: list[str], fields: list[str], model: type[T]
) -> ParseResult[T]:
    result: ParseResult[T] = ParseResult()
    for line_number, line in enumerate(lines, start=1):
        values = line.rstrip("\r\n").split("|")
        if len(values) != len(fields):
            result.errors.append(
                f"line {line_number}: expected {len(fields)} fields, got {len(values)}"
            )
            continue
        try:
            result.records.append(model(**dict(zip(fields, values, strict=True))))
        except ValidationError as exc:
            result.errors.append(f"line {line_number}: {exc}")
    return result


def parse_origination_file(path: Path) -> ParseResult[LoanOrigination]:
    lines = path.read_text(encoding="latin-1").splitlines()
    return _parse_lines(lines, ORIGINATION_FIELDS, LoanOrigination)


def parse_performance_file(path: Path) -> ParseResult[LoanPerformance]:
    lines = path.read_text(encoding="latin-1").splitlines()
    return _parse_lines(lines, PERFORMANCE_FIELDS, LoanPerformance)
