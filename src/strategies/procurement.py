"""Procurement strategy for crew, seeds, livestock, feed, and land expansion."""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "ANIMAL_COSTS",
    "DEFAULT_ANIMAL_RESERVED_TILES",
    "DEFAULT_LAND_COST_MULT",
    "DEFAULT_LAND_MIN_CREW",
    "DEFAULT_MAX_ANIMALS",
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
DEFAULT_MAX_ANIMALS: int = 2


def procure_land(
    market: list[list[Any]],
    state: GameState,
    target_crew: int,
    cost_mult: float = DEFAULT_LAND_COST_MULT,
    min_crew: int = DEFAULT_LAND_MIN_CREW,
) -> None:
    """Selectively purchase NE ($1,000) and SW ($2,000) land quadrants when capital and crew thresholds are met.

    Quadrant SE ($4,000) is strictly ignored.
    """
    if len(market) >= 10:
        return
    if target_crew < min_crew:
        return

    unlocked = state.unlocked_quadrants_set
    if "NE" not in unlocked:
        next_quad = "NE"
    elif "SW" not in unlocked:
        next_quad = "SW"
    else:
        # Next would be SE, which is never purchased
        return

    cost = LAND_COSTS[next_quad]
    required_funds = cost * cost_mult
    if state.money >= required_funds and state.can_afford(cost):
        market.append(["BUY_LAND"])


def procure_crew(
    market: list[list[Any]],
    state: GameState,
    target_crew: int,
    max_hire_hour: int = DEFAULT_MAX_HIRE_HOUR,
) -> None:
    """Hire additional hands in early hours if within target crew and affordable on Fibonacci curve."""
    if len(market) >= 10:
        return
    if state.hour > max_hire_hour:
        return

    current_crew = len(state.hands)
    hires_queued = 0
    simulated_money = state.money

    while current_crew + hires_queued < target_crew and len(market) < 10:
        hire_idx = state.hires_today + hires_queued
        hire_cost = FIBONACCI[min(hire_idx, len(FIBONACCI) - 1)]
        if simulated_money >= hire_cost:
            market.append(["HIRE"])
            simulated_money -= hire_cost
            hires_queued += 1
        else:
            break


def procure_seeds(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    target_crop: str,
    reserved_tiles: Collection[tuple[int, int]] = DEFAULT_ANIMAL_RESERVED_TILES,
) -> None:
    """Procure seeds to match unplanted empty unlocked tiles, prioritizing target_crop with wheat fallback."""
    if len(market) >= 10:
        return

    reserved_set = set(reserved_tiles)
    empty_unlocked = [
        t
        for t in board.empty_tiles(only_unlocked=True)
        if t.pos not in reserved_set
    ]
    if not empty_unlocked:
        return

    crop = target_crop if target_crop in SEED_COSTS else "WHEAT"
    crop_cost = SEED_COSTS[crop]
    held_target_seeds = state.seed_count(crop)
    needed = len(empty_unlocked) - held_target_seeds

    if needed <= 0:
        return

    simulated_money = state.money

    # Prioritize target_crop
    target_buy = min(needed, simulated_money // crop_cost)
    if target_buy > 0 and len(market) < 10:
        market.append(["BUY_SEED", crop, target_buy])
        simulated_money -= target_buy * crop_cost
        needed -= target_buy

    # Fall back to WHEAT if target_crop could not satisfy all empty tiles
    if needed > 0 and crop != "WHEAT" and len(market) < 10:
        wheat_cost = SEED_COSTS["WHEAT"]
        wheat_buy = min(needed, simulated_money // wheat_cost)
        if wheat_buy > 0:
            market.append(["BUY_SEED", "WHEAT", wheat_buy])


def procure_livestock(
    market: list[list[Any]],
    state: GameState,
    target_animal: str,
    animal_tiles: list[Any],
    max_animals: int = DEFAULT_MAX_ANIMALS,
) -> None:
    """Purchase livestock during productive window when budget allows and slots are available."""
    if len(market) >= 10:
        return
    if target_animal not in ANIMAL_COSTS:
        return

    step = state.step
    if step > 576:
        return

    # Check capacity and existing unplaced animals in shed
    shed_count = state.inventory(target_animal)
    if shed_count > 0:
        return

    active_count = sum(
        1
        for t in animal_tiles
        if getattr(t, "animal", None) == target_animal
        or getattr(t, "is_animal", False)
    )
    if active_count + shed_count >= max_animals:
        return

    cost = ANIMAL_COSTS[target_animal]
    if state.can_afford(cost):
        market.append(["BUY_ANIMAL", target_animal, 1])


def procure_feed(
    market: list[list[Any]],
    state: GameState,
    n_animals: int,
    target_animal: str = "NONE",
) -> None:
    """Maintain adequate wheat reserves for active animals or planned livestock."""
    if len(market) >= 10:
        return

    desired_reserve = max(
        n_animals * 2, 2 if target_animal in ANIMAL_COSTS else 0
    )
    if desired_reserve == 0:
        return

    current_wheat = state.inventory("WHEAT")
    if current_wheat < desired_reserve:
        wheat_price = state.price("WHEAT") or 25
        qty_needed = max(5, desired_reserve - current_wheat)
        if state.can_afford(wheat_price * qty_needed):
            market.append(["BUY_PRODUCT", "WHEAT", qty_needed])
        elif state.can_afford(wheat_price * (desired_reserve - current_wheat)):
            market.append(
                ["BUY_PRODUCT", "WHEAT", desired_reserve - current_wheat]
            )


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
    max_animals: int = DEFAULT_MAX_ANIMALS,
) -> None:
    """Execute all asset and commodity procurement decisions for this turn."""
    procure_crew(market, state, target_crew, max_hire_hour=max_hire_hour)
    procure_land(
        market, state, target_crew, cost_mult=cost_mult, min_crew=min_crew
    )
    procure_seeds(
        market,
        state,
        board,
        target_crop,
        reserved_tiles=reserved_tiles,
    )

    animal_tiles = board.animals()
    procure_feed(
        market,
        state,
        len(animal_tiles),
        target_animal=target_animal,
    )
    procure_livestock(
        market,
        state,
        target_animal,
        animal_tiles,
        max_animals=max_animals,
    )
