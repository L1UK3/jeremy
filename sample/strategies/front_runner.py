"""Front-running commodity gluts ahead of clone rivals for Jeremy V3."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sample.environment.state import GameState

__all__ = [
    "BASE_PRICE",
    "FRONT_RUN_HORIZON",
    "FRONT_RUN_ITEMS",
    "GLUT_WEIGHT",
    "front_run",
]

FRONT_RUN_HORIZON: int = 1
FRONT_RUN_ITEMS: tuple[str, ...] = ("MELON", "STRAWBERRY", "MILK", "WOOL")
BASE_PRICE: dict[str, int] = {
    "MELON": 250,
    "STRAWBERRY": 120,
    "MILK": 160,
    "WOOL": 200,
}
GLUT_WEIGHT: dict[str, float] = {
    "MELON": 3.5,
    "STRAWBERRY": 2.0,
    "MILK": 2.0,
    "WOOL": 3.2,
}


def front_run(
    action: dict[str, Any],
    state: GameState,
    step: int,
    trace: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    clone_confidence: int,
) -> None:
    """Sell one premium line immediately before a clone's expected glut."""
    if clone_confidence < 2 or FRONT_RUN_HORIZON <= 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    already: dict[str, int] = {}
    for order in orders:
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            already[order[1]] = already.get(order[1], 0) + max(
                0, int(order[2] or 0)
            )
    planned: dict[str, list[int]] = {}
    end = min(len(trace), step + FRONT_RUN_HORIZON + 1)
    for future_step in range(step + 1, end):
        distance = future_step - step
        for order in trace[future_step].get("market", []) or []:
            if not (
                isinstance(order, list)
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] in FRONT_RUN_ITEMS
            ):
                continue
            item = order[1]
            quantity = max(0, int(order[2] or 0))
            if item not in planned:
                planned[item] = [distance, quantity]
            else:
                planned[item][1] += quantity

    choices: list[tuple[float, str, int]] = []
    for item, (distance, quantity) in planned.items():
        stock = state.inventory(item)
        available = max(0, stock - already.get(item, 0))
        quantity = min(available, quantity)
        if quantity <= 0:
            continue
        base_p = BASE_PRICE.get(item, 100)
        price = float(state.price(item) or base_p)
        priority = (
            price * quantity * GLUT_WEIGHT.get(item, 1.0)
            + (FRONT_RUN_HORIZON + 1 - distance) * base_p
        )
        choices.append((priority, item, quantity))
    if choices:
        _, item, quantity = max(choices)
        orders.append(["SELL", item, quantity])
        action["market"] = orders[:10]
