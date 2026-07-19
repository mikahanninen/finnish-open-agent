"""Command-line interface for Finnish Open Agent.

One codebase, three delivery modes (the project vision):
  • CLI for humans        — `finnish-open-agent call <tool> key=value ...`
  • JSON output for AI    — add `--json`
  • MCP server for agents — `finnish-open-agent` (no args) or `... serve`

Every registered MCP tool is automatically exposed as a CLI subcommand, so new tools get a
human CLI and machine JSON for free. Run `finnish-open-agent list` to see them all.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
import sys
import typing

from . import tools as tools_pkg


def _first_line(text: str | None) -> str:
    for line in (text or "").strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def _registry() -> dict[str, tuple]:
    """Map tool name -> (async function, Pydantic input model | None)."""
    tools_pkg.load_all()
    reg: dict[str, tuple] = {}
    for mod in tools_pkg.MODULES:
        for name in getattr(mod, "__all__", []):
            fn = getattr(mod, name, None)
            if fn and inspect.iscoroutinefunction(fn):
                # Modules use `from __future__ import annotations`, so resolve the string
                # annotation to the actual Pydantic model class.
                hints = typing.get_type_hints(fn)
                model = hints.get("params")
                reg[name] = (fn, model)
    return reg


async def _run_tool(fn, model, kwargs: dict) -> str:
    if model is None:
        return await fn()
    return await fn(model(**kwargs))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finnish-open-agent",
        description="Finnish open data & public services — MCP server + CLI.",
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="Run the MCP server (stdio by default). This is also the default with no arguments.")
    sub.add_parser("list", help="List all available tools with a one-line summary.")
    cp = sub.add_parser("call", help="Call a tool with key=value arguments.")
    cp.add_argument("tool", help="Tool name (see `list`).")
    cp.add_argument("args", nargs="*", help="Arguments as key=value (e.g. place=Helsinki hours=6).")
    cp.add_argument("--json", action="store_true", help="Request JSON output where the tool supports it.")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point. No arguments (or `serve`) runs the MCP server; otherwise dispatch the CLI."""
    argv = list(sys.argv[1:] if argv is None else argv)

    # Default behaviour (used by MCP clients): run the server over stdio.
    if not argv or argv[0] == "serve":
        from .server import main as serve_main

        serve_main()
        return

    parser = _build_parser()
    ns = parser.parse_args(argv)

    # Keep tool output clean on stdout; send library logs to stderr only.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)

    reg = _registry()

    if ns.cmd == "list":
        for name in sorted(reg):
            print(f"{name}\t{_first_line(reg[name][0].__doc__)}")
        return

    if ns.cmd == "call":
        if ns.tool not in reg:
            print(f"Unknown tool '{ns.tool}'. Run `finnish-open-agent list`.", file=sys.stderr)
            sys.exit(2)
        fn, model = reg[ns.tool]
        kwargs: dict = {}
        for arg in ns.args:
            if "=" not in arg:
                print(f"Bad argument '{arg}' — expected key=value.", file=sys.stderr)
                sys.exit(2)
            key, value = arg.split("=", 1)
            kwargs[key] = value
        if ns.json and model is not None and "response_format" in getattr(model, "model_fields", {}):
            kwargs.setdefault("response_format", "json")
        try:
            print(asyncio.run(_run_tool(fn, model, kwargs)))
        except Exception as exc:  # noqa: BLE001 - surface a clean CLI error
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
