---
name: finnish-energy
description: >-
  Finnish electricity prices from the command line — hourly Nord Pool FI spot price (c/kWh
  incl. VAT), the current-hour price, and the cheapest upcoming hours to run appliances. Use
  whenever the user asks about Finnish electricity/spot/pörssisähkö prices or when to use power.
---

# Finnish electricity prices (CLI)

Prices are c/kWh **including 25.5% Finnish VAT**. No API key needed.

Hourly spot price for today (+ tomorrow after ~14:00 EET):

```bash
curl -s https://api.porssisahko.net/v1/latest-prices.json | jq '.prices[:6]'
```

Current-hour price:

```bash
curl -s https://api.spot-hinta.fi/JustNow | jq '{c_per_kwh:(.PriceWithTax*100)}'
```

Cheapest upcoming hours (schedule the sauna / EV / dishwasher):

```bash
curl -s https://api.spot-hinta.fi/TodayAndDayForward | jq 'sort_by(.PriceWithTax)[:5]'
```

Grid/production data (Fingrid) needs a free key from data.fingrid.fi:
`curl -H "x-api-key: $KEY" https://data.fingrid.fi/api/datasets/192/data`.

**Prefer the MCP tools when connected:** `energy_get_spot_prices`, `energy_get_price_now`,
`energy_cheapest_hours`, `energy_fingrid_latest`. Attribute: Nord Pool / Fingrid.
