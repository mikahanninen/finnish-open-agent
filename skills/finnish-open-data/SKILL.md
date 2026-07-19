---
name: finnish-open-data
description: >-
  Umbrella entry point for Finland's open data and public-service APIs from the command line.
  Use for general "Finnish open data / open API" questions; for a specific area prefer the
  focused skills: finnish-energy, finnish-weather, finnish-transport, finnish-registers,
  finnish-civic, finnish-culture, finnish-places.
---

# Finnish open data — index

This repository ships **focused per-domain skills**; pick the one matching the task (each has
ready-to-run `curl` recipes and the matching MCP tool names):

| Skill | Covers |
| --- | --- |
| `finnish-energy` | Electricity spot prices, cheapest hours, Fingrid |
| `finnish-weather` | FMI forecasts, observations, air quality, sea level/waves |
| `finnish-transport` | Trains, traffic, cameras, road weather, ships (AIS), routing |
| `finnish-registers` | PRH/YTJ companies, avoindata.fi, Statistics Finland, Suomi.fi services |
| `finnish-civic` | Eduskunta (Parliament): MPs, seats, votes |
| `finnish-culture` | Finna: libraries, museums, archives |
| `finnish-places` | National Land Survey geocoding |

General etiquette: identify yourself to Fintraffic with a `Digitraffic-User` header; prices
are c/kWh incl. Finnish VAT; times are ISO 8601 (Finland = UTC+2/+3). When an MCP server
(`finnish_services_mcp`) is connected, prefer its tools — see `docs/TOOLS.md`. Open data still
has licenses (mostly CC BY 4.0): attribute the originators.
