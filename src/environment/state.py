from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .board import SHED_ACCESS_TILES

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
    tiles: list[list[dict[str, Any] | None]]
    farmer: tuple[int, int]
    hands: list[list[int]]
    hires_today: int
    unlocked_quadrants: list[str]
    board_size: int
    unlocked_quadrants_set: frozenset[str]

    @classmethod
    def from_obs(cls, obs: dict[str, Any]) -> GameState:
        player: int = obs["player"]
        farm: dict[str, Any] = obs["farms"][player]
        private: dict[str, Any] = obs.get("private") or {}
        market: dict[str, Any] = obs.get("market") or {}
        unlocked: list[str] = farm.get("unlocked_quadrants", ["NW"])
        farmer_raw = farm.get("farmer", (0, 0))

        return cls(
            raw=obs,
            step=obs.get("step", 0),
            day=max(int(obs.get("day") or 0), int(obs.get("step") or 0) // 24),
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
        return self.seeds.get(crop, 0) > 0

    def can_afford(self, amount: int) -> bool:
        return self.money >= amount

    def worker_inventory(self, idx: int = 0) -> dict[str, int]:
        invs = self.private.get("inventories")
        if (
            isinstance(invs, list)
            and idx < len(invs)
            and isinstance(invs[idx], dict)
        ):
            return invs[idx]
        return {}

    def is_shed_adjacent(self, x: int, y: int) -> bool:
        return (x, y) in SHED_ACCESS_TILES
