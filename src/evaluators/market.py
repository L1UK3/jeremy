from __future__ import annotations

from typing import Any

from board import Board
from controller import AgentController
from economy import Economy
from market import Market
from state import GameState

__all__ = ["evaluate_market"]


def evaluate_market(
    state: GameState,
    board: Board,
    eco: Economy,
    market: Market,
    controller: AgentController,
    crop: str | None,
) -> list[list[Any]]:
    """Evaluate market sell orders, seed purchases, worker hiring, and feed."""
    market_orders: list[list[Any]] = []
    animals = board.animals()

    # Animal Feed Purchasing (Priority 1)
    if animals:
        wheat_stock = state.inventory("WHEAT")
        needed = max(0, len(animals) * 3 - wheat_stock)
        if needed > 0:
            price = max(1, state.price("WHEAT"))
            max_can_buy = min(needed, int(state.money // price))
            if max_can_buy > 0:
                buy_amt = min(10, max_can_buy)
                market_orders.append(["BUY_PRODUCT", "WHEAT", buy_amt])

    # Farmhand Hiring
    max_hires = controller.get_max_hires(state)
    feed_deficit = (
        max(0, len(animals) - state.inventory("WHEAT")) if animals else 0
    )
    budget = (
        state.money - 100
        if (feed_deficit > 0 and state.money > 100)
        else (state.money if feed_deficit == 0 else 0)
    )
    if budget > 0:
        count = eco.affordable_hires(
            max_hires_per_day=max_hires, max_budget=budget
        )
        for _ in range(min(8, count)):
            if len(market_orders) < 10:
                market_orders.append(["HIRE"])

    # Produce Selling
    shed_total = sum(state.shed.values())
    for item, count in state.shed.items():
        if not count or count <= 0 or item in ("seed", "fertilizer_seed"):
            continue

        if item == "WHEAT" and animals:
            sellable = max(0, count - len(animals) * 3)
        else:
            sellable = count

        if sellable <= 0:
            continue

        cur_price = state.price(item)
        score = market.sell_score(item)
        batch_size = min(10, sellable)

        should_sell = False
        if state.day >= 26:
            should_sell = True
        elif shed_total >= 50:
            should_sell = True
        elif item in ("MILK", "WOOL", "EGG", "FERTILIZER"):
            should_sell = True
        elif item == "MELON":
            if cur_price >= 160 or score >= 200 or sellable >= 15:
                should_sell = True
        elif cur_price >= 80:
            should_sell = True

        if should_sell and len(market_orders) < 10:
            market_orders.append(["SELL", item, batch_size])

    # Seed Purchases
    empty_tiles = board.empty_tiles_count
    target = min(12, empty_tiles)
    if crop and eco.should_buy_seed(crop, target) and len(market_orders) < 10:
        qty = target - state.seed_count(crop)
        if qty > 0:
            market_orders.append(["BUY_SEED", crop, qty])

    return market_orders[:10]
