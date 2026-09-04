"""Pydantic models for FRED (Federal Reserve Economic Data) API responses."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _missing_to_none(value: object) -> object | None:
    return None if value == "." else value


class Observation(BaseModel):
    date: date
    value: Annotated[float | None, BeforeValidator(_missing_to_none)]


class SeriesObservations(BaseModel):
    series_id: str
    observations: list[Observation]
