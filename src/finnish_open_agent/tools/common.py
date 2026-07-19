"""Shared helpers for tool modules: response format enum and formatting utils."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


def as_json(payload: Any) -> str:
    """Serialize a payload to pretty JSON (non-ASCII preserved for Finnish text)."""
    return json.dumps(payload, indent=2, ensure_ascii=False)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a simple GitHub-flavoured Markdown table."""
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)
