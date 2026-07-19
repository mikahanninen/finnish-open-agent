---
name: finnish-transport
description: >-
  Finnish transport from the command line — VR trains and stations, road traffic messages,
  road weather cameras & conditions, live ship positions (AIS), and public-transport routing.
  Use whenever the user asks about Finnish trains, traffic, roads, ships, or journey planning.
---

# Finnish transport (Fintraffic Digitraffic + Digitransit, CLI)

Send `-H 'Digitraffic-User: your-name/app'` to Digitraffic. Times are UTC.

Find a station code, then live trains:

```bash
curl -s -H 'Digitraffic-User: mika/foa' https://rata.digitraffic.fi/api/v1/metadata/stations \
  | jq '.[] | select(.stationName|test("Tampere")) | .stationShortCode'
curl -s -H 'Digitraffic-User: mika/foa' \
  'https://rata.digitraffic.fi/api/v1/live-trains/station/TPE?departing_trains=8'
```

Road traffic messages, weather cameras, and road-weather station data:

```bash
curl -s -H 'Digitraffic-User: mika/foa' \
  'https://tie.digitraffic.fi/api/traffic-message/v1/messages?inactiveHours=0&situationType=TRAFFIC_ANNOUNCEMENT'
curl -s -H 'Digitraffic-User: mika/foa' https://tie.digitraffic.fi/api/weathercam/v1/stations
curl -s -H 'Digitraffic-User: mika/foa' https://tie.digitraffic.fi/api/weather/v1/stations/1001/data
```

Live ships (AIS, `sog`=speed knots); join names from `/ais/v1/vessels`:

```bash
curl -s -H 'Digitraffic-User: mika/foa' https://meri.digitraffic.fi/api/ais/v1/locations | jq '.features[:3]'
```

Journey planning (Digitransit) needs a free key from portal-api.digitransit.fi — geocode then
POST a GraphQL `plan` query to `https://api.digitransit.fi/routing/v2/finland/gtfs/v1`.

**Prefer the MCP tools:** `transport_find_station`, `transport_get_station_trains`,
`transport_get_traffic_messages`, `transport_find_weather_cameras`, `transport_get_road_weather`,
`transport_get_vessels`, `transport_plan_route`. Attribute: Fintraffic / Digitraffic.
