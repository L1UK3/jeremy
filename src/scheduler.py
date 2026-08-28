from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from board import step_toward

if TYPE_CHECKING:
    from board import Board
    from economy import Economy
    from state import GameState

__all__ = [
    "CARE",
    "COLLECT_FERTILIZER",
    "DIG_WEED",
    "FEED",
    "FEED_URGENT",
    "HARVEST_BASE",
    "PLANT_BASE",
    "WATER",
    "WATER_URGENT",
    "Job",
    "Scheduler",
    "default_utility_scorer",
    "job_to_action",
]

# -------------------------------------------------------------------------
# Score Calibration Constants
# -------------------------------------------------------------------------

FEED_URGENT: float = 350.0
WATER_URGENT: float = 300.0
FEED: float = 200.0
CARE: float = 180.0
HARVEST_BASE: float = 150.0
DIG_WEED: float = 140.0
WATER: float = 120.0
PLANT_BASE: float = 75.0
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


def default_utility_scorer(
    job: Job, x: int, y: int, dist_penalty: float = 2.0
) -> float:
    """Distance-discounted utility from an actor position (x, y)."""
    return job.priority - (
        dist_penalty * (abs(x - job.target[0]) + abs(y - job.target[1]))
    )


def job_to_action(job: Job, x: int, y: int) -> list[str]:
    """Convert a job into an immediate tile action or movement step."""
    tx, ty = job.target
    if (x, y) == (tx, ty):
        act = job.action
        if act == "PLANT" and job.item:
            return ["PLANT", job.item]
        return [act]
    return [step_toward(x, y, tx, ty)]


# -------------------------------------------------------------------------
# Unified High-Performance Scheduler
# -------------------------------------------------------------------------


class Scheduler:
    """Unified job generator and spatial multi-agent task dispatcher."""

    __slots__ = ("jobs", "state")

    def __init__(self, state: GameState) -> None:
        self.state = state
        self.jobs: list[Job] = []

    def populate(
        self, board: Board, eco: Economy, target_crop: str | None = None
    ) -> None:
        """Streamlined single-pass job generation directly from board indexes."""
        self.jobs.clear()
        jobs = self.jobs
        prices = self.state.prices

        for tile in board.harvestable():
            if tile.is_animal and tile.animal:
                prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
                val = HARVEST_BASE + (tile.yield_units * prices.get(prod, 0))
                jobs.append(Job(val, "HARVEST", tile.pos, item=prod))
            elif tile.crop:
                val = HARVEST_BASE + (
                    tile.yield_units * prices.get(tile.crop, 0)
                )
                jobs.append(Job(val, "HARVEST", tile.pos, item=tile.crop))

        for tile in board.needs_water():
            prio = WATER_URGENT if tile.consecutive_unwatered >= 1 else WATER
            jobs.append(Job(prio, "WATER", tile.pos))

        for tile in board.weeds(only_unlocked=True):
            jobs.append(Job(DIG_WEED, "DIG", tile.pos))

        wheat_stock = self.state.inventory("WHEAT")
        if wheat_stock > 0:
            for tile in board.needs_feed()[:wheat_stock]:
                if not tile.fed_today:
                    prio = FEED_URGENT if tile.consecutive_unfed >= 1 else FEED
                    jobs.append(Job(prio, "FEED", tile.pos, item=tile.animal))

        for tile in board.needs_care():
            if not tile.cared_today:
                jobs.append(Job(CARE, "CARE", tile.pos, item=tile.animal))

        for tile in board.has_fertilizer_tiles():
            jobs.append(
                Job(
                    COLLECT_FERTILIZER,
                    "COLLECT_FERTILIZER",
                    tile.pos,
                    item="FERTILIZER",
                )
            )

        crop = target_crop or eco.best_crop()
        if crop and self.state.has_seed(crop):
            prio = PLANT_BASE + eco.crop_roi(crop)
            for tile in board.empty_tiles(only_unlocked=True):
                jobs.append(Job(prio, "PLANT", tile.pos, item=crop))

    def _assign_one(
        self, x: int, y: int, used: set[tuple[int, int]]
    ) -> list[str]:
        best_job: Job | None = None
        best_score: float = -1e9
        for j in self.jobs:
            if j.target not in used:
                score = j.priority - 2.0 * (
                    abs(x - j.target[0]) + abs(y - j.target[1])
                )
                if score > best_score:
                    best_score = score
                    best_job = j
        if best_job is not None:
            used.add(best_job.target)
            return job_to_action(best_job, x, y)
        return ["PASS"]

    def assign(self) -> tuple[list[str], list[list[str]]]:
        """Assign optimal, non-overlapping actions across farmer and all hands."""
        used: set[tuple[int, int]] = set()
        fx, fy = self.state.farmer
        farmer_act = self._assign_one(fx, fy, used)
        hands_acts = [
            self._assign_one(h[0], h[1], used) for h in self.state.hands
        ]
        return farmer_act, hands_acts
