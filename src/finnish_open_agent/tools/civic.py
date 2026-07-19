"""Civic tools: the Finnish Parliament (Eduskunta) open data.

Uses the Eduskunta open-data table API. The `SeatingOfParliament` table holds the current
200 members with their parliamentary group (party) code. No API key required.
Docs: https://avoindata.eduskunta.fi/
"""

from __future__ import annotations

from collections import Counter
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

# Parliamentary group codes → English names (current groups; unknown codes shown as-is).
PARTY_NAMES = {
    "kok": "National Coalition Party",
    "ps": "Finns Party",
    "sd": "Social Democratic Party",
    "sdp": "Social Democratic Party",
    "kesk": "Centre Party",
    "vihr": "Green League",
    "vas": "Left Alliance",
    "r": "Swedish People's Party",
    "rkp": "Swedish People's Party",
    "kd": "Christian Democrats",
    "liik": "Movement Now",
}


def _party_name(code: str) -> str:
    return PARTY_NAMES.get((code or "").lower(), code or "—")


def _rows_to_dicts(resp: dict) -> list[dict]:
    """Map an Eduskunta table response (columnNames + rowData) to a list of dicts."""
    cols = resp.get("columnNames", [])
    return [dict(zip(cols, row)) for row in resp.get("rowData", [])]


async def _seating() -> list[dict]:
    """Fetch the current parliament seating (<= 200 members), following pagination."""
    out: list[dict] = []
    page = 0
    while page < 5:
        data = await request_json(
            f"{config.EDUSKUNTA_BASE}/tables/SeatingOfParliament/rows",
            params={"perPage": 100, "page": page},  # API caps perPage at 100
        )
        out.extend(_rows_to_dicts(data))
        if not data.get("hasMore"):
            break
        page += 1
    # Normalise/trim whitespace often present in the source data.
    for m in out:
        m["lastname"] = (m.get("lastname") or "").strip()
        m["firstname"] = (m.get("firstname") or "").strip()
        m["party"] = (m.get("party") or "").strip()
    return out


class MpSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(
        default="", description="Name (or part of it) to search for. Empty = list everyone."
    )
    party: Optional[str] = Field(
        default=None, description="Filter by party/group code, e.g. 'kok', 'sd', 'ps', 'vihr', 'vas'."
    )
    limit: int = Field(default=20, ge=1, le=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="civic_search_mps", annotations={"title": "Search Members of Parliament", **_RO})
async def civic_search_mps(params: MpSearchInput) -> str:
    """Search current Finnish Members of Parliament (Eduskunta) by name and/or party.

    Args:
        params (MpSearchInput): query (str, name), party (optional group code),
            limit (int 1-200), response_format.

    Returns:
        str: Markdown table (Name, Party, Seat #) or JSON list of
        {"name","party","partyCode","seat"}. On failure "Error: ...".
    """
    try:
        members = await _seating()
        q = params.query.strip().lower()
        pc = (params.party or "").strip().lower()
        matches = []
        for m in members:
            full = f"{m['firstname']} {m['lastname']}".strip()
            if q and q not in full.lower():
                continue
            if pc and m["party"].lower() != pc:
                continue
            matches.append(m)
        matches.sort(key=lambda m: (m["lastname"], m["firstname"]))
        matches = matches[: params.limit]
        if not matches:
            return f"No current MPs found matching '{params.query}'" + (
                f" in party '{params.party}'." if params.party else "."
            )
        if params.response_format == ResponseFormat.JSON:
            return as_json(
                [
                    {
                        "name": f"{m['firstname']} {m['lastname']}".strip(),
                        "party": _party_name(m["party"]),
                        "partyCode": m["party"],
                        "seat": m.get("seatNumber"),
                    }
                    for m in matches
                ]
            )
        rows = [
            [f"{m['firstname']} {m['lastname']}".strip(), _party_name(m["party"]), m.get("seatNumber", "")]
            for m in matches
        ]
        return "# Members of Parliament\n\n" + md_table(["Name", "Party", "Seat"], rows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


@mcp.tool(
    name="civic_parliament_composition",
    annotations={"title": "Parliament seat composition", **_RO},
)
async def civic_parliament_composition() -> str:
    """Get the current seat distribution of the Finnish Parliament by party.

    Returns:
        str: Markdown table (Party, Seats) sorted by seat count, totalling ~200.
        On failure "Error: ...".
    """
    try:
        members = await _seating()
        counts = Counter(m["party"] for m in members if m["party"])
        if not counts:
            return "No seating data available right now."
        rows = [
            [_party_name(code), n]
            for code, n in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        ]
        total = sum(counts.values())
        return (
            f"# Finnish Parliament composition ({total} seats)\n\n"
            + md_table(["Party", "Seats"], rows)
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


def _int(v) -> int:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return 0


class VotesListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    year: Optional[int] = Field(
        default=None, description="Parliament year (defaults to the current year), e.g. 2025.", ge=1996, le=2100
    )
    limit: int = Field(default=10, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="civic_list_votes", annotations={"title": "Recent parliament votes", **_RO})
async def civic_list_votes(params: VotesListInput) -> str:
    """List recent plenary votes in the Finnish Parliament (Eduskunta) for a given year.

    Args:
        params (VotesListInput): year (int, default current), limit (int 1-50), response_format.

    Returns:
        str: Markdown table (Vote ID, Date, Title) newest first, or JSON. Use a Vote ID with
        civic_get_vote_breakdown. On failure "Error: ...".
    """
    from datetime import datetime, timezone

    try:
        year = params.year or datetime.now(timezone.utc).year
        data = await request_json(
            f"{config.EDUSKUNTA_BASE}/tables/SaliDBAanestys/rows",
            params={"columnName": "IstuntoVPVuosi", "columnValue": year, "perPage": 100, "page": 0},
        )
        rows = _rows_to_dicts(data)
        for r in rows:
            r["_when"] = r.get("AanestysAlkuaika") or r.get("IstuntoPvm") or ""
        rows.sort(key=lambda r: r["_when"], reverse=True)
        rows = rows[: params.limit]
        if not rows:
            return f"No votes found for {year} (try a different year)."
        out = [
            {
                "voteId": r.get("AanestysId"),
                "date": (r.get("IstuntoPvm") or "")[:10],
                "title": (r.get("AanestysOtsikko") or r.get("PaaKohtaOtsikko") or "").strip(),
            }
            for r in rows
        ]
        if params.response_format == ResponseFormat.JSON:
            return as_json({"year": year, "votes": out})
        trows = [[o["voteId"], o["date"], o["title"][:80]] for o in out]
        return f"# Recent parliament votes ({year})\n\n" + md_table(["Vote ID", "Date", "Title"], trows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class VoteBreakdownInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    vote_id: int = Field(..., description="Vote id (AanestysId) from civic_list_votes.", ge=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="civic_get_vote_breakdown", annotations={"title": "Parliament vote breakdown", **_RO})
async def civic_get_vote_breakdown(params: VoteBreakdownInput) -> str:
    """Get the yes/no/abstain/absent breakdown of a Finnish Parliament vote, by party.

    Args:
        params (VoteBreakdownInput): vote_id (int), response_format.

    Returns:
        str: Overall result (Yes vs No) plus a per-party table (Yes/No/Abstain/Absent).
        On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.EDUSKUNTA_BASE}/tables/SaliDBAanestysJakauma/rows",
            params={"columnName": "AanestysId", "columnValue": params.vote_id, "perPage": 100, "page": 0},
        )
        rows = [r for r in _rows_to_dicts(data) if (r.get("Tyyppi") or "").strip() == "eduskuntaryhma"]
        if not rows:
            return f"No breakdown found for vote {params.vote_id}. Check the vote id."
        parties = []
        tot = {"Jaa": 0, "Ei": 0, "Tyhjia": 0, "Poissa": 0}
        for r in rows:
            vals = {k: _int(r.get(k)) for k in tot}
            for k in tot:
                tot[k] += vals[k]
            parties.append({"party": (r.get("Ryhma") or "").strip(), **vals})
        parties.sort(key=lambda p: p["Jaa"] + p["Ei"], reverse=True)
        result = "PASSED (Yes)" if tot["Jaa"] > tot["Ei"] else ("REJECTED (No)" if tot["Ei"] > tot["Jaa"] else "TIE")
        if params.response_format == ResponseFormat.JSON:
            return as_json({"voteId": params.vote_id, "totals": tot, "result": result, "byParty": parties})
        prows = [[p["party"], p["Jaa"], p["Ei"], p["Tyhjia"], p["Poissa"]] for p in parties]
        return (
            f"# Vote {params.vote_id} — {result}\n\n"
            f"Totals: **Yes {tot['Jaa']} · No {tot['Ei']} · Abstain {tot['Tyhjia']} · Absent {tot['Poissa']}**\n\n"
            + md_table(["Party (group)", "Yes", "No", "Abstain", "Absent"], prows)
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = [
    "civic_search_mps",
    "civic_parliament_composition",
    "civic_list_votes",
    "civic_get_vote_breakdown",
]
