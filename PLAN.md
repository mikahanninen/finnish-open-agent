# Finnish Open Agent — Architecture & Plan

This document is the investigation and plan behind the repository: what Finnish open
data and public services exist, how we expose them to an agent, and in what order we
build them.

## 1. Vision

Be **open-source, portable, and agent-friendly** — one codebase, three delivery modes that
share one implementation so they never diverge:

- **CLI for humans** — `finnish-open-agent call <tool> key=value ...` runs any tool from the
  terminal (`cli.py` introspects the tool registry, so every tool is a subcommand).
- **JSON output for AI tools** — the same call with `--json` (or `response_format=json`)
  returns machine-readable output for scripting and pipelines.
- **Skills + MCP server for agents** — `finnish_services_mcp` presents every source as typed,
  documented MCP tools for Claude Desktop / Code / any MCP client; per-domain **skills**
  (Markdown playbooks) give agents the plain-`curl` path when no server is running.

Adding one `@mcp.tool` yields all three modes automatically — no per-mode wiring.

Guiding principles: **key-less first** (nearly every source is open), **agent-friendly
output** (Markdown for reading, JSON for chaining), **honest attribution** (open data still
has licences), and **easy extension** (adding a service is one module).

## 2. The Finnish open-data landscape

Finland is one of Europe's strongest open-data ecosystems. The national catalogue
[avoindata.fi](https://www.avoindata.fi/en) (CKAN, run by DVV) indexes thousands of
datasets, and most public agencies publish documented REST/WFS/GraphQL APIs. The sources
below are grouped by domain; **bold = implemented in v0.1**, the rest are the roadmap.

### ⚡ Energy
| Service | What | API | Auth |
| --- | --- | --- | --- |
| **porssisahko.net** | Hourly day-ahead spot price (FI), c/kWh incl. VAT | REST JSON | none |
| **spot-hinta.fi** | Current-hour price, rankings, cheapest-hours helpers | REST JSON | none |
| **Fingrid open data** | Grid load, production mix, wind/nuclear/hydro, imbalance | REST JSON | free key |
| ENTSO-E Transparency | Nordic/EU market data | REST XML | free key |

### 🌦️ Weather & environment
| Service | What | API | Auth |
| --- | --- | --- | --- |
| **FMI open data** | Forecasts (HARMONIE), station observations, **air quality**, radar, warnings | WFS 2.0 XML | none |
| **HSY / air quality** | Real-time air quality (Helsinki region, via FMI `urban::`) | WFS 2.0 XML | none |
| STUK / radiation | External radiation monitoring | REST | none |
| SYKE | Water, environment, floods | WFS/REST | none |

### 🚆 Transport & mobility
| Service | What | API | Auth |
| --- | --- | --- | --- |
| **Digitraffic — rail** | VR live trains, timetables, compositions, GPS | REST JSON / MQTT | none¹ |
| **Digitraffic — road** | Traffic messages, **weather cameras**, road weather stations, TMS | REST JSON | none¹ |
| Digitraffic — marine | AIS vessel positions, port calls | REST / WebSocket | none¹ |
| **Digitransit** | Nationwide journey planning + geocoding, stops, real-time | GraphQL | free key |
| Traficom | Vehicle & driving-licence open data | REST / files | none |
| Fintraffic railway | Infrastructure, RINF | REST | none |

¹ Fintraffic asks callers to send a `Digitraffic-User` identifier header (we do).

### 🏢 Registers, statistics & civic
| Service | What | API | Auth |
| --- | --- | --- | --- |
| **PRH / YTJ** | Business register (companies, Business IDs, forms) | REST JSON v3 | none |
| **avoindata.fi** | National open-data catalogue (dataset discovery) | CKAN REST | none |
| **Statistics Finland** | StatFin database (population, prices, economy…) | PxWeb REST | none |
| Suomi.fi PTV | Public-service catalogue (services & channels) | REST JSON | none² |
| **Eduskunta** | Parliament: MPs, seating/composition, votes, documents | REST / table API | none |
| **Finna** | Libraries, museums, archives search | REST JSON | none |
| **Maanmittauslaitos (NLS)** | Maps, **geocoding**, cadastral/property | WMTS/WFS/REST | free key |
| Kela / THL | Benefits & health statistics (aggregate) | files / REST | varies |
| DVV | Population/address data (mostly via avoindata) | files/REST | varies |

² PTV read API is open; writing requires authentication.

## 3. System architecture

```
                ┌─────────────────────────────────────────────┐
   MCP client   │            finnish_services_mcp             │
 (Claude etc.) ─┤  app.py  → FastMCP instance                 │
                │  tools/  → energy · weather · transport ·    │
                │            registers  (@mcp.tool)            │
                │  _http.py → shared async client, TTL cache,  │
                │            uniform error handling            │
                │  config.py → env-driven settings & base URLs │
                └───────────────┬─────────────────────────────┘
                                │ httpx (async)
        ┌───────────────┬───────┴───────┬────────────────┐
   porssisahko/     opendata.fmi.fi  rata/tie.        avoindata.fi
   spot-hinta/                        digitraffic.fi   prh · statfin
   fingrid
```

Every tool is: a **Pydantic input model** (validation + schema) → a **shared HTTP call**
→ **normalised output** in Markdown or JSON. No source-specific quirks leak into the tool
surface (e.g. FMI's XML becomes tidy rows; PRH's name history collapses to the current name).

### Why this shape
- **One HTTP layer** (`_http.py`) means caching, the `Digitraffic-User` header, timeouts, and
  actionable error messages are written once and reused (DRY, per MCP best practices).
- **One module per domain** keeps tools discoverable and lets contributors add a source without
  touching others. `tools/__init__.py::load_all()` auto-registers them.
- **Config via env** means the identical codebase runs as local **stdio** or remote
  **streamable-HTTP** (`FOA_TRANSPORT=http`) — see §5.

## 4. Skills (the CLI approach)

Skills live under `skills/` as **focused per-domain playbooks** (`finnish-energy`,
`finnish-weather`, `finnish-transport`, `finnish-registers`, `finnish-civic`,
`finnish-culture`, `finnish-places`) plus a `finnish-open-data` umbrella index. Splitting by
domain gives each skill a tight, well-triggering description and only the recipes it needs.
Each gives exact endpoints, key parameters, runnable `curl` examples, and the matching MCP
tool names. This satisfies two needs the MCP server alone doesn't:

1. **No-server usage** — an agent with only a shell can still get the data.
2. **Transparency** — humans see precisely which public endpoint is being called.

Future skills can be **workflow-oriented** (e.g. "plan a train trip", "compare electricity
plans", "due-diligence a Finnish company") that compose several tools/endpoints.

## 5. Runtime & deployment

- **Default: local stdio.** Simplest and most private; the client launches the server as a
  subprocess. This is the recommended mode and what the README config uses.
- **Optional: remote streamable-HTTP.** Set `FOA_TRANSPORT=http`. Bind to `127.0.0.1` by
  default; only expose behind auth/TLS. (SSE is intentionally not used — deprecated.)
- Packaged with **uv**; `finnish-open-agent` console script is the entry point.

## 6. Design decisions & conventions

- **Server name** `finnish_services_mcp`; **tool names** `{domain}_{action}[_{resource}]`
  (e.g. `transport_get_station_trains`) to avoid collisions with other MCP servers.
- **Read-only, open-world** annotations on all tools (nothing here mutates state).
- **Units & time**: prices in c/kWh incl. VAT; timestamps ISO 8601 (mostly UTC — Finland is
  UTC+2/+3). Tools note the timezone in output.
- **Caching**: short in-process TTL for slow-moving metadata (station lists); disabled for
  live data (prices, live trains).
- **Errors**: never raise to the client; return `"Error: …"` with a next step (e.g. how to
  get an API key, or to look up a station code first).

## 7. Roadmap

**Phase 1 — foundation & vertical slice.** Shared infra, 12 tools across the four domains,
tests, docs, skill. ✅

**Phase 2 — deepen the four domains.** ✅ (17 tools total)
- Transport: Digitransit GraphQL journey planning (`transport_plan_route`) + geocoding;
  road weather cameras (`transport_find_weather_cameras`). ✅
- Weather: air quality (`weather_get_air_quality`) via HSY urban + national FMI networks. ✅
- Energy: cheapest-upcoming-hours planner (`energy_cheapest_hours`). ✅
- Registers: Statistics Finland *data* fetch (`registers_statfin_get_table`, PxWeb POST with
  auto-default selections + json-stat2 parsing). ✅
- Still open for a later pass: marine AIS, FMI warnings/radar, Fingrid production-mix helper,
  ENTSO-E, Suomi.fi PTV search.

**Phase 3 — civic & culture.** ✅ (21 tools total)
- Eduskunta: `civic_search_mps`, `civic_parliament_composition` (current 200 MPs & seat split). ✅
- Finna cultural search: `culture_search` across libraries/museums/archives. ✅
- NLS geocoding: `places_geocode` (key-gated). ✅
- Still open for a later pass: Eduskunta vote breakdowns, Finna record detail, NLS map tiles.

**Phase 3.5 — domain deepening & tooling.** ✅ (28 tools total)
- Transport: marine AIS (`transport_get_vessels`), road-weather conditions
  (`transport_get_road_weather`). ✅
- Civic: recent votes (`civic_list_votes`) + per-party breakdowns (`civic_get_vote_breakdown`). ✅
- Registers: Suomi.fi PTV service search & detail (`registers_search_services`,
  `registers_get_service`). ✅
- Weather: sea level & waves (`weather_get_sea`). ✅
- AI-discoverability: `AGENTS.md`/`llms.txt` index + generated `docs/TOOLS.md`; per-domain
  skills; GitHub Actions CI (lint, tests, doc-freshness `--check`). ✅

**Phase 3.6 — CLI + wider coverage.** ✅ (30 tools)
- Unified `cli.py`: every tool usable as `call <tool> k=v [--json]`; realises the CLI/JSON/MCP
  vision from one codebase. ✅
- Transport: ship port calls (`transport_get_port_calls`). ✅
- New Library domain: `library_search` (Kirjastot.fi — public libraries & opening hours). ✅

**Phase 4 — quality & distribution.** Evaluation suite (per mcp-builder §4), rate-limit
handling, publish to an MCP registry, optional Docker image for the HTTP mode.

## 8. How to add a service (contributor guide)

1. Add base URL(s) to `config.py`.
2. Create/extend a module in `tools/` with a Pydantic input model and an `@mcp.tool`
   function that calls `_http.request_json`/`request_text` and returns Markdown+JSON.
3. Register the module in `tools/__init__.py` (`MODULES`).
4. Add an offline parse/format test and (optionally) a `-m live` smoke test.
5. Document the endpoint in `skills/finnish-open-data/SKILL.md`.

## 9. Licensing note

The code is MIT. The **data is not** — each source sets its own terms (most are CC BY 4.0
and require attribution to the originator: Fintraffic/Digitraffic, FMI, PRH, Statistics
Finland, DVV/avoindata.fi, Fingrid). Downstream users must attribute accordingly.
