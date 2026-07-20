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


async def test_vessels_live():
    from finnish_open_agent.tools.transport import VesselsInput

    out = await transport.transport_get_vessels(
        VesselsInput(min_lat=59.7, max_lat=60.4, min_lon=24.0, max_lon=26.0, limit=3)
    )
    assert ("MMSI" in out or "vessel" in out.lower()) and "Error" not in out


async def test_list_votes_live():
    from finnish_open_agent.tools.civic import VotesListInput

    out = await civic.civic_list_votes(VotesListInput(year=2025, limit=3))
    assert "Vote ID" in out and "Error" not in out


async def test_vote_breakdown_live():
    from finnish_open_agent.tools.civic import VoteBreakdownInput

    out = await civic.civic_get_vote_breakdown(VoteBreakdownInput(vote_id=55554))
    assert "Yes" in out and "Error" not in out


async def test_sea_level_live():
    from finnish_open_agent.tools.weather import SeaInput

    out = await weather.weather_get_sea(SeaInput(place="Helsinki", kind="sealevel", hours=2))
    assert "sealevel" in out.lower() and "Error" not in out


async def test_port_calls_live():
    from finnish_open_agent.tools.transport import PortCallsInput

    out = await transport.transport_get_port_calls(PortCallsInput(port="FIHEL", limit=3))
    assert ("Port" in out or "port" in out.lower()) and "Error" not in out


async def test_library_search_live():
    from finnish_open_agent.tools import library
    from finnish_open_agent.tools.library import LibrarySearchInput

    out = await library.library_search(LibrarySearchInput(query="Oodi", limit=2))
    assert "Oodi" in out and "Error" not in out


async def test_road_maintenance_live():
    from finnish_open_agent.tools.transport import RoadMaintenanceInput

    out = await transport.transport_get_road_maintenance(RoadMaintenanceInput(limit=3))
    assert "maintenance" in out.lower() and "Error" not in out


async def test_get_open_dataset_live():
    from finnish_open_agent.tools.registers import DatasetGetInput

    out = await registers.registers_get_open_dataset(
        DatasetGetInput(name="paakaupunkiseudun-ilmanlaatuindeksit")
    )
    assert "Error" not in out and ("Resource" in out or "resource" in out.lower())


async def test_radiation_live():
    out = await weather.weather_get_radiation()
    assert "radiation" in out.lower() and "Error" not in out


async def test_solar_live():
    from finnish_open_agent.tools.weather import SolarInput

    out = await weather.weather_get_solar(SolarInput(place="Helsinki", hours=2))
    assert "solar" in out.lower() and "Error" not in out


async def test_lightning_live():
    out = await weather.weather_get_lightning()
    assert "Lightning" in out and "Error" not in out


async def test_finna_record_live():
    from finnish_open_agent.tools.culture import RecordInput

    out = await culture.culture_get_record(RecordInput(record_id="eepos.136605"))
    assert "finna.fi/Record" in out and "Error" not in out


async def test_sea_forecast_live():
    from finnish_open_agent.tools.weather import SeaForecastInput

    out = await weather.weather_get_sea_forecast(SeaForecastInput(place="Helsinki", hours=3))
    assert "sea-level forecast" in out.lower() and "Error" not in out


async def test_health_indicator_live():
    from finnish_open_agent.tools import health
    from finnish_open_agent.tools.health import IndicatorGetInput

    out = await health.health_get_indicator(IndicatorGetInput(indicator_id=127, year=2022))
    assert "Whole country" in out and "Error" not in out


async def test_events_search_live():
    from finnish_open_agent.tools import events
    from finnish_open_agent.tools.events import EventSearchInput

    out = await events.events_search(EventSearchInput(query="museum", limit=3))
    assert "Error" not in out
