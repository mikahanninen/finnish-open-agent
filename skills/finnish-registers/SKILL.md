---
name: finnish-registers
description: >-
  Finnish registers & official data from the command line — the PRH/YTJ business register
  (companies, Y-tunnus), the avoindata.fi open-data catalogue, Statistics Finland (StatFin),
  and the Suomi.fi public-service catalogue. Use for Finnish companies, Business IDs, open
  datasets, official statistics, or public services.
---

# Finnish registers, data & services (CLI)

Business register (PRH/YTJ), Business ID format `1234567-8`:

```bash
curl -s 'https://avoindata.prh.fi/opendata-ytj-api/v3/companies?name=Supercell' \
  | jq '.companies[] | {id:.businessId.value, name:.names[0].name}'
curl -s 'https://avoindata.prh.fi/opendata-ytj-api/v3/companies?businessId=2336509-6' | jq '.companies[0]'
```

Open-data catalogue (avoindata.fi / CKAN). Use `avoindata.suomi.fi` directly — the old
`www.avoindata.fi` host now 301-redirects there, which silently breaks a plain `curl | jq`
pipe (curl doesn't follow redirects by default, so `jq` gets an HTML redirect page):

```bash
curl -s 'https://avoindata.suomi.fi/data/api/3/action/package_search?q=air%20quality&rows=5' \
  | jq '.result.results[] | {title, name}'
```

Statistics Finland (PxWeb) — browse, then POST a selection (codes are dynamic per table):

```bash
curl -s 'https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/vaerak/11ra.px' | jq '.variables[]|{code,last:.values[-1]}'
```

Suomi.fi public services (PTV) — list is paginated id+name; details by GUID:

```bash
curl -s 'https://api.palvelutietovaranto.suomi.fi/api/v11/Service?page=1' | jq '.itemList[:3]'
curl -s 'https://api.palvelutietovaranto.suomi.fi/api/v11/Service/<GUID>' | jq '.serviceNames'
```

**Prefer the MCP tools:** `registers_search_companies`, `registers_get_company`,
`registers_search_open_datasets`, `registers_statfin_browse`, `registers_statfin_get_table`,
`registers_search_services`, `registers_get_service`. Attribute: PRH, DVV, Statistics Finland.
