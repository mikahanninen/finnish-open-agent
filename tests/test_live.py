"""Optional live smoke tests. Run with:  uv run pytest -m live

These hit real Finnish open-data APIs, so they need network access and may be
skipped in offline CI with:  uv run pytest -m 'not live'
"""

from __future__ import annotations

import pytest

from finnish_open_agent.tools import energy, registers, weather
from finnish_open_agent.tools.energy import SpotPricesInput
from finnish_open_agent.tools.registers import CompanySearchInput
from finnish_open_agent.tools.weather import ForecastInput

pytestmark = pytest.mark.live


async def test_spot_prices_live():
    out = await energy.energy_get_spot_prices(SpotPricesInput(hours=3))
    assert "c/kWh" in out and "Error" not in out


async def test_forecast_live():
    out = await weather.weather_get_forecast(ForecastInput(place="Helsinki", hours=2))
    assert "Helsinki" in out and "Error" not in out


async def test_company_search_live():
    out = await registers.registers_search_companies(CompanySearchInput(name="Nokia"))
    assert "Business ID" in out and "Error" not in out
