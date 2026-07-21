# 🇫🇮 Finnish Open Agent

An agentic toolkit for **Finland's open data and public-service APIs**. It is open-source,
portable, and agent-friendly — one codebase, three ways to use it:

1. **CLI for humans** — `finnish-open-agent call <tool> key=value ...` runs any tool from the
   terminal.
2. **JSON output for AI tools** — add `--json` (or `response_format=json`) for machine-readable
   output.
3. **MCP server for agents** — `finnish_services_mcp` exposes every tool to Claude Desktop,
   Claude Code, or any MCP client; and **skills** (Markdown playbooks) teach agents the
   plain-`curl` path when no server is running.

Every tool is available in all three modes automatically. Most services need **no API key** —
everything here is public, open data.

## Domains (v0.10 — 40 tools)

Full, always-current tool reference: [`docs/TOOLS.md`](./docs/TOOLS.md) (auto-generated).

| Domain | Source | Tools |
| --- | --- | --- |
| ⚡ Energy | porssisahko.net, spot-hinta.fi, Fingrid | spot prices, price now, cheapest hours, Fingrid data |
| 🌦️ Weather | FMI, HSY, STUK | forecast, observations, air quality, sea level & waves, solar radiation, national radiation (STUK), lightning |
| 🚆 Transport | Fintraffic Digitraffic, Digitransit | stations & live trains, traffic messages, weather cameras, road-weather conditions, road maintenance, ships (AIS), port calls, journey routing |
| 🏢 Registers | PRH/YTJ, avoindata.fi, Statistics Finland, Suomi.fi | company search & detail, open-dataset search & detail, StatFin browse & data, public-service search & detail |
| 🏛️ Civic | Eduskunta (Parliament) | MP search, seat composition, recent votes, vote breakdowns |
| 🎭 Culture | Finna | cultural-heritage search & record detail |
| 🗺️ Places | National Land Survey (MML) | geocoding |
| 📚 Library | Kirjastot.fi | public library search & opening hours |
| 🩺 Health | THL Sotkanet | health & welfare indicator search & values |
| 🎫 Events | LinkedEvents | search events across Finland |

Three tools need a free key (see Configuration): `transport_plan_route` (Digitransit),
`energy_fingrid_latest` (Fingrid), and `places_geocode` (National Land Survey). Everything
else is key-less.

### Services & data sources

Every Finnish service this repository integrates, what it provides, and whether it needs a key:

| Service (provider) | Provides | Key | Domain |
| --- | --- | --- | --- |
| porssisahko.net / spot-hinta.fi | Hourly electricity spot price (Nord Pool FI), c/kWh incl. VAT | no | Energy |
| Fingrid open data | Grid load, production mix, wind/nuclear/hydro time series | free key | Energy |
| FMI — Finnish Meteorological Institute | Forecasts, station observations, sea level & waves | no | Weather |
| HSY (via FMI `urban::`) | Helsinki-region air quality | no | Weather |
| STUK (via FMI) | National external (background) radiation dose rate | no | Weather |
| Fintraffic Digitraffic — rail | VR live trains, timetables, station metadata | no | Transport |
| Fintraffic Digitraffic — road | Traffic messages, weather cameras, road-weather stations | no | Transport |
| Fintraffic Digitraffic — marine | AIS live ship positions, port calls | no | Transport |
| Digitransit | Nationwide public-transport journey planning + geocoding | free key | Transport |
| PRH / YTJ | Business register — companies, Business IDs (Y-tunnus) | no | Registers |
| avoindata.fi (DVV) | National open-data catalogue (dataset discovery) | no | Registers |
| Statistics Finland (Tilastokeskus) | StatFin statistical database (PxWeb) | no | Registers |
| Suomi.fi PTV | Finnish Service Catalogue — public services & channels | no | Registers |
| Eduskunta | Parliament — MPs, seat composition, votes & breakdowns | no | Civic |
| Finna (National Library) | Libraries, museums & archives search | no | Culture |
| Maanmittauslaitos (NLS) | Geocoding — place/address → coordinates | free key | Places |
| Kirjastot.fi | Public libraries — directory & opening hours | no | Library |
| THL Sotkanet | Health & welfare statistical indicators by region/year | no | Health |
| LinkedEvents | Events across Finland (concerts, exhibitions, etc.) | no | Events |

All data is public and open; each source sets its own license (mostly CC BY 4.0 — attribute
the originator). See the [tool reference](./docs/TOOLS.md) for the tools built on each.

See [`PLAN.md`](./PLAN.md) for architecture, [`AGENTS.md`](./AGENTS.md) for a code map, and
[`skills/`](./skills) for per-domain CLI playbooks.

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). No clone needed — `uvx` runs it
straight from GitHub (like `npx`):

```bash
# List every tool
uvx --from git+https://github.com/mikahanninen/finnish-open-agent finnish-open-agent list

# 1) CLI for humans
uvx --from git+https://github.com/mikahanninen/finnish-open-agent finnish-open-agent \
  call energy_cheapest_hours count=3

# 2) JSON output for AI/scripting — add --json
uvx --from git+https://github.com/mikahanninen/finnish-open-agent finnish-open-agent \
  call weather_get_forecast place=Helsinki hours=6 --json
```

Tip: alias it — `alias foa='uvx --from git+https://github.com/mikahanninen/finnish-open-agent finnish-open-agent'`
— then just `foa list`, `foa call library_search query=Oodi`.

### For development (clone)

```bash
git clone https://github.com/mikahanninen/finnish-open-agent.git
cd finnish-open-agent
uv venv && uv pip install -e ".[dev]"
uv run finnish-open-agent list
```

### Use it from Claude Desktop / Claude Code

Add to your MCP config (e.g. `claude_desktop_config.json`). This form needs no local path:

```json
{
  "mcpServers": {
    "finnish-open-agent": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/mikahanninen/finnish-open-agent",
        "finnish-open-agent"
      ],
      "env": { "FOA_APP_ID": "your-name/finnish-open-agent" }
    }
  }
}
```

If you cloned the repo instead, point `uv` at it: `"command": "uv"`, `"args":
["--directory", "/path/to/finnish-open-agent", "run", "finnish-open-agent"]`.

Then ask things like:

- "What are the 3 cheapest hours for electricity in Finland tonight?"
- "Give me the 12-hour weather forecast for Rovaniemi, and the air quality in Helsinki."
- "When do the next trains leave Tampere, and plan me a route from Helsinki to Otaniemi."
- "Look up the company Supercell and its Business ID."
- "What was Finland's population at the end of 2025?" (Statistics Finland)
- "What's the current seat split in the Finnish Parliament, and who are the Green MPs?"
- "Find archive photos of Tove Jansson in Finnish museums." (Finna)

## Configuration

All configuration is via environment variables (see [`.env.example`](./.env.example)):

| Variable | Default | Purpose |
| --- | --- | --- |
| `FOA_APP_ID` | `finnish-open-agent` | Identifier sent as `Digitraffic-User` header (Fintraffic asks callers to identify themselves) |
| `FOA_HTTP_TIMEOUT` | `30` | Per-request timeout (seconds) |
| `FOA_CACHE_TTL` | `120` | In-process cache TTL for slow-moving metadata (seconds; 0 disables) |
| `FINGRID_API_KEY` | — | Free key from data.fingrid.fi (only needed for `energy_fingrid_latest`) |
| `DIGITRANSIT_API_KEY` | — | Free key from portal-api.digitransit.fi (needed for `transport_plan_route`) |
| `NLS_API_KEY` | — | Free National Land Survey key (needed for `places_geocode`) |
| `FOA_TRANSPORT` | `stdio` | `stdio` (local) or `http` (remote streamable HTTP) |
| `FOA_HOST` / `FOA_PORT` | `127.0.0.1` / `8000` | Bind address for HTTP transport |

## 🇫🇮 Community collection

Beyond this repo's own tools, `finnish-open-agent` curates a directory of **other people's**
Finnish skills, MCP servers, and agentic tools. It's link-only — every project stays owned by
its author under its own license; nothing is copied here. Browse
[`ecosystem/CATALOG.md`](./ecosystem/CATALOG.md) (auto-generated from
[`ecosystem/registry.yaml`](./ecosystem/registry.yaml)).

Featured community entries:

- **[WilmAI](https://github.com/aikarjal/wilmai)** by `aikarjal` ([wilm.ai](https://www.wilm.ai/)) —
  an open-source CLI that reads the Wilma school system (schedule, homework, grades,
  attendance…) as clean JSON, with an AI-agent-friendly mode.
- **[maiklubi](https://github.com/jannemakela/maiklubi)** by Janne Mäkelä — an AI-friendly CLI
  for myclub.fi that consolidates family sports-club events, RSVPs, invoices, and notifications
  from the terminal or an AI agent.

Want your project listed? Add one entry to the registry and open a PR — see
[CONTRIBUTING.md](./CONTRIBUTING.md). To regenerate the catalog and the site's community table:

```bash
uv run python scripts/render_catalog.py
uv run python scripts/render_community_table.py
```

## CLI / skill approach

Prefer not to run a server? The [`skills/finnish-open-data`](./skills/finnish-open-data)
skill documents ready-to-run `curl` recipes for every source above. Install any or all of
the 11 skills into your agent with the [`skills` CLI](https://github.com/vercel-labs/skills)
(supports Claude Code, Cursor, Codex, and 70+ others):

```bash
npx skills add mikahanninen/finnish-open-agent                    # all 11 skills
npx skills add mikahanninen/finnish-open-agent -s finnish-weather # just one
npx skills add mikahanninen/finnish-open-agent -s finnish-weather,finnish-transport # a few
```

Remove them the same way:

```bash
npx skills remove -s finnish-weather   # just one
npx skills remove --all                # everything this CLI installed
```

Or drop a skill folder into your agent's skills directory by hand (e.g. `~/.claude/skills/`).

## Testing & CI

```bash
uv run python -m pytest -m "not live"   # offline unit tests (parsing, docs freshness)
uv run python -m pytest -m live         # optional live smoke tests against real APIs
uv run ruff check src tests scripts
uv run python scripts/render_tools.py    # regenerate docs/TOOLS.md
uv run python scripts/render_catalog.py  # regenerate ecosystem/CATALOG.md
```

GitHub Actions ([`.github/workflows/ci.yml`](./.github/workflows/ci.yml)) runs lint, offline
tests, and a **doc-freshness check** — a PR that changes tools or the registry without
regenerating `docs/TOOLS.md` / `ecosystem/CATALOG.md` fails CI, so the generated markdown can
never drift out of sync.

## Data sources & licensing

This project only calls **public, open** interfaces. Each source has its own terms; most
are CC BY 4.0 and ask for attribution. Attribute the originators (Fintraffic / Digitraffic,
Finnish Meteorological Institute, PRH, Statistics Finland, avoindata.fi / DVV) when you
publish derived data. This repository is MIT licensed; the data is not.

## License

MIT — see [`LICENSE`](./LICENSE).
