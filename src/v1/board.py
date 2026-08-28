from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

if TYPE_CHECKING:
    from state import GameState

__all__ = ["Board", "Tile", "manhattan_distance", "step_toward"]

CROP_SPECS: dict[str, tuple[int, int, int, bool]] = {
    crop: (
        data.get("first_yield_day", 0),
        data.get("max_yield_day", 0),
        data.get("max_yield", 0),
        bool(data.get("ongoing", False)),
    )
    for crop, data in CROPS.items()
}


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Compute Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)


def step_toward(fx: int, fy: int, tx: int, ty: int) -> str:
    """Compute single cardinal step direction from (fx, fy) toward (tx, ty)."""
    if fx > tx:
        return "WEST"
    if fx < tx:
        return "EAST"
    if fy > ty:
        return "NORTH"
    if fy < ty:
        return "SOUTH"
    return "PASS"


STATIC_POS: tuple[tuple[int, int], ...] = tuple(
    (x, y) for y in range(10) for x in range(10)
)
STATIC_QUADRANTS: tuple[str, ...] = tuple(
    "NW"
    if x < 5 and y < 5
    else ("NE" if x >= 5 and y < 5 else ("SW" if x < 5 and y >= 5 else "SE"))
    for y in range(10)
    for x in range(10)
)


class Tile:
    __slots__ = (
        "animal",
        "cared_today",
        "consecutive_unfed",
        "crop",
        "data",
        "empty",
        "fed_today",
        "fertilized_until_day",
        "fertilizer_available",
        "is_animal",
        "is_plant",
        "is_weed",
        "kind",
        "pending_care_bonus",
        "planted_day",
        "pos",
        "quadrant",
        "watered",
        "x",
        "y",
        "yield_units",
    )

    def __init__(
        self,
        x: int,
        y: int,
        data: Any,
        pos: tuple[int, int] | None = None,
        quadrant: str | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.data = data
        self.pos = pos if pos is not None else (x, y)
        self.quadrant = (
            quadrant
            if quadrant is not None
            else (
                "NW"
                if x < 5 and y < 5
                else (
                    "NE"
                    if x >= 5 and y < 5
                    else ("SW" if x < 5 and y >= 5 else "SE")
                )
            )
        )
        if data is None:
            self.empty = True
            self.is_plant = False
            self.is_weed = False
            self.is_animal = False
            self.animal = None
            self.kind = None
            self.crop = None
            self.watered = False
            self.yield_units = 0
            self.planted_day = None
            self.fertilized_until_day = None
            self.fed_today = False
            self.cared_today = False
            self.fertilizer_available = False
            self.consecutive_unfed = 0
            self.pending_care_bonus = 0
        elif isinstance(data, dict):
            kind = data.get("kind")
            self.kind = kind
            if kind == "PLANT":
                self.empty = False
                self.is_plant = True
                self.is_weed = False
                self.is_animal = False
                self.animal = None
                self.crop = data.get("crop")
                self.watered = bool(data.get("watered_today", False))
                self.yield_units = int(data.get("yield_units", 0))
                self.planted_day = data.get("planted_day")
                self.fertilized_until_day = data.get("fertilized_until_day")
                self.fed_today = False
                self.cared_today = False
                self.fertilizer_available = False
                self.consecutive_unfed = 0
                self.pending_care_bonus = 0
            elif kind == "WEED":
                self.empty = False
                self.is_plant = False
                self.is_weed = True
                self.is_animal = False
                self.animal = None
                self.crop = None
                self.watered = False
                self.yield_units = 0
                self.planted_day = None
                self.fertilized_until_day = None
                self.fed_today = False
                self.cared_today = False
                self.fertilizer_available = False
                self.consecutive_unfed = 0
                self.pending_care_bonus = 0
            elif kind in ("PASTURE", "COOP") or "animal" in data:
                animal_name = data.get("animal")
                self.empty = False
                self.is_plant = False
                self.is_weed = False
                self.is_animal = bool(animal_name)
                self.animal = animal_name
                self.crop = None
                self.watered = False
                self.yield_units = int(data.get("yield_units", 0))
                self.planted_day = data.get("placed_day")
                self.fertilized_until_day = None
                self.fed_today = bool(data.get("fed_today", False))
                self.cared_today = bool(data.get("cared_today", False))
                self.fertilizer_available = bool(
                    data.get("fertilizer_available", False)
                )
                self.consecutive_unfed = int(data.get("consecutive_unfed", 0))
                self.pending_care_bonus = int(data.get("pending_care_bonus", 0))
            else:
                self.empty = False
                self.is_plant = False
                self.is_weed = False
                self.is_animal = False
                self.animal = None
                self.crop = None
                self.watered = False
                self.yield_units = 0
                self.planted_day = None
                self.fertilized_until_day = None
                self.fed_today = False
                self.cared_today = False
                self.fertilizer_available = False
                self.consecutive_unfed = 0
                self.pending_care_bonus = 0
        else:
            self.empty = False
            self.is_plant = False
            self.is_weed = False
            self.is_animal = False
            self.animal = None
            self.kind = None
            self.crop = None
            self.watered = False
            self.yield_units = 0
            self.planted_day = None
            self.fertilized_until_day = None
            self.fed_today = False
            self.cared_today = False
            self.fertilizer_available = False
            self.consecutive_unfed = 0
            self.pending_care_bonus = 0

    def age(self, current_day: int) -> int:
        if self.planted_day is None:
            return 0
        return current_day - self.planted_day

    def is_ripe(self, current_day: int) -> bool:
        if not (self.is_plant and self.yield_units > 0 and self.crop):
            return False
        spec = CROP_SPECS.get(self.crop)
        if spec is None:
            return False
        age = (
            current_day - self.planted_day
            if self.planted_day is not None
            else 0
        )
        if age < spec[0]:  # first_yield_day
            return False
        return (
            spec[3]  # ongoing
            or self.yield_units >= spec[2]  # max_yield
            or age >= spec[1]  # max_yield_day
        )

    def distance(self, x: int, y: int) -> int:
        return abs(self.x - x) + abs(self.y - y)

    def is_fertilized(self, current_day: int) -> bool:
        return (
            self.fertilized_until_day is not None
            and self.fertilized_until_day >= current_day
        )

    def is_unlocked(
        self, unlocked_quadrants: list[str] | set[str] | frozenset[str]
    ) -> bool:
        return self.quadrant in unlocked_quadrants


EMPTY_TILES: tuple[Tile, ...] = tuple(
    Tile(x, y, None, STATIC_POS[i], STATIC_QUADRANTS[i])
    for i, (x, y) in enumerate(STATIC_POS)
)


class Board:
    def __init__(self, state: GameState) -> None:
        self.state = state
        self.size = state.board_size
        unlocked = state.unlocked_quadrants_set
        day = state.day

        tiles_list: list[Tile] = []
        empty_unlocked: list[Tile] = []
        all_empty: list[Tile] = []
        plants: list[Tile] = []
        weeds_unlocked: list[Tile] = []
        all_weeds: list[Tile] = []
        needs_water: list[Tile] = []
        harvestable: list[Tile] = []
        animals: list[Tile] = []
        needs_feed: list[Tile] = []
        needs_care: list[Tile] = []
        fertilizer_available: list[Tile] = []

        idx = 0
        for y, row in enumerate(state.tiles):
            for x, cell in enumerate(row):
                if cell is None and idx < 100:
                    tile = EMPTY_TILES[idx]
                    quad = tile.quadrant
                    tiles_list.append(tile)
                    all_empty.append(tile)
                    if quad in unlocked:
                        empty_unlocked.append(tile)
                    idx += 1
                    continue

                pos = STATIC_POS[idx] if idx < 100 else (x, y)
                quad = (
                    STATIC_QUADRANTS[idx]
                    if idx < 100
                    else (
                        "NW"
                        if x < 5 and y < 5
                        else (
                            "NE"
                            if x >= 5 and y < 5
                            else ("SW" if x < 5 and y >= 5 else "SE")
                        )
                    )
                )
                idx += 1

                tile = Tile(x, y, cell, pos, quad)
                tiles_list.append(tile)

                is_unl = quad in unlocked
                if tile.empty:
                    all_empty.append(tile)
                    if is_unl:
                        empty_unlocked.append(tile)
                elif tile.is_plant:
                    plants.append(tile)
                    if not tile.watered:
                        needs_water.append(tile)
                    if tile.is_ripe(day):
                        harvestable.append(tile)
                elif tile.is_weed:
                    all_weeds.append(tile)
                    if is_unl:
                        weeds_unlocked.append(tile)
                elif tile.is_animal:
                    animals.append(tile)
                    if not tile.fed_today:
                        needs_feed.append(tile)
                    if not tile.cared_today:
                        needs_care.append(tile)
                    if tile.fertilizer_available:
                        fertilizer_available.append(tile)
                    if tile.yield_units > 0:
                        harvestable.append(tile)

        self._tiles: tuple[Tile, ...] = tuple(tiles_list)
        self._empty_unlocked = empty_unlocked
        self._all_empty = all_empty
        self._plants = plants
        self._weeds_unlocked = weeds_unlocked
        self._all_weeds = all_weeds
        self._needs_water = needs_water
        self._harvestable = harvestable
        self._animals = animals
        self._needs_feed = needs_feed
        self._needs_care = needs_care
        self._fertilizer_available = fertilizer_available

    @property
    def empty_tiles_count(self) -> int:
        return len(self._empty_unlocked)

    def get_tile(self, x: int, y: int) -> Tile | None:
        if 0 <= x < self.size and 0 <= y < self.size:
            return self._tiles[y * self.size + x]
        return None

    def all_tiles(self) -> tuple[Tile, ...]:
        return self._tiles

    def empty_tiles(self, only_unlocked: bool = True) -> list[Tile]:
        return self._empty_unlocked if only_unlocked else self._all_empty

    def tiles(self) -> list[Tile]:
        return self._tiles

    def tile(self, x: int, y: int) -> Tile | None:
        if 0 <= x < 10 and 0 <= y < 10:
            return self._tiles[y * 10 + x]
        return None

    def plants(self) -> list[Tile]:
        return self._plants

    def weeds(self, only_unlocked: bool = True) -> list[Tile]:
        return self._weeds_unlocked if only_unlocked else self._all_weeds

    def crops(self, crop: str) -> list[Tile]:
        return [t for t in self._plants if t.crop == crop]

    def harvestable(self, crop: str | None = None) -> list[Tile]:
        if crop is None:
            return self._harvestable
        return [t for t in self._harvestable if t.crop == crop]

    def needs_water(self) -> list[Tile]:
        return self._needs_water

    def animals(self) -> list[Tile]:
        return self._animals

    def needs_feed(self) -> list[Tile]:
        return self._needs_feed

    def needs_care(self) -> list[Tile]:
        return self._needs_care

    def has_fertilizer_tiles(self) -> list[Tile]:
        return self._fertilizer_available

    def nearest_to(
        self,
        x: int,
        y: int,
        tiles: Iterable[Tile],
        exclude_pos: tuple[int, int] | None = None,
    ) -> Tile | None:
        best = None
        best_dist = 10**9
        for tile in tiles:
            if exclude_pos and tile.pos == exclude_pos:
                continue
            d = abs(tile.x - x) + abs(tile.y - y)
            if d < best_dist:
                best_dist = d
                best = tile
        return best

    def nearest(self, tiles: Iterable[Tile]) -> Tile | None:
        return self.nearest_to(self.state.x, self.state.y, tiles)

    def nearest_other(self, tiles: Iterable[Tile]) -> Tile | None:
        return self.nearest_to(
            self.state.x, self.state.y, tiles, exclude_pos=self.state.farmer
        )

    def nearest_shed(self, x: int, y: int) -> tuple[int, int]:
        """Return nearest shed interaction coordinate, preferring unlocked quadrants."""
        shed_candidates = [(4, 4), (5, 4), (4, 5), (5, 5)]
        best = (4, 4)
        best_dist = 10**9
        for sx, sy in shed_candidates:
            if self.state.is_tile_unlocked(sx, sy) or (sx, sy) == (4, 4):
                d = abs(sx - x) + abs(sy - y)
                if d < best_dist:
                    best_dist = d
                    best = (sx, sy)
        return best
