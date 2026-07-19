---
name: finnish-civic
description: >-
  Finnish Parliament (Eduskunta) open data from the command line — current Members of
  Parliament and seat composition, and plenary votes with per-party yes/no/abstain/absent
  breakdowns. Use whenever the user asks about the Finnish Parliament, MPs, parties/seats, or
  how parliament voted.
---

# Finnish Parliament — Eduskunta (CLI)

Key-less table API. `perPage` is capped at 100. List tables at
`https://avoindata.eduskunta.fi/api/v1/tables/`.

Current MPs & seat composition (`SeatingOfParliament`; party codes kok, ps, sd, kesk, vihr,
vas, r, kd):

```bash
curl -s 'https://avoindata.eduskunta.fi/api/v1/tables/SeatingOfParliament/rows?perPage=100&page=0' \
  | jq '.rowData | map({name:(.[3]+" "+.[2]), party:.[4]}) | group_by(.party) | map({party:.[0].party, seats:length})'
```

Recent votes for a parliament year (filter server-side; newest first within the year):

```bash
curl -s 'https://avoindata.eduskunta.fi/api/v1/tables/SaliDBAanestys/rows?columnName=IstuntoVPVuosi&columnValue=2025&perPage=5&page=0' \
  | jq '.rowData | map({id:.[0], date:.[4], title:.[12]})'
```

Per-party breakdown of one vote (Jaa=yes, Ei=no, Tyhjia=abstain, Poissa=absent):

```bash
curl -s 'https://avoindata.eduskunta.fi/api/v1/tables/SaliDBAanestysJakauma/rows?columnName=AanestysId&columnValue=55554&perPage=100&page=0' \
  | jq '.rowData | map({group:.[2], yes:.[3], no:.[4]})'
```

**Prefer the MCP tools:** `civic_search_mps`, `civic_parliament_composition`,
`civic_list_votes`, `civic_get_vote_breakdown`. Attribute: Eduskunta / Parliament of Finland.
