from agent.heuristics.scores import (
    MOVE_EMPTY,
    MOVE_HARVEST,
    MOVE_WATER,
    MOVE_WEED,
)
from environment.actions import Action, ActionBuilder
from environment.board import step_toward

# Backward compatibility alias
move_step = step_toward


def move_to(planner, tile) -> Action:
    """Compute a single Manhattan cardinal step from farmer to target tile."""
    fx, fy = planner.state.farmer
    step = step_toward(fx, fy, tile.x, tile.y)
    if step != "PASS":
        return ActionBuilder.move(step)
    return ActionBuilder.pass_turn()



def evaluate_movement(planner) -> None:
    """Evaluate directional movement toward nearest harvestable, thirsty, weed, or empty tile."""
    target_crop = getattr(planner, "active_crop", planner.config.target_crop)

    # Move to ripe harvestable crop
    if target := planner.board.nearest_other(planner.board.harvestable(target_crop)):
        planner.add(MOVE_HARVEST, move_to(planner, target))
        return

    # Move to thirsty crop
    if target := planner.board.nearest_other(planner.board.needs_water(target_crop)):
        planner.add(MOVE_WATER, move_to(planner, target))
        return

    # Move to clear weed on unlocked tile
    if target := planner.board.nearest_other(planner.board.weeds(only_unlocked=True)):
        planner.add(MOVE_WEED, move_to(planner, target))
        return

    # Move to empty soil for planting
    if target_crop and planner.state.has_seed(target_crop):
        if target := planner.board.nearest_other(planner.board.empty_tiles(only_unlocked=True)):
            planner.add(MOVE_EMPTY, move_to(planner, target))
