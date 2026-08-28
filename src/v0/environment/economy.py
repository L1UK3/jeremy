from __future__ import annotations

from typing import TYPE_CHECKING

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

if TYPE_CHECKING:
    from src.v0.environment.state import GameState

__all__ = ["Economy"]

CROP_PROPERTIES: dict[str, tuple[int, int]] = {
    crop: (data.get("seed", 0), data.get("max_yield_day", 1))
    for crop, data in CROPS.items()
}
FIBONACCI: tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)


class Economy:
    def __init__(self, state: GameState) -> None:
        self.state = state

    # ----------------------------
    # PRICE
    # ----------------------------

    def price(self, item: str) -> int:
        return self.state.price(item)

    # ----------------------------
    # INVENTORY
    # ----------------------------

    def inventory(self, item: str) -> int:
        return self.state.inventory(item)

    def seeds(self, crop: str) -> int:
        return self.state.seed_count(crop)

    # ----------------------------
    # ROI
    # ----------------------------

    def crop_cost(self, crop: str) -> int:
        return CROPS[crop]["seed"]

    def crop_grow_days(self, crop: str) -> int:
        return CROPS[crop]["max_yield_day"]

    def crop_revenue(self, crop: str) -> int:
        return self.price(crop)

    def crop_profit(self, crop: str) -> float:
        return float(self.crop_revenue(crop) - self.crop_cost(crop))

    def crop_roi(self, crop: str) -> float:
        grow = max(1, self.crop_grow_days(crop))
        return self.crop_profit(crop) / grow

    # ----------------------------
    # BEST CROP
    # ----------------------------

    def best_crop(self) -> str | None:
        best: str | None = None
        best_roi = -1e9
        days_remaining = 30 - self.state.day
        prices = self.state.prices

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

    # ----------------------------
    # BUY SEED
    # ----------------------------

    def should_buy_seed(self, crop: str | None, target_count: int = 1) -> bool:
        if not crop or self.seeds(crop) >= target_count:
            return False

        return self.state.can_afford(self.crop_cost(crop))

    # ----------------------------
    # LAND
    # ----------------------------

    def expansion_cost(self) -> int | None:
        num_unlocked = len(self.state.unlocked_quadrants_set)
        if num_unlocked == 1:
            return 1000
        if num_unlocked == 2:
            return 2000
        if num_unlocked == 3:
            return 4000
        return None

    def next_quadrant_target(self) -> tuple[int, int] | None:
        unlocked = self.state.unlocked_quadrants_set
        if "NE" not in unlocked:
            return (5, 0)
        if "SW" not in unlocked:
            return (0, 5)
        if "SE" not in unlocked:
            return (5, 5)
        return None

    def should_expand(self) -> bool:
        cost = self.expansion_cost()
        if cost is None:
            return False
        return self.state.money >= (cost + 300)

    # ----------------------------
    # FARMHAND
    # ----------------------------

    def hire_cost(self) -> int:
        idx = self.state.hires_today
        if idx < len(FIBONACCI):
            return FIBONACCI[idx]
        return 55

    def should_hire(self, max_hires_per_day: int = 3) -> bool:
        if self.state.hires_today >= max_hires_per_day:
            return False
        return self.state.money >= self.hire_cost()

    def affordable_hires(
        self, max_hires_per_day: int = 3, max_budget: float | None = None
    ) -> int:
        hires_today = self.state.hires_today
        hires_remaining = max(0, max_hires_per_day - hires_today)
        if hires_remaining == 0:
            return 0
        budget = (
            self.state.money
            if max_budget is None
            else min(self.state.money, max_budget)
        )
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
