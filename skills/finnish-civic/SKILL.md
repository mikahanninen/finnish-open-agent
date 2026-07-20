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
vas, r, kd). **200 MPs need two pages** — `perPage` is capped at 100, so page 0 alone silently
returns only half the seats with the wrong per-party counts:

```bash
for p in 0 1; do curl -s "https://avoindata.eduskunta.fi/api/v1/tables/SeatingOfParliament/rows?perPage=100&page=$p"; echo; done \
  | jq -s '[.[].rowData[]] | map({name:(.[3]+" "+.[2]), party:.[4]}) | group_by(.party) | map({party:.[0].party, seats:length}) | sort_by(-.seats)'
```

Votes for a parliament year (filter server-side). Rows come back **oldest first** and
`perPage` is capped at 100, so to get the *most recent* votes you must page until
`hasMore:false` and take the tail of the last page — don't assume page 0 is recent:

```bash
for p in 0 1 2 3 4 5; do
  r=$(curl -s "https://avoindata.eduskunta.fi/api/v1/tables/SaliDBAanestys/rows?columnName=IstuntoVPVuosi&columnValue=2026&perPage=100&page=$p")
  echo "$r" | jq '.hasMore' | grep -q false && { echo "$r" | jq '.rowData | map({id:.[0], date:.[4], title:.[12], asia:.[31]}) | sort_by(.id|tonumber) | reverse | .[:10]'; break; }
done
```

Per-party breakdown of one vote. Rows mix party groups with electoral-district, coalition, and
gender breakdowns (`Tyyppi` column) — filter to `eduskuntaryhma` for parties, and `tonumber`
the count columns since they come back space-padded (`"45        "`):

```bash
curl -s 'https://avoindata.eduskunta.fi/api/v1/tables/SaliDBAanestysJakauma/rows?columnName=AanestysId&columnValue=55554&perPage=100&page=0' \
  | jq '.rowData | map(select(.[8]=="eduskuntaryhma")) | map({group:.[2], yes:(.[3]|tonumber), no:(.[4]|tonumber), abstain:(.[5]|tonumber), absent:(.[6]|tonumber)})'
```

A vote's `asia` field (e.g. `VNS 2/2026 vp`) is just a code. For the plain-language title,
look up that code (the full string, including the trailing vp/rd) as `Eduskuntatunnus` in
`VaskiData` and pull `NimekeTeksti` out of the embedded XML:

```bash
curl -s -G 'https://avoindata.eduskunta.fi/api/v1/tables/VaskiData/rows' \
  --data-urlencode 'columnName=Eduskuntatunnus' --data-urlencode 'columnValue=VNS 2/2026 vp' \
  --data-urlencode 'perPage=1' --data-urlencode 'page=0' \
  | jq -r '.rowData[0][1]' | grep -o '<met1:NimekeTeksti>[^<]*' | sed 's/.*>//' | head -1
```

**Prefer the MCP tools:** `civic_search_mps`, `civic_parliament_composition`,
`civic_list_votes`, `civic_get_vote_breakdown`. Attribute: Eduskunta / Parliament of Finland.
