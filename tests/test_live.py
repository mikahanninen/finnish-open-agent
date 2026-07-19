"""Optional live smoke tests. Run with:  uv run pytest -m live

These hit real Finnish open-data APIs, so they need network access and may be
skipped in offline CI with:  uv run pytest -m 'not live'
"""

from __future__ import annotations

import pytest

from finnish_open_agent.tools import civic, culture, energy, registers, transport, weather
from finnish_open_agent.tools.culture import FinnaSearchInput
from finnish_open_agent.tools.energy import CheapestHoursInput, SpotPricesInput
from finnish_open_agent.tools.registers import CompanySearchInput, StatFinGetTableInput
from finnish_open_agent.tools.transport import WeatherCamsInput
from finnish_open_agent.tools.weather import AirQualityInput, ForecastInput

pytestmark = pytest.mark.live


async def test_spot_prices_live():
    out = await energy.energy_get_spot_prices(SpotPricesInput(hours=3))
    assert "c/kWh" in out and "Error" not in out


async def test_cheapest_hours_live():
    out = await energy.energy_cheapest_hours(CheapestHoursInput(count=2, within_hours=24))
    assert "c/kWh" in out and "Error" not in out


async def test_forecast_live():
    out = await weather.weather_get_forecast(ForecastInput(place="Helsinki", hours=2))
    assert "Helsinki" in out and "Error" not in out


async def test_air_quality_live():
    out = await weather.weather_get_air_quality(AirQualityInput(place="Tampere", hours=2))
    assert "air quality" in out.lower() and "Error" not in out


async def test_weather_cameras_live():
    out = await transport.transport_find_weather_cameras(WeatherCamsInput(query="Kirkkonummi"))
    assert "camera" in out.lower() and "Error" not in out


async def test_company_search_live():
    out = await registers.registers_search_companies(CompanySearchInput(name="Nokia"))
    assert "Business ID" in out and "Error" not in out


async def test_statfin_get_table_live():
    out = await registers.registers_statfin_get_table(
        StatFinGetTableInput(table_path="vaerak/11ra.px")
    )
    assert "value" in out and "Error" not in out


async def test_parliament_composition_live():
    out = await civic.civic_parliament_composition()
    assert "seats" in out.lower() and "Error" not in out


async def test_finna_search_live():
    out = await culture.culture_search(FinnaSearchInput(query="Sibelius", limit=2))
    assert "Finna" in out and "Error" not in out
