"""Offline check that docs/TOOLS.md is regenerated after tool changes."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_tools.py"


def _load():
    spec = importlib.util.spec_from_file_location("render_tools", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tools_md_is_up_to_date():
    rt = _load()
    rendered = rt.render(asyncio.run(rt._collect())).strip()
    actual = (ROOT / "docs" / "TOOLS.md").read_text(encoding="utf-8").strip()
    assert actual == rendered, "Run: python scripts/render_tools.py"
