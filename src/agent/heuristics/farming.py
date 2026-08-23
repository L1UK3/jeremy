from heuristics.scores import (
    SCORE_DIG_WEED,
    SCORE_FERTILIZER,
    SCORE_HARVEST_BASE,
    SCORE_PLANT_BASE,
    SCORE_WATER,
)

from environment.actions import ActionBuilder


def evaluate_farming(planner) -> None:
    """Evaluate tile-level farming actions: planting, weeding, watering, and harvesting."""
    tile = planner.state.current_tile

    if tile is None:
        crop = planner.config.target_crop
        if planner.state.has_seed(crop):
            roi = planner.eco.crop_roi(crop)
            planner.add(SCORE_PLANT_BASE + roi, ActionBuilder.plant(crop))
        return

    if not isinstance(tile, dict):
        return

    kind = tile.get("kind")

    if kind == "WEED":
        planner.add(SCORE_DIG_WEED, ActionBuilder.dig())
        return

    if kind != "PLANT":
        return

    crop = tile.get("crop")
    if crop == planner.config.target_crop:
        planted_day = tile.get("planted_day")
        age = (
            planner.state.day - planted_day if planted_day is not None else 0
        )
        yield_units = tile.get("yield_units", 0)

        if age >= planner.config.max_yield_day and yield_units > 0:
            value = yield_units * planner.eco.price(planner.config.target_crop)
            planner.add(SCORE_HARVEST_BASE + value, ActionBuilder.harvest())
            return

        if not tile.get("watered_today", False):
            planner.add(SCORE_WATER, ActionBuilder.water())
            return

        if tile.get("fertilized_until_day") < planner.state.day and planner.state.has_fertilizer():
            planner.add(SCORE_FERTILIZER, ActionBuilder.fertilize())
            return
