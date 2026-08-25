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
            return (
                fertilized_until_day is not None
                and fertilized_until_day >= current_day
            )
        return False

    def is_unlocked(self, unlocked_quadrants: list[str]) -> bool:
        if self.x < 5 and self.y < 5:
            return "NW" in unlocked_quadrants
        if self.x >= 5 and self.y < 5:
            return "NE" in unlocked_quadrants
        if self.x < 5 and self.y >= 5:
            return "SW" in unlocked_quadrants
        return "SE" in unlocked_quadrants


class Board:
    def __init__(self, state):
        self.state = state
        self.size = state.board_size
        self._tiles: tuple[Tile, ...] = tuple(
            Tile(x, y, cell)
            for y, row in enumerate(state.tiles)
            for x, cell in enumerate(row)
        )

    def get_tile(self, x: int, y: int) -> Tile | None:
        if 0 <= x < self.size and 0 <= y < self.size:
            return self._tiles[y * self.size + x]
        return None

    def all_tiles(self):
        yield from self._tiles

    def empty_tiles(self, only_unlocked: bool = True):
        for tile in self._tiles:
            if tile.empty:
                if not only_unlocked or tile.is_unlocked(
                    self.state.unlocked_quadrants
                ):
                    yield tile

    def plants(self):
        for tile in self._tiles:
            if tile.is_plant:
                yield tile

    def weeds(self, only_unlocked: bool = True):
        for tile in self._tiles:
            if tile.is_weed:
                if not only_unlocked or tile.is_unlocked(
                    self.state.unlocked_quadrants
                ):
                    yield tile

    def crops(self, crop: str):
        for tile in self._tiles:
            if tile.is_plant and tile.crop == crop:
                yield tile

    def harvestable(self, crop: str | None = None):
        day = self.state.day
        for tile in self._tiles:
            if (
                tile.is_plant
                and (crop is None or tile.crop == crop)
                and tile.is_ripe(day)
            ):
                yield tile

    def needs_water(self, crop: str | None = None):
        for tile in self._tiles:
            if (
                tile.is_plant
                and (crop is None or tile.crop == crop)
                and not tile.watered
            ):
                yield tile

    def nearest_to(
        self, x: int, y: int, tiles, exclude_pos: tuple[int, int] | None = None
    ) -> Tile | None:
        best = None
        best_dist = 10**9
        for tile in tiles:
            if exclude_pos and tile.pos == exclude_pos:
                continue
            d = tile.distance(x, y)
            if d < best_dist:
                best_dist = d
                best = tile
        return best

    def nearest(self, tiles):
        return self.nearest_to(self.state.x, self.state.y, tiles)

    def nearest_other(self, tiles):
        return self.nearest_to(
            self.state.x, self.state.y, tiles, exclude_pos=self.state.farmer
        )
