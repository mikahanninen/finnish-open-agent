#!/usr/bin/env python3
"""Generate docs/TOOLS.md from the live MCP tool list (so it can never go stale).

Introspects the registered FastMCP tools and renders a grouped Markdown reference:
tool name, one-line summary, and input parameters. Run in CI with --check to fail if
docs/TOOLS.md is out of date.

Usage:
    python scripts/render_tools.py            # write docs/TOOLS.md
    python scripts/render_tools.py --check     # fail if out of date
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finnish_open_agent.app import mcp  # noqa: E402
from finnish_open_agent.tools import load_all  # noqa: E402

OUT = ROOT / "docs" / "TOOLS.md"

DOMAIN_TITLES = {
    "energy": "⚡ Energy",
    "weather": "🌦️ Weather",
    "transport": "🚆 Transport",
    "registers": "🏢 Registers & data",
    "civic": "🏛️ Civic (Parliament)",
    "culture": "🎭 Culture",
    "places": "🗺️ Places",
}


def _first_line(text: str | None) -> str:
    for line in (text or "").strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


async def _collect() -> list[dict]:
    load_all()
    tools = await mcp.list_tools()
    rows = []
    for t in tools:
        schema = t.inputSchema or {}
        defs = schema.get("$defs", {})

        def resolve(info: dict) -> dict:
            ref = info.get("$ref")
            if ref and ref.startswith("#/$defs/"):
                return defs.get(ref.split("/")[-1], {})
            return info

        params = []
        # FastMCP wraps a single Pydantic model under one property (often via $ref); unwrap it.
        for pname, pinfo in schema.get("properties", {}).items():
            model = resolve(pinfo)
            nested = model.get("properties")
            if nested:
                nreq = set(model.get("required", []))
                for np, ninfo in nested.items():
                    params.append((np, np in nreq, ninfo.get("description", "")))
            else:
                params.append((pname, pname in set(schema.get("required", [])), pinfo.get("description", "")))
        rows.append({"name": t.name, "summary": _first_line(t.description), "params": params})
    return rows


def render(rows: list[dict]) -> str:
    out = [
        "# 🇫🇮 Finnish Open Agent — MCP tool reference",
        "",
        "> Auto-generated from the live MCP server by `scripts/render_tools.py`. "
        "**Do not edit by hand.**",
        "",
        f"**{len(rows)} tools.** All are read-only. See [`PLAN.md`](../PLAN.md) for architecture.",
        "",
    ]
    by_domain: dict[str, list[dict]] = {}
    for r in rows:
        domain = r["name"].split("_", 1)[0]
        by_domain.setdefault(domain, []).append(r)
    for domain in [d for d in DOMAIN_TITLES if d in by_domain] + [
        d for d in by_domain if d not in DOMAIN_TITLES
    ]:
        out.append(f"## {DOMAIN_TITLES.get(domain, domain.title())}")
        out.append("")
        for r in sorted(by_domain[domain], key=lambda x: x["name"]):
            out.append(f"### `{r['name']}`")
            out.append("")
            out.append(r["summary"])
            out.append("")
            if r["params"]:
                out.append("| Parameter | Required | Description |")
                out.append("| --- | --- | --- |")
                for pname, req, desc in r["params"]:
                    out.append(f"| `{pname}` | {'yes' if req else 'no'} | {' '.join((desc or '').split())} |")
                out.append("")
    return "\n".join(out)


def main() -> None:
    rows = asyncio.run(_collect())
    rendered = render(rows)
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current.strip() != rendered.strip():
            sys.exit("docs/TOOLS.md is out of date. Run: python scripts/render_tools.py")
        print("docs/TOOLS.md up to date.")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(rendered + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(rows)} tools).")


if __name__ == "__main__":
    main()
