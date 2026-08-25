from agent.heuristics.scores import SCORE_BUY_LAND
from environment.actions import ActionBuilder


def evaluate_expansion(planner) -> None:
    """Evaluate purchasing adjacent land quadrants."""
    if not planner.config.expand_land:
        return

    if not planner.eco.should_expand():
        return

    target = planner.eco.next_quadrant_target()
    if target is None:
        return

    planner.add(SCORE_BUY_LAND, ActionBuilder.buy_land(target[0], target[1]))
