# 🇫🇮 Finnish Open Agent

An agentic toolkit for **Finland's open data and public-service APIs**. It ships two
complementary things:

1. **An MCP server** (`finnish_services_mcp`) that exposes Finnish open APIs as clean,
   agent-friendly tools — usable from Claude Desktop, Claude Code, or any MCP client.
2. **Skills** (Markdown playbooks) that teach an agent how to reach the same data with a
   plain **CLI / `curl` approach** when an MCP server isn't available.

Most services need **no API key**. Everything here is public, open data.

## Domains in v0.1

| Domain | Source | Example tools |
| --- | --- | --- |
| ⚡ Energy | porssisahko.net, spot-hinta.fi, Fingrid | `energy_get_spot_prices`, `energy_get_price_now`, `energy_fingrid_latest` |
| 🌦️ Weather | Finnish Meteorological Institute (FMI) | `weather_get_forecast`, `weather_get_observations` |
| 🚆 Transport | Fintraffic Digitraffic (road + rail) | `transport_find_station`, `transport_get_station_trains`, `transport_get_traffic_messages` |
| 🏢 Registers | PRH/YTJ, avoindata.fi, Statistics Finland | `registers_search_companies`, `registers_get_company`, `registers_search_open_datasets`, `registers_statfin_browse` |

See [`PLAN.md`](./PLAN.md) for the full architecture and the roadmap of additional
services (Digitransit journey planning, Suomi.fi PTV, Eduskunta, Finna, and more).

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

- "What's the cheapest hour for electricity in Finland today?"
- "Give me the 12-hour weather forecast for Rovaniemi."
- "When do the next trains leave Tampere?"
- "Look up the company Supercell and its Business ID."
- "What open datasets exist about air quality in Finland?"

## Configuration

All configuration is via environment variables (see [`.env.example`](./.env.example)):

| Variable | Default | Purpose |
| --- | --- | --- |
| `FOA_APP_ID` | `finnish-open-agent` | Identifier sent as `Digitraffic-User` header (Fintraffic asks callers to identify themselves) |
| `FOA_HTTP_TIMEOUT` | `30` | Per-request timeout (seconds) |
| `FOA_CACHE_TTL` | `120` | In-process cache TTL for slow-moving metadata (seconds; 0 disables) |
| `FINGRID_API_KEY` | — | Free key from data.fingrid.fi (only needed for `energy_fingrid_latest`) |
| `DIGITRANSIT_API_KEY` | — | Optional Digitransit key for higher rate limits (roadmap) |
| `FOA_TRANSPORT` | `stdio` | `stdio` (local) or `http` (remote streamable HTTP) |
| `FOA_HOST` / `FOA_PORT` | `127.0.0.1` / `8000` | Bind address for HTTP transport |

## CLI / skill approach

Prefer not to run a server? The [`skills/finnish-open-data`](./skills/finnish-open-data)
skill documents ready-to-run `curl` recipes for every source above. Drop the folder into
your agent's skills directory (or `~/.claude/skills/`).

## Testing

```bash
uv run pytest              # offline unit tests (XML parsing, formatting)
uv run pytest -m live      # optional live smoke tests against real APIs
```

## Data sources & licensing

This project only calls **public, open** interfaces. Each source has its own terms; most
are CC BY 4.0 and ask for attribution. Attribute the originators (Fintraffic / Digitraffic,
Finnish Meteorological Institute, PRH, Statistics Finland, avoindata.fi / DVV) when you
publish derived data. This repository is MIT licensed; the data is not.

## License

MIT — see [`LICENSE`](./LICENSE).
