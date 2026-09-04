import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from agentic_analytics_copilot.fred.client import FredApiError, FredClient

SAMPLE_OBSERVATIONS = [
    {"date": "2023-01-01", "value": "6.27"},
    {"date": "2023-02-01", "value": "6.65"},
    {"date": "2023-03-01", "value": "."},
]


def _client(
    tmp_path: Path,
    handler: Any,  # Any: httpx.MockTransport's handler type is untyped in stubs
) -> FredClient:
    return FredClient(
        api_key="test-key",
        cache_dir=tmp_path,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )


def _write_cache(
    tmp_path: Path, series_id: str, cached_at: datetime, observations: list[dict[str, str]]
) -> None:
    (tmp_path / f"{series_id}.json").write_text(
        json.dumps({"cached_at": cached_at.isoformat(), "observations": observations})
    )


def test_get_series_parses_observations_and_missing_values(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"observations": SAMPLE_OBSERVATIONS})

    client = _client(tmp_path, handler)

    result = client.get_series("MORTGAGE30US")

    assert result.series_id == "MORTGAGE30US"
    assert len(result.observations) == 3
    assert result.observations[0].value == 6.27
    assert result.observations[2].value is None


def test_get_series_uses_fresh_cache_without_calling_api(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call the API when cache is fresh")

    _write_cache(tmp_path, "MORTGAGE30US", datetime.now(UTC), SAMPLE_OBSERVATIONS)
    client = _client(tmp_path, handler)

    result = client.get_series("MORTGAGE30US")

    assert len(result.observations) == 3


def test_get_series_retries_on_429_then_succeeds(tmp_path: Path) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(429)
        return httpx.Response(200, json={"observations": SAMPLE_OBSERVATIONS})

    client = _client(tmp_path, handler)

    result = client.get_series("MORTGAGE30US")

    assert calls["count"] == 3
    assert len(result.observations) == 3


def test_get_series_raises_on_non_retryable_error(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error_message": "Bad Request"})

    client = _client(tmp_path, handler)

    with pytest.raises(FredApiError):
        client.get_series("BAD_SERIES")


def test_get_series_falls_back_to_stale_cache_on_repeated_failure(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    _write_cache(
        tmp_path, "MORTGAGE30US", datetime.now(UTC) - timedelta(hours=48), SAMPLE_OBSERVATIONS
    )
    client = _client(tmp_path, handler)

    result = client.get_series("MORTGAGE30US")

    assert len(result.observations) == 3


def test_get_series_raises_when_no_cache_and_api_fails(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = _client(tmp_path, handler)

    with pytest.raises(FredApiError):
        client.get_series("MORTGAGE30US")


def test_get_series_retries_on_network_error_then_succeeds(tmp_path: Path) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 2:
            raise httpx.ConnectError("connection failed")
        return httpx.Response(200, json={"observations": SAMPLE_OBSERVATIONS})

    client = _client(tmp_path, handler)

    result = client.get_series("MORTGAGE30US")

    assert calls["count"] == 2
    assert len(result.observations) == 3


def test_get_series_honors_retry_after_header(tmp_path: Path) -> None:
    calls = {"count": 0}
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 2:
            return httpx.Response(429, headers={"Retry-After": "5"})
        return httpx.Response(200, json={"observations": SAMPLE_OBSERVATIONS})

    client = FredClient(
        api_key="test-key",
        cache_dir=tmp_path,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=sleeps.append,
    )

    client.get_series("MORTGAGE30US")

    assert sleeps == [5.0]
