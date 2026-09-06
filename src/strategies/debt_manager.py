"""Opening liquidity, debt repayment, and split sales scheduling for Jeremy V3."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from environment.state import GameState

__all__ = [
    "CLONE_THRESHOLD",
    "OPENING",
    "SPLIT_CAPS",
    "SPLIT_HORIZON",
    "SPLIT_ITEMS",
    "SPLIT_START",
    "SPLIT_STOP",
    "opening",
    "repay",
    "reset",
    "split",
]

OPENING: str = "feed5"
SPLIT_ITEMS: tuple[str, ...] = ("WHEAT", "FERTILIZER")
SPLIT_CAPS: dict[str, int] = {"WHEAT": 10, "FERTILIZER": 5}
SPLIT_START: int = 120
SPLIT_STOP: int = 715
SPLIT_HORIZON: int = 1
CLONE_THRESHOLD: int = 0
_DEBT: dict[int, dict[int, dict[str, int]]] = {0: {}, 1: {}}
_LAST: dict[int, int] = {0: -1, 1: -1}


def reset(seat: int, step: int) -> tuple[int, dict[int, dict[str, int]]]:
    """Reset debt state on new game."""
    seat_idx = 1 if seat == 1 else 0
    if step == 0 or step <= _LAST[seat_idx]:
        _DEBT[seat_idx] = {}
    _LAST[seat_idx] = step
    return seat_idx, _DEBT[seat_idx]


def opening(action: dict[str, Any], step: int) -> dict[str, Any]:
    """Adjust turn 0/1 opening orders for feed and initial animal purchase."""
    market = [list(order) for order in (action.get("market") or [])]
    if step == 0 and OPENING in {"feed5", "feed6"}:
        wanted = 5 if OPENING == "feed5" else 6
        rest = [
            order
            for order in market
            if not (
                len(order) >= 3
                and order[0] == "BUY_PRODUCT"
                and order[1] == "WHEAT"
            )
        ]
        action["market"] = [["BUY_PRODUCT", "WHEAT", wanted], *rest][:10]
    elif step == 0 and OPENING in {"bridge14", "bridge19"}:
        wanted = 14 if OPENING == "bridge14" else 19
        rest = [
            order
            for order in market
            if not (
                (
                    len(order) >= 3
                    and order[0] == "BUY_PRODUCT"
                    and order[1] == "WHEAT"
                )
                or (
                    len(order) >= 3
                    and order[0] == "BUY_ANIMAL"
                    and order[1] == "COW"
                )
            )
        ]
        action["market"] = [["BUY_PRODUCT", "WHEAT", wanted], *rest][:10]
    elif step == 1 and OPENING in {"bridge14", "bridge19"}:
        surplus = 9 if OPENING == "bridge14" else 14
        action["market"] = [
            ["SELL", "WHEAT", surplus],
            ["BUY_ANIMAL", "COW", 1],
            *market,
        ][:10]
    return action


def repay(action: dict[str, Any], debt: dict[str, int]) -> dict[str, Any]:
    """Reduce planned market orders by currently due debt."""
    if not debt:
        return action
    out: list[list[Any]] = []
    for raw in action.get("market") or []:
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and debt.get(order[1], 0) > 0:
            item = order[1]
            quantity = max(0, int(order[2] or 0))
            reduction = min(quantity, debt[item])
            quantity -= reduction
            debt[item] -= reduction
            if quantity <= 0:
                continue
            order[2] = quantity
        out.append(order)
    action["market"] = out
    return action


def split(
    action: dict[str, Any],
    state: GameState,
    step: int,
    debt_schedule: dict[int, dict[str, int]],
    trace: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    clone_confidence: int,
) -> dict[str, Any]:
    """Split commodity sales into an earlier turn to smooth market supply."""
    future_step = step + SPLIT_HORIZON
    if (
        not SPLIT_ITEMS
        or step < SPLIT_START
        or step >= SPLIT_STOP
        or future_step >= len(trace)
        or (CLONE_THRESHOLD > 0 and clone_confidence < CLONE_THRESHOLD)
    ):
        return action
    future: dict[str, int] = {}
    for order in trace[future_step].get("market") or []:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in SPLIT_ITEMS:
            future[order[1]] = future.get(order[1], 0) + max(
                0, int(order[2] or 0)
            )
    if not future:
        return action
    market = list(action.get("market") or [])
    if len(market) >= 10:
        return action
    committed: dict[str, int] = {}
    for order in market:
        if len(order) >= 3 and order[0] == "SELL":
            committed[order[1]] = committed.get(order[1], 0) + max(
                0, int(order[2] or 0)
            )
    for item in SPLIT_ITEMS:
        if len(market) >= 10:
            break
        planned = future.get(item, 0)
        cap = int(SPLIT_CAPS.get(item, planned) or planned)
        stock = state.inventory(item)
        available = max(0, stock - committed.get(item, 0))
        quantity = min(planned, cap, available)
        if quantity <= 0:
            continue
        market.append(["SELL", item, quantity])
        due = debt_schedule.setdefault(future_step, {})
        due[item] = due.get(item, 0) + quantity
    action["market"] = market
    return action
