"""Culture tool: Finna search across Finnish libraries, museums, and archives.

Finna (finna.fi, National Library of Finland) aggregates cultural-heritage records from
hundreds of organisations. No API key required. Docs: https://api.finna.fi/
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .. import config
from .._http import handle_error, request_json
from ..app import mcp
from .common import ResponseFormat, as_json

_RO = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

FINNA_FIELDS = ["title", "id", "year", "formats", "buildings", "authors"]


def _translated(items: list) -> str:
    """Extract human-readable 'translated' labels from Finna facet-style value lists."""
    out = []
    for it in items or []:
        if isinstance(it, dict):
            out.append(it.get("translated") or it.get("value") or "")
        else:
            out.append(str(it))
    return ", ".join(x for x in out if x)


class FinnaSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Search terms, e.g. 'Tove Jansson', 'Sibelius', 'Aalto'.", min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="culture_search", annotations={"title": "Search Finnish cultural heritage (Finna)", **_RO})
async def culture_search(params: FinnaSearchInput) -> str:
    """Search Finna — Finnish libraries, museums, and archives — for cultural-heritage records.

    Covers books, images, recordings, objects and archival material from hundreds of Finnish
    institutions. Each result links to its finna.fi record page.

    Args:
        params (FinnaSearchInput): query (str), limit (int 1-50), response_format.

    Returns:
        str: Markdown list of "Title (year) — format, holder + link", or JSON:
        {"total": int, "records": [{"title","year","formats","holder","url"}]}.
        On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.FINNA_BASE}/search",
            params={"lookfor": params.query, "limit": params.limit, "field[]": FINNA_FIELDS},
        )
        records = data.get("records", [])
        total = data.get("resultCount", len(records))
        out = []
        for r in records:
            authors = r.get("authors", {})
            primary = ""
            if isinstance(authors, dict):
                names = list((authors.get("primary") or {}).keys()) if isinstance(
                    authors.get("primary"), dict
                ) else (authors.get("primary") or [])
                primary = ", ".join(names) if names else ""
            out.append(
                {
                    "title": r.get("title", "(untitled)"),
                    "year": r.get("year", ""),
                    "formats": _translated(r.get("formats", [])),
                    "holder": _translated(r.get("buildings", [])),
                    "author": primary,
                    "url": f"https://www.finna.fi/Record/{r.get('id', '')}",
                }
            )
        if not out:
            return f"No Finna records found for '{params.query}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"total": total, "count": len(out), "records": out})
        lines = [f"# Finna results for '{params.query}' ({total:,} total)", ""]
        for o in out:
            head = o["title"] + (f" ({o['year']})" if o["year"] else "")
            bits = " · ".join(x for x in [o["formats"], o["holder"]] if x)
            lines.append(f"- **{head}**" + (f" — {bits}" if bits else "") + f"\n  {o['url']}")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


RECORD_FIELDS = ["title", "year", "formats", "summary", "subjects", "nonPresenterAuthors", "buildings", "languages"]


def _finna_authors(record: dict) -> str:
    out = []
    for a in record.get("nonPresenterAuthors", []) or []:
        if isinstance(a, dict) and a.get("name"):
            out.append(a["name"])
    return ", ".join(out)


class RecordInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    record_id: str = Field(..., description="Finna record id from culture_search, e.g. 'eepos.136605'.", min_length=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="culture_get_record", annotations={"title": "Get a Finna record", **_RO})
async def culture_get_record(params: RecordInput) -> str:
    """Get full details of a single Finna cultural-heritage record by its id.

    Args:
        params (RecordInput): record_id (str), response_format.

    Returns:
        str: Title, year, authors, format, subjects/keywords and summary, plus the finna.fi
        link; or JSON with the full record. On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.FINNA_BASE}/record",
            params={"id": params.record_id, "field[]": RECORD_FIELDS},
        )
        records = data.get("records", [])
        if not records:
            return f"No Finna record found with id '{params.record_id}'."
        r = records[0]
        if params.response_format == ResponseFormat.JSON:
            return as_json(r)
        subjects = ", ".join(
            s[0] if isinstance(s, list) and s else str(s) for s in (r.get("subjects") or [])
        )
        summary = " ".join(r.get("summary") or [])
        url = f"https://www.finna.fi/Record/{params.record_id}"
        lines = [
            f"# {r.get('title', '(untitled)')}" + (f" ({r['year']})" if r.get("year") else ""),
            "",
            f"- **Author(s):** {_finna_authors(r) or '—'}",
            f"- **Format:** {_translated(r.get('formats', []))}",
            f"- **Holdings:** {_translated(r.get('buildings', []))}",
        ]
        if subjects:
            lines.append(f"- **Subjects:** {subjects}")
        if summary:
            lines += ["", summary]
        lines += ["", url]
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = ["culture_search", "culture_get_record"]
