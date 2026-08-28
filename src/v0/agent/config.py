from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.v0.environment.economy import Economy
    from src.v0.environment.state import GameState

__all__ = ["DEFAULT_CONFIG", "AgentConfig"]


@dataclass(slots=True)
class AgentConfig:
    target_crop: str = "MELON"
    seed_target: int = 4
    expand_land: bool = True
    max_hires_per_day: int = 4
    max_quadrants: int = 3

    def get_crop(self, eco: Economy) -> str | None:
        return eco.best_crop()

    def get_max_hires(self, state: GameState) -> int:
        """Dynamically scale daily worker limit based on day, land, and capital."""
        day = state.day
        money = state.money
        quadrants = len(state.unlocked_quadrants_set)

        if day >= 28:
            return 5

        if day < 6:
            return 4 if money < 100 else 6

        if money >= 5000:
            return 14
        elif money >= 1200:
            return 8 + (quadrants * 2)
        elif money >= 400:
            return 6 + quadrants
        return 4


DEFAULT_CONFIG = AgentConfig()
