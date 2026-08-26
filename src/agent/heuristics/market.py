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

    # Sell produce
    if (
        (item := market.best_item_to_sell())
        and item != "fertilizer"
        and item != "seed"
    ):
        if count := planner.state.inventory(item):
            sell_amount = min(10, count)
            planner.add(SELL, ActionBuilder.sell(item, sell_amount))

    # Seed Purchases
    empty_tiles = sum(1 for _ in planner.board.empty_tiles())
    target = min(
        planner.config.seed_target, empty_tiles
    )
    if crop and planner.eco.should_buy_seed(crop, target):
        planner.add(
            BUY_SEED,
            ActionBuilder.buy_seed(
                crop, target - planner.state.seed_count(crop)
            ),
        )
