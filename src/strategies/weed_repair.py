"""Weed transaction repair layers for Jeremy V3.

Includes idle-tail cleaning, guarded tile protection, and productive route delays.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    x, y = position
    tx, ty = target
    if tx < x:
        return ["WEST"]
    if tx > x:
        return ["EAST"]
    if ty < y:
        return ["NORTH"]
    if ty > y:
        return ["SOUTH"]
    return ["DIG"]


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

    positions = [state.farmer, *(tuple(h) for h in state.hands)]
    ops: list[list[str]] = [
        list(action.get("farmer") or ["PASS"]),
        *[list(h) for h in (action.get("hands") or [])],
    ]
    ops.extend([["PASS"]] * (len(positions) - len(ops)))
    turns_left = ((step // 24) + 1) * 24 - step
    claimed: set[tuple[int, int]] = set()

    for actor in range(len(positions)):
        current = ops[actor] if ops[actor] else ["PASS"]
        if current[0] != "PASS":
            continue
        inventory = state.worker_inventory(actor)
        if sum(max(0, int(v or 0)) for v in inventory.values()) > 0:
            continue
        pos = positions[actor]
        choices = [target for target in weeds if target not in claimed]
        if not choices:
            break
        target = min(
            choices,
            key=lambda p: (abs(pos[0] - p[0]) + abs(pos[1] - p[1]), p[1], p[0]),
        )
        distance = abs(pos[0] - target[0]) + abs(pos[1] - target[1])
        if distance + 1 > turns_left:
            continue
        claimed.add(target)
        ops[actor] = weed_step(pos, target)

    action["farmer"] = ops[0]
    action["hands"] = ops[1:]
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
