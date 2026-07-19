"""Transport tools backed by Fintraffic Digitraffic (road & rail). No API key.

Please identify your app via the FOA_APP_ID env var (sent as the Digitraffic-User
header). Docs: https://www.digitraffic.fi/en/
"""

from __future__ import annotations

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


async def _stations() -> list[dict]:
    """Fetch (and cache) the passenger railway station metadata."""
    data = await request_json(f"{config.DIGITRAFFIC_RAIL_BASE}/metadata/stations")
    return [s for s in data if s.get("passengerTraffic")]


async def _resolve_station(query: str) -> Optional[dict]:
    """Resolve a station name or short code to its metadata record."""
    stations = await _stations()
    q = query.strip().upper()
    for s in stations:
        if s.get("stationShortCode", "").upper() == q:
            return s
    ql = query.strip().lower()
    matches = [s for s in stations if ql in s.get("stationName", "").lower()]
    return matches[0] if matches else None


class FindStationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Part of a station name, e.g. 'Tampere'.", min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


@mcp.tool(name="transport_find_station", annotations={"title": "Find railway station", **_RO})
async def transport_find_station(params: FindStationInput) -> str:
    """Find Finnish passenger railway stations and their short codes by name.

    Args:
        params (FindStationInput): query (str), limit (int 1-50).

    Returns:
        str: Markdown table of matching "Station | Code" pairs (use the code with
        transport_get_station_trains). On failure "Error: ...".
    """
    try:
        stations = await _stations()
        ql = params.query.strip().lower()
        matches = [
            s for s in stations
            if ql in s.get("stationName", "").lower()
            or ql == s.get("stationShortCode", "").lower()
        ][: params.limit]
        if not matches:
            return f"No station found matching '{params.query}'."
        rows = [[s["stationName"], s["stationShortCode"]] for s in matches]
        return md_table(["Station", "Code"], rows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class StationTrainsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    station: str = Field(..., description="Station name or short code, e.g. 'Helsinki' or 'HKI'.")
    arriving: int = Field(default=0, ge=0, le=20, description="Number of arriving trains to include.")
    departing: int = Field(default=8, ge=0, le=20, description="Number of departing trains to include.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="transport_get_station_trains", annotations={"title": "Live trains at station", **_RO})
async def transport_get_station_trains(params: StationTrainsInput) -> str:
    """Get live arriving/departing trains at a Finnish railway station (VR / Fintraffic).

    Args:
        params (StationTrainsInput): station (name or code), arriving (int), departing (int),
            response_format ('markdown'|'json').

    Returns:
        str: For each train: type+number, scheduled and estimated time at this station,
        commercial track, and whether cancelled. Times are UTC (Finland = UTC+3 in summer).
        On failure "Error: ...".
    """
    try:
        station = await _resolve_station(params.station)
        if station is None:
            return f"Unknown station '{params.station}'. Use transport_find_station to look it up."
        code = station["stationShortCode"]
        trains = await request_json(
            f"{config.DIGITRAFFIC_RAIL_BASE}/live-trains/station/{code}",
            params={
                "arrived_trains": 0,
                "arriving_trains": params.arriving,
                "departed_trains": 0,
                "departing_trains": params.departing,
                "include_nonstopping": "false",
            },
            cache=False,
        )
        summary = []
        for t in trains:
            rows = [r for r in t.get("timeTableRows", []) if r.get("stationShortCode") == code]
            for r in rows:
                summary.append(
                    {
                        "train": f"{t.get('trainType', '')}{t.get('trainNumber', '')}",
                        "category": t.get("trainCategory", ""),
                        "type": r.get("type"),
                        "scheduled": r.get("scheduledTime"),
                        "estimate": r.get("liveEstimateTime") or r.get("scheduledTime"),
                        "track": r.get("commercialTrack", ""),
                        "cancelled": r.get("cancelled", False),
                    }
                )
        summary.sort(key=lambda x: x["scheduled"] or "")
        if not summary:
            return f"No live trains reported at {station['stationName']} ({code}) right now."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"station": station["stationName"], "code": code, "trains": summary})
        rows = [
            [
                s["train"], s["type"], (s["scheduled"] or "").replace("T", " ").replace(".000Z", ""),
                (s["estimate"] or "").replace("T", " ").replace(".000Z", ""),
                s["track"], "CANCELLED" if s["cancelled"] else "",
            ]
            for s in summary
        ]
        return (
            f"# Live trains at {station['stationName']} ({code})\n\n"
            + md_table(["Train", "Dir", "Scheduled (UTC)", "Estimate (UTC)", "Track", "Note"], rows)
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class TrafficMessagesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    situation_type: str = Field(
        default="TRAFFIC_ANNOUNCEMENT",
        description="One of TRAFFIC_ANNOUNCEMENT, EXEMPTED_TRANSPORT, WEIGHT_RESTRICTION, ROAD_WORK.",
    )
    limit: int = Field(default=10, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="transport_get_traffic_messages", annotations={"title": "Road traffic messages", **_RO})
async def transport_get_traffic_messages(params: TrafficMessagesInput) -> str:
    """Get current Finnish road traffic disruption messages (Digitraffic).

    Args:
        params (TrafficMessagesInput): situation_type (str), limit (int 1-50),
            response_format ('markdown'|'json').

    Returns:
        str: Recent active road announcements with title, time and location.
        On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.DIGITRAFFIC_ROAD_BASE}/traffic-message/v1/messages",
            params={"inactiveHours": 0, "includeAreaGeometry": "false",
                    "situationType": params.situation_type},
            cache=False,
        )
        features = data.get("features", [])[: params.limit]
        items = []
        for f in features:
            props = f.get("properties", {})
            ann = (props.get("announcements") or [{}])[0]
            items.append(
                {
                    "title": ann.get("title", "").strip(),
                    "releaseTime": props.get("releaseTime", ""),
                    "type": props.get("situationType", ""),
                }
            )
        if not items:
            return f"No active '{params.situation_type}' road messages right now."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"count": len(items), "messages": items})
        rows = [[i["releaseTime"].replace("T", " ").split(".")[0], i["title"][:90]] for i in items]
        return f"# Active road messages ({params.situation_type})\n\n" + md_table(
            ["Released", "Message"], rows
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = [
    "transport_find_station",
    "transport_get_station_trains",
    "transport_get_traffic_messages",
]
