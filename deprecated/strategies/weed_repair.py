"""Weed transaction repair layers for Jeremy V3.

Includes idle-tail cleaning, guarded tile protection, and productive route delays.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from deprecated.environment.board import Board
    from deprecated.environment.state import GameState

__all__ = [
    "WEED_BLOCKED_OPS",
    "WEED_LAST_PLANNED_USE",
    "weed_repair_productive_route",
    "weed_step",
    "weed_tail_is_free",
    "weed_tile_at",
    "weed_trace_op",
    "weed_use_guarded",
]

WEED_BLOCKED_OPS: frozenset[str] = frozenset(
    {"BUILD_PASTURE", "BUILD_COOP", "PLANT", "PLACE"}
)

WEED_LAST_PLANNED_USE: dict[tuple[int, int], int] = {
    (0, 0): 599,
    (1, 0): 618,
    (2, 0): 621,
    (3, 0): 514,
    (4, 0): 587,
    (5, 0): 574,
    (6, 0): 642,
    (7, 0): 564,
    (8, 0): 569,
    (9, 0): 571,
    (0, 1): 594,
    (1, 1): 589,
    (2, 1): 643,
    (3, 1): 593,
    (4, 1): 586,
    (5, 1): 560,
    (6, 1): 620,
    (7, 1): 563,
    (8, 1): 568,
    (9, 1): 575,
    (0, 2): 573,
    (1, 2): 568,
    (2, 2): 563,
    (3, 2): 560,
    (4, 2): 14,
    (5, 2): 181,
    (6, 2): 566,
    (7, 2): 571,
    (8, 2): 637,
    (9, 2): 574,
    (0, 3): 612,
    (1, 3): 613,
    (2, 3): 608,
    (3, 3): 20,
    (4, 3): 9,
    (5, 3): 176,
    (6, 3): 198,
    (7, 3): 519,
    (8, 3): 610,
    (9, 3): 615,
    (0, 4): 618,
    (1, 4): 632,
    (2, 4): 129,
    (3, 4): 5,
    (4, 4): 4,
    (5, 4): 165,
    (6, 4): 165,
    (7, 4): 204,
    (8, 4): 594,
    (9, 4): 599,
    (0, 5): 617,
    (1, 5): 588,
    (2, 5): 583,
    (3, 5): 586,
    (4, 5): 581,
    (0, 6): 610,
    (1, 6): 613,
    (2, 6): 608,
    (3, 6): 591,
    (4, 6): 630,
    (0, 7): 636,
    (1, 7): 635,
    (2, 7): 634,
    (3, 7): 632,
    (4, 7): 635,
    (0, 8): 254,
    (1, 8): 257,
    (2, 8): 639,
    (3, 8): 637,
    (4, 8): 640,
    (0, 9): 263,
    (1, 9): 260,
    (2, 9): 257,
    (3, 9): 260,
    (4, 9): 259,
}

_weed_repair_pending: dict[int, list[list[str]]] = {}
_weed_repair_last_step: int = -1
_weed_repair_day: int = -1


def weed_trace_op(
    trace: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    step: int,
    actor: int,
) -> list[str]:
    """Fetch expected action for actor from trace."""
    if step < 0 or step >= len(trace):
        return ["PASS"]
    row = trace[step]
    if actor == 0:
        return list(row.get("farmer") or ["PASS"])
    hands = row.get("hands") or []
    return list(hands[actor - 1] if actor - 1 < len(hands) else ["PASS"])


def weed_tail_is_free(
    trace: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    step: int,
    actor: int,
) -> bool:
    """Check if worker's schedule for remainder of the day is entirely PASS."""
    end = min(len(trace), ((step // 24) + 1) * 24)
    for future in range(step, end):
        op = weed_trace_op(trace, future, actor)
        if not isinstance(op, list) or not op or op[0] != "PASS":
            return False
    return True


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


def weed_use_guarded(
    state: GameState,
    board: Board,
    action: dict[str, Any],
    trace: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> dict[str, Any]:
    """Clear weeds only if tile has a planned future use in route schedule."""
    step = state.step
    if step >= 672:
        return action

    weeds = [
        tile.pos
        for tile in board.weeds()
        if WEED_LAST_PLANNED_USE.get(tile.pos, -1) > step
    ]
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
        if current[0] != "PASS" or not weed_tail_is_free(trace, step, actor):
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
