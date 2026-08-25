from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

from agent.heuristics.scores import (
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
    target_crop = getattr(planner, "active_crop", planner.config.target_crop)

    if tile is None:
        if target_crop and planner.state.has_seed(target_crop):
            roi = planner.eco.crop_roi(target_crop)
            planner.add(SCORE_PLANT_BASE + roi, ActionBuilder.plant(target_crop))
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
    planted_day = tile.get("planted_day")
    age = planner.state.day - planted_day if planted_day is not None else 0
    yield_units = tile.get("yield_units", 0)
    max_yield_day = CROPS.get(crop, {}).get("max_yield_day", 10) if crop else 10

    # Harvest mature crops immediately
    if age >= max_yield_day and yield_units > 0:
        value = yield_units * planner.eco.price(crop or target_crop)
        planner.add(SCORE_HARVEST_BASE + value, ActionBuilder.harvest())
        return

    # Water thirsty plants
    if not tile.get("watered_today", False):
        planner.add(SCORE_WATER, ActionBuilder.water())
        return

    # Apply fertilizer if unfertilized and available
    fert_until = tile.get("fertilized_until_day")
    if (fert_until is None or fert_until < planner.state.day) and planner.state.has_fertilizer():
        planner.add(SCORE_FERTILIZER, ActionBuilder.fertilize())
        return
