from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GameState:
    raw: dict
    step: int
    day: int
    hour: int
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
    hires_today: int
    unlocked_quadrants: list[str]
    board_size: int

    @classmethod
    def from_obs(cls, obs: dict) -> "GameState":
        player = obs["player"]
        farm = obs["farms"][player]
        private = obs.get("private", {}) or {}
        market = obs.get("market", {}) or {}

        return cls(
            raw=obs,
            step=obs.get("step", 0),
            day=obs.get("day", 0),
            hour=obs.get("hour", 0),
            player=player,
            farm=farm,
            private=private,
            market=market,
            money=farm.get("money", 0),
            prices=market.get("prices", {}),
            shed=private.get("shed", {}),
            seeds=private.get("seeds", {}),
            tiles=farm.get("tiles", []),
            farmer=tuple(farm.get("farmer", [0, 0])),
            hands=farm.get("hands", []),
            hires_today=farm.get("hires_today", 0),
            unlocked_quadrants=farm.get("unlocked_quadrants", ["NW"]),
            board_size=len(farm.get("tiles", [])),
        )

    @property
    def x(self) -> int:
        return self.farmer[0]

    @property
    def y(self) -> int:
        return self.farmer[1]

    @property
    def current_tile(self) -> Any:
        return self.tiles[self.y][self.x]

    def price(self, item: str) -> int:
        return self.prices.get(item, 0)

    def inventory(self, item: str) -> int:
        return self.shed.get(item, 0)

    def seed_count(self, crop: str) -> int:
        return self.seeds.get(crop, 0)

    def has_seed(self, crop: str) -> bool:
        return self.seed_count(crop) > 0

    def can_afford(self, amount: int) -> bool:
        return self.money >= amount
