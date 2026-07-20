# 🇫🇮 Finnish Open Agent — MCP tool reference

> Auto-generated from the live MCP server by `scripts/render_tools.py`. **Do not edit by hand.**

**36 tools.** All are read-only. See [`PLAN.md`](../PLAN.md) for architecture.

## ⚡ Energy

### `energy_cheapest_hours`

Find the cheapest upcoming hours to run electricity-hungry appliances in Finland.

| Parameter | Required | Description |
| --- | --- | --- |
| `count` | no | How many cheap hours to return. |
| `within_hours` | no | Only consider hours starting within this many hours from now (search window). |
| `response_format` | no |  |

### `energy_fingrid_latest`

Get the most recent values for a Fingrid open-data dataset (grid/production/consumption).

| Parameter | Required | Description |
| --- | --- | --- |
| `dataset_id` | yes | Fingrid dataset id, e.g. 192=electricity production, 193=consumption, 245=wind power generation, 124=total consumption forecast. See data.fingrid.fi. |
| `last_n` | no | Number of most recent data points. |

### `energy_get_price_now`

Get the electricity spot price for the current hour in Finland.

### `energy_get_spot_prices`

Get hourly Finnish electricity spot (exchange) prices for today and tomorrow.

| Parameter | Required | Description |
| --- | --- | --- |
| `hours` | no | How many of the most recent/upcoming hourly prices to return (1-48). |
| `response_format` | no | 'markdown' for reading, 'json' for processing. |

## 🌦️ Weather

### `weather_get_air_quality`

Get recent air-quality observations for a Finnish location from FMI.

| Parameter | Required | Description |
| --- | --- | --- |
| `place` | yes | Finnish place name, e.g. 'Helsinki'. |
| `hours` | no | How many past hours to include. |
| `parameters` | no | FMI air-quality parameters. AQINDEX_PT1H_avg=air-quality index, PM25/PM10=particulates µg/m³, NO2/O3/SO2/CO=gases. |
| `response_format` | no |  |

### `weather_get_forecast`

Get an hourly HARMONIE weather forecast for a Finnish location from FMI.

| Parameter | Required | Description |
| --- | --- | --- |
| `place` | yes | Finnish place name, e.g. 'Helsinki', 'Rovaniemi', 'Tampere'. |
| `hours` | no | Number of forecast hours (1-60). |
| `parameters` | no | Comma-separated FMI forecast parameters (e.g. 'Temperature,WindSpeedMS'). |
| `response_format` | no |  |

### `weather_get_lightning`

Get current lightning-strike activity over Finland and the Baltic from FMI.

### `weather_get_observations`

Get recent real weather-station observations for a Finnish location from FMI.

| Parameter | Required | Description |
| --- | --- | --- |
| `place` | yes | Finnish place/station name, e.g. 'Helsinki'. |
| `hours` | no | How many past hours of observations. |
| `parameters` | no | FMI observation parameters (t2m=temp, ws_10min=wind, rh=humidity, r_1h=rain). |
| `response_format` | no |  |

### `weather_get_radiation`

Get Finland's current external (background) radiation levels from STUK, nationwide.

### `weather_get_sea`

Get recent sea-level (mareograph) or wave observations for a Finnish coastal location (FMI).

| Parameter | Required | Description |
| --- | --- | --- |
| `place` | yes | Coastal place/station, e.g. 'Helsinki', 'Kemi', 'Hanko'. |
| `kind` | no | 'sealevel' (mareograph) or 'wave' (buoys). |
| `hours` | no | How many past hours to include. |
| `response_format` | no |  |

### `weather_get_solar`

Get recent solar-radiation observations for a Finnish location from FMI.

| Parameter | Required | Description |
| --- | --- | --- |
| `place` | yes | Finnish place with a radiation station, e.g. 'Helsinki', 'Jokioinen', 'Sodankylä'. |
| `hours` | no | How many past hours to include. |
| `response_format` | no |  |

## 🚆 Transport

### `transport_find_station`

Find Finnish passenger railway stations and their short codes by name.

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | yes | Part of a station name, e.g. 'Tampere'. |
| `limit` | no |  |

### `transport_find_weather_cameras`

Find Finnish road weather-camera stations by name (Fintraffic Digitraffic).

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | yes | Text to match in a camera station name, e.g. 'Kirkkonummi' or 'vt1'. |
| `limit` | no |  |
| `response_format` | no |  |

### `transport_get_port_calls`

Get recent and upcoming ship port calls at Finnish ports (Fintraffic Digitraffic).

| Parameter | Required | Description |
| --- | --- | --- |
| `port` | no | UN/LOCODE of a Finnish port to filter by, e.g. FIHEL (Helsinki), FITKU (Turku), FIKTK (Kotka), FIRAU (Rauma), FIOUL (Oulu). Omit for all ports. |
| `limit` | no |  |
| `response_format` | no |  |

### `transport_get_road_maintenance`

Get recent road maintenance activity on Finnish state roads (Fintraffic Digitraffic).

| Parameter | Required | Description |
| --- | --- | --- |
| `limit` | no |  |
| `response_format` | no |  |

### `transport_get_road_weather`

Get current road-weather sensor readings from a Fintraffic road weather station.

| Parameter | Required | Description |
| --- | --- | --- |
| `station` | yes | Road weather station name or numeric id, e.g. 'Kirkkonummi' or '1001'. |
| `all_sensors` | no | Return every sensor instead of the curated set. |
| `response_format` | no |  |

### `transport_get_station_trains`

Get live arriving/departing trains at a Finnish railway station (VR / Fintraffic).

| Parameter | Required | Description |
| --- | --- | --- |
| `station` | yes | Station name or short code, e.g. 'Helsinki' or 'HKI'. |
| `arriving` | no | Number of arriving trains to include. |
| `departing` | no | Number of departing trains to include. |
| `response_format` | no |  |

### `transport_get_traffic_messages`

Get current Finnish road traffic disruption messages (Digitraffic).

| Parameter | Required | Description |
| --- | --- | --- |
| `situation_type` | no | One of TRAFFIC_ANNOUNCEMENT, EXEMPTED_TRANSPORT, WEIGHT_RESTRICTION, ROAD_WORK. |
| `limit` | no |  |
| `response_format` | no |  |

### `transport_get_vessels`

Get live ship positions in Finnish/Baltic waters from Fintraffic AIS (Digitraffic).

| Parameter | Required | Description |
| --- | --- | --- |
| `min_lat` | no | Bounding box south latitude. |
| `max_lat` | no | Bounding box north latitude. |
| `min_lon` | no | Bounding box west longitude. |
| `max_lon` | no | Bounding box east longitude. |
| `moving_only` | no | Only include vessels currently moving (speed > 0.5 kn). |
| `limit` | no |  |
| `response_format` | no |  |

### `transport_plan_route`

Plan a public-transport journey between two Finnish places (Digitransit / HSL nationwide).

| Parameter | Required | Description |
| --- | --- | --- |
| `from_place` | yes | Origin address or place, e.g. 'Helsinki railway station'. |
| `to_place` | yes | Destination address or place, e.g. 'Espoo, Otaniemi'. |
| `itineraries` | no | Number of route options. |
| `response_format` | no |  |

## 🏢 Registers & data

### `registers_get_company`

Get detailed registry information for a Finnish company by its Business ID.

| Parameter | Required | Description |
| --- | --- | --- |
| `business_id` | yes | Finnish Business ID (Y-tunnus), format 1234567-8. |
| `response_format` | no |  |

### `registers_get_open_dataset`

Get an avoindata.fi dataset's details and its downloadable resources / API endpoints.

| Parameter | Required | Description |
| --- | --- | --- |
| `name` | yes | Dataset name/slug from registers_search_open_datasets (the last URL path segment). |
| `response_format` | no |  |

### `registers_get_service`

Get details of a Suomi.fi public service (PTV) by its GUID.

| Parameter | Required | Description |
| --- | --- | --- |
| `service_id` | yes | PTV service GUID from registers_search_services. |
| `response_format` | no |  |

### `registers_search_companies`

Search the Finnish Business Information System (PRH/YTJ) for companies by name.

| Parameter | Required | Description |
| --- | --- | --- |
| `name` | yes | Company name or part of it, e.g. 'Nokia'. |
| `page` | no | Result page (100 companies/page). |
| `response_format` | no |  |

### `registers_search_open_datasets`

Search Finland's national open-data catalogue (avoindata.fi / CKAN) for datasets.

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | yes | Search terms, e.g. 'air quality', 'population', 'kirjasto'. |
| `rows` | no | Number of datasets to return. |
| `response_format` | no |  |

### `registers_search_services`

Search the Suomi.fi Finnish Service Catalogue (PTV) for public services by name.

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | yes | Words to match in a public service name, e.g. 'varhaiskasvatus', 'passport'. |
| `limit` | no |  |
| `response_format` | no |  |

### `registers_statfin_browse`

Browse the Statistics Finland (Tilastokeskus) PxWeb StatFin database tree.

| Parameter | Required | Description |
| --- | --- | --- |
| `path` | no | PxWeb path under StatFin, e.g. '' for top level, 'vaerak' for a subject. |
| `response_format` | no |  |

### `registers_statfin_get_table`

Fetch actual statistical values from a Statistics Finland (StatFin) PxWeb table.

| Parameter | Required | Description |
| --- | --- | --- |
| `table_path` | yes | PxWeb table path under StatFin, e.g. 'vaerak/11ra.px' (discover ids with registers_statfin_browse). |
| `selections` | no | Optional {variable_code: [value_codes]} to select. Any variable you omit defaults to its most recent/last value. Get codes from registers_statfin_browse on the table. |
| `max_cells` | no | Max data cells to return. |
| `response_format` | no |  |

## 🏛️ Civic (Parliament)

### `civic_get_vote_breakdown`

Get the yes/no/abstain/absent breakdown of a Finnish Parliament vote, by party.

| Parameter | Required | Description |
| --- | --- | --- |
| `vote_id` | yes | Vote id (AanestysId) from civic_list_votes. |
| `response_format` | no |  |

### `civic_list_votes`

List recent plenary votes in the Finnish Parliament (Eduskunta) for a given year.

| Parameter | Required | Description |
| --- | --- | --- |
| `year` | no | Parliament year (defaults to the current year), e.g. 2025. |
| `limit` | no |  |
| `response_format` | no |  |

### `civic_parliament_composition`

Get the current seat distribution of the Finnish Parliament by party.

### `civic_search_mps`

Search current Finnish Members of Parliament (Eduskunta) by name and/or party.

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | no | Name (or part of it) to search for. Empty = list everyone. |
| `party` | no | Filter by party/group code, e.g. 'kok', 'sd', 'ps', 'vihr', 'vas'. |
| `limit` | no |  |
| `response_format` | no |  |

## 🎭 Culture

### `culture_get_record`

Get full details of a single Finna cultural-heritage record by its id.

| Parameter | Required | Description |
| --- | --- | --- |
| `record_id` | yes | Finna record id from culture_search, e.g. 'eepos.136605'. |
| `response_format` | no |  |

### `culture_search`

Search Finna — Finnish libraries, museums, and archives — for cultural-heritage records.

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | yes | Search terms, e.g. 'Tove Jansson', 'Sibelius', 'Aalto'. |
| `limit` | no |  |
| `response_format` | no |  |

## 🗺️ Places

### `places_geocode`

Geocode a Finnish place name or address to coordinates (National Land Survey / MML).

| Parameter | Required | Description |
| --- | --- | --- |
| `text` | yes | Place name or address, e.g. 'Mannerheimintie 1, Helsinki'. |
| `limit` | no |  |
| `response_format` | no |  |

## Library

### `library_search`

Search Finnish public libraries by name and/or city, with today's opening hours.

| Parameter | Required | Description |
| --- | --- | --- |
| `query` | no | Library name to search, e.g. 'Oodi', 'pääkirjasto'. |
| `city` | no | Filter by city/municipality, e.g. 'Tampere'. |
| `limit` | no |  |
| `response_format` | no |  |

