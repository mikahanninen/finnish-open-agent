"""Library tools: the Finnish public library directory (Kirjastot.fi).

Search Finnish public libraries and see today's opening hours. Key-less.
Docs: https://api.kirjastot.fi/
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

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


def _today_hours(item: dict) -> str:
    """Summarise today's opening hours from a library's schedules list."""
    scheds = item.get("schedules") or []
    if not scheds:
        return ""
    day = scheds[0]
    if day.get("closed"):
        return "closed today"
    times = day.get("times") or []
    spans = [f"{t.get('from')}–{t.get('to')}" for t in times if t.get("from")]
    return ", ".join(spans) if spans else ""


class LibrarySearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(default="", description="Library name to search, e.g. 'Oodi', 'pääkirjasto'.")
    city: Optional[str] = Field(default=None, description="Filter by city/municipality, e.g. 'Tampere'.")
    limit: int = Field(default=10, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="library_search", annotations={"title": "Search Finnish libraries", **_RO})
async def library_search(params: LibrarySearchInput) -> str:
    """Search Finnish public libraries by name and/or city, with today's opening hours.

    Args:
        params (LibrarySearchInput): query (str), city (optional), limit (int 1-50),
            response_format.

    Returns:
        str: Markdown table (Library, City, Open today) or JSON list of
        {"name","city","address","openToday","email"}. On failure "Error: ...".
    """
    try:
        today = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Helsinki")).strftime("%Y-%m-%d")
        query_params: dict = {
            "lang": "en",
            "limit": params.limit,
            "with": "schedules",
            "period.start": today,
            "period.end": today,
        }
        if params.query:
            query_params["q"] = params.query
        if params.city:
            query_params["city.name"] = params.city
        data = await request_json(f"{config.KIRJASTOT_BASE}/library", params=query_params)
        items = data.get("items", [])
        out = []
        for it in items:
            addr = it.get("address") or {}
            city = addr.get("city", "")
            street = addr.get("street", "")
            out.append(
                {
                    "name": it.get("name", ""),
                    "city": city,
                    "address": f"{street}, {city}".strip(", "),
                    "openToday": _today_hours(it),
                    "email": it.get("email") or "",
                }
            )
        if not out:
            return f"No libraries found for '{params.query or params.city}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"total": data.get("total", len(out)), "count": len(out), "libraries": out})
        rows = [[o["name"], o["city"], o["openToday"] or "—"] for o in out]
        return "# Finnish libraries\n\n" + md_table(["Library", "City", "Open today"], rows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = ["library_search"]
