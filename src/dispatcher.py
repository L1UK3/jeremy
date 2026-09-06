from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from environment.board import (
    CROP_SPECS,
    SHED_ACCESS_TILES,
    manhattan_distance,
    step_toward,
)

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "CARE",
    "COLLECT_FERTILIZER",
    "DIG_WEED",
    "DROP_SHED",
    "FEED",
    "FEED_URGENT",
    "FERTILIZE",
    "HARVEST_BASE",
    "HARVEST_PREMIUM",
    "PLANT_BASE",
    "PLANT_CASCADE",
    "RESERVED_ANIMAL_TILES",
    "WATER",
    "WATER_BONUS",
    "WATER_URGENT",
    "Job",
    "_harvest_actions",
    "_plant_task",
    "assign_jobs",
    "default_utility_scorer",
    "generate_jobs",
    "job_to_action",
    "needs_center_drop",
    "schedule_tasks",
]

# Priority scores
FEED_URGENT: float = 350.0
WATER_URGENT: float = 300.0
DROP_SHED: float = 260.0
HARVEST_PREMIUM: float = 250.0
FEED: float = 200.0
CARE: float = 180.0
WATER_BONUS: float = 160.0
HARVEST_BASE: float = 150.0
DIG_WEED: float = 140.0
WATER: float = 120.0
PLANT_BASE: float = 75.0
PLANT_CASCADE: float = 65.0
FERTILIZE: float = 70.0
COLLECT_FERTILIZER: float = 60.0

RESERVED_ANIMAL_TILES: frozenset[tuple[int, int]] = frozenset({(3, 4), (4, 3)})

PRODUCE_ITEMS: frozenset[str] = frozenset(
    {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"}
)

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


def needs_center_drop(inv: dict[str, int], hour: int) -> bool:
    """Return True if unit should haul carried items to center shed."""
    carried = sum(inv.values())
    if carried >= 3:
        return True
    if hour >= 20 and any(inv.get(prod, 0) > 0 for prod in PRODUCE_ITEMS):
        return True
    return False


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
            return ["HARVEST"]
        if act == "DROP_SHED":
            return ["DROP"]
        return [act]
    if job.action == "DROP_SHED" and (x, y) in SHED_ACCESS_TILES:
        return ["DROP"]
    return [step_toward(x, y, tx, ty)]


def generate_jobs(
    state: GameState,
    board: Board,
    target_crop: str | None = None,
    crop_weights: tuple[float, ...] | list[float] | None = None,
) -> list[Job]:
    """Streamlined single-pass chore generation directly from board spatial indexes."""
    jobs: list[Job] = []
    prices = state.prices

    # Identify unplanted unlocked tiles excluding reserved animal tiles
    unplanted_unlocked = [
        t
        for t in board.empty_tiles(only_unlocked=True)
        if t.pos not in RESERVED_ANIMAL_TILES
    ]
    has_unplanted = len(unplanted_unlocked) > 0
    emergency_harvest = state.money < 50 and has_unplanted

    harvest_positions: set[tuple[int, int]] = set()

    # 1. Animal harvestable produce
    for tile in board.animals():
        if tile.yield_units > 0 and tile.animal:
            prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
            val = HARVEST_PREMIUM + (tile.yield_units * prices.get(prod, 0))
            jobs.append(Job(val, "HARVEST", tile.pos, item=prod))
            harvest_positions.add(tile.pos)

    # 2. Crop harvest (adaptive: max yield or emergency early harvest)
    for tile in board.plants():
        if not (tile.crop and tile.yield_units > 0):
            continue
        spec = CROP_SPECS.get(tile.crop)
        if spec is None:
            continue
        crop_age = tile.age(state.day)
        if crop_age < spec.first_yield_day:
            continue

        if spec.ongoing:
            is_ripe = True
        elif emergency_harvest:
            is_ripe = True
        else:
            is_ripe = crop_age >= spec.max_yield_day

        if is_ripe:
            base = (
                HARVEST_PREMIUM
                if tile.crop in ("MELON", "CARROT")
                else HARVEST_BASE
            )
            val = base + (tile.yield_units * prices.get(tile.crop, 0))
            jobs.append(Job(val, "HARVEST", tile.pos, item=tile.crop))
            harvest_positions.add(tile.pos)

    # 3. Water plants that are not being harvested, prioritizing bonus windows
    for tile in board.needs_water():
        if tile.pos in harvest_positions:
            continue
        if tile.consecutive_unwatered >= 1:
            prio = WATER_URGENT
        elif tile.crop:
            spec = CROP_SPECS.get(tile.crop)
            bonus_start = (
                (spec.max_yield_day + 1) // 2
                if spec and not spec.ongoing
                else 0
            )
            crop_age = tile.age(state.day)
            if (
                spec
                and not spec.ongoing
                and bonus_start <= crop_age < spec.max_yield_day
            ):
                prio = WATER_BONUS
            else:
                prio = WATER
        else:
            prio = WATER
        jobs.append(Job(prio, "WATER", tile.pos))

    # 4. Dig weeds
    for tile in board.weeds(only_unlocked=True):
        jobs.append(Job(DIG_WEED, "DIG", tile.pos))

    # 5. Animal feeding
    wheat_stock = state.inventory("WHEAT")
    if wheat_stock > 0:
        for tile in board.needs_feed()[:wheat_stock]:
            if not tile.fed_today:
                prio = FEED_URGENT if tile.consecutive_unfed >= 1 else FEED
                jobs.append(Job(prio, "FEED", tile.pos, item=tile.animal))

    # 6. Animal care
    for tile in board.needs_care():
        if not tile.cared_today:
            jobs.append(Job(CARE, "CARE", tile.pos, item=tile.animal))

    # 7. Fertilize plants
    fertilizer_stock = state.inventory("FERTILIZER")
    if fertilizer_stock > 0:
        for tile in board.plants():
            if tile.pos not in harvest_positions and not getattr(
                tile, "fertilized", False
            ):
                jobs.append(
                    Job(FERTILIZE, "FERTILIZE", tile.pos, item="FERTILIZER")
                )

    # 8. Collect animal fertilizer
    for tile in board.has_fertilizer_tiles():
        jobs.append(
            Job(
                COLLECT_FERTILIZER,
                "COLLECT_FERTILIZER",
                tile.pos,
                item="FERTILIZER",
            )
        )

    # 9. Center drop chores for units carrying >= 3 items or produce at hour >= 20
    used_shed_tiles: set[tuple[int, int]] = set()
    num_units = 1 + len(state.hands)
    for u in range(num_units):
        inv = state.worker_inventory(u)
        if needs_center_drop(inv, state.hour):
            u_pos = state.farmer if u == 0 else tuple(state.hands[u - 1])
            candidates = [
                s for s in SHED_ACCESS_TILES if s not in used_shed_tiles
            ]
            if not candidates:
                candidates = list(SHED_ACCESS_TILES)
            best_shed = min(
                candidates,
                key=lambda s: manhattan_distance(
                    s[0], s[1], u_pos[0], u_pos[1]
                ),
            )
            used_shed_tiles.add(best_shed)
            jobs.append(Job(DROP_SHED, "DROP_SHED", best_shed))

    # 10. Planting chores on unplanted unlocked tiles (excluding reserved animal tiles)
    if unplanted_unlocked:
        primary = target_crop if target_crop in CROP_SPECS else "WHEAT"
        secondary_crops = (
            ["WHEAT"]
            + [
                c
                for c in ("CARROT", "TOMATO", "STRAWBERRY", "MELON")
                if c != primary and c != "WHEAT"
            ]
            if primary != "WHEAT"
            else ["CARROT", "TOMATO", "STRAWBERRY", "MELON"]
        )

        available_seeds = {
            c: state.seed_count(c)
            for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
        }

        for tile in unplanted_unlocked:
            chosen_crop: str | None = None
            prio = PLANT_BASE
            if available_seeds.get(primary, 0) > 0:
                chosen_crop = primary
                prio = PLANT_BASE
            else:
                for sec in secondary_crops:
                    if available_seeds.get(sec, 0) > 0:
                        chosen_crop = sec
                        prio = PLANT_CASCADE
                        break

            if chosen_crop is not None:
                jobs.append(_plant_task(prio, tile.pos, chosen_crop))
                available_seeds[chosen_crop] -= 1
            else:
                # No more seeds in stock
                break

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
    """Assign optimal, non-overlapping actions across farmer and all hands from a single job pool."""
    unit_positions: list[tuple[int, int]] = [state.farmer]
    for h in state.hands:
        unit_positions.append((h[0], h[1]))

    n_units = len(unit_positions)
    unit_actions: list[list[str]] = [["PASS"] for _ in range(n_units)]
    used_targets: set[tuple[int, int]] = set()
    unassigned_units: set[int] = set(range(n_units))

    def is_eligible(u_idx: int, job: Job) -> bool:
        if job.action == "DROP_SHED":
            inv = state.worker_inventory(u_idx)
            return needs_center_drop(inv, state.hour)
        return True

    while unassigned_units:
        best_unit: int | None = None
        best_job: Job | None = None
        best_score: float = -1e9

        for u_idx in unassigned_units:
            ux, uy = unit_positions[u_idx]
            for job in jobs:
                if job.target in used_targets:
                    continue
                if not is_eligible(u_idx, job):
                    continue
                score = default_utility_scorer(job, ux, uy)
                if score > best_score:
                    best_score = score
                    best_unit = u_idx
                    best_job = job

        if best_unit is not None and best_job is not None:
            ux, uy = unit_positions[best_unit]
            unit_actions[best_unit] = job_to_action(
                best_job, ux, uy, state=state, board=board
            )
            used_targets.add(best_job.target)
            unassigned_units.remove(best_unit)
        else:
            break

    farmer_act = unit_actions[0]
    hands_acts = unit_actions[1:]
    return farmer_act, hands_acts


def schedule_tasks(
    state: GameState, board: Board, target_crop: str | None = None
) -> tuple[list[str], list[list[str]]]:
    """Top-level pipeline generating prioritized chores and assigning tasks to units."""
    jobs = generate_jobs(state, board, target_crop=target_crop)
    return assign_jobs(state, jobs, board=board)
