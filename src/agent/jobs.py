from __future__ import annotations

from typing import TYPE_CHECKING

from agent.scheduler import Job
from agent.scores import DIG_WEED, HARVEST_BASE, PLANT_BASE, WATER

if TYPE_CHECKING:
    from agent.planner import Planner

__all__ = [
    "harvest_jobs",
    "plant_jobs",
    "schedule_jobs",
    "water_jobs",
    "weed_jobs",
]


def harvest_jobs(planner: Planner) -> list[Job]:
    """Generate harvest jobs for all ripe plants matching active crop."""
    prices = planner.state.prices
    return [
        Job(
            priority=HARVEST_BASE
            + (tile.yield_units * prices.get(tile.crop, 0)),
            action="HARVEST",
            target=tile.pos,
            item=tile.crop,
        )
        for tile in planner.board.harvestable()
    ]


def water_jobs(planner: Planner) -> list[Job]:
    """Generate watering jobs for thirsty crops."""
    return [
        Job(
            priority=WATER,
            action="WATER",
            target=tile.pos,
        )
        for tile in planner.board.needs_water()
    ]


def weed_jobs(planner: Planner) -> list[Job]:
    """Generate weed clearing jobs on unlocked farm tiles."""
    return [
        Job(
            priority=DIG_WEED,
            action="DIG",
            target=tile.pos,
        )
        for tile in planner.board.weeds(only_unlocked=True)
    ]


def plant_jobs(planner: Planner, crop: str) -> list[Job]:
    """Generate planting jobs on empty unlocked tiles if seeds are available."""
    if not (crop and planner.state.has_seed(crop)):
        return []
    priority = PLANT_BASE + planner.eco.crop_roi(crop)
    return [
        Job(
            priority=priority,
            action="PLANT",
            target=tile.pos,
            item=crop,
        )
        for tile in planner.board.empty_tiles(only_unlocked=True)
    ]


def schedule_jobs(planner: Planner, target_crop: str | None = None) -> None:
    planner.scheduler.clear()
    crop = target_crop or planner.config.get_crop(planner.eco)
    planner.scheduler.extend_jobs(harvest_jobs(planner))
    planner.scheduler.extend_jobs(water_jobs(planner))
    planner.scheduler.extend_jobs(weed_jobs(planner))
    planner.scheduler.extend_jobs(plant_jobs(planner, crop))

