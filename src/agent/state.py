from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GameState:
    raw: dict
    day: int
    player: int
    farm: dict
    private: dict
    market: dict
    money: int
    prices: dict[str, int]
    shed: dict[str, int]
    seeds: dict[str, int]
    tiles: list[list[Any]]
    farmer: tuple[int, int]
    hands: list
    unlocked_quadrants: list[int]
    board_size: int

    @classmethod
    def from_obs(cls, obs):
        player = obs["player"]
        farm = obs["farms"][player]
        private = obs.get("private", {})
        market = obs.get("market", {})

        return cls(
            raw=obs,
            day=obs["day"],
            player=player,
            farm=farm,
            private=private,
            market=market,
            money=farm["money"],
            prices=market.get("prices", {}),
            shed=private.get("shed", {}),
            seeds=private.get("seeds", {}),
            tiles=farm["tiles"],
            farmer=tuple(farm["farmer"]),
            hands=farm.get("farmhands", []),
            unlocked_quadrants=farm["unlocked_quadrants"],
            board_size=len(farm["tiles"]),
        )

    @property
    def x(self):
        return self.farmer[0]

    @property
    def y(self):
        return self.farmer[1]

    @property
    def current_tile(self):
        return self.tiles[self.y][self.x]

    def price(self, item):
        return self.prices.get(item, 0)

    def inventory(self, item):
        return self.shed.get(item, 0)

    def seed_count(self, crop):
        return self.seeds.get(crop, 0)

    def has_seed(self, crop):
        return self.seed_count(crop) > 0

    def can_afford(self, amount):
        return self.money >= amount
