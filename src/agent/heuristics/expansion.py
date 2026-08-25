from agent.heuristics.scores import BUY_LAND
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

    if len(planner.state.unlocked_quadrants) >= planner.config.max_quadrants:
        return

    planner.add(BUY_LAND, ActionBuilder.buy_land(target[0], target[1]))
