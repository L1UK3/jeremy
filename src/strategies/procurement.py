"""Procurement strategy for crew, seeds, livestock, feed, and land."""

from __future__ import annotations

import math
from collections.abc import Collection
from typing import TYPE_CHECKING, Any

from dispatcher import get_animal_reserved_tiles
from environment.board import CROP_SPECS
from parameters import (
    DEFAULT_PARAMETERS,
    ProcurementParams,
    get_active_parameters,
)

if TYPE_CHECKING:
    from environment.board import Board, Tile
    from environment.state import GameState

__all__ = [
    "ANIMAL_COSTS",
    "DEFAULT_ACTIONS_PER_HAND",
    "DEFAULT_ANIMAL_RESERVED_TILES",
    "DEFAULT_EXPANSION_DAY_NE",
    "DEFAULT_EXPANSION_DAY_SW",
    "DEFAULT_LABOR_FLOOR",
    "DEFAULT_LAND_COST_MULT",
    "DEFAULT_LAND_MIN_CREW",
    "DEFAULT_MAX_DAILY_HIRES",
    "DEFAULT_MAX_HIRE_HOUR",
    "FIBONACCI",
    "LAND_COSTS",
    "SEED_COSTS",
    "apply_procurement",
    "compute_quadrant_labor_floor",
    "estimate_daily_action_demand",
    "identify_active_crop",
    "procure_crew",
    "procure_feed",
    "procure_land",
    "procure_livestock",
    "procure_seeds",
    "within_maturation_horizon",
]

SEED_COSTS: dict[str, int] = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "STRAWBERRY": 100,
    "MELON": 80,
}

ANIMAL_COSTS: dict[str, int] = {
    "GOOSE": 300,
    "COW": 400,
    "SHEEP": 500,
}

LAND_COSTS: dict[str, int] = {
    "NE": 1000,
    "SW": 2000,
}

FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144)

# Hyperparameters exposed for Optuna tuning
DEFAULT_LAND_COST_MULT: float = DEFAULT_PARAMETERS.procurement.land_cost_mult
DEFAULT_LABOR_FLOOR: int = DEFAULT_PARAMETERS.procurement.land_min_crew
DEFAULT_LAND_MIN_CREW: int = DEFAULT_LABOR_FLOOR
DEFAULT_MAX_HIRE_HOUR: int = DEFAULT_PARAMETERS.procurement.max_hire_hour
DEFAULT_EXPANSION_DAY_NE: int = DEFAULT_PARAMETERS.procurement.expansion_day_ne
DEFAULT_EXPANSION_DAY_SW: int = DEFAULT_PARAMETERS.procurement.expansion_day_sw
DEFAULT_ACTIONS_PER_HAND: float = (
    DEFAULT_PARAMETERS.procurement.actions_per_hand
)
DEFAULT_MAX_DAILY_HIRES: int = DEFAULT_PARAMETERS.procurement.max_daily_hires
DEFAULT_ANIMAL_RESERVED_TILES: frozenset[tuple[int, int]] = frozenset(
    {(3, 4), (4, 3)}
)


def compute_quadrant_labor_floor(num_quads: int) -> int:
    """Calculate deterministic labor floor proportional to unlocked quadrants.

    Provides 2 hands for 1 unlocked quadrant, 4 hands for 2 quadrants,
    and 6 hands for 3 quadrants.
    """
    return min(max(num_quads, 1) * 2, 6)


def identify_active_crop(state: GameState, board: Board | None = None) -> str:
    """Identify dominant active crop on the farm, defaulting to WHEAT."""
    if board is not None:
        plants = board.plants()
        if plants:
            crop_counts: dict[str, int] = {}
            for p in plants:
                if p.crop:
                    crop_counts[p.crop] = crop_counts.get(p.crop, 0) + 1
            if crop_counts:
                return max(crop_counts, key=crop_counts.get)
        return "WHEAT"

    crop_counts: dict[str, int] = {}
    for row in state.tiles:
        for cell in row:
            if isinstance(cell, dict) and cell.get("kind") == "PLANT":
                c = cell.get("crop")
                if c:
                    crop_counts[c] = crop_counts.get(c, 0) + 1
    if crop_counts:
        return max(crop_counts, key=crop_counts.get)
    return "WHEAT"


_LAST_LAND_PURCHASE_DAY: int = -1
_LAST_LAND_PURCHASE_STEP: int = -1


def procure_land(
    market: list[list[Any]],
    state: GameState,
    target_crew: int = 0,
    budget: int | None = None,
    cost_mult: float = DEFAULT_LAND_COST_MULT,
    min_crew: int = DEFAULT_LAND_MIN_CREW,
    expansion_day_ne: int = DEFAULT_EXPANSION_DAY_NE,
    expansion_day_sw: int = DEFAULT_EXPANSION_DAY_SW,
    target_crop: str = "WHEAT",
    labor_floor: int | None = None,
) -> int:
    """Purchase NE ($1k) or SW ($2k) quadrant when thresholds are met.

    Quadrant SE ($4,000) is strictly ignored.
    """
    global _LAST_LAND_PURCHASE_DAY, _LAST_LAND_PURCHASE_STEP
    if state.step == 0 or state.step <= _LAST_LAND_PURCHASE_STEP:
        _LAST_LAND_PURCHASE_DAY = -1
    _LAST_LAND_PURCHASE_STEP = state.step

    avail_budget = state.money if budget is None else budget
    if len(market) >= 10:
        return avail_budget
    if any(o[0] == "BUY_LAND" for o in market):
        return avail_budget

    min_spacing = max(0, expansion_day_sw - expansion_day_ne)
    unlocked = state.unlocked_quadrants_set
    if "NE" not in unlocked:
        if state.day < expansion_day_ne:
            return avail_budget
        next_quad = "NE"
    elif "SW" not in unlocked:
        if state.day < expansion_day_sw:
            return avail_budget
        if _LAST_LAND_PURCHASE_DAY != -1 and (
            state.day < _LAST_LAND_PURCHASE_DAY + min_spacing
        ):
            return avail_budget
        next_quad = "SW"
    else:
        return avail_budget

    land_cost = LAND_COSTS[next_quad]
    active_crop = identify_active_crop(state)
    seed_cost = SEED_COSTS.get(active_crop, 10)
    tile_stocking_cost = 25 * seed_cost
    hire_idx = state.hires_today
    crew_maintenance_cost = (
        FIBONACCI[min(hire_idx, len(FIBONACCI) - 1)]
        + FIBONACCI[min(hire_idx + 1, len(FIBONACCI) - 1)]
    )
    required_funds = max(
        int(land_cost * cost_mult),
        land_cost + tile_stocking_cost + crew_maintenance_cost,
    )

    if state.money >= required_funds and avail_budget >= land_cost:
        market.append(["BUY_LAND"])
        avail_budget -= land_cost
        _LAST_LAND_PURCHASE_DAY = state.day
    return avail_budget


def estimate_daily_action_demand(
    state: GameState,
    board: Board,
    target_crop: str = "WHEAT",
    reserved_tiles: Collection[tuple[int, int]] | None = None,
) -> int:
    """Estimate total discrete chores required on the farm during the current day.

    Accounts for watering, harvesting, shed hauling, planting empty tiles,
    initial watering of new plantings, weed clearing, and livestock maintenance.
    """
    reserved_set = (
        set(reserved_tiles)
        if reserved_tiles is not None
        else DEFAULT_ANIMAL_RESERVED_TILES
    )

    # 1. Watering: all plants currently in the ground that are unwatered today
    water_actions = len(board.needs_water())

    # 2. Harvesting: ripe plants and animals with yield ready for collection
    total_harvests = len(board.harvestable())

    # Hauling: backpack capacity is 3, so trips to shed are needed
    drop_actions = (total_harvests + 2) // 3 if total_harvests > 0 else 0

    # 3. Planting: empty unlocked tiles (excluding reserved animal tiles)
    empty_unlocked = [
        t
        for t in board.empty_tiles(only_unlocked=True)
        if t.pos not in reserved_set
    ]
    plant_actions = len(empty_unlocked)
    # New plantings count as day 1 unwatered and must be watered today
    new_plant_water_actions = plant_actions

    # 4. Weeds: clearing weeds on unlocked tiles
    weed_actions = len(board.weeds(only_unlocked=True))

    # 5. Livestock maintenance: feed, care, and fertilizer gathering
    feed_actions = len(board.needs_feed())
    care_actions = len(board.needs_care())
    fertilizer_actions = len(board.has_fertilizer_tiles())

    # 6. Unplaced animals in shed
    unplaced_animals = sum(
        state.inventory(a) for a in ("GOOSE", "COW", "SHEEP")
    )

    total_actions = (
        water_actions
        + total_harvests
        + drop_actions
        + plant_actions
        + new_plant_water_actions
        + weed_actions
        + feed_actions
        + care_actions
        + fertilizer_actions
        + unplaced_animals
    )
    return total_actions


def procure_crew(
    market: list[list[Any]],
    state: GameState,
    target_crew: int,
    budget: int | None = None,
    max_hire_hour: int = DEFAULT_MAX_HIRE_HOUR,
    labor_floor: int | None = None,
    board: Board | None = None,
    actions_per_hand: float = DEFAULT_ACTIONS_PER_HAND,
    max_daily_hires: int = DEFAULT_MAX_DAILY_HIRES,
    target_crop: str = "WHEAT",
    reserved_tiles: Collection[tuple[int, int]] | None = None,
) -> int:
    """Hire Farm Hands in early hours respecting action demand, quadrant floor, and Fibonacci costs."""
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10 or state.hour > max_hire_hour:
        return avail_budget

    has_pending_expansion = any(o[0] == "BUY_LAND" for o in market)
    num_quads = len(state.unlocked_quadrants_set) + (
        1 if has_pending_expansion else 0
    )
    quadrant_floor = (
        compute_quadrant_labor_floor(num_quads)
        if labor_floor is None
        else labor_floor
    )

    action_crew = 0
    if board is not None:
        total_actions = estimate_daily_action_demand(
            state, board, target_crop=target_crop, reserved_tiles=reserved_tiles
        )
        action_crew = max(
            0, math.ceil(total_actions / max(1.0, actions_per_hand)) - 1
        )

    midgame_floor = (
        10 if (num_quads >= 3 and 11 <= state.day <= 25)
        else (8 if (num_quads >= 2 and 8 <= state.day <= 25) else 0)
    )

    effective_target_crew = max(
        quadrant_floor, target_crew, action_crew, midgame_floor
    )
    effective_target_crew = min(effective_target_crew, max_daily_hires)


    current_crew = len(state.hands)
    hires_queued = 0
    remaining_money = state.money

    while (
        current_crew + hires_queued < effective_target_crew and len(market) < 10
    ):
        hire_idx = state.hires_today + hires_queued
        hire_cost = (
            FIBONACCI[hire_idx] if hire_idx < len(FIBONACCI) else FIBONACCI[-1]
        )
        if avail_budget >= hire_cost and remaining_money >= hire_cost:
            market.append(["HIRE"])
            avail_budget -= hire_cost
            remaining_money -= hire_cost
            hires_queued += 1
        else:
            break
    return avail_budget


def within_maturation_horizon(crop: str, day: int) -> bool:
    """Return True if crop can produce at least one yield before Day 30."""
    spec = CROP_SPECS.get(crop)
    return spec is not None and (day + spec.first_yield_day < 30)


_can_mature = within_maturation_horizon


def procure_seeds(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    target_crop: str,
    budget: int | None = None,
    reserved_tiles: Collection[tuple[int, int]] = DEFAULT_ANIMAL_RESERVED_TILES,
    fallback_crop: str = "WHEAT",
    wheat_anchor: int = 0,
) -> int:
    """Procure seeds to match unplanted empty tiles with Maturation Horizon and fallback."""
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10 or state.day >= 28:
        return avail_budget

    reserved_set = set(reserved_tiles)
    empty_unlocked = [
        t
        for t in board.empty_tiles(only_unlocked=True)
        if t.pos not in reserved_set
    ]
    if not empty_unlocked:
        return avail_budget

    already_ordered_seeds = sum(
        order[2]
        for order in market
        if len(order) >= 3
        and order[0] == "BUY_SEED"
        and isinstance(order[2], int)
    )
    total_held_seeds = sum(state.seeds.values()) + already_ordered_seeds
    needed = len(empty_unlocked) - total_held_seeds

    if needed <= 0:
        return avail_budget

    # Dedicated wheat anchor: ensure at least wheat_anchor wheat plants/seeds are active
    if wheat_anchor > 0 and state.day < 28 and len(market) < 10:
        active_wheat = len(board.crops("WHEAT"))
        ordered_wheat = sum(
            order[2]
            for order in market
            if len(order) >= 3
            and order[0] == "BUY_SEED"
            and order[1] == "WHEAT"
            and isinstance(order[2], int)
        )
        held_wheat_seeds = state.seed_count("WHEAT") + ordered_wheat
        needed_wheat = max(0, wheat_anchor - (active_wheat + held_wheat_seeds))
        wheat_to_buy = min(
            needed_wheat, needed, avail_budget // SEED_COSTS["WHEAT"]
        )
        if wheat_to_buy > 0:
            market.append(["BUY_SEED", "WHEAT", wheat_to_buy])
            avail_budget -= wheat_to_buy * SEED_COSTS["WHEAT"]
            needed -= wheat_to_buy

    if needed <= 0:
        return avail_budget


    # Mid-game cash engine: between Days 8 and 22, empty tiles default to STRAWBERRY
    if (
        8 <= state.day <= 22
        and within_maturation_horizon("STRAWBERRY", state.day)
        and (len(state.unlocked_quadrants_set) >= 2 or target_crop != "MELON")
    ):
        desired_crop = "STRAWBERRY"
    else:
        desired_crop = target_crop if target_crop in SEED_COSTS else fallback_crop

    crop: str | None = None
    if within_maturation_horizon(desired_crop, state.day):
        crop = desired_crop
    elif within_maturation_horizon(fallback_crop, state.day):
        crop = fallback_crop
    else:
        for alt in ("WHEAT", "CARROT", "TOMATO"):
            if within_maturation_horizon(alt, state.day):
                crop = alt
                break
        if crop is None:
            return avail_budget


    crop_cost = SEED_COSTS[crop]
    target_buy = min(needed, avail_budget // crop_cost)
    if target_buy > 0 and len(market) < 10:
        market.append(["BUY_SEED", crop, target_buy])
        avail_budget -= target_buy * crop_cost
        needed -= target_buy


    if (
        needed > 0
        and crop != fallback_crop
        and len(market) < 10
        and within_maturation_horizon(fallback_crop, state.day)
    ):
        fallback_cost = SEED_COSTS[fallback_crop]
        fallback_buy = min(needed, avail_budget // fallback_cost)
        if fallback_buy > 0:
            market.append(["BUY_SEED", fallback_crop, fallback_buy])
            avail_budget -= fallback_buy * fallback_cost

    return avail_budget


def procure_livestock(
    market: list[list[Any]],
    state: GameState,
    target_animal: str,
    animal_tiles: Collection[Tile],
    budget: int | None = None,
    max_animals: int | None = None,
) -> int:
    """Purchase livestock when budget allows and animal slots are open."""
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10 or target_animal not in ANIMAL_COSTS:
        return avail_budget

    shed_count = state.inventory(target_animal)
    if shed_count > 0:
        return avail_budget

    capacity = (
        len(DEFAULT_ANIMAL_RESERVED_TILES)
        if max_animals is None
        else max_animals
    )
    active_count = sum(
        1
        for t in animal_tiles
        if getattr(t, "animal", None) == target_animal
        or getattr(t, "is_animal", False)
    )
    if active_count >= capacity:
        return avail_budget

    cost = ANIMAL_COSTS[target_animal]
    if avail_budget >= cost:
        market.append(["BUY_ANIMAL", target_animal, 1])
        avail_budget -= cost
    return avail_budget


def procure_feed(
    market: list[list[Any]],
    state: GameState,
    n_animals: int,
    target_animal: str = "NONE",
    budget: int | None = None,
) -> int:
    """Maintain adequate wheat feed reserves for active or target livestock."""
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10:
        return avail_budget

    desired_reserve = max(
        n_animals * 2, 2 if target_animal in ANIMAL_COSTS else 0
    )
    if desired_reserve == 0:
        return avail_budget

    current_wheat = state.inventory("WHEAT")
    needed = desired_reserve - current_wheat
    if needed > 0:
        wheat_price = state.price("WHEAT") or 25
        qty = min(needed, avail_budget // wheat_price)
        if qty > 0:
            market.append(["BUY_PRODUCT", "WHEAT", qty])
            avail_budget -= qty * wheat_price

    return avail_budget


def apply_procurement(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    target_crop: str,
    target_animal: str,
    target_crew: int,
    cost_mult: float | None = None,
    min_crew: int | None = None,
    max_hire_hour: int | None = None,
    reserved_tiles: Collection[tuple[int, int]] | None = None,
    max_animals: int | None = None,
    params: ProcurementParams | None = None,
) -> int:
    """Execute all asset and commodity procurement decisions.

    Tracks and deducts shared budget across each procurement order.
    """
    pp = params or get_active_parameters().procurement
    actual_cost_mult = cost_mult if cost_mult is not None else pp.land_cost_mult
    actual_min_crew = min_crew if min_crew is not None else pp.land_min_crew
    actual_max_hire_hour = (
        max_hire_hour if max_hire_hour is not None else pp.max_hire_hour
    )
    capacity = max_animals if max_animals is not None else pp.max_animals
    reserved_count = (
        pp.reserved_animal_tiles
        if hasattr(pp, "reserved_animal_tiles")
        else capacity
    )
    actual_reserved = (
        reserved_tiles
        if reserved_tiles is not None
        else get_animal_reserved_tiles(reserved_count)
    )

    budget = state.money
    budget = procure_land(
        market,
        state,
        target_crew=target_crew,
        budget=budget,
        cost_mult=actual_cost_mult,
        min_crew=actual_min_crew,
        expansion_day_ne=pp.expansion_day_ne,
        expansion_day_sw=pp.expansion_day_sw,
        target_crop=target_crop,
    )
    budget = procure_crew(
        market,
        state,
        target_crew,
        budget=budget,
        max_hire_hour=actual_max_hire_hour,
        board=board,
        actions_per_hand=pp.actions_per_hand,
        max_daily_hires=pp.max_daily_hires,
        target_crop=target_crop,
        reserved_tiles=actual_reserved,
    )

    animal_tiles = board.animals()
    budget = procure_feed(
        market,
        state,
        len(animal_tiles),
        target_animal=target_animal,
        budget=budget,
    )
    budget = procure_livestock(
        market,
        state,
        target_animal,
        animal_tiles,
        budget=budget,
        max_animals=capacity,
    )

    has_animals = (
        len(animal_tiles) > 0
        or state.inventory("COW") > 0
        or state.inventory("SHEEP") > 0
        or state.inventory("GOOSE") > 0
        or target_animal in ANIMAL_COSTS
    )
    wheat_anchor = 6 if (state.day == 0 or has_animals) else 0

    budget = procure_seeds(
        market,
        state,
        board,
        target_crop,
        budget=budget,
        reserved_tiles=actual_reserved,
        fallback_crop=pp.seed_fallback_crop,
        wheat_anchor=wheat_anchor,
    )
    return budget


