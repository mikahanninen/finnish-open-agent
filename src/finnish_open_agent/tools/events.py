"""Events tool backed by LinkedEvents — events in Finland (Helsinki region and beyond).

Key-less. Docs: https://api.hel.fi/linkedevents/v1/
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from .. import config
from .._http import handle_error, request_json
from ..app import mcp
from .common import ResponseFormat, as_json


def _loc(value) -> str:
    """Pick a Finnish-then-English string from a LinkedEvents localized field."""
    if isinstance(value, dict):
        return (value.get("fi") or value.get("en") or value.get("sv") or "").strip()
    return (value or "").strip() if isinstance(value, str) else ""


_RO = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}


class EventSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(default="", description="Free-text search, e.g. 'jazz', 'lasten', 'museum'.")
    upcoming_only: bool = Field(default=True, description="Only include events starting from today.")
    limit: int = Field(default=10, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="events_search", annotations={"title": "Search events in Finland", **_RO})
async def events_search(params: EventSearchInput) -> str:
    """Search events in Finland (Helsinki region and beyond) via LinkedEvents.

    Args:
        params (EventSearchInput): query (str), upcoming_only (bool), limit (int 1-50),
            response_format.

    Returns:
        str: Markdown list of "Event — start · place" with a link, or JSON. On failure "Error: ...".
    """
    try:
        q: dict = {"page_size": params.limit, "include": "location", "sort": "start_time"}
        if params.query:
            q["text"] = params.query
        if params.upcoming_only:
            q["start"] = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Helsinki")).strftime("%Y-%m-%d")
        data = await request_json(f"{config.LINKEDEVENTS_BASE}/event/", params=q)
        events = data.get("data", [])
        out = []
        for e in events:
            loc = e.get("location") or {}
            place = _loc(loc.get("name")) if isinstance(loc, dict) else ""
            out.append(
                {
                    "name": _loc(e.get("name")) or "(untitled)",
                    "start": e.get("start_time", ""),
                    "place": place,
                    "url": _loc(e.get("info_url")) or f"https://linkedevents.fi/event/{e.get('id', '')}",
                }
            )
        if not out:
            return f"No events found for '{params.query}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"count": len(out), "events": out})
        lines = [f"# Events{f' — {params.query}' if params.query else ''}", ""]
        for o in out:
            start = (o["start"] or "").replace("T", " ")[:16]
            bits = " · ".join(x for x in [start, o["place"]] if x)
            lines.append(f"- **{o['name']}**" + (f" — {bits}" if bits else "") + (f"\n  {o['url']}" if o["url"] else ""))
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = ["events_search"]
