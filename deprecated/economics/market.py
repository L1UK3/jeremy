from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from deprecated.environment.state import GameState

__all__ = ["Market"]


class Market:
    __slots__ = ("state",)

    HISTORY_LEN: int = 20
    _history: ClassVar[dict[str, deque[int]]] = {}

    def __init__(self, state: GameState) -> None:
        self.state = state
        self._update()

    @classmethod
    def reset_history(cls) -> None:
        """Clear cached market history across episodes/matches."""
        cls._history.clear()

    def _update(self) -> None:
        for item, price in self.state.prices.items():
            if item not in self._history:
                self._history[item] = deque(maxlen=self.HISTORY_LEN)
            self._history[item].append(price)

    def sell_score(self, item: str) -> float:
        """Calculate composite sell score based on current price, short-term trend, and price range."""
        if self.state.inventory(item) == 0:
            return -999999.0
        now = self.state.price(item)
        h = self._history.get(item)
        if not h:
            return float(now) + 50.0
        low = min(h)
        high = max(h)
        trend = (h[-1] - h[0]) if len(h) >= 2 else 0
        norm = 0.5 if high == low else (now - low) / (high - low)
        return float(now) + float(trend) + (norm * 100.0)
