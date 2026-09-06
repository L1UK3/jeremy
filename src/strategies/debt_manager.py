"""Opening liquidity, debt repayment, and split sales scheduling for Jeremy V3."""

from __future__ import annotations

from typing import Any

__all__ = [
    "OPENING",
    "opening",
    "repay",
    "reset",
]

OPENING: str = "feed5"
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
