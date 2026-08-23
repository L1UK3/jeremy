from dataclasses import dataclass
from typing import Any

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS


@dataclass(slots=True)
class Tile:
    x: int
    y: int
    data: Any

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    @property
    def empty(self) -> bool:
        return self.data is None

    @property
    def is_plant(self) -> bool:
        return isinstance(self.data, dict) and self.data.get("kind") == "PLANT"

    @property
    def is_weed(self) -> bool:
        return isinstance(self.data, dict) and self.data.get("kind") == "WEED"

    @property
    def crop(self) -> str | None:
        if isinstance(self.data, dict) and self.data.get("kind") == "PLANT":
            return self.data.get("crop")
        return None

    @property
    def watered(self) -> bool:
        if isinstance(self.data, dict) and self.data.get("kind") == "PLANT":
            return bool(self.data.get("watered_today", False))
        return False

    @property
    def yield_units(self) -> int:
        if isinstance(self.data, dict) and self.data.get("kind") == "PLANT":
            return int(self.data.get("yield_units", 0))
        return 0

    @property
    def planted_day(self) -> int | None:
        if isinstance(self.data, dict) and self.data.get("kind") == "PLANT":
            return self.data.get("planted_day")
        return None

    def age(self, current_day: int) -> int:
        if self.planted_day is None:
            return 0
        return current_day - self.planted_day

    def is_ripe(self, current_day: int) -> bool:
        if not self.is_plant or self.yield_units <= 0:
            return False
        if self.crop and self.crop in CROPS:
            max_yield_day = CROPS[self.crop].get("max_yield_day", 0)
            return self.age(current_day) >= max_yield_day
        return True

    def distance(self, x: int, y: int) -> int:
        return abs(self.x - x) + abs(self.y - y)

    def is_fertilized(self, current_day: int) -> bool:
        if isinstance(self.data, dict) and self.data.get("kind") == "PLANT":
            fertilized_until_day = self.data.get("fertilized_until_day")
            return fertilized_until_day is not None and fertilized_until_day >= current_day
        return False


class Board:
    def __init__(self, state):
        self.state = state
        self.tiles = state.tiles
        self.size = state.board_size

    def all_tiles(self):
        for y in range(self.size):
            for x in range(self.size):
                yield Tile(x, y, self.tiles[y][x])

    def empty_tiles(self):
        for tile in self.all_tiles():
            if tile.empty:
                yield tile

    def plants(self):
        for tile in self.all_tiles():
            if tile.is_plant:
                yield tile

    def weeds(self):
        for tile in self.all_tiles():
            if tile.is_weed:
                yield tile

    def crops(self, crop: str):
        for tile in self.plants():
            if tile.crop == crop:
                yield tile

    def harvestable(self, crop: str | None = None):
        tiles = self.crops(crop) if crop else self.plants()
        for tile in tiles:
            if tile.is_ripe(self.state.day):
                yield tile

    def needs_water(self, crop: str | None = None):
        tiles = self.crops(crop) if crop else self.plants()
        for tile in tiles:
            if not tile.watered:
                yield tile

    def nearest(self, tiles):
        fx, fy = self.state.farmer
        best = None
        best_dist = 10**9

        for tile in tiles:
            d = tile.distance(fx, fy)
            if d < best_dist:
                best_dist = d
                best = tile

        return best

    def nearest_other(self, tiles):
        """Find the nearest tile excluding the farmer's current coordinates."""
        fx, fy = self.state.farmer
        other_tiles = (t for t in tiles if t.pos != (fx, fy))
        return self.nearest(other_tiles)
