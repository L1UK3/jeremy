from __future__ import annotations

from typing import TYPE_CHECKING

from agent.scores import BUY_FEED, BUY_LAND, BUY_SEED, HIRE_HAND, SELL
from environment.actions import Action, ActionBuilder

if TYPE_CHECKING:
    from agent.planner import Planner

__all__ = ["evaluate_expansion", "evaluate_market"]


def evaluate_market(planner: Planner) -> None:
    """Evaluate market sell orders, seed purchases, worker hiring, and feed."""
    crop = planner.config.get_crop(planner.eco)
    animals = planner.board.animals()

    # Animal Feed Purchasing
    if animals:
        wheat_stock = planner.state.inventory("WHEAT")
        needed = max(0, len(animals) * 2 - wheat_stock)
        if needed > 0:
            price = max(1, planner.state.price("WHEAT"))
            max_can_buy = min(needed, int(planner.state.money // price))
            if max_can_buy > 0:
                buy_amt = min(10, max_can_buy)
                planner.add(
                    BUY_FEED, ActionBuilder.buy_product("WHEAT", buy_amt)
                )

    # Farmhand Hiring (dynamically scaled, morning batching)
    max_hires = planner.config.get_max_hires(planner.state)
    feed_deficit = (
        max(0, len(animals) - planner.state.inventory("WHEAT"))
        if animals
        else 0
    )
    budget = (
        planner.state.money - 100
        if (feed_deficit > 0 and planner.state.money > 100)
        else (planner.state.money if feed_deficit == 0 else 0)
    )
    if budget > 0:
        count = planner.eco.affordable_hires(
            max_hires_per_day=max_hires, max_budget=budget
        )
        if count > 0:
            hire_act = Action(score=HIRE_HAND)
            for _ in range(min(8, count)):
                hire_act.market.append(["HIRE"])
            planner.add(HIRE_HAND, hire_act)

    # Sell produce
    if (
        (item := planner.market.best_item_to_sell())
        and item != "fertilizer"
        and item != "seed"
    ):
        if count := planner.state.inventory(item):
            reserved = len(animals) * 2 if (animals and item == "WHEAT") else 0
            sell_amount = min(10, count - reserved)
            if sell_amount > 0:
                planner.add(SELL, ActionBuilder.sell(item, sell_amount))

    # Seed Purchases
    empty_tiles = planner.board.empty_tiles_count
    target = min(planner.config.seed_target, empty_tiles)
    if crop and planner.eco.should_buy_seed(crop, target):
        planner.add(
            BUY_SEED,
            ActionBuilder.buy_seed(
                crop, target - planner.state.seed_count(crop)
            ),
        )


def evaluate_expansion(planner: Planner) -> None:
    """Evaluate purchasing adjacent land quadrants."""
    if not planner.config.expand_land or planner.state.day < 13:
        return

    if (
        len(planner.state.unlocked_quadrants_set)
        >= planner.config.max_quadrants
    ):
        return

    if not planner.eco.should_expand():
        return

    if target := planner.eco.next_quadrant_target():
        planner.add(BUY_LAND, ActionBuilder.buy_land(target[0], target[1]))
