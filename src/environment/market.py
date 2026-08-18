from collections import deque


class Market:
    HISTORY_LEN = 20

    def __init__(self, state):
        self.state = state
        if not hasattr(Market, "_history"):
            Market._history = {}
        self.history = Market._history
        self._update()

    def _update(self) -> None:
        for item, price in self.state.prices.items():
            if item not in self.history:
                self.history[item] = deque(maxlen=self.HISTORY_LEN)
            self.history[item].append(price)

    def price(self, item: str) -> int:
        return self.state.price(item)

    def average(self, item: str) -> float:
        h = self.history.get(item)
        if not h:
            return float(self.price(item))
        return sum(h) / len(h)

    def minimum(self, item: str) -> int:
        h = self.history.get(item)
        if not h:
            return self.price(item)
        return min(h)

    def maximum(self, item: str) -> int:
        h = self.history.get(item)
        if not h:
            return self.price(item)
        return max(h)

    def trend(self, item: str) -> int:
        h = self.history.get(item)
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

    def expensive(self, item: str) -> bool:
        return self.normalized_price(item) >= 0.80

    def cheap(self, item: str) -> bool:
        return self.normalized_price(item) <= 0.20

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
