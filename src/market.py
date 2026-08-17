from collections import deque


class Market:

    HISTORY = 20

    def __init__(self, state):

        self.state = state

        if not hasattr(Market, "_history"):
            Market._history = {}

        self.history = Market._history

        self._update()

    # ---------------------------------------------------------

    def _update(self):

        for item, price in self.state.prices.items():

            if item not in self.history:
                self.history[item] = deque(maxlen=self.HISTORY)

            self.history[item].append(price)

    # ---------------------------------------------------------

    def price(self, item):

        return self.state.price(item)

    # ---------------------------------------------------------

    def average(self, item):

        h = self.history.get(item)

        if not h:
            return self.price(item)

        return sum(h) / len(h)

    # ---------------------------------------------------------

    def minimum(self, item):

        h = self.history.get(item)

        if not h:
            return self.price(item)

        return min(h)

    # ---------------------------------------------------------

    def maximum(self, item):

        h = self.history.get(item)

        if not h:
            return self.price(item)

        return max(h)

    # ---------------------------------------------------------

    def trend(self, item):

        h = self.history.get(item)

        if h is None:
            return 0

        if len(h) < 2:
            return 0

        return h[-1] - h[0]

    # ---------------------------------------------------------

    def normalized_price(self, item):

        low = self.minimum(item)
        high = self.maximum(item)
        now = self.price(item)

        if high == low:
            return 0.5

        return (now - low) / (high - low)

    # ---------------------------------------------------------

    def expensive(self, item):

        return self.normalized_price(item) >= 0.80

    # ---------------------------------------------------------

    def cheap(self, item):

        return self.normalized_price(item) <= 0.20

    # ---------------------------------------------------------

    def sell_score(self, item):

        if self.state.inventory(item) == 0:
            return -999999

        score = self.price(item)

        score += self.trend(item)

        score += self.normalized_price(item) * 100

        return score

    # ---------------------------------------------------------

    def best_item_to_sell(self):

        best = None
        best_score = -1e9

        for item in self.state.shed.keys():

            s = self.sell_score(item)

            if s > best_score:

                best_score = s
                best = item

        return best
