# Skills

Focused CLI/curl playbooks for Finnish open data — one per domain, so each has a tight,
well-triggering description and only the recipes it needs.

Install with the [`skills` CLI](https://github.com/vercel-labs/skills) (supports Claude Code,
Cursor, Codex, and 70+ other agents):

```bash
npx skills add mikahanninen/finnish-open-agent          # all 11 skills
npx skills add mikahanninen/finnish-open-agent -s finnish-weather   # just one
```

Remove them the same way — `npx skills remove -s finnish-weather` for just one, or
`npx skills remove --all` for everything this CLI installed.

Or drop any folder into your agent's skills directory by hand (e.g. `~/.claude/skills/`).

| Skill | Use it for | Matching MCP tools |
| --- | --- | --- |
| [`finnish-energy`](./finnish-energy) | Electricity spot prices, cheapest hours, Fingrid | `energy_*` |
| [`finnish-weather`](./finnish-weather) | FMI forecasts, observations, air quality, sea | `weather_*` |
| [`finnish-transport`](./finnish-transport) | Trains, traffic, cameras, road weather, ships, routing | `transport_*` |
| [`finnish-registers`](./finnish-registers) | Companies (PRH), avoindata.fi, StatFin, Suomi.fi services | `registers_*` |
| [`finnish-civic`](./finnish-civic) | Parliament: MPs, seats, votes | `civic_*` |
| [`finnish-culture`](./finnish-culture) | Finna: libraries, museums, archives | `culture_search` |
| [`finnish-places`](./finnish-places) | National Land Survey geocoding | `places_geocode` |
| [`finnish-library`](./finnish-library) | Public libraries & opening hours (Kirjastot.fi) | `library_search` |
| [`finnish-health`](./finnish-health) | Health & welfare statistics (THL Sotkanet) | `health_*` |
| [`finnish-events`](./finnish-events) | Events across Finland (LinkedEvents) | `events_search` |
| [`finnish-open-data`](./finnish-open-data) | Umbrella index (general "Finnish open data") | — |

When the `finnish_services_mcp` MCP server is connected, prefer its tools over curl — see the
generated [tool reference](../docs/TOOLS.md).
