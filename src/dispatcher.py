from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from environment.board import (
    CROP_SPECS,
    SHED_ACCESS_TILES,
    manhattan_distance,
    step_toward,
)
from model.constants import QUAD_BOUNDS
from parameters import DispatcherParams, get_active_parameters

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "ALL_CANDIDATE_ANIMAL_TILES",
    "BUILD_COOP",
    "BUILD_PASTURE",
    "DROP_SHED",
    "PICKUP_ANIMAL",
    "PLACE",
    "PLANT_BASE",
    "PLANT_CASCADE",
    "Job",
    "_harvest_actions",
    "_plant_job",
    "_quadrant_animal_tiles",
    "assign_chores",
    "assign_jobs",
    "default_utility_scorer",
    "generate_jobs",
    "get_animal_plot_candidates",
    "get_animal_reserved_tiles",
    "job_to_action",
    "needs_center_drop",
    "schedule_tasks",
]


BUILD_COOP: str = "BUILD_COOP"
BUILD_PASTURE: str = "BUILD_PASTURE"
PICKUP_ANIMAL: str = "PICKUP_ANIMAL"
PLACE: str = "PLACE"
DROP_SHED: float = 260.0
PLANT_BASE: float = 75.0
PLANT_CASCADE: float = 65.0
QUADRANT_ORDER: tuple[str, ...] = ("NW", "NE", "SW", "SE")


_NW_ANIMAL_TILES: tuple[tuple[int, int], ...] = (
    (4, 4),
    (3, 4),
    (2, 4),
    (4, 3),
    (3, 3),
    (4, 2),
)
ALL_CANDIDATE_ANIMAL_TILES: tuple[tuple[int, int], ...] = _NW_ANIMAL_TILES


def _get_all_animal_plot_candidates(
    animals_per_quadrant: int | None = None,
) -> tuple[tuple[int, int], ...]:
    """Return all animal-plot candidates in deterministic quadrant order."""
    active = get_active_parameters().plot_allocation
    per_quadrant = (
        animals_per_quadrant
        if animals_per_quadrant is not None
        else active.animals_per_quadrant
    )
    candidates: list[tuple[int, int]] = []
    for slot in range(max(0, per_quadrant)):
        for quadrant in QUADRANT_ORDER:
            tiles = _quadrant_animal_tiles(quadrant)
            if slot < len(tiles):
                candidates.append(tiles[slot])
    return tuple(candidates)


def _quadrant_animal_tiles(quadrant: str) -> tuple[tuple[int, int], ...]:
    """Reflect the NW candidate pattern into the requested quadrant across center boundary."""
    if quadrant == "NE":
        return tuple((9 - x, y) for x, y in _NW_ANIMAL_TILES)
    if quadrant == "SW":
        return tuple((x, 9 - y) for x, y in _NW_ANIMAL_TILES)
    if quadrant == "SE":
        return tuple((9 - x, 9 - y) for x, y in _NW_ANIMAL_TILES)
    return _NW_ANIMAL_TILES


def get_animal_plot_candidates(
    unlocked_quadrants: frozenset[str] | set[str] | None = None,
    animals_per_quadrant: int | None = None,
    max_animals: int | None = None,
) -> tuple[tuple[int, int], ...]:
    """Return balanced animal-plot candidates in deterministic quadrant order."""
    active = get_active_parameters().plot_allocation
    quadrants = (
        frozenset(unlocked_quadrants)
        if unlocked_quadrants is not None
        else frozenset({"NW"})
    )
    per_quadrant = (
        animals_per_quadrant
        if animals_per_quadrant is not None
        else active.animals_per_quadrant
    )
    if max_animals is not None and quadrants:
        per_quadrant = max(
            per_quadrant,
            (max_animals + len(quadrants) - 1) // len(quadrants),
        )
    candidates: list[tuple[int, int]] = []
    for slot in range(max(0, per_quadrant)):
        for quadrant in QUADRANT_ORDER:
            if quadrant in quadrants:
                tiles = _quadrant_animal_tiles(quadrant)
                if slot < len(tiles):
                    candidates.append(tiles[slot])
    if max_animals is not None:
        candidates = candidates[: max(0, max_animals)]
    return tuple(candidates)


RESERVED_ANIMAL_TILES: frozenset[tuple[int, int]] = frozenset(
    ALL_CANDIDATE_ANIMAL_TILES[:2]
)


def get_animal_reserved_tiles(
    max_animals: int | None = None,
    unlocked_quadrants: frozenset[str] | set[str] | None = None,
    target_animals: int | None = None,
) -> frozenset[tuple[int, int]]:
    """Return reserved animal tiles capped to target animals and quadrant quotas."""
    quadrants = (
        frozenset(unlocked_quadrants)
        if unlocked_quadrants is not None
        else None
    )

    if target_animals is not None:
        plot_params = get_active_parameters().plot_allocation
        if quadrants is not None:
            plot_quota = len(quadrants) * plot_params.animals_per_quadrant
        else:
            plot_quota = len(ALL_CANDIDATE_ANIMAL_TILES)

        count = min(target_animals, plot_quota)
        if max_animals is not None:
            count = min(count, max_animals)
        count = max(0, count)
    elif max_animals is not None:
        count = max(0, max_animals)
    else:
        if quadrants is not None:
            plot_params = get_active_parameters().plot_allocation
            count = len(quadrants) * plot_params.animals_per_quadrant
        else:
            count = get_active_parameters().dispatcher.reserved_animal_tiles

    if count == 0:
        return frozenset()

    if quadrants is not None:
        return frozenset(
            get_animal_plot_candidates(
                unlocked_quadrants=quadrants,
                max_animals=count,
            )
        )
    return frozenset(ALL_CANDIDATE_ANIMAL_TILES[:count])


PRODUCE_ITEMS: frozenset[str] = frozenset(
    {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"}
)

ANIMAL_PRODUCT: dict[str, str] = {
    "COW": "MILK",
    "SHEEP": "WOOL",
    "GOOSE": "EGG",
}


class Job(NamedTuple):
    """Lightweight immutable chore specification for multi-agent scheduling."""

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


def _plant_job(priority: float, pos: tuple[int, int], crop: str) -> Job:
    """Generate a planting job specification."""
    return Job(priority=priority, action="PLANT", target=pos, item=crop)


def _harvest_actions(watered_today: bool = True, day: int = 0) -> list[str]:
    """Determine immediate harvest or maintenance action for a crop tile."""
    return ["WATER"] if not watered_today and day < 29 else ["HARVEST"]


def default_utility_scorer(
    job: Job, x: int, y: int, dist_penalty: float | None = None
) -> float:
    """Distance-discounted utility from an actor position (x, y)."""
    penalty = (
        dist_penalty
        if dist_penalty is not None
        else get_active_parameters().dispatcher.dist_penalty
    )
    return job.priority - (
        penalty * (abs(x - job.target[0]) + abs(y - job.target[1]))
    )


def job_to_action(
    job: Job,
    x: int,
    y: int,
    state: GameState | None = None,
    board: Board | None = None,
    u_idx: int | None = None,
) -> list[str]:
    """Convert a job into an immediate tile action or movement step."""
    tx, ty = job.target
    act = job.action

    actual_uidx = u_idx
    if actual_uidx is None and state is not None:
        if (x, y) == state.farmer:
            actual_uidx = 0
        else:
            for h_idx, h_pos in enumerate(state.hands):
                if (x, y) == (h_pos[0], h_pos[1]):
                    actual_uidx = h_idx + 1
                    break
        if actual_uidx is None:
            actual_uidx = 0

    if act == "PICKUP_ANIMAL":
        if (x, y) in SHED_ACCESS_TILES:
            inv = (
                state.worker_inventory(actual_uidx) if state is not None else {}
            )
            if sum(inv.values()) > 0:
                return ["DROP"]
            return ["PICKUP", job.item, 1] if job.item else ["PASS"]
        return [step_toward(x, y, tx, ty)]

    if act == "PLACE":
        if (x, y) == (tx, ty):
            return ["PLACE", job.item] if job.item else ["PLACE"]
        return [step_toward(x, y, tx, ty)]

    if act == "FEED":
        inv = state.worker_inventory(actual_uidx) if state is not None else {}
        if inv.get("WHEAT", 0) > 0:
            if (x, y) == (tx, ty):
                return ["FEED"]
            return [step_toward(x, y, tx, ty)]
        else:
            if (x, y) in SHED_ACCESS_TILES:
                if sum(inv.values()) >= 3 and inv.get("WHEAT", 0) == 0:
                    return ["DROP"]
                if state and state.inventory("WHEAT") > 0:
                    return ["PICKUP", "WHEAT", 1]
            sx, sy = board.nearest_shed(x, y) if board else (4, 4)
            return [step_toward(x, y, sx, sy)]

    if act == "FERTILIZE":
        inv = state.worker_inventory(actual_uidx) if state is not None else {}
        if inv.get("FERTILIZER", 0) > 0:
            if (x, y) == (tx, ty):
                return ["FERTILIZE"]
            return [step_toward(x, y, tx, ty)]
        else:
            if (x, y) in SHED_ACCESS_TILES:
                if sum(inv.values()) >= 3 and inv.get("FERTILIZER", 0) == 0:
                    return ["DROP"]
                if state and state.inventory("FERTILIZER") > 0:
                    return ["PICKUP", "FERTILIZER", 1]
            sx, sy = board.nearest_shed(x, y) if board else (4, 4)
            return [step_toward(x, y, sx, sy)]

    if (x, y) == (tx, ty):
        if act == "PLANT" and job.item:
            if state is not None:
                current_tile = state.tiles[ty][tx]
                if current_tile is not None:
                    is_weed = current_tile == "WEED" or (
                        isinstance(current_tile, dict)
                        and current_tile.get("kind") == "WEED"
                    )
                    if is_weed:
                        return ["DIG"]
                    return ["PASS"]
            return ["PLANT", job.item]
        if act == "HARVEST":
            return ["HARVEST"]
        if act == "DROP_SHED":
            return ["DROP"]
        if act in ("BUILD_COOP", "BUILD_PASTURE"):
            if state is not None:
                current_tile = state.tiles[ty][tx]
                if current_tile is not None:
                    return ["PASS"]
            return [act]
        return [act]
    if job.action == "DROP_SHED" and (x, y) in SHED_ACCESS_TILES:
        return ["DROP"]
    return [step_toward(x, y, tx, ty)]


def generate_jobs(
    state: GameState,
    board: Board,
    target_crop: str | None = None,
    crop_weights: tuple[float, ...] | list[float] | None = None,
    params: DispatcherParams | None = None,
    target_animal: str | None = None,
    max_animals: int | None = None,
    target_animals: int | None = None,
) -> list[Job]:
    """Streamlined single-pass chore generation directly from board spatial indexes."""
    dp = params or get_active_parameters().dispatcher
    effective_max_animals = (
        max_animals if max_animals is not None else dp.reserved_animal_tiles
    )
    active_reserved_tiles = get_animal_reserved_tiles(
        max_animals=effective_max_animals,
        unlocked_quadrants=state.unlocked_quadrants_set,
        target_animals=target_animals,
    )
    jobs: list[Job] = []
    prices = state.prices

    unplanted_unlocked = [
        t
        for t in board.empty_tiles(only_unlocked=True)
        if t.pos not in active_reserved_tiles
    ]
    has_unplanted = len(unplanted_unlocked) > 0
    emergency_harvest = state.money < 50 and has_unplanted

    harvest_positions: set[tuple[int, int]] = set()

    for tile in board.animals():
        if tile.yield_units > 0 and tile.animal:
            prod = ANIMAL_PRODUCT.get(tile.animal, tile.animal)
            val = dp.prio_harvest_premium + (
                tile.yield_units * prices.get(prod, 0)
            )
            jobs.append(Job(val, "HARVEST", tile.pos, item=prod))
            harvest_positions.add(tile.pos)

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
        elif emergency_harvest or state.day >= 28:
            is_ripe = True
        elif tile.crop == "MELON" and crop_age >= 10:
            is_ripe = True
        else:
            is_ripe = crop_age >= spec.max_yield_day

        if is_ripe:
            base = (
                dp.prio_harvest_premium
                if tile.crop in ("MELON", "CARROT")
                else dp.prio_harvest_base
            )
            val = base + (tile.yield_units * prices.get(tile.crop, 0))
            jobs.append(Job(val, "HARVEST", tile.pos, item=tile.crop))
            harvest_positions.add(tile.pos)

    occupied_coops = 0
    occupied_pastures = 0
    empty_coops = 0
    empty_pastures = 0

    for r in range(len(state.tiles)):
        for c in range(len(state.tiles[r])):
            t = state.tiles[r][c]
            if isinstance(t, dict):
                k = t.get("kind")
                if k == "COOP":
                    if t.get("animal"):
                        occupied_coops += 1
                    else:
                        empty_coops += 1
                elif k == "PASTURE":
                    if t.get("animal"):
                        occupied_pastures += 1
                    else:
                        empty_pastures += 1

    total_structures = (
        occupied_coops + occupied_pastures + empty_coops + empty_pastures
    )

    if total_structures < effective_max_animals:
        animals_needing_housing: list[str] = []
        for a in ("GOOSE", "COW", "SHEEP"):
            for _ in range(state.inventory(a)):
                animals_needing_housing.append(a)

        if (
            target_animal in ("GOOSE", "COW", "SHEEP")
            and not animals_needing_housing
        ):
            animals_needing_housing.append(target_animal)

        available_empty_coops = empty_coops
        available_empty_pastures = empty_pastures
        built_structures = 0
        remaining_capacity = effective_max_animals - total_structures

        for animal in animals_needing_housing:
            if built_structures >= remaining_capacity:
                break

            if animal == "GOOSE":
                if available_empty_coops > 0:
                    available_empty_coops -= 1
                    continue
                action_name = "BUILD_COOP"
            elif animal in ("COW", "SHEEP"):
                if available_empty_pastures > 0:
                    available_empty_pastures -= 1
                    continue
                action_name = "BUILD_PASTURE"
            else:
                continue

            plot_params = get_active_parameters().plot_allocation
            structure_counts: dict[str, int] = dict.fromkeys(QUADRANT_ORDER, 0)
            for y, row in enumerate(state.tiles):
                for x, tile in enumerate(row):
                    if not (
                        isinstance(tile, dict)
                        and tile.get("kind") in ("COOP", "PASTURE")
                    ):
                        continue
                    quadrant = (
                        "NW"
                        if x < 5 and y < 5
                        else "NE"
                        if x >= 5 and y < 5
                        else "SW"
                        if x < 5
                        else "SE"
                    )
                    structure_counts[quadrant] += 1

            planned_structure_targets = {
                j.target for j in jobs if j.action in (BUILD_COOP, BUILD_PASTURE)
            }
            for x, y in planned_structure_targets:
                quadrant = (
                    "NW"
                    if x < 5 and y < 5
                    else "NE"
                    if x >= 5 and y < 5
                    else "SW"
                    if x < 5 and y >= 5
                    else "SE"
                )
                structure_counts[quadrant] += 1

            candidate_by_quadrant = {
                quadrant: (
                    list(_quadrant_animal_tiles(quadrant))
                    if quadrant in state.unlocked_quadrants_set
                    else []
                )
                for quadrant in QUADRANT_ORDER
            }
            plot_params = get_active_parameters().plot_allocation
            quad_limit = (
                max(
                    plot_params.animals_per_quadrant,
                    (
                        effective_max_animals
                        + len(state.unlocked_quadrants_set)
                        - 1
                    )
                    // max(1, len(state.unlocked_quadrants_set)),
                )
                if effective_max_animals > 0
                else plot_params.animals_per_quadrant
            )
            candidate_quadrants = sorted(
                (
                    quadrant
                    for quadrant in QUADRANT_ORDER
                    if quadrant in state.unlocked_quadrants_set
                    and structure_counts[quadrant] < quad_limit
                    and any(
                        state.tiles[y][x] is None
                        and (x, y) not in planned_structure_targets
                        for x, y in candidate_by_quadrant[quadrant]
                    )
                ),
                key=lambda quadrant: (
                    structure_counts[quadrant],
                    QUADRANT_ORDER.index(quadrant),
                ),
            )
            target_tile: tuple[int, int] | None = None
            for quadrant in candidate_quadrants:
                for rx, ry in candidate_by_quadrant[quadrant]:
                    if (
                        state.tiles[ry][rx] is None
                        and (rx, ry) not in planned_structure_targets
                    ):
                        target_tile = (rx, ry)
                        break
                if target_tile is not None:
                    break

            if target_tile is None:
                for quadrant in candidate_quadrants:
                    (ymin, ymax, xmin, xmax) = QUAD_BOUNDS[quadrant]
                    for ry in range(ymin, ymax):
                        for rx in range(xmin, xmax):
                            if (
                                state.tiles[ry][rx] is None
                                and (rx, ry) not in planned_structure_targets
                            ):
                                target_tile = (rx, ry)
                                break
                        if target_tile is not None:
                            break
                    if target_tile is not None:
                        break

            if target_tile is not None:
                prio = getattr(dp, "prio_build_structure", 220.0)
                jobs.append(Job(prio, action_name, target_tile, item=animal))
                built_structures += 1

    num_units = 1 + len(state.hands)
    targeted_structures: set[tuple[int, int]] = set()

    for u in range(num_units):
        inv = state.worker_inventory(u)
        for animal in ("GOOSE", "COW", "SHEEP"):
            if inv.get(animal, 0) > 0:
                matching_kind = "COOP" if animal == "GOOSE" else "PASTURE"
                for r in range(len(state.tiles)):
                    for c in range(len(state.tiles[r])):
                        t = state.tiles[r][c]
                        if (
                            isinstance(t, dict)
                            and t.get("kind") == matching_kind
                            and not t.get("animal")
                        ):
                            pos = (c, r)
                            if pos not in targeted_structures:
                                prio = getattr(dp, "prio_place_animal", 245.0)
                                jobs.append(
                                    Job(prio, "PLACE", pos, item=animal)
                                )
                                targeted_structures.add(pos)
                                break

    pickup_idx = 0
    for animal in ("GOOSE", "COW", "SHEEP"):
        shed_qty = state.inventory(animal)
        if shed_qty > 0:
            matching_kind = "COOP" if animal == "GOOSE" else "PASTURE"
            empty_matching_structures: list[tuple[int, int]] = []
            for r in range(len(state.tiles)):
                for c in range(len(state.tiles[r])):
                    t = state.tiles[r][c]
                    if (
                        isinstance(t, dict)
                        and t.get("kind") == matching_kind
                        and not t.get("animal")
                    ):
                        pos = (c, r)
                        if pos not in targeted_structures:
                            empty_matching_structures.append(pos)

            already_assigned = sum(
                1
                for j in jobs
                if j.action in ("PICKUP_ANIMAL", "PLACE") and j.item == animal
            )
            needed_pickups = min(
                shed_qty - already_assigned, len(empty_matching_structures)
            )

            for _ in range(needed_pickups):
                target_structure = empty_matching_structures.pop(0)
                targeted_structures.add(target_structure)
                shed_target = SHED_ACCESS_TILES[
                    pickup_idx % len(SHED_ACCESS_TILES)
                ]
                pickup_idx += 1
                prio = getattr(dp, "prio_pickup_animal", 240.0)
                jobs.append(
                    Job(prio, "PICKUP_ANIMAL", shed_target, item=animal)
                )

    from strategies.explosion import is_valid_terminal_water

    for tile in board.needs_water():
        if tile.pos in harvest_positions:
            continue
        if not is_valid_terminal_water(tile, state.day):
            continue

        crop_age = tile.age(state.day)
        spec = CROP_SPECS.get(tile.crop) if tile.crop else None
        bonus_start = (
            (spec.max_yield_day + 1) // 2
            if spec and not spec.ongoing
            else 0
        )

        # Urgent priority deactivation: disable urgent priority during termination
        if tile.consecutive_unwatered >= 1 and state.day < 28:
            prio = dp.prio_water_urgent
        elif (
            spec
            and not spec.ongoing
            and bonus_start <= crop_age <= spec.max_yield_day
        ):
            prio = dp.prio_water_bonus
        else:
            prio = dp.prio_water
        jobs.append(Job(prio, "WATER", tile.pos))

    for tile in board.weeds(only_unlocked=True):
        dig_prio = (
            360.0
            if (state.day >= 28 and sum(state.seeds.values()) > 0)
            else dp.prio_dig_weed
        )
        jobs.append(Job(dig_prio, "DIG", tile.pos))

    worker_wheat = sum(
        state.worker_inventory(u).get("WHEAT", 0) for u in range(num_units)
    )
    total_wheat = state.inventory("WHEAT") + worker_wheat
    if total_wheat > 0:
        feed_candidates = sorted(
            board.needs_feed(),
            key=lambda t: t.consecutive_unfed,
            reverse=True,
        )
        for tile in feed_candidates[:total_wheat]:
            if not tile.fed_today:
                prio = (
                    dp.prio_feed_urgent
                    if tile.consecutive_unfed >= 1
                    else dp.prio_feed
                )
                jobs.append(Job(prio, "FEED", tile.pos, item=tile.animal))

    for tile in board.needs_care():
        if not tile.cared_today:
            jobs.append(Job(dp.prio_care, "CARE", tile.pos, item=tile.animal))

    avail_fert = sum(
        state.worker_inventory(u).get("FERTILIZER", 0) for u in range(num_units)
    ) + state.inventory("FERTILIZER")
    if avail_fert > 0 and state.day >= 10:
        fert_count = 0
        for tile in board.plants():
            if fert_count >= avail_fert:
                break
            if tile.pos in harvest_positions:
                continue
            is_fert = (
                tile.is_fertilized(state.day)
                if hasattr(tile, "is_fertilized")
                else getattr(tile, "fertilized", False)
            )
            if not is_fert and tile.crop in ("STRAWBERRY", "MELON"):
                jobs.append(
                    Job(
                        dp.prio_fertilize,
                        "FERTILIZE",
                        tile.pos,
                        item="FERTILIZER",
                    )
                )
                fert_count += 1

    for tile in board.has_fertilizer_tiles():
        jobs.append(
            Job(
                dp.prio_collect_fertilizer,
                "COLLECT_FERTILIZER",
                tile.pos,
                item="FERTILIZER",
            )
        )

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
            jobs.append(Job(dp.prio_drop_shed, "DROP_SHED", best_shed))

    if unplanted_unlocked and state.hour < 23:
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

        structure_targets = {
            j.target for j in jobs if j.action in (BUILD_COOP, BUILD_PASTURE)
        }

        for tile in unplanted_unlocked:
            if tile.pos in structure_targets:
                continue
            chosen_crop: str | None = None
            prio = 350.0 if state.day >= 28 else dp.prio_plant_base
            if state.day >= 28:
                crops_order = [*secondary_crops, primary]
                for c in crops_order:
                    if available_seeds.get(c, 0) > 0:
                        chosen_crop = c
                        break
            else:
                if available_seeds.get(primary, 0) > 0:
                    chosen_crop = primary
                else:
                    for sec in secondary_crops:
                        if available_seeds.get(sec, 0) > 0:
                            chosen_crop = sec
                            prio = dp.prio_plant_cascade
                            break

            if chosen_crop is not None:
                prio_to_use = prio
                if chosen_crop == "STRAWBERRY" and (
                    tile.x >= 5 or tile.y >= 5
                ):
                    prio_to_use = max(prio_to_use, 260.0)
                jobs.append(_plant_job(prio_to_use, tile.pos, chosen_crop))
                available_seeds[chosen_crop] -= 1
            else:
                break

    return jobs


def _assign_one(
    jobs: list[Job],
    x: int,
    y: int,
    used: set[tuple[int, int]],
    state: GameState | None = None,
    board: Board | None = None,
    dist_penalty: float | None = None,
) -> list[str]:
    penalty = (
        dist_penalty
        if dist_penalty is not None
        else get_active_parameters().dispatcher.dist_penalty
    )
    best_job: Job | None = None
    best_score: float = -1e9
    for j in jobs:
        if j.target not in used:
            score = j.priority - penalty * (
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
    state: GameState,
    jobs: list[Job],
    board: Board | None = None,
    params: DispatcherParams | None = None,
) -> tuple[list[str], list[list[str]]]:
    """Assign optimal, non-overlapping actions across farmer and all hands from a single job pool."""
    dp = params or get_active_parameters().dispatcher
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
        if job.action == "PLACE":
            inv = state.worker_inventory(u_idx)
            return bool(job.item and inv.get(job.item, 0) > 0)
        if job.action == "PICKUP_ANIMAL":
            inv = state.worker_inventory(u_idx)
            if any(inv.get(a, 0) > 0 for a in ("GOOSE", "COW", "SHEEP")):
                return False
            return True
        if job.action == "FEED":
            inv = state.worker_inventory(u_idx)
            if sum(inv.values()) >= 3 and inv.get("WHEAT", 0) == 0:
                return False
            return True
        if job.action == "COLLECT_FERTILIZER":
            inv = state.worker_inventory(u_idx)
            return sum(inv.values()) < 3
        if job.action == "FERTILIZE":
            inv = state.worker_inventory(u_idx)
            return inv.get("FERTILIZER", 0) > 0
        return True

    assigned_jobs: dict[int, Job] = {}
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
                penalty = 0.75 if job.action == "PLANT" else dp.dist_penalty
                score = default_utility_scorer(
                    job, ux, uy, dist_penalty=penalty
                )
                if job.action == "FEED":
                    inv = state.worker_inventory(u_idx)
                    if inv.get("WHEAT", 0) > 0:
                        score += 150.0
                elif job.action == "PLANT":
                    if job.item == "STRAWBERRY":
                        score += 80.0
                    if state.hour < 14:
                        score += 110.0
                    elif state.hour < 18:
                        score += 50.0
                if score > best_score:
                    best_score = score
                    best_unit = u_idx
                    best_job = job

        if best_unit is not None and best_job is not None:
            ux, uy = unit_positions[best_unit]
            unit_actions[best_unit] = job_to_action(
                best_job, ux, uy, state=state, board=board, u_idx=best_unit
            )
            assigned_jobs[best_unit] = best_job
            used_targets.add(best_job.target)
            unassigned_units.remove(best_unit)
        else:
            break

    # Farmer Priority: prevent hired hands from starving the main farmer of chores
    if 0 in unassigned_units and assigned_jobs:
        fx, fy = unit_positions[0]
        best_farmer_job: Job | None = None
        best_farmer_score: float = -1e9
        for job in jobs:
            if not is_eligible(0, job):
                continue
            penalty = 0.75 if job.action == "PLANT" else dp.dist_penalty
            score = default_utility_scorer(
                job, fx, fy, dist_penalty=penalty
            )
            if job.action == "FEED":
                inv = state.worker_inventory(0)
                if inv.get("WHEAT", 0) > 0:
                    score += 150.0
            elif job.action == "PLANT":
                if job.item == "STRAWBERRY":
                    score += 80.0
                if state.hour < 14:
                    score += 110.0
                elif state.hour < 18:
                    score += 50.0
            if score > best_farmer_score:
                best_farmer_score = score
                best_farmer_job = job

        if best_farmer_job is not None:
            # Displace any hand currently assigned to this target
            for h_idx, h_job in list(assigned_jobs.items()):
                if h_job.target == best_farmer_job.target and h_idx != 0:
                    unit_actions[h_idx] = ["PASS"]
                    del assigned_jobs[h_idx]
                    break
            unit_actions[0] = job_to_action(
                best_farmer_job, fx, fy, state=state, board=board, u_idx=0
            )
            assigned_jobs[0] = best_farmer_job
            unassigned_units.remove(0)

    # 3. Idle Farmer Repositioning Fallback
    if unit_actions[0] == ["PASS"]:
        fx, fy = unit_positions[0]
        if (fx, fy) not in SHED_ACCESS_TILES:
            target_shed = (
                board.nearest_shed(fx, fy) if board is not None else (4, 4)
            )
            step = step_toward(fx, fy, target_shed[0], target_shed[1])
            if step != "PASS":
                unit_actions[0] = [step]
        else:
            quad_counts: dict[str, int] = dict.fromkeys(state.unlocked_quadrants_set, 0)
            if board is not None:
                for plant in board.plants():
                    qx = "E" if plant.x >= 5 else "W"
                    qy = "S" if plant.y >= 5 else "N"
                    q = qy + qx
                    if q in quad_counts:
                        quad_counts[q] += 1
            if any(count > 0 for count in quad_counts.values()):
                best_quad = max(quad_counts, key=lambda k: quad_counts[k])
                quad_centers = {
                    "NW": (2, 2),
                    "NE": (7, 2),
                    "SW": (2, 7),
                    "SE": (7, 7),
                }
                cx, cy = quad_centers.get(best_quad, (2, 2))
                step = step_toward(fx, fy, cx, cy)
                if step != "PASS":
                    unit_actions[0] = [step]

    return unit_actions[0], unit_actions[1:]


def assign_chores(
    state: GameState,
    board: Board,
    target_crop: str | None = None,
    target_animal: str | None = None,
    params: DispatcherParams | None = None,
    max_animals: int | None = None,
) -> tuple[list[str], list[list[str]]]:
    """Top-level pipeline generating prioritized chores and assigning them to units."""
    dp = params or get_active_parameters().dispatcher
    jobs = generate_jobs(
        state,
        board,
        target_crop=target_crop,
        target_animal=target_animal,
        params=dp,
        max_animals=max_animals,
    )
    return assign_jobs(state, jobs, board=board, params=dp)


schedule_tasks = assign_chores
