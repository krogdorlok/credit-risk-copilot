"""Typed client for the FRED (Federal Reserve Economic Data) API.

Retries follow agentic_analytics_copilot.retry. Caches successful responses to
disk. On a live-API failure (network error, repeated 429s, or a 5xx) falls back
to the most recent cached response, even if past TTL, since stale macro data
beats none. Cache TTL is 24 hours: the series this project pulls (mortgage
rates, Treasury yields, home prices, housing starts) update at most daily, so
anything fresher than a day is never actually stale.
"""

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from agentic_analytics_copilot.fred.schema import SeriesObservations
from agentic_analytics_copilot.retry import get_with_retry

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
CACHE_TTL = timedelta(hours=24)


class FredApiError(Exception):
    pass


class FredClient:
    def __init__(
        self,
        api_key: str,
        cache_dir: Path = Path("data/cache/fred"),
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._http = http_client or httpx.Client(timeout=10.0)
        self._sleep = sleep

    def get_series(self, series_id: str) -> SeriesObservations:
        cached = self._read_cache(series_id)
        if cached is not None:
            data, cached_at = cached
            if datetime.now(UTC) - cached_at < CACHE_TTL:
                return data

        try:
            observations = self._fetch(series_id)
        except FredApiError:
            if cached is not None:
                return cached[0]
            raise

        self._write_cache(series_id, observations)
        return SeriesObservations.model_validate(
            {"series_id": series_id, "observations": observations}
        )

    def _fetch(self, series_id: str) -> list[dict[str, Any]]:  # Any: raw FRED JSON observation
        params = {"series_id": series_id, "api_key": self._api_key, "file_type": "json"}
        response = get_with_retry(self._http, BASE_URL, FredApiError, self._sleep, params)
        result: list[dict[str, Any]] = response.json()["observations"]
        return result

    def _cache_path(self, series_id: str) -> Path:
        return self._cache_dir / f"{series_id}.json"

    def _read_cache(self, series_id: str) -> tuple[SeriesObservations, datetime] | None:
        path = self._cache_path(series_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(payload["cached_at"])
        data = SeriesObservations.model_validate(
            {"series_id": series_id, "observations": payload["observations"]}
        )
        return data, cached_at

    def _write_cache(self, series_id: str, observations: list[dict[str, Any]]) -> None:
        payload = {"cached_at": datetime.now(UTC).isoformat(), "observations": observations}
        self._cache_path(series_id).write_text(json.dumps(payload))
