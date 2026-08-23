from agent.heuristics.scores import SCORE_BUY_SEED, SCORE_SELL
from environment.actions import ActionBuilder


def evaluate_market(planner) -> None:
    """Evaluate market sell orders and seed purchases."""
    crop = planner.config.target_crop
    inventory = planner.eco.inventory(crop)

    if inventory > 0 and planner.eco.should_sell(
        crop, threshold=planner.config.sell_threshold
    ):
        planner.add(SCORE_SELL, ActionBuilder.sell(crop, inventory))

    if planner.eco.should_buy_seed(crop, target_count=planner.config.seed_target):
        amount = planner.config.seed_target - planner.state.seed_count(crop)
        if amount > 0:
            planner.add(SCORE_BUY_SEED, ActionBuilder.buy_seed(crop, amount))
