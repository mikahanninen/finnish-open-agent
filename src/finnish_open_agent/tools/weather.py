"""Weather tools backed by the Finnish Meteorological Institute (FMI) open data WFS.

FMI serves data as XML (WFS 2.0 "simple feature" stored queries). We parse the
BsWfs simple-feature response into tidy per-timestamp rows. No API key required.
Docs: https://en.ilmatieteenlaitos.fi/open-data-manual
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from .. import config
from .._http import handle_error, request_text
from ..app import mcp
from .common import ResponseFormat, as_json

_RO = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

# Human-friendly labels for the most common forecast parameters.
FORECAST_DEFAULT = "Temperature,WindSpeedMS,WindDirection,Humidity,PrecipitationAmount,WeatherSymbol3"
OBSERVATION_DEFAULT = "t2m,ws_10min,wd_10min,rh,r_1h"


def _local(tag: str) -> str:
    """Strip the XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def _parse_simple_features(xml_text: str) -> list[dict]:
    """Parse an FMI BsWfs simple-feature collection into a list of pivoted rows.

    Returns a list of {"time": ISO8601, <param>: float|None, ...} sorted by time.
    """
    root = ET.fromstring(xml_text)
    by_time: dict[str, dict[str, float | None]] = defaultdict(dict)
    for elem in root.iter():
        if _local(elem.tag) != "BsWfsElement":
            continue
        time_val = name_val = value_val = None
        for child in elem:
            local = _local(child.tag)
            if local == "Time":
                time_val = (child.text or "").strip()
            elif local == "ParameterName":
                name_val = (child.text or "").strip()
            elif local == "ParameterValue":
                raw = (child.text or "").strip()
                try:
                    value_val = float(raw)
                    if value_val != value_val:  # NaN check
                        value_val = None
                except ValueError:
                    value_val = None
        if time_val and name_val:
            by_time[time_val][name_val] = value_val
    rows = [{"time": t, **vals} for t, vals in by_time.items()]
    rows.sort(key=lambda r: r["time"])
    return rows


async def _fmi_query(
    stored_query: str, place: str, parameters: str, hours: int, send_parameters: bool = True
) -> list[dict]:
    """Query an FMI simple-feature stored query and return parsed rows.

    Some stored queries (e.g. air quality) return nothing when a ``parameters`` filter is
    sent; for those pass ``send_parameters=False`` and filter columns client-side.
    """
    query: dict[str, str] = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": stored_query,
        "place": place,
        "timestep": "60",
    }
    if send_parameters:
        query["parameters"] = parameters
    text = await request_text(config.FMI_WFS_BASE, params=query)
    rows = _parse_simple_features(text)
    return rows[: hours * max(1, len(parameters.split(",")))]  # trim generously; dedup below


class ForecastInput(BaseModel):
    """Input for an FMI point forecast."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    place: str = Field(
        ..., description="Finnish place name, e.g. 'Helsinki', 'Rovaniemi', 'Tampere'.",
        min_length=1, max_length=80,
    )
    hours: int = Field(default=12, ge=1, le=60, description="Number of forecast hours (1-60).")
    parameters: str = Field(
        default=FORECAST_DEFAULT,
        description="Comma-separated FMI forecast parameters (e.g. 'Temperature,WindSpeedMS').",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="weather_get_forecast", annotations={"title": "FMI weather forecast", **_RO})
async def weather_get_forecast(params: ForecastInput) -> str:
    """Get an hourly HARMONIE weather forecast for a Finnish location from FMI.

    Args:
        params (ForecastInput): place (str), hours (int 1-60),
            parameters (comma list; default temp/wind/humidity/precip/symbol),
            response_format ('markdown'|'json').

    Returns:
        str: Markdown or JSON with one row per hour:
        {"place": str, "rows": [{"time": ISO8601, "Temperature": float, ...}]}.
        WeatherSymbol3 is FMI's numeric weather-symbol code. On failure "Error: ...".
    """
    try:
        rows = await _fmi_query(
            "fmi::forecast::harmonie::surface::point::simple",
            params.place, params.parameters, params.hours,
        )
        # Keep only the first N distinct timestamps.
        seen: list[str] = []
        trimmed = []
        for r in rows:
            if r["time"] not in seen:
                seen.append(r["time"])
            if len(seen) > params.hours:
                break
            trimmed.append(r)
        # collapse to one dict per timestamp
        merged: dict[str, dict] = {}
        for r in trimmed:
            merged.setdefault(r["time"], {"time": r["time"]}).update(r)
        result = list(merged.values())[: params.hours]
        if not result:
            return f"No forecast found for '{params.place}'. Check the place name spelling."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"place": params.place, "rows": result})
        cols = [c for c in params.parameters.split(",")]
        header = "| Time (UTC) | " + " | ".join(cols) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(cols)) + " |"
        lines = [f"# FMI forecast for {params.place}", "", header, sep]
        for r in result:
            vals = [("" if r.get(c) is None else str(r.get(c))) for c in cols]
            lines.append(f"| {r['time']} | " + " | ".join(vals) + " |")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class ObservationInput(BaseModel):
    """Input for FMI weather-station observations."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    place: str = Field(..., description="Finnish place/station name, e.g. 'Helsinki'.", min_length=1)
    hours: int = Field(default=6, ge=1, le=48, description="How many past hours of observations.")
    parameters: str = Field(
        default=OBSERVATION_DEFAULT,
        description="FMI observation parameters (t2m=temp, ws_10min=wind, rh=humidity, r_1h=rain).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="weather_get_observations", annotations={"title": "FMI weather observations", **_RO})
async def weather_get_observations(params: ObservationInput) -> str:
    """Get recent real weather-station observations for a Finnish location from FMI.

    Args:
        params (ObservationInput): place (str), hours (int 1-48),
            parameters (comma list; default t2m/ws_10min/wd_10min/rh/r_1h),
            response_format ('markdown'|'json').

    Returns:
        str: Markdown table or JSON of {"time", <param>...} rows, oldest first.
        On failure "Error: ...".
    """
    try:
        rows = await _fmi_query(
            "fmi::observations::weather::simple", params.place, params.parameters, params.hours
        )
        merged: dict[str, dict] = {}
        for r in rows:
            merged.setdefault(r["time"], {"time": r["time"]}).update(r)
        result = list(merged.values())[-params.hours :]
        if not result:
            return f"No observations found for '{params.place}'. Try a larger town nearby."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"place": params.place, "rows": result})
        cols = params.parameters.split(",")
        header = "| Time (UTC) | " + " | ".join(cols) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(cols)) + " |"
        lines = [f"# FMI observations near {params.place}", "", header, sep]
        for r in result:
            vals = [("" if r.get(c) is None else str(r.get(c))) for c in cols]
            lines.append(f"| {r['time']} | " + " | ".join(vals) + " |")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


AIR_QUALITY_DEFAULT = "AQINDEX_PT1H_avg,PM25_PT1H_avg,PM10_PT1H_avg,NO2_PT1H_avg,O3_PT1H_avg"


class AirQualityInput(BaseModel):
    """Input for FMI air-quality observations."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    place: str = Field(..., description="Finnish place name, e.g. 'Helsinki'.", min_length=1)
    hours: int = Field(default=6, ge=1, le=48, description="How many past hours to include.")
    parameters: str = Field(
        default=AIR_QUALITY_DEFAULT,
        description="FMI air-quality parameters. AQINDEX_PT1H_avg=air-quality index, "
        "PM25/PM10=particulates µg/m³, NO2/O3/SO2/CO=gases.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="weather_get_air_quality", annotations={"title": "FMI air quality", **_RO})
async def weather_get_air_quality(params: AirQualityInput) -> str:
    """Get recent air-quality observations for a Finnish location from FMI.

    The air-quality index (AQINDEX_PT1H_avg) is roughly: 1 good, 2 satisfactory, 3 fair,
    4 poor, 5+ very poor. Particulates (PM2.5/PM10) and gases are in µg/m³.

    Args:
        params (AirQualityInput): place (str), hours (int 1-48),
            parameters (comma list; default index/PM2.5/PM10/NO2/O3), response_format.

    Returns:
        str: Markdown table or JSON of {"time", <param>...} rows, oldest first.
        On failure "Error: ...". If a station has no readings, suggests a larger city.
    """
    try:
        cols = params.parameters.split(",")

        async def fetch(stored_query: str) -> list[dict]:
            # The air-quality queries return nothing if a `parameters` filter is sent, so we
            # fetch all parameters and select requested columns client-side. Merge by time
            # without overwriting a real value with a NaN (place may span several stations).
            text = await request_text(
                config.FMI_WFS_BASE,
                params={
                    "service": "WFS", "version": "2.0.0", "request": "getFeature",
                    "storedquery_id": stored_query, "place": params.place, "timestep": "60",
                },
            )
            merged: dict[str, dict] = {}
            for r in _parse_simple_features(text):
                slot = merged.setdefault(r["time"], {"time": r["time"]})
                for k, v in r.items():
                    if k == "time":
                        continue
                    if v is not None or k not in slot:
                        slot[k] = v
            # Keep only timestamps that actually have a requested value.
            return [row for row in merged.values() if any(row.get(c) is not None for c in cols)]

        # HSY urban network (covers Helsinki region) first, then the national FMI network.
        rows = await fetch("urban::observations::airquality::hourly::simple")
        if not rows:
            rows = await fetch("fmi::observations::airquality::hourly::simple")
        result = sorted(rows, key=lambda r: r["time"])[-params.hours :]
        if not result:
            return (
                f"No recent air-quality readings for '{params.place}'. Try a city with a "
                "monitoring station (e.g. Helsinki, Tampere, Turku, Oulu)."
            )
        if params.response_format == ResponseFormat.JSON:
            return as_json({"place": params.place, "rows": result})
        cols = params.parameters.split(",")
        header = "| Time (UTC) | " + " | ".join(cols) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(cols)) + " |"
        lines = [f"# FMI air quality near {params.place}", "", header, sep]
        for r in result:
            vals = [("" if r.get(c) is None else str(r.get(c))) for c in cols]
            lines.append(f"| {r['time']} | " + " | ".join(vals) + " |")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class SeaInput(BaseModel):
    """Input for FMI marine observations (sea level or waves)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    place: str = Field(..., description="Coastal place/station, e.g. 'Helsinki', 'Kemi', 'Hanko'.", min_length=1)
    kind: str = Field(default="sealevel", description="'sealevel' (mareograph) or 'wave' (buoys).")
    hours: int = Field(default=6, ge=1, le=48, description="How many past hours to include.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="weather_get_sea", annotations={"title": "FMI sea level & waves", **_RO})
async def weather_get_sea(params: SeaInput) -> str:
    """Get recent sea-level (mareograph) or wave observations for a Finnish coastal location (FMI).

    Sea-level parameters include WATLEV / WLEVN2K (water level, cm; theoretical mean & N2000
    reference) and TW (water temperature °C). Wave data includes significant wave height.

    Args:
        params (SeaInput): place (str), kind ('sealevel'|'wave'), hours (int 1-48), response_format.

    Returns:
        str: Markdown table or JSON of {"time", <param>...} rows, oldest first.
        On failure "Error: ...". Wave buoys operate mainly in open sea and warmer months.
    """
    query = (
        "fmi::observations::mareograph::instant::simple"
        if params.kind == "sealevel"
        else "fmi::observations::wave::simple"
    )
    try:
        # These queries return NaN-heavy or empty results with a `parameters` filter, so
        # fetch all parameters and pivot client-side (same pattern as air quality).
        text = await request_text(
            config.FMI_WFS_BASE,
            params={
                "service": "WFS", "version": "2.0.0", "request": "getFeature",
                "storedquery_id": query, "place": params.place, "timestep": "60",
            },
        )
        merged: dict[str, dict] = {}
        for r in _parse_simple_features(text):
            slot = merged.setdefault(r["time"], {"time": r["time"]})
            for k, v in r.items():
                if k == "time":
                    continue
                if v is not None or k not in slot:
                    slot[k] = v
        cols = sorted({k for row in merged.values() for k in row if k != "time"})
        rows = [row for row in merged.values() if any(row.get(c) is not None for c in cols)]
        result = sorted(rows, key=lambda r: r["time"])[-params.hours :]
        if not result:
            return (
                f"No {params.kind} data for '{params.place}'. Use a coastal station "
                "(e.g. Helsinki, Hanko, Kemi for sea level; open-sea buoys for waves)."
            )
        if params.response_format == ResponseFormat.JSON:
            return as_json({"place": params.place, "kind": params.kind, "rows": result})
        header = "| Time (UTC) | " + " | ".join(cols) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(cols)) + " |"
        lines = [f"# FMI {params.kind} near {params.place}", "", header, sep]
        for r in result:
            vals = [("" if r.get(c) is None else str(r.get(c))) for c in cols]
            lines.append(f"| {r['time']} | " + " | ".join(vals) + " |")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


def _extract_values(xml_text: str, param_name: str) -> list[float]:
    """Collect all non-NaN ParameterValue floats for a given parameter across all features."""
    root = ET.fromstring(xml_text)
    out: list[float] = []
    for elem in root.iter():
        if _local(elem.tag) != "BsWfsElement":
            continue
        name = value = None
        for child in elem:
            local = _local(child.tag)
            if local == "ParameterName":
                name = (child.text or "").strip()
            elif local == "ParameterValue":
                try:
                    v = float((child.text or "").strip())
                    value = None if v != v else v
                except ValueError:
                    value = None
        if name == param_name and value is not None:
            out.append(value)
    return out


@mcp.tool(name="weather_get_radiation", annotations={"title": "External radiation (STUK)", **_RO})
async def weather_get_radiation() -> str:
    """Get Finland's current external (background) radiation levels from STUK, nationwide.

    Summarises the latest 10-minute-average dose rate (µSv/h) across STUK's ~250 monitoring
    stations. Typical Finnish background is roughly 0.05–0.30 µSv/h. Source: STUK via FMI.

    Returns:
        str: Station count, average, min and max dose rate (µSv/h) and a plain-language status.
        On failure "Error: ...".
    """
    try:
        text = await request_text(
            config.FMI_WFS_BASE,
            params={
                "service": "WFS", "version": "2.0.0", "request": "getFeature",
                "storedquery_id": "stuk::observations::external-radiation::latest::simple",
            },
        )
        vals = _extract_values(text, "DR_PT10M_avg")
        if not vals:
            return "No external-radiation readings available right now."
        n, mn, mx = len(vals), min(vals), max(vals)
        avg = sum(vals) / n
        status = (
            "Normal background levels across the country."
            if mx <= 0.40
            else "Some stations read above typical background — see STUK for details."
        )
        return (
            "# External radiation in Finland (STUK)\n\n"
            f"- **Stations reporting:** {n}\n"
            f"- **Average dose rate:** {avg:.3f} µSv/h\n"
            f"- **Range:** {mn:.3f} – {mx:.3f} µSv/h\n\n"
            f"{status}"
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class SolarInput(BaseModel):
    """Input for FMI solar-radiation observations."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    place: str = Field(..., description="Finnish place with a radiation station, e.g. 'Helsinki', 'Jokioinen', 'Sodankylä'.", min_length=1)
    hours: int = Field(default=6, ge=1, le=48, description="How many past hours to include.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="weather_get_solar", annotations={"title": "FMI solar radiation", **_RO})
async def weather_get_solar(params: SolarInput) -> str:
    """Get recent solar-radiation observations for a Finnish location from FMI.

    Parameters include GLOB_1MIN (global radiation W/m²), DIFF_1MIN (diffuse), DIR_1MIN
    (direct), UVB_U (UV-B) and SUND_1MIN (sunshine). Only some stations measure radiation.

    Args:
        params (SolarInput): place (str), hours (int 1-48), response_format.

    Returns:
        str: Markdown table or JSON of {"time", <param>...} rows, most recent last.
        On failure "Error: ...".
    """
    try:
        text = await request_text(
            config.FMI_WFS_BASE,
            params={
                "service": "WFS", "version": "2.0.0", "request": "getFeature",
                "storedquery_id": "fmi::observations::radiation::simple",
                "place": params.place, "timestep": "60",
            },
        )
        merged: dict[str, dict] = {}
        for r in _parse_simple_features(text):
            slot = merged.setdefault(r["time"], {"time": r["time"]})
            for k, v in r.items():
                if k == "time":
                    continue
                if v is not None or k not in slot:
                    slot[k] = v
        cols = sorted({k for row in merged.values() for k in row if k != "time"})
        rows = [row for row in merged.values() if any(row.get(c) is not None for c in cols)]
        result = sorted(rows, key=lambda r: r["time"])[-params.hours :]
        if not result:
            return f"No solar-radiation data for '{params.place}'. Try Helsinki, Jokioinen, or Sodankylä."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"place": params.place, "rows": result})
        header = "| Time (UTC) | " + " | ".join(cols) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(cols)) + " |"
        lines = [f"# FMI solar radiation at {params.place}", "", header, sep]
        for r in result:
            vals = [("" if r.get(c) is None else str(r.get(c))) for c in cols]
            lines.append(f"| {r['time']} | " + " | ".join(vals) + " |")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = [
    "weather_get_forecast",
    "weather_get_observations",
    "weather_get_air_quality",
    "weather_get_sea",
    "weather_get_radiation",
    "weather_get_solar",
]
