"""Health & welfare tools backed by THL Sotkanet — Finnish health/welfare indicators.

Sotkanet publishes thousands of health and welfare statistical indicators by region and year.
Key-less. Docs: https://sotkanet.fi/sotkanet/en/haku
"""

from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .. import config
from .._http import handle_error, request_json
from ..app import mcp
from .common import ResponseFormat, as_json, md_table

_RO = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

WHOLE_COUNTRY_REGION = 658  # Sotkanet region id for "Whole country".

_INDICATORS: list[dict] | None = None
_INDICATORS_TS: float = 0.0


async def _indicators() -> list[dict]:
    """Fetch and cache the Sotkanet indicator catalogue."""
    global _INDICATORS, _INDICATORS_TS
    if _INDICATORS is not None and (time.monotonic() - _INDICATORS_TS) < 3600:
        return _INDICATORS
    data = await request_json(f"{config.SOTKANET_BASE}/indicators")
    _INDICATORS = data if isinstance(data, list) else []
    _INDICATORS_TS = time.monotonic()
    return _INDICATORS


def _title(obj: dict) -> str:
    t = obj.get("title") or {}
    return (t.get("en") or t.get("fi") or "").strip()


class IndicatorSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Words to match in an indicator title, e.g. 'obesity', 'unemployment', 'alcohol'.", min_length=2)
    limit: int = Field(default=15, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="health_search_indicators", annotations={"title": "Search THL health indicators", **_RO})
async def health_search_indicators(params: IndicatorSearchInput) -> str:
    """Search THL Sotkanet for health & welfare indicators by title (English or Finnish).

    The first call caches the indicator catalogue (large) for an hour.

    Args:
        params (IndicatorSearchInput): query (str), limit (int 1-50), response_format.

    Returns:
        str: Markdown table (Indicator ID, Title) or JSON. Use an Indicator ID with
        health_get_indicator. On failure "Error: ...".
    """
    try:
        inds = await _indicators()
        ql = params.query.strip().lower()
        matches = []
        for ind in inds:
            t = ind.get("title") or {}
            hay = f"{t.get('en', '')} {t.get('fi', '')}".lower()
            if ql in hay:
                matches.append({"id": ind.get("id"), "title": _title(ind)})
            if len(matches) >= params.limit:
                break
        if not matches:
            return f"No health indicators found matching '{params.query}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"count": len(matches), "indicators": matches})
        rows = [[m["id"], m["title"][:90]] for m in matches]
        return "# THL Sotkanet indicators\n\n" + md_table(["Indicator ID", "Title"], rows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class IndicatorGetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    indicator_id: int = Field(..., description="Sotkanet indicator id from health_search_indicators.", ge=1)
    year: int = Field(..., description="Year, e.g. 2022.", ge=1990, le=2100)
    region: Optional[int] = Field(
        default=None, description="Sotkanet region id. Omit for the whole country (id 658)."
    )
    gender: str = Field(default="total", description="'total', 'male', or 'female'.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="health_get_indicator", annotations={"title": "Get THL indicator value", **_RO})
async def health_get_indicator(params: IndicatorGetInput) -> str:
    """Get a THL Sotkanet health/welfare indicator's value for a year (whole country by default).

    Args:
        params (IndicatorGetInput): indicator_id (int), year (int), region (optional id;
            default whole country), gender ('total'|'male'|'female'), response_format.

    Returns:
        str: The indicator title and the value for the chosen region/year, plus its unit
        context; or JSON. On failure "Error: ...".
    """
    try:
        region = params.region or WHOLE_COUNTRY_REGION
        rows = await request_json(
            f"{config.SOTKANET_BASE}/json",
            params={"indicator": params.indicator_id, "years": params.year, "genders": params.gender},
        )
        rows = rows if isinstance(rows, list) else []
        match = next((r for r in rows if r.get("region") == region), None)
        # Look up the indicator title (best-effort).
        title = ""
        for ind in await _indicators():
            if ind.get("id") == params.indicator_id:
                title = _title(ind)
                break
        if match is None:
            return (
                f"No value for indicator {params.indicator_id} (region {region}, {params.year}). "
                "Check the year/region, or omit region for the whole country."
            )
        scope = "Whole country" if region == WHOLE_COUNTRY_REGION else f"Region {region}"
        if params.response_format == ResponseFormat.JSON:
            return as_json({"indicator": params.indicator_id, "title": title, "region": region,
                            "year": params.year, "gender": params.gender, "value": match.get("value")})
        return (
            f"# {title or f'Indicator {params.indicator_id}'}\n\n"
            f"- **{scope}, {params.year} ({params.gender}):** {match.get('value')}\n"
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = ["health_search_indicators", "health_get_indicator"]
