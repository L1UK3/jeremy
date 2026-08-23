from agent.heuristics.scores import SCORE_BUY_LAND
from environment.actions import ActionBuilder


def evaluate_expansion(planner) -> None:
    """Evaluate purchasing adjacent land quadrants."""
    if not planner.config.expand_land:
        return

    target = planner.board.nearest(planner.board.empty_tiles())
    if not planner.eco.should_expand() or target is None:
        return

    planner.add(SCORE_BUY_LAND, ActionBuilder.buy_land(target.x, target.y))
