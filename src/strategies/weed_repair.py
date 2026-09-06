"""Weed transaction repair layers for Jeremy V3.

Includes idle-tail cleaning, guarded tile protection, and productive route delays.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from environment.board import manhattan_distance, step_toward

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "WEED_BLOCKED_OPS",
    "weed_clear_state_based",
    "weed_repair_productive_route",
    "weed_step",
    "weed_tile_at",
]

WEED_BLOCKED_OPS: frozenset[str] = frozenset(
    {"BUILD_PASTURE", "BUILD_COOP", "PLANT", "PLACE"}
)

_weed_repair_pending: dict[int, list[list[str]]] = {}
_weed_repair_last_step: int = -1
_weed_repair_day: int = -1


def weed_step(position: tuple[int, int], target: tuple[int, int]) -> list[str]:
    """Navigate or dig toward weed target."""
    if position == target:
        return ["DIG"]
    return [step_toward(position[0], position[1], target[0], target[1])]


def weed_tile_at(board: Board, position: tuple[int, int]) -> bool:
    """Check if (x, y) is occupied by weed using Board/Tile models."""
    tile = board.tile(position[0], position[1])
    return tile.is_weed if tile else False


def weed_clear_state_based(
    state: GameState,
    board: Board,
    action: dict[str, Any],
) -> dict[str, Any]:
    """Clear reachable weeds dynamically when units are idle."""
    step = state.step
    if step >= 672:
        return action

    weeds = [tile.pos for tile in board.weeds(only_unlocked=True)]
    if not weeds:
        return action

    farmer_act = list(action.get("farmer") or ["PASS"])
    hands_acts = [list(h) for h in (action.get("hands") or [])]
    turns_left = ((step // 24) + 1) * 24 - step
    claimed: set[tuple[int, int]] = set()

    if farmer_act[0] == "PASS" and sum(state.worker_inventory(0).values()) == 0:
        fx, fy = state.farmer
        choices = [target for target in weeds if target not in claimed]
        if choices:
            target = min(
                choices,
                key=lambda p: (
                    manhattan_distance(fx, fy, p[0], p[1]),
                    p[1],
                    p[0],
                ),
            )
            dist = manhattan_distance(fx, fy, target[0], target[1])
            if dist + 1 <= turns_left:
                claimed.add(target)
                farmer_act = weed_step((fx, fy), target)

    for h_idx, h_act in enumerate(hands_acts):
        if (
            h_idx < len(state.hands)
            and h_act
            and h_act[0] == "PASS"
            and sum(state.worker_inventory(h_idx + 1).values()) == 0
        ):
            hx, hy = state.hands[h_idx]
            choices = [target for target in weeds if target not in claimed]
            if choices:
                target = min(
                    choices,
                    key=lambda p: (
                        manhattan_distance(hx, hy, p[0], p[1]),
                        p[1],
                        p[0],
                    ),
                )
                dist = manhattan_distance(hx, hy, target[0], target[1])
                if dist + 1 <= turns_left:
                    claimed.add(target)
                    hands_acts[h_idx] = weed_step((hx, hy), target)

    action["farmer"] = farmer_act
    action["hands"] = hands_acts
    return action


def weed_repair_productive_route(
    state: GameState,
    board: Board,
    action: dict[str, Any],
) -> dict[str, Any]:
    """Delay planned productive operations blocked by weeds underfoot."""
    global _weed_repair_pending, _weed_repair_last_step, _weed_repair_day
    step = state.step
    day = state.day
    if step == 0 or step <= _weed_repair_last_step or day != _weed_repair_day:
        _weed_repair_pending = {}
    _weed_repair_last_step = step
    _weed_repair_day = day
    if step >= 672:
        return action

    positions = [state.farmer, *(tuple(h) for h in state.hands)]
    ops: list[list[str]] = [
        list(action.get("farmer") or ["PASS"]),
        *[list(h) for h in (action.get("hands") or [])],
    ]
    original_len = len(ops)
    ops.extend([["PASS"]] * max(0, len(positions) - len(ops)))

    for actor, position in enumerate(positions):
        scheduled = ops[actor] if ops[actor] else ["PASS"]
        pending = _weed_repair_pending.get(actor)
        if pending:
            ops[actor] = pending.pop(0)
            if scheduled[0] != "PASS":
                pending.append(scheduled)
            if pending:
                _weed_repair_pending[actor] = pending
            else:
                _weed_repair_pending.pop(actor, None)
            continue

        if scheduled[0] in WEED_BLOCKED_OPS and weed_tile_at(board, position):
            ops[actor] = ["DIG"]
            _weed_repair_pending[actor] = [scheduled]

    keep = max(original_len, len(positions))
    action["farmer"] = ops[0]
    action["hands"] = ops[1:keep]
    return action
