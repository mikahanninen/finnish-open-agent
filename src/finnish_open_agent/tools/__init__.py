"""Tool modules. Importing each module registers its tools on the shared ``mcp``.

Add new domains here (e.g. ``from . import culture``) and they are picked up
automatically by ``server.py`` via :func:`load_all`.
"""

from __future__ import annotations

from . import civic, culture, energy, library, places, registers, transport, weather

MODULES = [energy, weather, transport, registers, civic, culture, places, library]


def load_all() -> None:
    """No-op that guarantees every tool module has been imported (and registered)."""
    # Importing the modules above is sufficient; this function exists so callers
    # can express intent explicitly and so linters don't flag unused imports.
    return None


__all__ = [
    "energy", "weather", "transport", "registers", "civic", "culture", "places", "library",
    "MODULES", "load_all",
]
