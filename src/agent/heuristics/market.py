from agent.heuristics.scores import BUY_SEED, HIRE_HAND, SELL
from environment.actions import ActionBuilder


def evaluate_market(planner) -> None:
    """Evaluate market sell orders, seed purchases, and worker hiring."""
    crop = planner.config.get_crop(planner.eco)
    market = planner.market

    # Farmhand Hiring
    if planner.eco.should_hire(
        max_hires_per_day=planner.config.max_hires_per_day
    ):
        planner.add(HIRE_HAND, ActionBuilder.hire_hand())

    # Always sell available produce in inventory (up to 10 units)
    if (
        (item := market.best_item_to_sell())
        and item != "fertilizer"
        and item != "seed"
    ):
        if count := planner.state.inventory(item):
            sell_amount = min(10, count)
            planner.add(SELL, ActionBuilder.sell(item, sell_amount))

    # Seed Purchases
    if planner.eco.should_buy_seed(
        crop, target_count=planner.config.seed_target
    ):
        amount = planner.config.seed_target - planner.state.seed_count(crop)
        if amount > 0:
            planner.add(BUY_SEED, ActionBuilder.buy_seed(crop, amount))
