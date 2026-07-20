"""Offline unit tests: no network required (parsing & formatting)."""

from __future__ import annotations

from finnish_open_agent.tools.civic import _int, _party_name, _rows_to_dicts
from finnish_open_agent.tools.common import md_table
from finnish_open_agent.tools.culture import _translated
from finnish_open_agent.tools.registers import _current_name, _parse_jsonstat2, _ptv_localized
from finnish_open_agent.tools.weather import _parse_simple_features


def test_int_strips_and_parses():
    assert _int("54        ") == 54
    assert _int(None) == 0
    assert _int("x") == 0


def test_ptv_localized_prefers_finnish_and_type():
    items = [
        {"language": "en", "value": "Early childhood education", "type": "Summary"},
        {"language": "fi", "value": "Varhaiskasvatus", "type": "Summary"},
        {"language": "fi", "value": "Pitkä kuvaus", "type": "Description"},
    ]
    assert _ptv_localized(items, type_filter="Summary") == "Varhaiskasvatus"
    assert _ptv_localized(items, type_filter="Description") == "Pitkä kuvaus"


def test_party_name_maps_known_and_passes_unknown():
    assert _party_name("kok") == "National Coalition Party"
    assert _party_name("VIHR") == "Green League"  # case-insensitive
    assert _party_name("zzz") == "zzz"  # unknown code shown as-is


def test_rows_to_dicts_zips_columns():
    resp = {"columnNames": ["a", "b"], "rowData": [[1, 2], [3, 4]]}
    assert _rows_to_dicts(resp) == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]


def test_translated_extracts_labels():
    items = [{"translated": "Kirja", "value": "0/Book/"}, {"value": "CD"}]
    assert _translated(items) == "Kirja, CD"


def test_library_today_hours():
    from finnish_open_agent.tools.library import _today_hours

    assert _today_hours({"schedules": [{"closed": False, "times": [{"from": "10:00", "to": "20:00"}]}]}) == "10:00–20:00"
    assert _today_hours({"schedules": [{"closed": True}]}) == "closed today"
    assert _today_hours({}) == ""


def test_health_title_prefers_english():
    from finnish_open_agent.tools.health import _title

    assert _title({"title": {"fi": "Väestö", "en": "Population"}}) == "Population"
    assert _title({"title": {"fi": "Väestö"}}) == "Väestö"
    assert _title({}) == ""


def test_events_localized_pick():
    from finnish_open_agent.tools.events import _loc

    assert _loc({"fi": "Konsertti", "en": "Concert"}) == "Konsertti"
    assert _loc({"en": "Concert"}) == "Concert"
    assert _loc("plain") == "plain"
    assert _loc(None) == ""

SAMPLE_FMI = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:BsWfs="http://xml.fmi.fi/schema/wfs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2">
  <wfs:member>
    <BsWfs:BsWfsElement gml:id="e1">
      <BsWfs:Time>2026-07-19T21:00:00Z</BsWfs:Time>
      <BsWfs:ParameterName>Temperature</BsWfs:ParameterName>
      <BsWfs:ParameterValue>16.7</BsWfs:ParameterValue>
    </BsWfs:BsWfsElement>
  </wfs:member>
  <wfs:member>
    <BsWfs:BsWfsElement gml:id="e2">
      <BsWfs:Time>2026-07-19T21:00:00Z</BsWfs:Time>
      <BsWfs:ParameterName>WindSpeedMS</BsWfs:ParameterName>
      <BsWfs:ParameterValue>3.85</BsWfs:ParameterValue>
    </BsWfs:BsWfsElement>
  </wfs:member>
  <wfs:member>
    <BsWfs:BsWfsElement gml:id="e3">
      <BsWfs:Time>2026-07-19T22:00:00Z</BsWfs:Time>
      <BsWfs:ParameterName>Temperature</BsWfs:ParameterName>
      <BsWfs:ParameterValue>NaN</BsWfs:ParameterValue>
    </BsWfs:BsWfsElement>
  </wfs:member>
</wfs:FeatureCollection>"""


def test_parse_simple_features_pivots_by_time():
    rows = _parse_simple_features(SAMPLE_FMI)
    assert len(rows) == 2  # two distinct timestamps
    first = rows[0]
    assert first["time"] == "2026-07-19T21:00:00Z"
    assert first["Temperature"] == 16.7
    assert first["WindSpeedMS"] == 3.85


def test_parse_simple_features_handles_nan():
    rows = _parse_simple_features(SAMPLE_FMI)
    second = rows[1]
    assert second["Temperature"] is None  # NaN -> None


def test_current_name_prefers_active_primary():
    company = {
        "names": [
            {"name": "Old Name Oy", "type": "1", "endDate": "2020-01-01"},
            {"name": "New Name Oy", "type": "1"},  # active (no endDate)
            {"name": "Aputoiminimi", "type": "3"},
        ]
    }
    assert _current_name(company) == "New Name Oy"


def test_parse_jsonstat2_flattens_row_major():
    # 2 areas x 2 years, value array row-major over [Area, Year].
    res = {
        "label": "Demo table",
        "id": ["Area", "Year"],
        "size": [2, 2],
        "dimension": {
            "Area": {"label": "Area", "category": {
                "index": {"FI": 0, "SE": 1}, "label": {"FI": "Finland", "SE": "Sweden"}}},
            "Year": {"label": "Year", "category": {
                "index": {"2024": 0, "2025": 1}, "label": {"2024": "2024", "2025": "2025"}}},
        },
        "value": [10, 11, 20, 21],
    }
    title, headers, rows = _parse_jsonstat2(res, max_cells=50)
    assert title == "Demo table"
    assert headers == ["Area", "Year", "value"]
    assert rows[0] == ["Finland", "2024", "10"]
    assert rows[1] == ["Finland", "2025", "11"]
    assert rows[2] == ["Sweden", "2024", "20"]
    assert rows[3] == ["Sweden", "2025", "21"]


def test_parse_jsonstat2_respects_max_cells():
    res = {
        "label": "t", "id": ["X"], "size": [3],
        "dimension": {"X": {"label": "X", "category": {
            "index": {"a": 0, "b": 1, "c": 2}, "label": {"a": "a", "b": "b", "c": "c"}}}},
        "value": [1, 2, 3],
    }
    _, _, rows = _parse_jsonstat2(res, max_cells=2)
    assert len(rows) == 2


def test_md_table_shape():
    table = md_table(["A", "B"], [["1", "2"], ["3", "4"]])
    lines = table.splitlines()
    assert lines[0] == "| A | B |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| 1 | 2 |"
