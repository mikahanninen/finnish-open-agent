"""Energy tools: electricity spot prices (Nord Pool FI area) and Fingrid grid data.

Data sources:
  • porssisahko.net  — hourly day-ahead spot price, c/kWh incl. 25.5% VAT (no key)
  • spot-hinta.fi    — current-hour price and ranking helpers (no key)
  • Fingrid open data — grid/production/consumption time series (free API key)
"""

from __future__ import annotations


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


class SpotPricesInput(BaseModel):
    """Input for fetching upcoming hourly electricity spot prices."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    hours: int = Field(
        default=24,
        ge=1,
        le=48,
        description="How many of the most recent/upcoming hourly prices to return (1-48).",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="'markdown' for reading, 'json' for processing."
    )


@mcp.tool(name="energy_get_spot_prices", annotations={"title": "Electricity spot prices", **_RO})
async def energy_get_spot_prices(params: SpotPricesInput) -> str:
    """Get hourly Finnish electricity spot (exchange) prices for today and tomorrow.

    Prices are the Nord Pool day-ahead price for the FI bidding zone, in cents per
    kWh (c/kWh) including Finnish VAT (25.5%). Tomorrow's prices publish around
    14:00 EET. Source: porssisahko.net.

    Args:
        params (SpotPricesInput):
            - hours (int): number of most-recent hourly entries to show (1-48, default 24)
            - response_format ('markdown'|'json')

    Returns:
        str: Markdown table (time, c/kWh) or JSON:
        {"unit": "c/kWh incl. VAT", "count": int,
         "prices": [{"start": ISO8601, "end": ISO8601, "price": float}, ...]}
        On failure: "Error: ...".
    """
    try:
        data = await request_json(f"{config.PORSSISAHKO_BASE}/latest-prices.json")
        prices = sorted(data.get("prices", []), key=lambda p: p["startDate"])
        prices = prices[-params.hours :]
        norm = [
            {"start": p["startDate"], "end": p["endDate"], "price": round(p["price"], 3)}
            for p in prices
        ]
        if params.response_format == ResponseFormat.JSON:
            return as_json({"unit": "c/kWh incl. VAT", "count": len(norm), "prices": norm})
        if not norm:
            return "No spot prices available right now."
        rows = [[p["start"].replace("T", " ").replace(".000Z", " UTC"), f"{p['price']:.2f}"] for p in norm]
        cheapest = min(norm, key=lambda p: p["price"])
        priciest = max(norm, key=lambda p: p["price"])
        return (
            "# Finnish electricity spot price (c/kWh incl. VAT)\n\n"
            + md_table(["Hour (UTC)", "c/kWh"], rows)
            + f"\n\nCheapest: {cheapest['price']:.2f} c/kWh · Most expensive: {priciest['price']:.2f} c/kWh"
        )
    except Exception as exc:  # noqa: BLE001 - convert to agent-friendly text
        return handle_error(exc)


@mcp.tool(name="energy_get_price_now", annotations={"title": "Current electricity price", **_RO})
async def energy_get_price_now() -> str:
    """Get the electricity spot price for the current hour in Finland.

    Returns the current-hour price (c/kWh incl. VAT) and where it ranks among today's
    24 hourly prices (rank 1 = cheapest hour today), computed from porssisahko.net.

    Returns:
        str: e.g. "Now 2.71 c/kWh incl. VAT — rank 4/24 (a cheaper hour today)".
        On failure: "Error: ...".
    """
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    try:
        data = await request_json(f"{config.PORSSISAHKO_BASE}/latest-prices.json", cache=False)
        prices = data.get("prices", [])
        now = datetime.now(timezone.utc)
        # Current-hour price: the entry whose [startDate, endDate) contains now.
        current = None
        for p in prices:
            start = datetime.fromisoformat(p["startDate"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(p["endDate"].replace("Z", "+00:00"))
            if start <= now < end:
                current = p
                break
        if current is None:
            return "No current-hour price available right now."
        # Rank within today's (Helsinki-local) 24 hourly prices.
        today = now.astimezone(ZoneInfo("Europe/Helsinki")).date()
        todays = [
            p for p in prices
            if datetime.fromisoformat(p["startDate"].replace("Z", "+00:00"))
            .astimezone(ZoneInfo("Europe/Helsinki")).date() == today
        ]
        todays_sorted = sorted(todays, key=lambda p: p["price"])
        rank = next((i + 1 for i, p in enumerate(todays_sorted)
                     if p["startDate"] == current["startDate"]), None)
        total = len(todays_sorted) or 24
        price_c = round(current["price"], 2)
        note = ""
        if rank:
            if rank <= total / 3:
                note = " (a cheaper hour today)"
            elif rank >= 2 * total / 3:
                note = " (a pricier hour today)"
        rank_txt = f" — rank {rank}/{total}{note}" if rank else ""
        local = now.astimezone(ZoneInfo("Europe/Helsinki")).strftime("%Y-%m-%d %H:%M %Z")
        return f"Now ({local}): {price_c:.2f} c/kWh incl. VAT{rank_txt}"
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class FingridInput(BaseModel):
    """Input for a Fingrid open-data time series query."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    dataset_id: int = Field(
        ...,
        description="Fingrid dataset id, e.g. 192=electricity production, 193=consumption, "
        "245=wind power generation, 124=total consumption forecast. See data.fingrid.fi.",
        ge=1,
    )
    last_n: int = Field(default=5, ge=1, le=50, description="Number of most recent data points.")


@mcp.tool(name="energy_fingrid_latest", annotations={"title": "Fingrid grid data", **_RO})
async def energy_fingrid_latest(params: FingridInput) -> str:
    """Get the most recent values for a Fingrid open-data dataset (grid/production/consumption).

    Requires a free API key in the FINGRID_API_KEY environment variable (register at
    data.fingrid.fi). Useful dataset ids: 192 (real-time production), 193 (consumption),
    245 (wind generation), 188 (nuclear), 191 (hydro).

    Args:
        params (FingridInput): dataset_id (int), last_n (int, 1-50).

    Returns:
        str: JSON list of {"startTime","endTime","value"} points, newest first.
        If no API key is set, returns an actionable error explaining how to get one.
    """
    if not config.FINGRID_API_KEY:
        return (
            "Error: Fingrid requires a free API key. Register at https://data.fingrid.fi/ "
            "and set the FINGRID_API_KEY environment variable."
        )
    try:
        data = await request_json(
            f"{config.FINGRID_BASE}/datasets/{params.dataset_id}/data",
            params={"pageSize": params.last_n, "sortBy": "startTime", "sortOrder": "desc"},
            headers={"x-api-key": config.FINGRID_API_KEY},
            cache=False,
        )
        return as_json(data)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = ["energy_get_spot_prices", "energy_get_price_now", "energy_fingrid_latest"]
