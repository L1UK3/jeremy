from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple

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
    "Job",
    "Scheduler",
    "care_jobs",
    "collect_fertilizer_jobs",
    "default_utility_scorer",
    "feed_jobs",
    "harvest_jobs",
    "job_to_action",
    "plant_jobs",
    "schedule_jobs",
    "water_jobs",
    "weed_jobs",
]

# -------------------------------------------------------------------------
# Score Calibration Constants
# -------------------------------------------------------------------------

FEED_URGENT: float = 1000.0
FEED: float = 500.0
CARE: float = 500.0
HARVEST_BASE: float = 150.0
WATER: float = 120.0
PLANT_BASE: float = 75.0
COLLECT_FERTILIZER: float = 65.0
DIG_WEED: float = 60.0

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
    actor: str = "farmer"
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
# Task Generators
# -------------------------------------------------------------------------


def harvest_jobs(
    state: GameState, board: Board, prices: dict[str, int] | None = None
) -> list[Job]:
    """Generate harvest jobs for all ripe plants and productive animals."""
    p = prices or state.prices
    jobs: list[Job] = []
    for tile in board.harvestable():
        if tile.is_animal and tile.animal:
            prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
            jobs.append(
                Job(
                    HARVEST_BASE + (tile.yield_units * p.get(prod, 0)),
                    "HARVEST",
                    tile.pos,
                    item=prod,
                )
            )
        elif tile.crop:
            jobs.append(
                Job(
                    HARVEST_BASE + (tile.yield_units * p.get(tile.crop, 0)),
                    "HARVEST",
                    tile.pos,
                    item=tile.crop,
                )
            )
    return jobs


def feed_jobs(state: GameState, board: Board) -> list[Job]:
    """Generate feeding jobs for unfed animals if wheat is available in shed."""
    wheat_count = state.inventory("WHEAT")
    if wheat_count <= 0:
        return []
    jobs: list[Job] = []
    for tile in board.needs_feed()[:wheat_count]:
        priority = FEED_URGENT if tile.consecutive_unfed >= 1 else FEED
        jobs.append(Job(priority, "FEED", tile.pos, item=tile.animal))
    return jobs


def care_jobs(board: Board) -> list[Job]:
    """Generate care/petting jobs for animals that have not been cared for today."""
    return [
        Job(CARE, "CARE", tile.pos, item=tile.animal)
        for tile in board.needs_care()
    ]


def collect_fertilizer_jobs(board: Board) -> list[Job]:
    """Generate fertilizer collection jobs for animal tiles with ready fertilizer."""
    return [
        Job(
            COLLECT_FERTILIZER,
            "COLLECT_FERTILIZER",
            tile.pos,
            item="FERTILIZER",
        )
        for tile in board.has_fertilizer_tiles()
    ]


def water_jobs(board: Board) -> list[Job]:
    """Generate watering jobs for thirsty crops."""
    return [Job(WATER, "WATER", tile.pos) for tile in board.needs_water()]


def weed_jobs(board: Board) -> list[Job]:
    """Generate weed clearing jobs on unlocked farm tiles."""
    return [
        Job(DIG_WEED, "DIG", tile.pos)
        for tile in board.weeds(only_unlocked=True)
    ]


def plant_jobs(
    state: GameState, board: Board, eco: Economy, crop: str
) -> list[Job]:
    """Generate planting jobs on empty unlocked tiles if seeds are available."""
    if not (crop and state.has_seed(crop)):
        return []
    priority = PLANT_BASE + eco.crop_roi(crop)
    return [
        Job(priority, "PLANT", tile.pos, item=crop)
        for tile in board.empty_tiles(only_unlocked=True)
    ]


def schedule_jobs(planner: Any, target_crop: str | None = None) -> None:
    """Populate planner's scheduler with all active crop and field jobs in one pass."""
    planner.scheduler.populate(
        board=planner.board,
        eco=planner.eco,
        target_crop=target_crop
        or (
            planner.config.get_crop(planner.eco)
            if hasattr(planner, "config")
            else planner.eco.best_crop()
        ),
    )


# -------------------------------------------------------------------------
# Unified High-Performance Scheduler
# -------------------------------------------------------------------------


class Scheduler:
    """Unified job generator and spatial multi-agent task dispatcher."""

    __slots__ = ("jobs", "scorer", "state")

    def __init__(
        self,
        state: GameState,
        scorer: Callable[[Job, int, int], float] = default_utility_scorer,
    ) -> None:
        self.state = state
        self.jobs: list[Job] = []
        self.scorer = scorer

    def add_job(
        self,
        action: str,
        x: int,
        y: int,
        priority: float,
        actor: str = "farmer",
        item: str | None = None,
    ) -> None:
        self.jobs.append(Job(priority, action, (x, y), actor, item))

    def extend_jobs(self, jobs: Sequence[Job]) -> None:
        self.jobs.extend(jobs)

    def clear(self) -> None:
        self.jobs.clear()

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
            jobs.append(Job(WATER, "WATER", tile.pos))

        for tile in board.weeds(only_unlocked=True):
            jobs.append(Job(DIG_WEED, "DIG", tile.pos))

        wheat_stock = self.state.inventory("WHEAT")
        if wheat_stock > 0:
            for tile in board.needs_feed()[:wheat_stock]:
                prio = FEED_URGENT if tile.consecutive_unfed >= 1 else FEED
                jobs.append(Job(prio, "FEED", tile.pos, item=tile.animal))

        for tile in board.needs_care():
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
        if self.scorer is default_utility_scorer:
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

        available = (j for j in self.jobs if j.target not in used)
        if best := max(
            available, key=lambda j: self.scorer(j, x, y), default=None
        ):
            used.add(best.target)
            return job_to_action(best, x, y)
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
