"""HTTP GET with retry and exponential backoff, shared by the FRED and SEC EDGAR clients.

Retries network errors, 429s, and 5xx responses up to MAX_ATTEMPTS, starting at a
1 second wait and doubling each time, or waiting exactly as long as a Retry-After
header asks. Any other non-200 response fails immediately.
"""

from collections.abc import Callable, Mapping

import httpx

MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def get_with_retry(
    http: httpx.Client,
    url: str,
    error: type[Exception],
    sleep: Callable[[float], None],
    params: Mapping[str, str] | None = None,
) -> httpx.Response:
    backoff = 1.0
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = http.get(url, params=params)
        except httpx.TransportError as exc:
            last_error = exc
        else:
            if response.status_code == 200:
                return response
            if response.status_code not in RETRYABLE_STATUS_CODES:
                raise error(f"HTTP {response.status_code} from {url}")
            last_error = error(f"HTTP {response.status_code} from {url}")
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                backoff = float(retry_after)

        if attempt < MAX_ATTEMPTS - 1:
            sleep(backoff)
            backoff *= 2

    raise error(f"{url} failed after {MAX_ATTEMPTS} attempts") from last_error
