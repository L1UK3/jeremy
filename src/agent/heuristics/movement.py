from agent.heuristics.scores import (
    SCORE_MOVE_EMPTY,
    SCORE_MOVE_HARVEST,
    SCORE_MOVE_WATER,
)
from environment.actions import Action, ActionBuilder


def move_to(planner, tile) -> Action:
    """Compute a single Manhattan cardinal step from farmer to target tile."""
    fx, fy = planner.state.farmer
    if fx > tile.x:
        return ActionBuilder.move("WEST")
    if fx < tile.x:
        return ActionBuilder.move("EAST")
    if fy > tile.y:
        return ActionBuilder.move("NORTH")
    if fy < tile.y:
        return ActionBuilder.move("SOUTH")
    return ActionBuilder.pass_turn()


def evaluate_movement(planner) -> None:
    """Evaluate directional movement toward nearest harvestable, thirsty, or empty tile."""
    crop = planner.config.target_crop

    # Move to ripe harvestable crop
    if target := planner.board.nearest_other(planner.board.harvestable(crop)):
        planner.add(SCORE_MOVE_HARVEST, move_to(planner, target))
        return

    # Move to thirsty crop
    if target := planner.board.nearest_other(planner.board.needs_water(crop)):
        planner.add(SCORE_MOVE_WATER, move_to(planner, target))
        return

    # Move to empty soil for planting
    if planner.state.has_seed(crop):
        if target := planner.board.nearest_other(planner.board.empty_tiles()):
            planner.add(SCORE_MOVE_EMPTY, move_to(planner, target))
