"""Procurement strategy for crew, seeds, livestock, and feed."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from environment.board import Board
    from environment.state import GameState

__all__ = [
    "ANIMAL_COSTS",
    "FIBONACCI",
    "SEED_COSTS",
    "apply_procurement",
    "procure_crew",
    "procure_feed",
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

FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)


def procure_crew(
    market: list[list[Any]], state: GameState, target_crew: int
) -> None:
    """Hire additional hands in early hours if within target crew and affordable."""
    if len(market) >= 10:
        return
    if len(state.hands) < target_crew and state.hour <= 2:
        hire_cost = FIBONACCI[min(state.hires_today, len(FIBONACCI) - 1)]
        if state.can_afford(hire_cost):
            market.append(["HIRE"])


def procure_seeds(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    target_crop: str,
) -> None:
    """Procure seeds to populate available empty unlocked tiles."""
    if len(market) >= 10:
        return
    empty_unlocked = board.empty_tiles(only_unlocked=True)
    if empty_unlocked and state.seed_count(target_crop) < 6:
        seed_cost = SEED_COSTS.get(target_crop, 10)
        needed = min(6, len(empty_unlocked) + 1)
        if state.can_afford(seed_cost * needed):
            market.append(["BUY_SEED", target_crop, needed])


def procure_livestock(
    market: list[list[Any]],
    state: GameState,
    target_animal: str,
    animal_tiles: list[Any],
) -> None:
    """Purchase livestock during productive mid-game window when feed is secured."""
    if len(market) >= 10:
        return
    step = state.step
    if (
        target_animal in ANIMAL_COSTS
        and 48 <= step <= 576
        and state.inventory(target_animal) == 0
        and sum(1 for t in animal_tiles if t.animal == target_animal) < 2
        and state.can_afford(ANIMAL_COSTS[target_animal])
        and state.inventory("WHEAT") >= 2
    ):
        market.append(["BUY_ANIMAL", target_animal, 1])


def procure_feed(
    market: list[list[Any]],
    state: GameState,
    n_animals: int,
) -> None:
    """Maintain adequate wheat reserves for all owned animals."""
    if len(market) >= 10:
        return
    if n_animals > 0 and state.inventory("WHEAT") < n_animals * 2:
        wheat_price = state.price("WHEAT") or 25
        if state.can_afford(wheat_price * 5):
            market.append(["BUY_PRODUCT", "WHEAT", 5])


def apply_procurement(
    market: list[list[Any]],
    state: GameState,
    board: Board,
    target_crop: str,
    target_animal: str,
    target_crew: int,
) -> None:
    """Execute all asset and commodity procurement decisions for this turn."""
    procure_crew(market, state, target_crew)
    procure_seeds(market, state, board, target_crop)

    animal_tiles = board.animals()
    procure_livestock(market, state, target_animal, animal_tiles)
    procure_feed(market, state, len(animal_tiles))
