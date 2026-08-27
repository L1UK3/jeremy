from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["GameState"]


@dataclass(slots=True)
class GameState:
    raw: dict[str, Any]
    step: int
    day: int
    hour: int
    player: int
    farm: dict[str, Any]
    private: dict[str, Any]
    market: dict[str, Any]
    money: int
    prices: dict[str, int]
    shed: dict[str, int]
    seeds: dict[str, int]
    tiles: list[list[Any]]
    farmer: tuple[int, int]
    hands: list[list[int]]
    hires_today: int
    unlocked_quadrants: list[str]
    board_size: int
    unlocked_quadrants_set: frozenset[str]

    @classmethod
    def from_obs(cls, obs: dict[str, Any]) -> GameState:
        player = obs["player"]
        farm = obs["farms"][player]
        private = obs.get("private", {}) or {}
        market = obs.get("market", {}) or {}
        unlocked = farm.get("unlocked_quadrants", ["NW"])
        farmer_raw = farm.get("farmer", (0, 0))

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
            farmer=(farmer_raw[0], farmer_raw[1]),
            hands=farm.get("hands", []),
            hires_today=farm.get("hires_today", 0),
            unlocked_quadrants=unlocked,
            board_size=len(farm.get("tiles", [])),
            unlocked_quadrants_set=frozenset(unlocked),
        )

    @property
    def x(self) -> int:
        return self.farmer[0]

    @property
    def y(self) -> int:
        return self.farmer[1]

    @property
    def current_tile(self) -> Any:
        return self.tiles[self.farmer[1]][self.farmer[0]]

    def is_quadrant_unlocked(self, quadrant: str) -> bool:
        return quadrant in self.unlocked_quadrants_set

    def is_tile_unlocked(self, x: int, y: int) -> bool:
        if x < 5 and y < 5:
            return "NW" in self.unlocked_quadrants_set
        if x >= 5 and y < 5:
            return "NE" in self.unlocked_quadrants_set
        if x < 5 and y >= 5:
            return "SW" in self.unlocked_quadrants_set
        return "SE" in self.unlocked_quadrants_set

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

    def has_fertilizer(self) -> bool:
        return self.inventory("fertilizer") > 0
