#!/usr/bin/env python3
"""Validate ecosystem/registry.yaml and (re)generate ecosystem/CATALOG.md.

The registry is the single source of truth for the community collection. This
script checks that every entry has the required fields, then renders a grouped,
human-readable catalog that links out to each project. We never copy code — the
catalog only links to sources, preserving each author's ownership and license.

Usage:
    python scripts/render_catalog.py            # write CATALOG.md
    python scripts/render_catalog.py --check     # validate + fail if out of date
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: `uv pip install -e '.[dev]'` (or `pip install pyyaml`).")

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "ecosystem" / "registry.yaml"
CATALOG = ROOT / "ecosystem" / "CATALOG.md"

REQUIRED = ["id", "name", "kinds", "author", "license", "description"]
DOMAIN_ORDER = ["energy", "weather", "transport", "registers", "education", "civic", "other"]
DOMAIN_TITLES = {
    "energy": "⚡ Energy",
    "weather": "🌦️ Weather & environment",
    "transport": "🚆 Transport & mobility",
    "registers": "🏢 Registers, data & statistics",
    "education": "🎓 Education",
    "civic": "🏛️ Civic & government",
    "other": "🧩 Other",
}
KIND_BADGE = {"mcp": "MCP", "skill": "Skill", "agent": "Agent", "library": "Library"}


def load_registry() -> dict:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "entries" not in data:
        sys.exit("registry.yaml must be a mapping with an 'entries' list.")
    return data


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(data.get("entries", [])):
        where = entry.get("id", f"#{i}")
        for field in REQUIRED:
            if not entry.get(field):
                errors.append(f"[{where}] missing required field '{field}'")
        if not entry.get("first_party") and not entry.get("repo"):
            errors.append(f"[{where}] external entries must have a 'repo' URL")
        eid = entry.get("id")
        if eid in seen_ids:
            errors.append(f"[{where}] duplicate id '{eid}'")
        seen_ids.add(eid)
        for kind in entry.get("kinds", []):
            if kind not in KIND_BADGE:
                errors.append(f"[{where}] unknown kind '{kind}' (allowed: {', '.join(KIND_BADGE)})")
    return errors


def entry_link(entry: dict, self_repo: str) -> str:
    if entry.get("first_party"):
        path = entry.get("path", "")
        return f"{self_repo}/tree/main/{path}" if path else self_repo
    return entry["repo"]


def render(data: dict) -> str:
    self_repo = (data.get("self_repo") or "").rstrip("/")
    entries = data["entries"]
    lines = [
        "# 🇫🇮 Finnish Agentic Ecosystem — Catalog",
        "",
        "> Auto-generated from [`registry.yaml`](./registry.yaml) by "
        "`scripts/render_catalog.py`. **Do not edit by hand.**",
        "",
        "A curated, link-only index of skills, MCP servers, and agentic tools for Finnish "
        "services. Every project below is owned by its author and used under its own license — "
        "we link, we don't copy. To add yours, see "
        "[CONTRIBUTING.md](../CONTRIBUTING.md).",
        "",
        f"**{len(entries)} entries.** Badges: "
        + " · ".join(f"`{b}`" for b in KIND_BADGE.values())
        + ".",
        "",
    ]

    by_domain: dict[str, list[dict]] = {}
    for e in entries:
        domains = e.get("domains") or ["other"]
        by_domain.setdefault(domains[0], []).append(e)

    ordered = sorted(by_domain, key=lambda d: DOMAIN_ORDER.index(d) if d in DOMAIN_ORDER else 99)
    for domain in ordered:
        lines.append(f"## {DOMAIN_TITLES.get(domain, domain.title())}")
        lines.append("")
        for e in sorted(by_domain[domain], key=lambda x: (not x.get("first_party"), x["name"])):
            badges = " ".join(f"`{KIND_BADGE[k]}`" for k in e.get("kinds", []))
            link = entry_link(e, self_repo)
            fp = " · _first-party_" if e.get("first_party") else ""
            desc = " ".join(e["description"].split())
            tags = ", ".join(e.get("tags", []))
            lines.append(f"### [{e['name']}]({link}) {badges}")
            lines.append("")
            lines.append(desc)
            lines.append("")
            meta = [f"**Author:** {e['author']}{fp}", f"**License:** {e['license']}"]
            if e.get("language"):
                meta.append(f"**Lang:** {e['language']}")
            if e.get("homepage"):
                meta.append(f"**Site:** {e['homepage']}")
            if tags:
                meta.append(f"**Tags:** {tags}")
            lines.append(" · ".join(meta))
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "Listing here is not an endorsement, and licenses are recorded as stated by each "
        "author — verify a project's license and code before using it."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    check = "--check" in sys.argv
    data = load_registry()
    errors = validate(data)
    if errors:
        print("Registry validation failed:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        sys.exit(1)
    rendered = render(data)
    if check:
        current = CATALOG.read_text(encoding="utf-8") if CATALOG.exists() else ""
        if current.strip() != rendered.strip():
            sys.exit("CATALOG.md is out of date. Run: python scripts/render_catalog.py")
        print("Registry valid and CATALOG.md up to date.")
        return
    CATALOG.write_text(rendered + "\n", encoding="utf-8")
    print(f"Wrote {CATALOG.relative_to(ROOT)} ({len(data['entries'])} entries).")


if __name__ == "__main__":
    main()
