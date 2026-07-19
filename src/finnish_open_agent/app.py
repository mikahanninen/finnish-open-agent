"""The shared FastMCP application instance.

Tool modules import ``mcp`` from here and register their tools with the
``@mcp.tool`` decorator. ``server.py`` imports the tool modules (which triggers
registration) and then runs the server. Keeping the instance in its own module
avoids circular imports between ``server`` and the ``tools`` package.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

INSTRUCTIONS = """\
Finnish Open Agent exposes Finland's open data and public-service APIs as tools.

Domains covered in this version:
  • Energy     — electricity spot (Nord Pool FI) prices, Fingrid grid data
  • Weather    — FMI forecasts, observations & air quality
  • Transport  — Digitraffic road & rail, Digitransit journey planning
  • Registers  — PRH/YTJ business register, avoindata.fi, Statistics Finland
  • Civic      — Eduskunta (Parliament): members & seat composition
  • Culture    — Finna: libraries, museums & archives search
  • Places     — National Land Survey geocoding
  • Library    — Kirjastot.fi: public libraries & opening hours

Most tools need no API key. Prices are in c/kWh incl. Finnish VAT unless noted.
Times are ISO 8601; Finnish local time is UTC+2 (winter) / UTC+3 (summer).
Prefer response_format='markdown' for reading, 'json' for further processing.
"""

# Server name follows the {service}_mcp convention from MCP best practices.
mcp = FastMCP("finnish_services_mcp", instructions=INSTRUCTIONS)
