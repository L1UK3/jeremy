from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


class Economy:

    def __init__(self, state):
        self.state = state

    # ----------------------------
    # PRICE
    # ----------------------------

    def price(self, item):
        return self.state.price(item)

    # ----------------------------
    # INVENTORY
    # ----------------------------

    def inventory(self, item):
        return self.state.inventory(item)

    def seeds(self, crop):
        return self.state.seed_count(crop)

    # ----------------------------
    # ROI
    # ----------------------------

    def crop_cost(self, crop):
        return CROPS[crop]["seed"]

    def crop_grow_days(self, crop):
        return CROPS[crop]["max_yield_day"]

    def crop_revenue(self, crop):
        return self.price(crop)

    def crop_profit(self, crop):
        return self.crop_revenue(crop) - self.crop_cost(crop)

    def crop_roi(self, crop):

        grow = max(1, self.crop_grow_days(crop))

        return self.crop_profit(crop) / grow

    # ----------------------------
    # BEST CROP
    # ----------------------------

    def best_crop(self):

        best = None
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

    def should_sell(self, item):

        if self.inventory(item) == 0:
            return False

        return self.price(item) > self.crop_cost(item)

    # ----------------------------
    # BUY SEED
    # ----------------------------

    def should_buy_seed(self, crop):

        if self.seeds(crop) > 0:
            return False

        return self.state.can_afford(
            self.crop_cost(crop)
        )

    # ----------------------------
    # LAND
    # ----------------------------

    def should_expand(self):

        return self.state.money > 5000

    # ----------------------------
    # FARMHAND
    # ----------------------------

    def should_hire(self):

        return self.state.money > 10000
