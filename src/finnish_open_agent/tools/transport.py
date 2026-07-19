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


async def _digitransit_geocode(text: str) -> Optional[dict]:
    """Resolve a place/address to {name, lat, lon} via Digitransit geocoding (needs key)."""
    data = await request_json(
        f"{config.DIGITRANSIT_GEOCODING_BASE}/search",
        params={"text": text, "size": 1, "boundary.country": "FIN"},
        headers={"digitransit-subscription-key": config.DIGITRANSIT_API_KEY or ""},
    )
    feats = data.get("features", [])
    if not feats:
        return None
    lon, lat = feats[0]["geometry"]["coordinates"]
    return {"name": feats[0]["properties"].get("label", text), "lat": lat, "lon": lon}


_PLAN_QUERY = """
query Plan($fromLat: Float!, $fromLon: Float!, $toLat: Float!, $toLon: Float!, $n: Int!) {
  plan(from: {lat: $fromLat, lon: $fromLon}, to: {lat: $toLat, lon: $toLon}, numItineraries: $n) {
    itineraries {
      duration
      startTime
      endTime
      walkDistance
      legs {
        mode
        duration
        from { name }
        to { name }
        route { shortName }
      }
    }
  }
}
"""


class PlanRouteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    from_place: str = Field(..., description="Origin address or place, e.g. 'Helsinki railway station'.")
    to_place: str = Field(..., description="Destination address or place, e.g. 'Espoo, Otaniemi'.")
    itineraries: int = Field(default=3, ge=1, le=5, description="Number of route options.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="transport_plan_route", annotations={"title": "Plan public-transport route", **_RO})
async def transport_plan_route(params: PlanRouteInput) -> str:
    """Plan a public-transport journey between two Finnish places (Digitransit / HSL nationwide).

    Geocodes both endpoints, then returns itineraries with legs (walk, bus, tram, train,
    metro, ferry) including departure/arrival times and line numbers.

    Requires a Digitransit subscription key in DIGITRANSIT_API_KEY (free at
    portal-api.digitransit.fi). Without it, returns an actionable error.

    Args:
        params (PlanRouteInput): from_place (str), to_place (str), itineraries (int 1-5),
            response_format ('markdown'|'json').

    Returns:
        str: For each itinerary: total duration, start/end (Finnish local time) and a
        leg-by-leg summary. On failure "Error: ...".
    """
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    if not config.DIGITRANSIT_API_KEY:
        return (
            "Error: Route planning needs a free Digitransit subscription key. Register at "
            "https://portal-api.digitransit.fi/ and set the DIGITRANSIT_API_KEY environment variable."
        )
    try:
        origin = await _digitransit_geocode(params.from_place)
        dest = await _digitransit_geocode(params.to_place)
        if origin is None or dest is None:
            miss = params.from_place if origin is None else params.to_place
            return f"Could not locate '{miss}'. Try a more specific address."
        data = await request_json(
            config.DIGITRANSIT_ROUTING_BASE,
            method="POST",
            headers={"digitransit-subscription-key": config.DIGITRANSIT_API_KEY,
                     "Content-Type": "application/json"},
            json_body={
                "query": _PLAN_QUERY,
                "variables": {
                    "fromLat": origin["lat"], "fromLon": origin["lon"],
                    "toLat": dest["lat"], "toLon": dest["lon"], "n": params.itineraries,
                },
            },
            cache=False,
        )
        itins = (((data.get("data") or {}).get("plan") or {}).get("itineraries")) or []
        if not itins:
            return f"No routes found from {origin['name']} to {dest['name']}."

        def fin(ms: int) -> str:
            return datetime.fromtimestamp(ms / 1000, timezone.utc).astimezone(
                ZoneInfo("Europe/Helsinki")
            ).strftime("%H:%M")

        if params.response_format == ResponseFormat.JSON:
            return as_json({"from": origin["name"], "to": dest["name"], "itineraries": itins})
        lines = [f"# {origin['name']} → {dest['name']}", ""]
        for i, it in enumerate(itins, 1):
            mins = round(it["duration"] / 60)
            legs = []
            for leg in it["legs"]:
                line = (leg.get("route") or {}).get("shortName")
                legs.append(f"{leg['mode'].lower()}" + (f" {line}" if line else ""))
            lines.append(
                f"**Option {i}** — {mins} min, {fin(it['startTime'])}→{fin(it['endTime'])}: "
                + " › ".join(legs)
            )
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class WeatherCamsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Text to match in a camera station name, e.g. 'Kirkkonummi' or 'vt1'.")
    limit: int = Field(default=10, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="transport_find_weather_cameras", annotations={"title": "Find road weather cameras", **_RO})
async def transport_find_weather_cameras(params: WeatherCamsInput) -> str:
    """Find Finnish road weather-camera stations by name (Fintraffic Digitraffic).

    Args:
        params (WeatherCamsInput): query (str), limit (int 1-50), response_format.

    Returns:
        str: Matching camera stations with id, name, coordinates and number of camera
        presets (image angles). Image URLs follow https://weathercam.digitraffic.fi/<presetId>.jpg.
        On failure "Error: ...".
    """
    try:
        data = await request_json(f"{config.DIGITRAFFIC_ROAD_BASE}/weathercam/v1/stations")
        ql = params.query.strip().lower()
        matches = []
        for f in data.get("features", []):
            props = f.get("properties", {})
            name = props.get("name", "") or props.get("id", "")
            if ql in name.lower() or ql == props.get("id", "").lower():
                coords = f.get("geometry", {}).get("coordinates", [None, None])
                matches.append(
                    {
                        "id": props.get("id", ""),
                        "name": name,
                        "lon": coords[0],
                        "lat": coords[1],
                        "cameras": len(props.get("presets", []) or props.get("cameraPresets", [])),
                    }
                )
            if len(matches) >= params.limit:
                break
        if not matches:
            return f"No weather cameras found matching '{params.query}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"count": len(matches), "cameras": matches})
        rows = [[m["id"], m["name"], f"{m['lat']}, {m['lon']}", m["cameras"]] for m in matches]
        return "# Road weather cameras\n\n" + md_table(
            ["ID", "Name", "Lat, Lon", "Angles"], rows
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = [
    "transport_find_station",
    "transport_get_station_trains",
    "transport_get_traffic_messages",
    "transport_plan_route",
    "transport_find_weather_cameras",
]
