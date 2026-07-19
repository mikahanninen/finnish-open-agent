# 🇫🇮 Finnish Open Agent

An agentic toolkit for **Finland's open data and public-service APIs**. It ships two
complementary things:

1. **An MCP server** (`finnish_services_mcp`) that exposes Finnish open APIs as clean,
   agent-friendly tools — usable from Claude Desktop, Claude Code, or any MCP client.
2. **Skills** (Markdown playbooks) that teach an agent how to reach the same data with a
   plain **CLI / `curl` approach** when an MCP server isn't available.

Most services need **no API key**. Everything here is public, open data.

## Domains (v0.5 — 28 tools)

Full, always-current tool reference: [`docs/TOOLS.md`](./docs/TOOLS.md) (auto-generated).

| Domain | Source | Tools |
| --- | --- | --- |
| ⚡ Energy | porssisahko.net, spot-hinta.fi, Fingrid | spot prices, price now, cheapest hours, Fingrid data |
| 🌦️ Weather | FMI, HSY | forecast, observations, air quality, sea level & waves |
| 🚆 Transport | Fintraffic Digitraffic, Digitransit | stations & live trains, traffic messages, weather cameras, road-weather conditions, ships (AIS), journey routing |
| 🏢 Registers | PRH/YTJ, avoindata.fi, Statistics Finland, Suomi.fi | company search & detail, open-dataset search, StatFin browse & data, public-service search & detail |
| 🏛️ Civic | Eduskunta (Parliament) | MP search, seat composition, recent votes, vote breakdowns |
| 🎭 Culture | Finna | cultural-heritage search |
| 🗺️ Places | National Land Survey (MML) | geocoding |

Three tools need a free key (see Configuration): `transport_plan_route` (Digitransit),
`energy_fingrid_latest` (Fingrid), and `places_geocode` (National Land Survey). Everything
else is key-less.

See [`PLAN.md`](./PLAN.md) for architecture, [`AGENTS.md`](./AGENTS.md) for a code map, and
[`skills/`](./skills) for per-domain CLI playbooks.

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv venv
uv pip install -e ".[dev]"

# Run the MCP server over stdio (default)
uv run finnish-open-agent
```

### Use it from Claude Desktop / Claude Code

Add to your MCP config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "finnish-open-agent": {
      "command": "uv",
      "args": ["--directory", "/Users/mika/koodi/finnish-open-agent", "run", "finnish-open-agent"],
      "env": { "FOA_APP_ID": "mika/finnish-open-agent" }
    }
  }
}
```

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

Featured community entry: **[WilmAI](https://github.com/aikarjal/wilmai)** by `aikarjal`
([wilm.ai](https://www.wilm.ai/)) — an open-source CLI that reads the Wilma school system
(schedule, homework, grades, attendance…) as clean JSON, with an AI-agent-friendly mode.

Want your project listed? Add one entry to the registry and open a PR — see
[CONTRIBUTING.md](./CONTRIBUTING.md). To regenerate the catalog:

```bash
uv run python scripts/render_catalog.py
```

## CLI / skill approach

Prefer not to run a server? The [`skills/finnish-open-data`](./skills/finnish-open-data)
skill documents ready-to-run `curl` recipes for every source above. Drop the folder into
your agent's skills directory (or `~/.claude/skills/`).

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
