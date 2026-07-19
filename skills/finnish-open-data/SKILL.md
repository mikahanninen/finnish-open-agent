---
name: finnish-open-data
description: >-
  Access Finland's open data and public-service APIs from the command line (curl/jq) —
  electricity spot prices, FMI weather forecasts & observations, Fintraffic Digitraffic
  road/rail data, the PRH/YTJ business register, the avoindata.fi catalogue, and Statistics
  Finland. Use whenever the user asks about Finnish electricity prices, Finnish weather,
  Finnish trains or road traffic, a Finnish company / Business ID (Y-tunnus), Finnish open
  datasets, or Finnish statistics — and no dedicated MCP tool is available.
---

# Finnish Open Data — CLI playbook

Reach Finland's public, open APIs with plain `curl`. Almost none need an API key. Prefer the
`finnish_services_mcp` MCP tools when they are connected; use these recipes when they are not,
or when the user wants a copy-pasteable command.

**Etiquette:** send an identifying `Digitraffic-User` header to Fintraffic endpoints. Prices
are c/kWh incl. Finnish VAT. Times are ISO 8601, mostly UTC (Finland = UTC+2/+3).
Pipe through `jq` for readable output.

## ⚡ Electricity spot price

Hourly day-ahead price for today (+tomorrow after ~14:00 EET), c/kWh incl. VAT:

```bash
curl -s https://api.porssisahko.net/v1/latest-prices.json | jq '.prices[:5]'
```

Current-hour price and its cheapness rank:

```bash
curl -s https://api.spot-hinta.fi/JustNow | jq '{price_c_per_kwh: (.PriceWithTax*100), rank: .Rank}'
```

Cheapest N hours of the day (planning appliances):

```bash
curl -s 'https://api.spot-hinta.fi/TodayAndDayForward' | jq 'sort_by(.PriceWithTax)[:5]'
```

## 🌦️ Weather (Finnish Meteorological Institute)

FMI serves XML via WFS "stored queries". Forecast for a place (temperature, wind, humidity):

```bash
curl -s 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature\
&storedquery_id=fmi::forecast::harmonie::surface::point::simple\
&place=Helsinki&parameters=Temperature,WindSpeedMS,Humidity&timestep=60'
```

Recent station observations (t2m=temp °C, ws_10min=wind m/s, rh=humidity %, r_1h=rain mm):

```bash
curl -s 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature\
&storedquery_id=fmi::observations::weather::simple&place=Tampere&parameters=t2m,ws_10min,rh'
```

Each `<BsWfs:BsWfsElement>` holds a `Time`, `ParameterName`, and `ParameterValue`; pivot by
time to build rows. List all stored queries with
`...&request=describeStoredQueries`.

## 🚆 Transport (Fintraffic Digitraffic)

Always send `-H 'Digitraffic-User: your-name/your-app'`.

Find a railway station short code:

```bash
curl -s -H 'Digitraffic-User: mika/foa' \
  https://rata.digitraffic.fi/api/v1/metadata/stations \
  | jq '.[] | select(.stationName|test("Tampere")) | {stationName, stationShortCode}'
```

Live departing trains from a station (use the short code, e.g. TPE):

```bash
curl -s -H 'Digitraffic-User: mika/foa' \
  'https://rata.digitraffic.fi/api/v1/live-trains/station/TPE?departing_trains=8&include_nonstopping=false' \
  | jq '.[] | {train: (.trainType+(.trainNumber|tostring)), cancelled}'
```

Current road traffic disruption messages:

```bash
curl -s -H 'Digitraffic-User: mika/foa' \
  'https://tie.digitraffic.fi/api/traffic-message/v1/messages?inactiveHours=0&situationType=TRAFFIC_ANNOUNCEMENT' \
  | jq '.features[].properties.announcements[0].title'
```

## 🏢 Business register (PRH / YTJ)

Search companies by name (Business ID = Y-tunnus, format `1234567-8`):

```bash
curl -s 'https://avoindata.prh.fi/opendata-ytj-api/v3/companies?name=Supercell' \
  | jq '.companies[] | {businessId: .businessId.value, name: .names[0].name}'
```

Full details for one company:

```bash
curl -s 'https://avoindata.prh.fi/opendata-ytj-api/v3/companies?businessId=2336509-6' | jq '.companies[0]'
```

## 📚 National open-data catalogue (avoindata.fi / CKAN)

Discover which datasets/APIs exist for a topic:

```bash
curl -s 'https://www.avoindata.fi/data/api/3/action/package_search?q=air%20quality&rows=5' \
  | jq '.result.results[] | {title, publisher: .organization.title, name}'
```

Dataset page: `https://www.avoindata.fi/data/en_GB/dataset/<name>`.

## 📊 Statistics Finland (PxWeb / StatFin)

Browse the database tree (empty path = top level; `l`=level, `t`=table):

```bash
curl -s 'https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/' | jq '.[] | {id, text, type}'
```

Get a table's variables, then POST a JSON query to fetch values:

```bash
curl -s 'https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/synt/statfin_synt_pxt_12dx.px' | jq '.variables[].code'
```

## When to prefer the MCP server

If `finnish_services_mcp` is connected, call its tools instead of curl — they validate inputs,
add the identifier header, cache metadata, normalise FMI's XML, and return clean Markdown/JSON:
`energy_get_spot_prices`, `energy_get_price_now`, `weather_get_forecast`,
`weather_get_observations`, `transport_find_station`, `transport_get_station_trains`,
`transport_get_traffic_messages`, `registers_search_companies`, `registers_get_company`,
`registers_search_open_datasets`, `registers_statfin_browse`.

## Attribution

Open data still has licences (mostly CC BY 4.0). Credit the originators — Fintraffic /
Digitraffic, Finnish Meteorological Institute, PRH, Statistics Finland, avoindata.fi / DVV,
Fingrid — in anything you publish.
