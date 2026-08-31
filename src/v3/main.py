"""Jeremy V2 — Phased Action Path Agent."""

import json
from pathlib import Path
from typing import Any

PASS = ["PASS"]
TRACE_FILE = Path(__file__).resolve().parent / "trace.json"
MOVESETS: dict[str, list[dict[str, Any]]] = (
    json.loads(TRACE_FILE.read_text(encoding="utf-8"))
    if TRACE_FILE.is_file()
    else {}
)

PHASE_SCHEDULE: tuple[tuple[int, int, str], ...] = (
    (0, 24, "opening"),
    (24, 168, "formation"),
    (168, 192, "expansion_1"),
    (192, 432, "productive_scale"),
    (432, 456, "expansion_2"),
    (456, 672, "demand_conversion"),
    (672, 720, "liquidation"),
)

ACTIONS: tuple[dict[str, Any], ...] = tuple(
    MOVESETS.get(name, [])[step - start]
    for start, end, name in PHASE_SCHEDULE
    for step in range(start, end)
)


def select_phase(step: int) -> tuple[str, int]:
    for start, end, name in PHASE_SCHEDULE:
        if step < end:
            return name, step - start
    return "liquidation", min(47, max(0, step - 672))


def get_path_action(path_name: str, local_index: int) -> dict[str, Any]:
    actions = MOVESETS.get(path_name) or []
    act = (
        actions[local_index]
        if 0 <= local_index < len(actions)
        else {"farmer": PASS, "hands": [], "market": []}
    )
    return {
        "farmer": list(act.get("farmer") or PASS),
        "hands": [list(c) for c in act.get("hands") or []],
        "market": [list(o) for o in act.get("market") or []],
    }


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    farm = (obs.get("farms") or [{}])[obs.get("player", 0)]
    n_hands = len(farm.get("hands") or ())
    try:
        path_name, local_index = select_phase(obs.get("step", 0))
        act = get_path_action(path_name, local_index)
        hands = [list(c) for c in act.get("hands") or []]
        if len(hands) < n_hands:
            hands.extend([PASS] * (n_hands - len(hands)))
        return {
            "farmer": list(act.get("farmer") or PASS),
            "hands": hands[:n_hands],
            "market": [list(o) for o in act.get("market") or []],
        }
    except Exception:
        return {"farmer": PASS, "hands": [PASS] * n_hands, "market": []}
