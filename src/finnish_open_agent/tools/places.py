"""Places tool: geocoding via the National Land Survey of Finland (Maanmittauslaitos).

Converts Finnish place names and addresses to coordinates using the NLS geocoding (Pelias)
API. Requires a free API key in NLS_API_KEY (register at maanmittauslaitos.fi).
"""

from __future__ import annotations

import base64

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


class GeocodeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    text: str = Field(..., description="Place name or address, e.g. 'Mannerheimintie 1, Helsinki'.", min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="places_geocode", annotations={"title": "Geocode a Finnish place/address", **_RO})
async def places_geocode(params: GeocodeInput) -> str:
    """Geocode a Finnish place name or address to coordinates (National Land Survey / MML).

    Requires a free NLS API key in the NLS_API_KEY environment variable (register at
    maanmittauslaitos.fi). Returns WGS84 (EPSG:4326) longitude/latitude.

    Args:
        params (GeocodeInput): text (str), limit (int 1-20), response_format.

    Returns:
        str: Markdown table (Label, Lat, Lon, Type) or JSON list of
        {"label","lat","lon","type"}. Without a key, returns an actionable error.
    """
    if not config.NLS_API_KEY:
        return (
            "Error: Geocoding needs a free National Land Survey API key. Register at "
            "https://www.maanmittauslaitos.fi/rajapinnat/api-avaimen-ohje and set NLS_API_KEY."
        )
    try:
        # HTTP Basic auth (key as username, blank password) per MML's docs — keeps the key
        # out of the URL/query string, unlike the api-key=... query-param alternative they
        # also support (query-string keys leak into proxy/access logs and browser history).
        basic = base64.b64encode(f"{config.NLS_API_KEY}:".encode()).decode()
        data = await request_json(
            f"{config.NLS_GEOCODING_BASE}/search",
            params={
                "text": params.text,
                "size": params.limit,
                "crs": "EPSG:4326",
            },
            headers={"Authorization": f"Basic {basic}"},
        )
        feats = data.get("features", [])
        out = []
        for f in feats:
            props = f.get("properties", {})
            lon, lat = (f.get("geometry", {}).get("coordinates") or [None, None])[:2]
            out.append(
                {
                    "label": props.get("label") or props.get("name", ""),
                    "lat": lat,
                    "lon": lon,
                    "type": props.get("layer") or props.get("type", ""),
                }
            )
        if not out:
            return f"No location found for '{params.text}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"count": len(out), "results": out})
        rows = [[o["label"], o["lat"], o["lon"], o["type"]] for o in out]
        return f"# Geocoding: '{params.text}'\n\n" + md_table(["Label", "Lat", "Lon", "Type"], rows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = ["places_geocode"]
