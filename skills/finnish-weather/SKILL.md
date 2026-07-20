---
name: finnish-weather
description: >-
  Finnish weather from the Finnish Meteorological Institute (FMI) via the command line —
  forecasts, station observations, air quality, and sea level / waves. Use whenever the user
  asks about weather, temperature, wind, rain, air quality, or sea conditions in Finland.
---

# Finnish weather & environment (FMI, CLI)

FMI serves XML via WFS stored queries (no key). Each `<BsWfs:BsWfsElement>` has a `Time`,
`ParameterName`, `ParameterValue`; pivot by time.

Forecast (HARMONIE):

```bash
curl -s 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature\
&storedquery_id=fmi::forecast::harmonie::surface::point::simple\
&place=Helsinki&parameters=Temperature,WindSpeedMS,Humidity&timestep=60'
```

Station observations (`t2m`=temp, `ws_10min`=wind, `rh`=humidity, `r_1h`=rain):

```bash
curl -s 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature\
&storedquery_id=fmi::observations::weather::simple&place=Tampere&parameters=t2m,ws_10min,rh'
```

Air quality — **do NOT send `&parameters=`** (returns 0); use `urban::` for the Helsinki
region and `fmi::` elsewhere. `AQINDEX_PT1H_avg` = index (1 good … 5+ very poor):

```bash
curl -s 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature\
&storedquery_id=urban::observations::airquality::hourly::simple&place=Helsinki'
```

Sea level / waves (coastal stations): stored queries
`fmi::observations::mareograph::instant::simple` (WATLEV cm, TW °C) and
`fmi::observations::wave::simple`.

Solar radiation (GLOB_1MIN W/m², UVB_U) with `fmi::observations::radiation::simple&place=...`.
National background radiation (STUK, dose rate `DR_PT10M_avg` µSv/h; normal ≈ 0.1):

```bash
curl -s 'https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature\
&storedquery_id=stuk::observations::external-radiation::latest::simple' | grep -c BsWfsElement
```

**Prefer the MCP tools:** `weather_get_forecast`, `weather_get_observations`,
`weather_get_air_quality`, `weather_get_sea`, `weather_get_solar`, `weather_get_radiation`.
Attribute: Finnish Meteorological Institute / STUK.
