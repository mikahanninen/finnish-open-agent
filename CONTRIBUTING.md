# Contributing

Two kinds of contributions are welcome: improving the **Finnish Open Agent** MCP server /
skill itself, and **listing your own** Finnish skill / MCP / agent in the community catalog.

## Listing your project in the catalog

This repo aims to be a friendly directory of Finnish agentic tooling. We **link to your
project at its source and never copy your code** — you keep ownership, license, stars, and
control. Getting listed takes one small PR.

### Inclusion criteria

- **Finnish relevance** — it helps with a Finnish service, dataset, or public/private system.
- **A public source** — a repo (or package) others can actually look at and use.
- **A clear license** — state it. We record the license exactly as you declare it. Projects
  without any license are "all rights reserved"; we can still *link* to them, but please add a
  license so others know what they may do. (Consider MIT/Apache-2.0 for skills & MCPs.)
- **Honest description** — say what it does and, if it touches personal data or credentials
  (e.g. school, banking, health logins), note that plainly.

Listing is not an endorsement, and we don't vet security — users verify projects themselves.

### How to add an entry

1. Fork and edit [`ecosystem/registry.yaml`](./ecosystem/registry.yaml): append an entry.

   ```yaml
   - id: my-cool-thing            # unique, kebab-case
     name: My Cool Thing
     kinds: [mcp, skill]          # any of: mcp, skill, agent, library
     author: your-handle
     repo: "https://github.com/you/my-cool-thing"
     license: MIT
     language: Python
     domains: [transport]         # energy | weather | transport | registers | education | civic | other
     tags: [hsl, tickets]
     description: >-
       One or two sentences on what it does (English).
     description_fi: >-
       Sama kahdessa lauseessa suomeksi — the site shows this table in both
       languages, so a Finnish description is required for community entries.
   ```

2. Regenerate the catalog and the site's community table, and validate:

   ```bash
   uv run python scripts/render_catalog.py            # writes ecosystem/CATALOG.md
   uv run python scripts/render_community_table.py     # writes docs/index.html's community table
   uv run python scripts/render_catalog.py --check           # CI runs both --check variants
   uv run python scripts/render_community_table.py --check
   ```

3. Open a PR. Please only add/curate your own entry (or fix stale info). We may tidy wording.

Prefer not to self-list? Open an issue with the link and we'll add it.

## Contributing to the MCP server / skill

- Python, managed with `uv`. Set up: `uv venv && uv pip install -e ".[dev]"`.
- Add a service: base URL in `config.py`, a tool module under `src/finnish_open_agent/tools/`
  (Pydantic input + `@mcp.tool`, returning Markdown **or** JSON), register it in
  `tools/__init__.py`, and document the endpoint in the CLI skill.
- Keep it key-less where possible; gate anything needing a key behind an env var with an
  actionable error when it's missing.
- Tests: `uv run python -m pytest -m "not live"` (offline) and `-m live` (hits real APIs).
- Lint: `uv run ruff check src tests scripts`.

## Attribution & data licenses

The code here is MIT. The **data** each tool fetches is not — most Finnish open data is
CC BY 4.0 and requires crediting the originator (Fintraffic/Digitraffic, FMI, PRH, Statistics
Finland, avoindata.fi/DVV, Fingrid). Attribute accordingly in anything you publish.
