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

    # Sell produce intelligently across all inventory items
    shed_total = sum(planner.state.shed.values())
    for item, count in list(planner.state.shed.items()):
        if not count or count <= 0 or item in ("seed", "fertilizer_seed"):
            continue

        # Wheat: reserve 2-day buffer for livestock
        if item == "WHEAT" and animals:
            sellable = max(0, count - len(animals) * 2)
        else:
            sellable = count

        if sellable <= 0:
            continue

        cur_price = planner.state.price(item)
        score = planner.market.sell_score(item)
        batch_size = min(10, sellable)

        should_sell = False
        if planner.state.day >= 26:
            should_sell = True
        elif shed_total >= 50:
            should_sell = True
        elif item in ("MILK", "WOOL", "EGG", "FERTILIZER"):
            should_sell = True
        elif item == "MELON":
            # Sell melons in high-price windows or when stock builds up
            if cur_price >= 160 or score >= 200 or sellable >= 15:
                should_sell = True
        elif cur_price >= 80:
            should_sell = True

        if should_sell:
            planner.add(SELL, ActionBuilder.sell(item, batch_size))

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
