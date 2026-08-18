from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


class Economy:
    def __init__(self, state):
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
        for crop in CROPS.keys():
            roi = self.crop_roi(crop)
            if roi > best_roi:
                best_roi = roi
                best = crop
        return best

    # ----------------------------
    # SELL
    # ----------------------------

    def should_sell(self, item: str) -> bool:
        if self.inventory(item) == 0:
            return False

        return self.price(item) > self.crop_cost(item)

    # ----------------------------
    # BUY SEED
    # ----------------------------

    def should_buy_seed(self, crop: str) -> bool:
        if self.seeds(crop) > 0:
            return False

        return self.state.can_afford(self.crop_cost(crop))

    # ----------------------------
    # LAND
    # ----------------------------

    def should_expand(self) -> bool:
        return self.state.money > 5000

    # ----------------------------
    # FARMHAND
    # ----------------------------

    def should_hire(self) -> bool:
        return self.state.money > 10000
