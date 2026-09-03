from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from economics.economy import best_crop, crop_roi
from environment.board import step_toward

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "CARE",
    "COLLECT_FERTILIZER",
    "DIG_WEED",
    "FEED",
    "FEED_URGENT",
    "FERTILIZE",
    "HARVEST_BASE",
    "HARVEST_PREMIUM",
    "PLANT_BASE",
    "WATER",
    "WATER_URGENT",
    "Job",
    "_harvest_actions",
    "_plant_task",
    "assign_jobs",
    "default_utility_scorer",
    "generate_jobs",
    "job_to_action",
    "schedule_tasks",
]

# priority scores
FEED_URGENT: float = 350.0
WATER_URGENT: float = 300.0
HARVEST_PREMIUM: float = 250.0
FEED: float = 200.0
CARE: float = 180.0
HARVEST_BASE: float = 150.0
DIG_WEED: float = 140.0
WATER: float = 120.0
PLANT_BASE: float = 75.0
FERTILIZE: float = 70.0
COLLECT_FERTILIZER: float = 65.0

ANIMAL_PRODUCT: dict[str, str] = {
    "COW": "MILK",
    "SHEEP": "WOOL",
    "GOOSE": "EGG",
}


class Job(NamedTuple):
    """Lightweight immutable task specification for multi-agent scheduling."""

    priority: float
    action: str
    target: tuple[int, int]
    item: str | None = None


def _plant_task(priority: float, pos: tuple[int, int], crop: str) -> Job:
    """Generate a planting job specification."""
    return Job(priority=priority, action="PLANT", target=pos, item=crop)


def _harvest_actions(watered_today: bool = True, day: int = 0) -> list[str]:
    """Determine immediate harvest or maintenance action for a crop tile."""
    return ["WATER"] if not watered_today and day < 29 else ["HARVEST"]


def default_utility_scorer(
    job: Job, x: int, y: int, dist_penalty: float = 2.0
) -> float:
    """Distance-discounted utility from an actor position (x, y)."""
    return job.priority - (
        dist_penalty * (abs(x - job.target[0]) + abs(y - job.target[1]))
    )


def job_to_action(
    job: Job,
    x: int,
    y: int,
    state: GameState | None = None,
    board: Board | None = None,
) -> list[str]:
    """Convert a job into an immediate tile action or movement step."""
    tx, ty = job.target
    if (x, y) == (tx, ty):
        act = job.action
        if act == "PLANT" and job.item:
            return ["PLANT", job.item]
        if act == "HARVEST":
            tile = board.tile(x, y) if board else None
            if tile and (
                tile.is_animal or (tile.crop and tile.yield_units >= 4)
            ):
                return ["HARVEST"]
            watered = tile.watered if tile else True
            day = state.day if state else 0
            return _harvest_actions(watered_today=watered, day=day)
        return [act]
    return [step_toward(x, y, tx, ty)]


def generate_jobs(
    state: GameState,
    board: Board,
    target_crop: str | None = None,
    crop_weights: tuple[float, ...] | list[float] | None = None,
) -> list[Job]:
    """Streamlined single-pass job generation directly from board spatial indexes."""
    jobs: list[Job] = []
    prices = state.prices

    for tile in board.harvestable():
        if tile.is_animal and tile.animal:
            prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
            val = HARVEST_PREMIUM + (tile.yield_units * prices.get(prod, 0))
            jobs.append(Job(val, "HARVEST", tile.pos, item=prod))
        elif tile.crop:
            base = (
                HARVEST_PREMIUM
                if tile.crop in ("MELON", "CARROT")
                else HARVEST_BASE
            )
            val = base + (tile.yield_units * prices.get(tile.crop, 0))
            jobs.append(Job(val, "HARVEST", tile.pos, item=tile.crop))

    for tile in board.needs_water():
        prio = WATER_URGENT if tile.consecutive_unwatered >= 1 else WATER
        jobs.append(Job(prio, "WATER", tile.pos))

    for tile in board.weeds(only_unlocked=True):
        jobs.append(Job(DIG_WEED, "DIG", tile.pos))

    wheat_stock = state.inventory("WHEAT")
    if wheat_stock > 0:
        for tile in board.needs_feed()[:wheat_stock]:
            if not tile.fed_today:
                prio = FEED_URGENT if tile.consecutive_unfed >= 1 else FEED
                jobs.append(Job(prio, "FEED", tile.pos, item=tile.animal))

    for tile in board.needs_care():
        if not tile.cared_today:
            jobs.append(Job(CARE, "CARE", tile.pos, item=tile.animal))

    fertilizer_stock = state.inventory("FERTILIZER")
    if fertilizer_stock > 0:
        for tile in board.plants():
            if not getattr(tile, "fertilized", False) and not tile.is_ripe(
                state.day
            ):
                jobs.append(
                    Job(FERTILIZE, "FERTILIZE", tile.pos, item="FERTILIZER")
                )

    for tile in board.has_fertilizer_tiles():
        jobs.append(
            Job(
                COLLECT_FERTILIZER,
                "COLLECT_FERTILIZER",
                tile.pos,
                item="FERTILIZER",
            )
        )

    empty_tiles = board.empty_tiles(only_unlocked=True)
    if empty_tiles:
        if crop_weights and len(crop_weights) == 5:
            crops_to_plant = [
                c
                for i, c in enumerate(
                    ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
                )
                if crop_weights[i] > 0.15 and state.has_seed(c)
            ]
            if crops_to_plant:
                for idx, tile in enumerate(empty_tiles):
                    c = crops_to_plant[idx % len(crops_to_plant)]
                    priority = PLANT_BASE + crop_roi(state, c)
                    jobs.append(_plant_task(priority, tile.pos, c))
            else:
                crop = target_crop or best_crop(state)
                if crop and state.has_seed(crop):
                    priority = PLANT_BASE + crop_roi(state, crop)
                    for tile in empty_tiles:
                        jobs.append(_plant_task(priority, tile.pos, crop))
        else:
            crop = target_crop or best_crop(state)
            if crop and state.has_seed(crop):
                priority = PLANT_BASE + crop_roi(state, crop)
                for tile in empty_tiles:
                    jobs.append(_plant_task(priority, tile.pos, crop))

    return jobs


def _assign_one(
    jobs: list[Job],
    x: int,
    y: int,
    used: set[tuple[int, int]],
    state: GameState | None = None,
    board: Board | None = None,
) -> list[str]:
    best_job: Job | None = None
    best_score: float = -1e9
    for j in jobs:
        if j.target not in used:
            score = j.priority - 2.0 * (
                abs(x - j.target[0]) + abs(y - j.target[1])
            )
            if score > best_score:
                best_score = score
                best_job = j
    if best_job is not None:
        used.add(best_job.target)
        return job_to_action(best_job, x, y, state=state, board=board)
    return ["PASS"]


def assign_jobs(
    state: GameState, jobs: list[Job], board: Board | None = None
) -> tuple[list[str], list[list[str]]]:
    """Assign optimal, non-overlapping actions across farmer and all hands."""
    used: set[tuple[int, int]] = set()
    fx, fy = state.farmer
    farmer_act = _assign_one(jobs, fx, fy, used, state=state, board=board)
    hands_acts = [
        _assign_one(jobs, h[0], h[1], used, state=state, board=board)
        for h in state.hands
    ]
    return farmer_act, hands_acts


def schedule_tasks(
    state: GameState, board: Board, target_crop: str | None = None
) -> tuple[list[str], list[list[str]]]:
    """Top-level pipeline generating prioritized chores and assigning tasks to units."""
    jobs = generate_jobs(state, board, target_crop=target_crop)
    return assign_jobs(state, jobs, board=board)
