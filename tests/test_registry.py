"""Offline checks that the community registry stays valid and the catalog is current."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_catalog.py"
COMMUNITY_SCRIPT = ROOT / "scripts" / "render_community_table.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("render_catalog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_community_module():
    spec = importlib.util.spec_from_file_location("render_community_table", COMMUNITY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registry_is_valid():
    rc = _load_module()
    data = rc.load_registry()
    assert rc.validate(data) == []


def test_catalog_is_up_to_date():
    rc = _load_module()
    data = rc.load_registry()
    expected = rc.render(data).strip()
    actual = (ROOT / "ecosystem" / "CATALOG.md").read_text(encoding="utf-8").strip()
    assert actual == expected, "Run: python scripts/render_catalog.py"


def test_wilma_entry_present_and_attributed():
    rc = _load_module()
    entries = {e["id"]: e for e in rc.load_registry()["entries"]}
    wilma = entries.get("wilmai")
    assert wilma is not None
    assert wilma["author"] == "aikarjal"
    assert wilma["repo"].startswith("https://github.com/aikarjal/wilmai")


def test_maiklubi_entry_present_and_attributed():
    rc = _load_module()
    entries = {e["id"]: e for e in rc.load_registry()["entries"]}
    maiklubi = entries.get("maiklubi")
    assert maiklubi is not None
    assert maiklubi["author"] == "Janne Mäkelä"
    assert maiklubi["repo"].startswith("https://github.com/jannemakela/maiklubi")


def test_community_entries_have_finnish_descriptions():
    rc = _load_module()
    for entry in rc.load_registry()["entries"]:
        if not entry.get("first_party"):
            assert entry.get("description_fi"), f"{entry['id']} is missing description_fi"


def test_community_table_is_up_to_date():
    ct = _load_community_module()
    entries = ct.load_community_entries()
    expected_rows = ct.render_rows(entries)
    expected_i18n = ct.render_i18n(entries)
    current = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert expected_rows in current, "Run: python scripts/render_community_table.py"
    assert expected_i18n in current, "Run: python scripts/render_community_table.py"
