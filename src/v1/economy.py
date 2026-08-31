from __future__ import annotations

from typing import TYPE_CHECKING

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

if TYPE_CHECKING:
    from state import GameState

__all__ = [
    "CROP_PROPERTIES",
    "FIBONACCI",
    "affordable_hires",
    "best_crop",
    "crop_cost",
    "crop_roi",
    "expansion_cost",
    "hire_cost",
    "max_daily_hires",
    "next_quadrant_target",
    "should_buy_seed",
    "should_expand",
]

CROP_PROPERTIES: dict[str, tuple[int, int]] = {
    crop: (int(data.get("seed", 0)), int(data.get("max_yield_day", 1)))
    for crop, data in CROPS.items()
}
FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)


def crop_cost(crop: str) -> int:
    """Return the seed purchase cost for a crop."""
    return CROP_PROPERTIES.get(crop, (0, 1))[0]


def crop_roi(state: GameState, crop: str) -> float:
    """Calculate daily return on investment for a crop based on live market prices."""
    seed_cost, max_yield_day = CROP_PROPERTIES.get(crop, (0, 1))
    grow = max_yield_day if max_yield_day > 0 else 1
    revenue = state.price(crop)
    return float(revenue - seed_cost) / float(grow)


def best_crop(state: GameState) -> str | None:
    """Determine the highest ROI crop that can fully mature before Day 30."""
    best: str | None = None
    best_roi = -1e9
    days_remaining = 30 - state.day
    prices = state.prices

    for crop, (seed_cost, max_yield_day) in CROP_PROPERTIES.items():
        if max_yield_day > days_remaining:
            continue

        revenue = prices.get(crop, 0)
        grow = max_yield_day if max_yield_day > 0 else 1
        roi = (revenue - seed_cost) / grow
        if roi > best_roi:
            best_roi = roi
            best = crop
    return best


def should_buy_seed(
    state: GameState, crop: str | None, target_count: int = 1
) -> bool:
    """Determine whether the agent should purchase seeds for the focus crop."""
    if not crop or state.seed_count(crop) >= target_count:
        return False
    return state.can_afford(crop_cost(crop))


def expansion_cost(state: GameState) -> int | None:
    """Return the coin cost to unlock the next quadrant, or None if fully unlocked."""
    num_unlocked = len(state.unlocked_quadrants_set)
    if num_unlocked == 1:
        return 1000
    if num_unlocked == 2:
        return 2000
    if num_unlocked == 3:
        return 4000
    return None


def next_quadrant_target(state: GameState) -> tuple[int, int] | None:
    """Return the coordinates of the next recommended quadrant to unlock."""
    unlocked = state.unlocked_quadrants_set
    if "NE" not in unlocked:
        return (5, 0)
    if "SW" not in unlocked:
        return (0, 5)
    if "SE" not in unlocked:
        return (5, 5)
    return None


def should_expand(state: GameState) -> bool:
    """Determine whether the agent has enough capital + buffer to buy the next quadrant."""
    cost = expansion_cost(state)
    if cost is None:
        return False
    num_unlocked = len(state.unlocked_quadrants_set)
    buffer = 1000 if num_unlocked >= 2 else 300
    return state.money >= (cost + buffer)


def max_daily_hires(state: GameState) -> int:
    """Dynamically scale daily worker limit based on day, unlocked quadrants, and capital."""
    day = state.day
    money = state.money
    quadrants = len(state.unlocked_quadrants_set)

    if day >= 28:
        return 5
    if day < 6:
        return 4 if money < 100 else 6
    if money >= 5000:
        return 14
    if money >= 1200:
        return 8 + (quadrants * 2)
    if money >= 400:
        return 6 + quadrants
    return 4


def hire_cost(state: GameState) -> int:
    """Return the cost to hire the next farmhand today."""
    idx = state.hires_today
    if idx < len(FIBONACCI):
        return FIBONACCI[idx]
    return 55


def affordable_hires(
    state: GameState,
    max_hires_per_day: int | None = None,
    max_budget: float | None = None,
) -> int:
    """Calculate the number of farmhands affordable under daily limits and budget."""
    limit = (
        max_daily_hires(state)
        if max_hires_per_day is None
        else max_hires_per_day
    )
    hires_today = state.hires_today
    hires_remaining = max(0, limit - hires_today)
    if hires_remaining == 0:
        return 0

    budget = state.money if max_budget is None else min(state.money, max_budget)
    affordable = 0
    running_cost = 0
    for i in range(hires_remaining):
        idx = hires_today + i
        cost = FIBONACCI[idx] if idx < len(FIBONACCI) else 55
        if running_cost + cost <= budget:
            running_cost += cost
            affordable += 1
        else:
            break
    return affordable
