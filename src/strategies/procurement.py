"""Procurement strategy for crew, seeds, livestock, feed, and land."""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from environment.board import Board, Tile
    from environment.state import GameState

__all__ = [
    "ANIMAL_COSTS",
    "DEFAULT_ANIMAL_RESERVED_TILES",
    "DEFAULT_LAND_COST_MULT",
    "DEFAULT_LAND_MIN_CREW",
    "DEFAULT_MAX_HIRE_HOUR",
    "FIBONACCI",
    "LAND_COSTS",
    "SEED_COSTS",
    "apply_procurement",
    "procure_crew",
    "procure_feed",
    "procure_land",
    "procure_livestock",
    "procure_seeds",
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

FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)

# Hyperparameters exposed for Optuna tuning
DEFAULT_LAND_COST_MULT: float = 2.0
DEFAULT_LAND_MIN_CREW: int = 3
DEFAULT_MAX_HIRE_HOUR: int = 2
DEFAULT_ANIMAL_RESERVED_TILES: frozenset[tuple[int, int]] = frozenset(
    {(3, 4), (4, 3)}
)


def procure_land(
    market: list[list[Any]],
    state: GameState,
    target_crew: int,
    budget: int | None = None,
    cost_mult: float = DEFAULT_LAND_COST_MULT,
    min_crew: int = DEFAULT_LAND_MIN_CREW,
) -> int:
    """Purchase NE ($1k) or SW ($2k) quadrant when thresholds are met.

    Quadrant SE ($4,000) is strictly ignored.
    """
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10:
        return avail_budget
    if target_crew < min_crew:
        return avail_budget

    unlocked = state.unlocked_quadrants_set
    if "NE" not in unlocked:
        next_quad = "NE"
    elif "SW" not in unlocked:
        next_quad = "SW"
    else:
        return avail_budget

    cost = LAND_COSTS[next_quad]
    required_funds = int(cost * cost_mult)
    if state.money >= required_funds and avail_budget >= cost:
        market.append(["BUY_LAND"])
        avail_budget -= cost
    return avail_budget


def procure_crew(
    market: list[list[Any]],
    state: GameState,
    target_crew: int,
    budget: int | None = None,
    max_hire_hour: int = DEFAULT_MAX_HIRE_HOUR,
) -> int:
    """Hire hands in early hours if within target crew and affordable."""
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10 or state.hour > max_hire_hour:
        return avail_budget

    current_crew = len(state.hands)
    hires_queued = 0

    while current_crew + hires_queued < target_crew and len(market) < 10:
        hire_idx = state.hires_today + hires_queued
        hire_cost = FIBONACCI[min(hire_idx, len(FIBONACCI) - 1)]
        if avail_budget >= hire_cost:
            market.append(["HIRE"])
            avail_budget -= hire_cost
            hires_queued += 1
        else:
            break
    return avail_budget


def procure_seeds(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    target_crop: str,
    budget: int | None = None,
    reserved_tiles: Collection[tuple[int, int]] = DEFAULT_ANIMAL_RESERVED_TILES,
) -> int:
    """Procure seeds to match unplanted empty tiles with wheat fallback."""
    avail_budget = state.money if budget is None else budget
    if len(market) >= 10:
        return avail_budget

    reserved_set = set(reserved_tiles)
    empty_unlocked = [
        t
        for t in board.empty_tiles(only_unlocked=True)
        if t.pos not in reserved_set
    ]
    if not empty_unlocked:
        return avail_budget

    crop = target_crop if target_crop in SEED_COSTS else "WHEAT"
    crop_cost = SEED_COSTS[crop]
    total_held_seeds = sum(state.seeds.values())
    needed = len(empty_unlocked) - total_held_seeds

    if needed <= 0:
        return avail_budget

    # Prioritize target_crop
    target_buy = min(needed, avail_budget // crop_cost)
    if target_buy > 0 and len(market) < 10:
        market.append(["BUY_SEED", crop, target_buy])
        avail_budget -= target_buy * crop_cost
        needed -= target_buy

    # Fall back to WHEAT if target_crop could not satisfy all empty tiles
    if needed > 0 and crop != "WHEAT" and len(market) < 10:
        wheat_cost = SEED_COSTS["WHEAT"]
        wheat_buy = min(needed, avail_budget // wheat_cost)
        if wheat_buy > 0:
            market.append(["BUY_SEED", "WHEAT", wheat_buy])
            avail_budget -= wheat_buy * wheat_cost

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
    if active_count + shed_count >= capacity:
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
    cost_mult: float = DEFAULT_LAND_COST_MULT,
    min_crew: int = DEFAULT_LAND_MIN_CREW,
    max_hire_hour: int = DEFAULT_MAX_HIRE_HOUR,
    reserved_tiles: Collection[tuple[int, int]] = DEFAULT_ANIMAL_RESERVED_TILES,
    max_animals: int | None = None,
) -> int:
    """Execute all asset and commodity procurement decisions.

    Tracks and deducts shared budget across each procurement order.
    """
    budget = state.money
    budget = procure_crew(
        market,
        state,
        target_crew,
        budget=budget,
        max_hire_hour=max_hire_hour,
    )
    budget = procure_land(
        market,
        state,
        target_crew,
        budget=budget,
        cost_mult=cost_mult,
        min_crew=min_crew,
    )
    budget = procure_seeds(
        market,
        state,
        board,
        target_crop,
        budget=budget,
        reserved_tiles=reserved_tiles,
    )

    animal_tiles = board.animals()
    budget = procure_feed(
        market,
        state,
        len(animal_tiles),
        target_animal=target_animal,
        budget=budget,
    )
    capacity = len(reserved_tiles) if max_animals is None else max_animals
    budget = procure_livestock(
        market,
        state,
        target_animal,
        animal_tiles,
        budget=budget,
        max_animals=capacity,
    )
    return budget
