"""Offline checks that the community registry stays valid and the catalog is current."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_catalog.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("render_catalog", SCRIPT)
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
    wilma = entries.get("wilma-bot")
    assert wilma is not None
    assert wilma["author"] == "jookos"
    assert wilma["repo"].startswith("https://github.com/jookos/wilma-bot")
