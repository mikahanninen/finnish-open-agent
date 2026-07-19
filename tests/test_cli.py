"""Offline checks for the CLI tool registry (no network)."""

from __future__ import annotations

from pydantic import BaseModel

from finnish_open_agent.cli import _registry


def test_registry_exposes_all_tools():
    reg = _registry()
    # A representative tool from every domain should be present.
    for name in [
        "energy_get_spot_prices",
        "weather_get_forecast",
        "transport_get_port_calls",
        "registers_search_companies",
        "civic_parliament_composition",
        "culture_search",
        "places_geocode",
        "library_search",
    ]:
        assert name in reg, name


def test_registry_resolves_pydantic_models():
    reg = _registry()
    fn, model = reg["library_search"]
    assert callable(fn)
    assert model is not None and issubclass(model, BaseModel)


def test_noarg_tool_has_no_model():
    reg = _registry()
    _, model = reg["civic_parliament_composition"]
    assert model is None
