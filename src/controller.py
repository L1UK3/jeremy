from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from economy import Economy
    from state import GameState


__all__ = ["AgentController"]


@dataclass(slots=True)
class AgentController:
    expand_land: bool = True

    def get_crop(self, eco: Economy) -> str | None:
        """Determines the best crop for the agent to focus on to make the most profit.

        returns:
            - {str | None} - recommended crop type
        """
        return eco.best_crop()

    def get_max_hires(self, state: GameState) -> int:
        """
        dynamically scale daily worker limit based on:
        - day
        - unlocked quadrants
        - capital

        returns:
            - {int} - maxmimum recommended daily worker limit
        """
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

    def get_max_quadrants(self, state: GameState, max_limit: int = 3) -> int:
        """Dynamically scale the quadrant limit based on day and capital.

        - Day < 8: 1 quadrant (NW)
        - Day 8 to 21: max 2 quadrants (NW + NE)
        - Day 22+: max 3 quadrants (NW + NE + SW) when capital allows

        args:
            - max_limit {int} - maximum allowed quadrants (default: 3)
        returns:
            - {int} - maximum recommended quadrants
        """
        if not self.expand_land:
            return 1

        day = state.day
        money = state.money

        if day < 8:
            return 1
        if day < 22 or money < 3000:
            return min(2, max_limit)
        return min(3, max_limit)
