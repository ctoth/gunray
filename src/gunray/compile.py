"""Maher-style compilation is not exercised by the current local suite surface."""

from __future__ import annotations


def compilation_surface() -> str:
    """Return a marker used by internal smoke tests."""

    return "maher_compilation_placeholder"
