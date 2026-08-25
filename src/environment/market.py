from collections import deque

from environment.state import GameState


class Market:
    HISTORY_LEN = 20
    _history: dict[str, deque[int]] = {}

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

    def price(self, item: str) -> int:
        return self.state.price(item)


    def minimum(self, item: str) -> int:
        h = self._history.get(item)
        if not h:
            return self.price(item)
        return min(h)

    def maximum(self, item: str) -> int:
        h = self._history.get(item)
        if not h:
            return self.price(item)
        return max(h)

    def trend(self, item: str) -> int:
        h = self._history.get(item)
        if not h or len(h) < 2:
            return 0
        return h[-1] - h[0]

    def normalized_price(self, item: str) -> float:
        low = self.minimum(item)
        high = self.maximum(item)
        now = self.price(item)
        if high == low:
            return 0.5
        return (now - low) / (high - low)

    def sell_score(self, item: str) -> float:
        if self.state.inventory(item) == 0:
            return -999999.0
        score = float(self.price(item))
        score += float(self.trend(item))
        score += self.normalized_price(item) * 100.0
        return score

    def best_item_to_sell(self) -> str | None:
        best = None
        best_score = -1e9
        for item in self.state.shed.keys():
            s = self.sell_score(item)
            if s > best_score:
                best_score = s
                best = item
        return best
