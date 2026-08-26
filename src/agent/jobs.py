from agent.scheduler import Job
from agent.scores import DIG_WEED, HARVEST_BASE, PLANT_BASE, WATER


def harvest_jobs(planner, crop: str) -> list[Job]:
    """Generate harvest jobs for all ripe plants matching active crop."""
    return [
        Job(
            priority=HARVEST_BASE
            + (tile.yield_units * planner.eco.price(tile.crop)),
            action="HARVEST",
            target=tile.pos,
            item=tile.crop,
        )
        for tile in planner.board.harvestable(crop)
        if tile.is_ripe(planner.state.day)
    ]


def water_jobs(planner, crop: str) -> list[Job]:
    """Generate watering jobs for thirsty crops."""
    return [
        Job(
            priority=WATER,
            action="WATER",
            target=tile.pos,
        )
        for tile in planner.board.needs_water(crop)
    ]


def weed_jobs(planner, crop: str) -> list[Job]:
    """Generate weed clearing jobs on unlocked farm tiles."""
    return [
        Job(
            priority=DIG_WEED,
            action="DIG",
            target=tile.pos,
        )
        for tile in planner.board.weeds(only_unlocked=True)
    ]


def plant_jobs(planner, crop: str) -> list[Job]:
    """Generate planting jobs on empty unlocked tiles if seeds are available."""
    if not (crop and planner.state.has_seed(crop)):
        return []
    roi = planner.eco.crop_roi(crop)
    return [
        Job(
            priority=PLANT_BASE + roi,
            action="PLANT",
            target=tile.pos,
            item=crop,
        )
        for tile in planner.board.empty_tiles(only_unlocked=True)
    ]


def schedule_jobs(planner, target_crop: str | None = None) -> None:
    planner.scheduler.clear()
    crop = target_crop or planner.config.get_crop(planner.eco)
    planner.scheduler.extend_jobs(harvest_jobs(planner, crop))
    planner.scheduler.extend_jobs(water_jobs(planner, crop))
    planner.scheduler.extend_jobs(weed_jobs(planner, crop))
    planner.scheduler.extend_jobs(plant_jobs(planner, crop))
