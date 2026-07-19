# Skills

Focused CLI/curl playbooks for Finnish open data — one per domain, so each has a tight,
well-triggering description and only the recipes it needs. Drop any folder into your agent's
skills directory (e.g. `~/.claude/skills/`).

| Skill | Use it for | Matching MCP tools |
| --- | --- | --- |
| [`finnish-energy`](./finnish-energy) | Electricity spot prices, cheapest hours, Fingrid | `energy_*` |
| [`finnish-weather`](./finnish-weather) | FMI forecasts, observations, air quality, sea | `weather_*` |
| [`finnish-transport`](./finnish-transport) | Trains, traffic, cameras, road weather, ships, routing | `transport_*` |
| [`finnish-registers`](./finnish-registers) | Companies (PRH), avoindata.fi, StatFin, Suomi.fi services | `registers_*` |
| [`finnish-civic`](./finnish-civic) | Parliament: MPs, seats, votes | `civic_*` |
| [`finnish-culture`](./finnish-culture) | Finna: libraries, museums, archives | `culture_search` |
| [`finnish-places`](./finnish-places) | National Land Survey geocoding | `places_geocode` |
| [`finnish-open-data`](./finnish-open-data) | Umbrella index (general "Finnish open data") | — |

When the `finnish_services_mcp` MCP server is connected, prefer its tools over curl — see the
generated [tool reference](../docs/TOOLS.md).
