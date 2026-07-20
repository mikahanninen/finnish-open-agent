"""Registers & catalogues: PRH/YTJ business register, avoindata.fi (CKAN), Statistics Finland.

All key-less. Sources:
  • PRH open data YTJ v3 — Finnish Business Information System
  • avoindata.fi CKAN API — national open-data catalogue (search datasets)
  • Statistics Finland PxWeb API — browse the StatFin statistical database
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


def _current_name(company: dict) -> str:
    """Pick the current registered company name from a PRH company record."""
    names = company.get("names", [])
    active = [n for n in names if not n.get("endDate")]
    primary = [n for n in active if n.get("type") == "1"] or active or names
    return primary[0]["name"] if primary else "(unknown)"


class CompanySearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(..., description="Company name or part of it, e.g. 'Nokia'.", min_length=1)
    page: int = Field(default=1, ge=1, le=100, description="Result page (100 companies/page).")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_search_companies", annotations={"title": "Search Finnish companies", **_RO})
async def registers_search_companies(params: CompanySearchInput) -> str:
    """Search the Finnish Business Information System (PRH/YTJ) for companies by name.

    Args:
        params (CompanySearchInput): name (str), page (int), response_format.

    Returns:
        str: Markdown table (Business ID, Current name, Registered) or JSON:
        {"total": int, "companies": [{"businessId","name","registrationDate"}]}.
        Use the Business ID with registers_get_company for full details.
    """
    try:
        data = await request_json(
            f"{config.PRH_YTJ_BASE}/companies", params={"name": params.name, "page": params.page}
        )
        companies = data.get("companies", [])
        total = data.get("totalResults", len(companies))
        out = [
            {
                "businessId": c.get("businessId", {}).get("value", ""),
                "name": _current_name(c),
                "registrationDate": c.get("businessId", {}).get("registrationDate", ""),
            }
            for c in companies
        ]
        if not out:
            return f"No companies found matching '{params.name}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"total": total, "count": len(out), "companies": out})
        rows = [[o["businessId"], o["name"], o["registrationDate"]] for o in out]
        return (
            f"# Companies matching '{params.name}' ({total} total)\n\n"
            + md_table(["Business ID", "Name", "Registered"], rows)
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class CompanyGetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    business_id: str = Field(
        ..., description="Finnish Business ID (Y-tunnus), format 1234567-8.",
        pattern=r"^\d{7}-\d$",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_get_company", annotations={"title": "Get Finnish company details", **_RO})
async def registers_get_company(params: CompanyGetInput) -> str:
    """Get detailed registry information for a Finnish company by its Business ID.

    Args:
        params (CompanyGetInput): business_id (str, 'NNNNNNN-N'), response_format.

    Returns:
        str: Company name, business ID, company form, main line of business,
        registration date and registered address (JSON has the full record).
        On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.PRH_YTJ_BASE}/companies", params={"businessId": params.business_id}
        )
        companies = data.get("companies", [])
        if not companies:
            return f"No company found with Business ID {params.business_id}."
        c = companies[0]
        if params.response_format == ResponseFormat.JSON:
            return as_json(c)
        name = _current_name(c)
        form = (c.get("companyForms") or [{}])[0].get("descriptions", [{}])
        form_txt = next((d.get("description") for d in form if d.get("languageCode") == "3"), "")
        line = (c.get("mainBusinessLine") or {})
        line_desc = next(
            (d.get("description") for d in line.get("descriptions", []) if d.get("languageCode") == "3"),
            "",
        )
        addrs = c.get("addresses", [])
        addr_txt = ""
        if addrs:
            a = addrs[0]
            addr_txt = f"{a.get('street', '')} {a.get('postCode', '')} {a.get('postOffices', [{}])[0].get('city', '') if a.get('postOffices') else ''}".strip()
        return (
            f"# {name}\n\n"
            f"- **Business ID:** {c.get('businessId', {}).get('value', '')}\n"
            f"- **Company form:** {form_txt}\n"
            f"- **Main line of business:** {line.get('type', '')} {line_desc}\n"
            f"- **Registered:** {c.get('businessId', {}).get('registrationDate', '')}\n"
            f"- **Address:** {addr_txt or 'n/a'}\n"
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class DatasetSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Search terms, e.g. 'air quality', 'population', 'kirjasto'.")
    rows: int = Field(default=10, ge=1, le=50, description="Number of datasets to return.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_search_open_datasets", annotations={"title": "Search avoindata.fi", **_RO})
async def registers_search_open_datasets(params: DatasetSearchInput) -> str:
    """Search Finland's national open-data catalogue (avoindata.fi / CKAN) for datasets.

    Use this to discover which open datasets and APIs exist for a topic before deciding
    how to fetch the data.

    Args:
        params (DatasetSearchInput): query (str), rows (int 1-50), response_format.

    Returns:
        str: Markdown list of "Title — publisher (URL)" or JSON with the CKAN results.
        On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.AVOINDATA_CKAN_BASE}/package_search",
            params={"q": params.query, "rows": params.rows},
        )
        result = data.get("result", {})
        datasets = result.get("results", [])
        total = result.get("count", 0)
        out = []
        for d in datasets:
            out.append(
                {
                    "title": (d.get("title") or d.get("name", "")).strip(),
                    "publisher": (d.get("organization") or {}).get("title", ""),
                    "resources": d.get("num_resources", 0),
                    "url": f"https://avoindata.suomi.fi/data/en_GB/dataset/{d.get('name', '')}",
                }
            )
        if not out:
            return f"No datasets found for '{params.query}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"total": total, "count": len(out), "datasets": out})
        lines = [f"# avoindata.fi results for '{params.query}' ({total} total)", ""]
        for o in out:
            lines.append(f"- **{o['title']}** — {o['publisher']} ({o['resources']} resources)\n  {o['url']}")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class DatasetGetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(
        ..., description="Dataset name/slug from registers_search_open_datasets (the last URL path segment).",
        min_length=1,
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_get_open_dataset", annotations={"title": "Get avoindata.fi dataset", **_RO})
async def registers_get_open_dataset(params: DatasetGetInput) -> str:
    """Get an avoindata.fi dataset's details and its downloadable resources / API endpoints.

    Use after registers_search_open_datasets to see a dataset's actual data links (CSV, JSON,
    WFS, API URLs) and formats.

    Args:
        params (DatasetGetInput): name (dataset slug), response_format.

    Returns:
        str: Markdown with the dataset title, publisher, and a table of resources
        (name, format, URL); or JSON with the full CKAN record. On failure "Error: ...".
    """
    try:
        data = await request_json(
            f"{config.AVOINDATA_CKAN_BASE}/package_show", params={"id": params.name}
        )
        r = data.get("result", {})
        if not r:
            return f"No dataset found with name '{params.name}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json(r)
        resources = r.get("resources", [])
        title = (r.get("title") or r.get("name", "")).strip()
        publisher = (r.get("organization") or {}).get("title", "")
        rows = [
            [(res.get("name") or "(unnamed)").strip()[:50], (res.get("format") or "").upper(), res.get("url", "")]
            for res in resources
        ]
        table = md_table(["Resource", "Format", "URL"], rows) if rows else "_No downloadable resources listed._"
        return f"# {title}\n\n{publisher}\n\n{table}"
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class StatFinBrowseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(
        default="",
        description="PxWeb path under StatFin, e.g. '' for top level, 'vaerak' for a subject.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_statfin_browse", annotations={"title": "Browse Statistics Finland", **_RO})
async def registers_statfin_browse(params: StatFinBrowseInput) -> str:
    """Browse the Statistics Finland (Tilastokeskus) PxWeb StatFin database tree.

    Call with an empty path to list top-level subject areas, then drill down using
    the returned ids. Entries of type 'l' are sub-levels; type 't' are data tables.

    Args:
        params (StatFinBrowseInput): path (str), response_format.

    Returns:
        str: Markdown list of "id — text (level/table)" or JSON of the node list.
        On failure "Error: ...".
    """
    try:
        path = params.path.strip("/")
        url = f"{config.STATFIN_PXWEB_BASE}/StatFin/{path}".rstrip("/")
        data = await request_json(url)
        if params.response_format == ResponseFormat.JSON:
            return as_json(data)
        if isinstance(data, dict):  # a table's variable metadata was returned
            return as_json(data)
        lines = [f"# StatFin: /{path or '(root)'}", ""]
        for node in data:
            kind = "table" if node.get("type") == "t" else "level"
            lines.append(f"- `{node.get('id')}` — {node.get('text')} ({kind})")
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


def _labels_in_order(category: dict) -> list[tuple[str, str]]:
    """Return [(code, label)] for a json-stat2 category, ordered by its index positions."""
    index = category.get("index", {})
    labels = category.get("label", {})
    if isinstance(index, list):  # index can be a plain ordered list of codes
        return [(code, labels.get(code, code)) for code in index]
    ordered = sorted(index.items(), key=lambda kv: kv[1])  # {code: position}
    return [(code, labels.get(code, code)) for code, _ in ordered]


def _parse_jsonstat2(res: dict, max_cells: int) -> tuple[str, list[str], list[list[str]]]:
    """Flatten a json-stat2 response into (title, column_headers, rows)."""
    order = res["id"]
    sizes = res["size"]
    dims = res["dimension"]
    values = res["value"]
    per_dim = [_labels_in_order(dims[code]["category"]) for code in order]
    headers = [dims[code].get("label", code) for code in order] + ["value"]
    rows: list[list[str]] = []
    for i, val in enumerate(values):
        if i >= max_cells:
            break
        idx = i
        coord = []
        for j in range(len(sizes) - 1, -1, -1):
            pos = idx % sizes[j]
            idx //= sizes[j]
            coord.insert(0, per_dim[j][pos][1])
        rows.append(coord + ["" if val is None else str(val)])
    return res.get("label", "StatFin table"), headers, rows


class StatFinGetTableInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    table_path: str = Field(
        ...,
        description="PxWeb table path under StatFin, e.g. 'vaerak/11ra.px' "
        "(discover ids with registers_statfin_browse).",
    )
    selections: dict[str, list[str]] | None = Field(
        default=None,
        description="Optional {variable_code: [value_codes]} to select. Any variable you omit "
        "defaults to its most recent/last value. Get codes from registers_statfin_browse on the table.",
    )
    max_cells: int = Field(default=50, ge=1, le=500, description="Max data cells to return.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_statfin_get_table", annotations={"title": "Get Statistics Finland data", **_RO})
async def registers_statfin_get_table(params: StatFinGetTableInput) -> str:
    """Fetch actual statistical values from a Statistics Finland (StatFin) PxWeb table.

    Reads the table's metadata, builds a PxWeb query (defaulting any unspecified variable to
    its most recent value), and returns the resulting figures. Pair with
    registers_statfin_browse to discover table paths and variable/value codes.

    Args:
        params (StatFinGetTableInput): table_path (str, e.g. 'vaerak/11ra.px'),
            selections (optional {var_code: [value_codes]}), max_cells (int), response_format.

    Returns:
        str: Markdown table of dimension labels + value, or JSON
        {"title", "columns", "rows"}. On failure "Error: ...".
    """
    try:
        url = f"{config.STATFIN_PXWEB_BASE}/StatFin/{params.table_path.strip('/')}"
        meta = await request_json(url)
        variables = meta.get("variables", [])
        if not variables:
            return f"No such StatFin table '{params.table_path}'. Use registers_statfin_browse to find it."
        sel = params.selections or {}
        query = []
        for v in variables:
            code = v["code"]
            values = sel.get(code) or [v["values"][-1]]  # default: most recent/last value
            query.append({"code": code, "selection": {"filter": "item", "values": values}})
        res = await request_json(
            url, method="POST",
            json_body={"query": query, "response": {"format": "json-stat2"}},
            headers={"Content-Type": "application/json"}, cache=False,
        )
        title, headers, rows = _parse_jsonstat2(res, params.max_cells)
        if params.response_format == ResponseFormat.JSON:
            return as_json({"title": title, "columns": headers, "rows": rows})
        return f"# {title}\n\n" + md_table(headers, rows)
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


# Module-level cache of the full PTV service list (id, name). Services change slowly, so we
# build this once (it spans ~29 pages) and reuse it for name searches.
_PTV_SERVICES: list[dict] | None = None
_PTV_TS: float = 0.0


async def _ptv_services() -> list[dict]:
    """Fetch and cache the full Suomi.fi PTV service list as [{id, name}] (paginated)."""
    global _PTV_SERVICES, _PTV_TS
    import time

    if _PTV_SERVICES is not None and (time.monotonic() - _PTV_TS) < 3600:
        return _PTV_SERVICES
    out: list[dict] = []
    page = 1
    while page <= 40:  # safety cap; catalogue is ~29 pages
        data = await request_json(f"{config.PTV_BASE}/Service", params={"page": page})
        out.extend(data.get("itemList", []))
        if page >= data.get("pageCount", page):
            break
        page += 1
    _PTV_SERVICES = out
    _PTV_TS = time.monotonic()
    return out


def _ptv_localized(items: list, prefer: str = "fi", type_filter: str | None = None) -> str:
    """Pick a localized value (prefer Finnish) from a PTV name/description list."""
    cands = [i for i in items or [] if (type_filter is None or i.get("type") == type_filter)]
    for lang in (prefer, "en", "sv"):
        for i in cands:
            if i.get("language") == lang and i.get("value"):
                return i["value"].strip()
    return (cands[0].get("value", "").strip() if cands else "")


class ServiceSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Words to match in a public service name, e.g. 'varhaiskasvatus', 'passport'.", min_length=2)
    limit: int = Field(default=15, ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_search_services", annotations={"title": "Search Suomi.fi services", **_RO})
async def registers_search_services(params: ServiceSearchInput) -> str:
    """Search the Suomi.fi Finnish Service Catalogue (PTV) for public services by name.

    Matches against the full national catalogue of public services (municipal & state). The
    first call builds a catalogue index (~29 pages) and is cached for an hour.

    Args:
        params (ServiceSearchInput): query (str), limit (int 1-50), response_format.

    Returns:
        str: Markdown table (Service, Service ID) or JSON. Use a Service ID with
        registers_get_service for full details. On failure "Error: ...".
    """
    try:
        services = await _ptv_services()
        ql = params.query.strip().lower()
        matches = [s for s in services if ql in (s.get("name", "") or "").lower()][: params.limit]
        if not matches:
            return f"No Suomi.fi services found matching '{params.query}'."
        if params.response_format == ResponseFormat.JSON:
            return as_json({"count": len(matches), "services": matches})
        rows = [[s.get("name", ""), s.get("id", "")] for s in matches]
        return (
            f"# Suomi.fi services matching '{params.query}'\n\n"
            + md_table(["Service", "Service ID"], rows)
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


class ServiceGetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    service_id: str = Field(..., description="PTV service GUID from registers_search_services.", min_length=8)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(name="registers_get_service", annotations={"title": "Get Suomi.fi service details", **_RO})
async def registers_get_service(params: ServiceGetInput) -> str:
    """Get details of a Suomi.fi public service (PTV) by its GUID.

    Args:
        params (ServiceGetInput): service_id (GUID), response_format.

    Returns:
        str: Service name, summary/description, service classes and area coverage
        (JSON returns the full PTV record). On failure "Error: ...".
    """
    try:
        d = await request_json(f"{config.PTV_BASE}/Service/{params.service_id}")
        if params.response_format == ResponseFormat.JSON:
            return as_json(d)
        name = _ptv_localized(d.get("serviceNames", []))
        summary = _ptv_localized(d.get("serviceDescriptions", []), type_filter="Summary") or \
            _ptv_localized(d.get("serviceDescriptions", []), type_filter="Description")
        classes = []
        for c in d.get("serviceClasses", []):
            cn = _ptv_localized(c.get("name", [])) if isinstance(c.get("name"), list) else c.get("name", "")
            if cn:
                classes.append(cn)
        area = d.get("areaType", "")
        return (
            f"# {name or '(unnamed service)'}\n\n"
            f"{summary}\n\n"
            f"- **Service classes:** {', '.join(classes) or 'n/a'}\n"
            f"- **Area:** {area}\n"
            f"- **Service ID:** {d.get('id', params.service_id)}\n"
        )
    except Exception as exc:  # noqa: BLE001
        return handle_error(exc)


__all__ = [
    "registers_search_companies",
    "registers_get_company",
    "registers_search_open_datasets",
    "registers_get_open_dataset",
    "registers_statfin_browse",
    "registers_statfin_get_table",
    "registers_search_services",
    "registers_get_service",
]
