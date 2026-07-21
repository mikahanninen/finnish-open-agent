# AGENTS.md — orientation for AI agents

This file helps an AI agent (or a new contributor) navigate this repository quickly. It is
hand-maintained but short; the detailed, always-current references are auto-generated.

## What this repo is

**Finnish Open Agent** — an MCP server (`finnish_services_mcp`) plus CLI skills that expose
Finland's open data and public-service APIs as agent tools, and a curated, link-only registry
of other Finnish skills/MCPs. Python, managed with `uv`. Most APIs need no key.

## Where to look (in priority order)

| File | What it gives you |
| --- | --- |
| [`docs/TOOLS.md`](./docs/TOOLS.md) | **Auto-generated** reference of every MCP tool + parameters. Start here to see capabilities. |
| [`README.md`](./README.md) | Human overview, install, configuration, domain table. |
| [`PLAN.md`](./PLAN.md) | Architecture, the full Finnish open-data landscape, and the roadmap. |
| [`ecosystem/CATALOG.md`](./ecosystem/CATALOG.md) | **Auto-generated** catalog of community Finnish skills/MCPs (from `ecosystem/registry.yaml`). |
| [`skills/`](./skills) | Per-domain CLI/curl skills (energy, weather, transport, registers, civic, culture, places, library, health, events, plus an open-data umbrella). |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to add a tool or list a project. |

## Code map

```
src/finnish_open_agent/
  cli.py            CLI entry point: `list`, `call <tool> k=v --json`, default = serve
  app.py            FastMCP instance + server instructions
  server.py         MCP server runner (stdio default; FOA_TRANSPORT=http for remote)
  config.py         base URLs + env-driven settings & API keys
  _http.py          shared async client, TTL cache, error formatting
  tools/            one module per domain; each @mcp.tool lives here
    energy · weather · transport · registers · civic · culture · places · library
scripts/
  render_tools.py           regenerates docs/TOOLS.md  (CI runs --check)
  render_catalog.py         regenerates ecosystem/CATALOG.md  (CI runs --check)
  render_community_table.py regenerates the community table in docs/index.html  (CI runs --check)
tests/              offline (test_parsing/registry/docs/cli) + live (test_live, -m live)
```

## Three delivery modes (one codebase)

The `cli.py` registry introspects every `@mcp.tool` so each tool is usable as:
CLI (`finnish-open-agent call <tool> k=v`), JSON (`--json`), and MCP (`serve`). New tools get
all three automatically — no per-tool CLI wiring.

## Run it

```bash
uv venv && uv pip install -e ".[dev]"
uv run finnish-open-agent list          # list tools (CLI)
uv run finnish-open-agent call energy_get_price_now   # call one
uv run finnish-open-agent               # stdio MCP server (default)
uv run python -m pytest -m "not live"   # offline tests
uv run ruff check src tests scripts
```

## Conventions (follow these when editing)

- Tools are named `{domain}_{action}[_{resource}]`, are read-only, and return **Markdown or
  JSON** (`response_format`). Inputs are Pydantic models with described `Field`s.
- All HTTP goes through `_http.request_json` / `request_text` (adds the `Digitraffic-User`
  header, caching, and uniform `"Error: ..."` messages). Never call `httpx` directly in a tool.
- Key-less by default; anything needing a key checks an env var and returns an actionable error.
- After changing tools or the registry, regenerate docs: `python scripts/render_tools.py` and
  `python scripts/render_catalog.py` (CI fails if these are stale).
- Data has its own licenses (mostly CC BY 4.0) — attribute originators; see `CONTRIBUTING.md`.
