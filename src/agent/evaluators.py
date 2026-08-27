from __future__ import annotations

from typing import TYPE_CHECKING

from agent.scores import BUY_LAND, BUY_SEED, HIRE_HAND, SELL
from environment.actions import ActionBuilder

if TYPE_CHECKING:
    from agent.planner import Planner

__all__ = ["evaluate_expansion", "evaluate_market"]


def evaluate_market(planner: Planner) -> None:
    """Evaluate market sell orders, seed purchases, and worker hiring."""
    crop = planner.config.get_crop(planner.eco)

    # Farmhand Hiring
    if planner.eco.should_hire(
        max_hires_per_day=planner.config.max_hires_per_day
    ):
        planner.add(HIRE_HAND, ActionBuilder.hire_hand())

    # Sell produce
    if (
        (item := planner.market.best_item_to_sell())
        and item != "fertilizer"
        and item != "seed"
    ):
        if count := planner.state.inventory(item):
            sell_amount = min(10, count)
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

