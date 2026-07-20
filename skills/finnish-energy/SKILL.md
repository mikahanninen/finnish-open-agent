---
name: finnish-energy
description: >-
  Finnish electricity prices from the command line — hourly Nord Pool FI spot price (c/kWh
  incl. VAT), the current-hour price, and the cheapest upcoming hours to run appliances. Use
  whenever the user asks about Finnish electricity/spot/pörssisähkö prices or when to use power.
---

# Finnish electricity prices (CLI)

Prices are c/kWh **including 25.5% Finnish VAT**. No API key needed.

Hourly spot price, next 6 hours from now (+ tomorrow after ~14:00 EET). The API returns
`prices` **newest-first** — `.prices[:6]` grabs the furthest-future hours, not the upcoming
ones, so filter by time and sort ascending instead:

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
curl -s https://api.porssisahko.net/v1/latest-prices.json \
  | jq --arg now "$NOW" '.prices | map(select(.startDate >= $now)) | sort_by(.startDate) | .[0:6]'
```

Current-hour price:

```bash
curl -s https://api.spot-hinta.fi/JustNow | jq '{c_per_kwh:(.PriceWithTax*100)}'
```

Cheapest upcoming hours (schedule the sauna / EV / dishwasher). `TodayAndDayForward` returns
**15-minute slots for the whole 48h window including already-past ones** — sorting by price
alone (no time filter) can surface hours from earlier today. Filter to the future first:

```bash
NOW=$(TZ=Europe/Helsinki date +%Y-%m-%dT%H:%M:%S)
curl -s https://api.spot-hinta.fi/TodayAndDayForward \
  | jq --arg now "$NOW" '[.[] | select(.DateTime[0:19] >= $now)] | sort_by(.PriceWithTax)[:5]'
```

Grid/production data (Fingrid) needs a free key from data.fingrid.fi:
`curl -H "x-api-key: $KEY" https://data.fingrid.fi/api/datasets/192/data`.

**Prefer the MCP tools when connected:** `energy_get_spot_prices`, `energy_get_price_now`,
`energy_cheapest_hours`, `energy_fingrid_latest`. Attribute: Nord Pool / Fingrid.
