"""Central configuration for the Finnish Open Agent MCP server.

All settings are read from environment variables so the same code works both as a
local stdio server and as a remote HTTP server. Nothing here is required to run
the open, key-less services (energy spot prices, FMI weather, Digitraffic,
PRH/YTJ, avoindata.fi). Optional API keys unlock the few services that need them.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Identity / politeness
# ---------------------------------------------------------------------------
# Several Finnish APIs (notably Fintraffic / Digitraffic) ask every caller to
# identify themselves with a header so they can contact you about breaking
# changes. Set FOA_APP_ID to something like "my-company/my-app".
APP_ID: str = os.environ.get("FOA_APP_ID", "finnish-open-agent")
USER_AGENT: str = f"{APP_ID} (+https://github.com/)"

# ---------------------------------------------------------------------------
# HTTP behaviour
# ---------------------------------------------------------------------------
HTTP_TIMEOUT: float = float(os.environ.get("FOA_HTTP_TIMEOUT", "30"))
# Simple in-process response cache TTL (seconds). Keeps us polite to upstream
# APIs for slow-moving metadata like station lists. 0 disables caching.
CACHE_TTL: float = float(os.environ.get("FOA_CACHE_TTL", "120"))

# ---------------------------------------------------------------------------
# Optional API keys (services that require registration)
# ---------------------------------------------------------------------------
# Free key from https://data.fingrid.fi/ -> "My subscriptions".
FINGRID_API_KEY: str | None = os.environ.get("FINGRID_API_KEY") or None
# Optional Digitransit subscription key (higher rate limits) from
# https://portal-api.digitransit.fi/. The API also works key-less for light use.
DIGITRANSIT_API_KEY: str | None = os.environ.get("DIGITRANSIT_API_KEY") or None
# Free National Land Survey key from https://www.maanmittauslaitos.fi/rajapinnat/api-avaimen-ohje
NLS_API_KEY: str | None = os.environ.get("NLS_API_KEY") or None

# ---------------------------------------------------------------------------
# Base URLs (kept here so they are easy to audit / override in tests)
# ---------------------------------------------------------------------------
PORSSISAHKO_BASE = "https://api.porssisahko.net/v1"
SPOT_HINTA_BASE = "https://api.spot-hinta.fi"
FINGRID_BASE = "https://data.fingrid.fi/api"
FMI_WFS_BASE = "https://opendata.fmi.fi/wfs"
DIGITRAFFIC_RAIL_BASE = "https://rata.digitraffic.fi/api/v1"
DIGITRAFFIC_ROAD_BASE = "https://tie.digitraffic.fi/api"
DIGITRAFFIC_MARINE_BASE = "https://meri.digitraffic.fi/api"
PRH_YTJ_BASE = "https://avoindata.prh.fi/opendata-ytj-api/v3"
AVOINDATA_CKAN_BASE = "https://avoindata.suomi.fi/data/api/3/action"  # www.avoindata.fi 301s here
STATFIN_PXWEB_BASE = "https://pxdata.stat.fi/PxWeb/api/v1/en"
# Digitransit (journey planning + geocoding). Both require a subscription key.
DIGITRANSIT_ROUTING_BASE = "https://api.digitransit.fi/routing/v2/finland/gtfs/v1"
DIGITRANSIT_GEOCODING_BASE = "https://api.digitransit.fi/geocoding/v1"
# Civic & culture (key-less).
EDUSKUNTA_BASE = "https://avoindata.eduskunta.fi/api/v1"
FINNA_BASE = "https://api.finna.fi/v1"
# Suomi.fi Finnish Service Catalogue (PTV), open read API.
PTV_BASE = "https://api.palvelutietovaranto.suomi.fi/api/v11"
# Kirjastot.fi — Finnish public library directory & opening hours (key-less).
KIRJASTOT_BASE = "https://api.kirjastot.fi/v4"
# THL Sotkanet — health & welfare statistical indicators (key-less).
SOTKANET_BASE = "https://sotkanet.fi/rest/1.1"
# LinkedEvents — events in Finland (Helsinki region + more), key-less.
LINKEDEVENTS_BASE = "https://api.hel.fi/linkedevents/v1"
# National Land Survey (Maanmittauslaitos) geocoding — needs a free API key.
NLS_GEOCODING_BASE = "https://avoin-paikkatieto.maanmittauslaitos.fi/geocoding/v2/pelias"
