from agent.heuristics.scores import SCORE_BUY_SEED, SCORE_HIRE_HAND, SCORE_SELL
from environment.actions import ActionBuilder


def evaluate_market(planner) -> None:
    """Evaluate market sell orders and seed purchases."""
    crop = planner.config.target_crop
    inventory = planner.eco.inventory(crop)

    if planner.eco.should_hire(
        max_hires_per_day=planner.config.max_hires_per_day
    ):
        planner.add(SCORE_HIRE_HAND, ActionBuilder.hire_hand())

    if inventory > 0 and planner.eco.should_sell(
        crop, threshold=planner.config.sell_threshold
    ):
        planner.add(SCORE_SELL, ActionBuilder.sell(crop, inventory))

    if planner.eco.should_buy_seed(
        crop, target_count=planner.config.seed_target
    ):
        amount = planner.config.seed_target - planner.state.seed_count(crop)
        if amount > 0:
            planner.add(SCORE_BUY_SEED, ActionBuilder.buy_seed(crop, amount))
