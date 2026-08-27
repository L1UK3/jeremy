from __future__ import annotations

from typing import TYPE_CHECKING

from agent.scheduler import Job
from agent.scores import (
    CARE,
    COLLECT_FERTILIZER,
    DIG_WEED,
    FEED,
    FEED_URGENT,
    HARVEST_BASE,
    PLANT_BASE,
    WATER,
)

if TYPE_CHECKING:
    from agent.planner import Planner

__all__ = [
    "care_jobs",
    "collect_fertilizer_jobs",
    "feed_jobs",
    "harvest_jobs",
    "plant_jobs",
    "schedule_jobs",
    "water_jobs",
    "weed_jobs",
]

ANIMAL_PRODUCT: dict[str, str] = {
    "COW": "MILK",
    "SHEEP": "WOOL",
    "GOOSE": "EGG",
}


def harvest_jobs(planner: Planner) -> list[Job]:
    """Generate harvest jobs for all ripe plants and productive animals."""
    prices = planner.state.prices
    jobs: list[Job] = []
    for tile in planner.board.harvestable():
        if tile.is_animal and tile.animal:
            prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
            jobs.append(
                Job(
                    priority=HARVEST_BASE
                    + (tile.yield_units * prices.get(prod, 0)),
                    action="HARVEST",
                    target=tile.pos,
                    item=prod,
                )
            )
        elif tile.crop:
            jobs.append(
                Job(
                    priority=HARVEST_BASE
                    + (tile.yield_units * prices.get(tile.crop, 0)),
                    action="HARVEST",
                    target=tile.pos,
                    item=tile.crop,
                )
            )
    return jobs


def feed_jobs(planner: Planner) -> list[Job]:
    """Generate feeding jobs for unfed animals if wheat is available in shed."""
    wheat_count = planner.state.inventory("WHEAT")
    if wheat_count <= 0:
        return []

    jobs: list[Job] = []
    for tile in planner.board.needs_feed():
        priority = FEED_URGENT if tile.consecutive_unfed >= 1 else FEED
        jobs.append(
            Job(
                priority=priority,
                action="FEED",
                target=tile.pos,
                item=tile.animal,
            )
        )
    return jobs[:wheat_count]


def care_jobs(planner: Planner) -> list[Job]:
    """Generate care/petting jobs for animals that have not been cared for today."""
    return [
        Job(
            priority=CARE,
            action="CARE",
            target=tile.pos,
            item=tile.animal,
        )
        for tile in planner.board.needs_care()
    ]


def collect_fertilizer_jobs(planner: Planner) -> list[Job]:
    """Generate fertilizer collection jobs for animal tiles with ready fertilizer."""
    return [
        Job(
            priority=COLLECT_FERTILIZER,
            action="COLLECT_FERTILIZER",
            target=tile.pos,
            item="FERTILIZER",
        )
        for tile in planner.board.has_fertilizer_tiles()
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
