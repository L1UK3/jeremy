"""Scripted trace loader and O(1) step trajectory pre-computation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "FLAT_TRACE",
    "PHASE_SCHEDULE",
    "TRACE",
    "get_path_action",
    "select_phase",
]

PHASE_SCHEDULE: tuple[tuple[int, int, str], ...] = (
    (0, 24, "opening"),
    (24, 168, "formation"),
    (168, 192, "expansion_1"),
    (192, 432, "productive_scale"),
    (432, 456, "expansion_2"),
    (456, 672, "demand_conversion"),
    (672, 720, "liquidation"),
)


def _load_trace() -> dict[str, list[dict[str, Any]]]:
    candidates = (
        Path(__file__).parent / "trace.json"
        if "__file__" in globals()
        else None,
        Path("src/trajectories/trace.json"),
        Path("trajectories/trace.json"),
        Path("src/trace.json"),
        Path("trace.json"),
    )
    for p in candidates:
        if p and p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {}


TRACE: dict[str, list[dict[str, Any]]] = _load_trace()


def select_phase(step: int) -> tuple[str, int]:
    """Select the active phase name and phase-relative turn offset."""
    for start, end, name in PHASE_SCHEDULE:
        if step < end:
            return name, step - start
    return "liquidation", min(47, max(0, step - 672))


def get_path_action(path_name: str, local_index: int) -> dict[str, Any]:
    """Extract deep-copied canonical action dictionary for given phase and offset."""
    actions = TRACE.get(path_name) or []
    act = (
        actions[local_index]
        if 0 <= local_index < len(actions)
        else {"farmer": ["PASS"], "hands": [], "market": []}
    )
    return {
        "farmer": list(act.get("farmer") or ["PASS"]),
        "hands": [list(c) for c in act.get("hands", [])],
        "market": [list(o) for o in act.get("market", [])],
    }


# Pre-compute immutable 720-step trace lookup table on module initialization
FLAT_TRACE: tuple[dict[str, Any], ...] = tuple(
    get_path_action(*select_phase(s)) for s in range(720)
)
