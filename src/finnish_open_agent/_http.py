"""Shared async HTTP client, tiny TTL cache, and error formatting.

Every service module goes through :func:`request_json`, :func:`request_text`, or
:func:`request_bytes` so that user-agent headers, timeouts, caching, and error
handling are consistent in one place (DRY).
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from . import config

# ---------------------------------------------------------------------------
# Minimal in-process TTL cache (per server process; fine for stdio usage)
# ---------------------------------------------------------------------------
_CACHE: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    if config.CACHE_TTL <= 0:
        return None
    hit = _CACHE.get(key)
    if hit is None:
        return None
    expires_at, value = hit
    if time.monotonic() > expires_at:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    if config.CACHE_TTL > 0:
        _CACHE[key] = (time.monotonic() + config.CACHE_TTL, value)


def _default_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": config.USER_AGENT,
        # Fintraffic / Digitraffic requested identifier header.
        "Digitraffic-User": config.APP_ID,
        "Accept-Encoding": "gzip",
    }
    if extra:
        headers.update(extra)
    return headers


class ApiError(Exception):
    """Raised for upstream API failures with an agent-friendly message."""


def _raise_for_status(resp: httpx.Response) -> None:
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        detail = exc.response.text[:300].strip()
        hint = {
            400: "Bad request — check parameter names/values.",
            401: "Unauthorized — this service needs an API key (see README).",
            403: "Forbidden — missing/invalid API key or blocked user-agent.",
            404: "Not found — check the identifier (e.g. business ID, station code).",
            429: "Rate limit exceeded — wait and retry, or set an API key for higher limits.",
        }.get(code, "Upstream service returned an error.")
        raise ApiError(f"HTTP {code} from {resp.request.url}. {hint} {detail}".strip()) from exc


async def request_json(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: Any | None = None,
    cache: bool = True,
) -> Any:
    """Perform an HTTP request and return parsed JSON, with optional caching."""
    cache_key = f"{method}:{url}:{sorted((params or {}).items())}" if method == "GET" else ""
    if cache and cache_key:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    async with httpx.AsyncClient(timeout=config.HTTP_TIMEOUT, follow_redirects=True) as client:
        resp = await client.request(
            method, url, params=params, headers=_default_headers(headers), json=json_body
        )
        _raise_for_status(resp)
        data = resp.json()

    if cache and cache_key:
        _cache_set(cache_key, data)
    return data


async def request_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    cache: bool = True,
) -> str:
    """Perform a GET request and return the response body as text (e.g. XML)."""
    cache_key = f"TXT:{url}:{sorted((params or {}).items())}"
    if cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    async with httpx.AsyncClient(timeout=config.HTTP_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url, params=params, headers=_default_headers(headers))
        _raise_for_status(resp)
        text = resp.text

    if cache:
        _cache_set(cache_key, text)
    return text


def handle_error(exc: Exception) -> str:
    """Format any exception into a consistent, actionable error string."""
    if isinstance(exc, ApiError):
        return f"Error: {exc}"
    if isinstance(exc, httpx.TimeoutException):
        return "Error: Request to the Finnish service timed out. Please try again."
    if isinstance(exc, httpx.HTTPError):
        return f"Error: Network problem contacting the service: {type(exc).__name__}."
    return f"Error: Unexpected {type(exc).__name__}: {exc}"
