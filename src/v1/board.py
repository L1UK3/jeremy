from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

if TYPE_CHECKING:
    from state import GameState

__all__ = [
    "SHED_ACCESS_TILES",
    "Board",
    "Tile",
    "manhattan_distance",
    "step_toward",
]

CROP_SPECS: dict[str, tuple[int, int, int, bool]] = {
    crop: (
        data.get("first_yield_day", 0),
        data.get("max_yield_day", 0),
        data.get("max_yield", 0),
        bool(data.get("ongoing", False)),
    )
    for crop, data in CROPS.items()
}

SHED_ACCESS_TILES: tuple[tuple[int, int], ...] = (
    (4, 4),
    (5, 4),
    (4, 5),
    (5, 5),
)

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


class Tile:
    __slots__ = (
        "animal",
        "cared_today",
        "consecutive_unfed",
        "crop",
        "empty",
        "fed_today",
        "fertilizer_available",
        "is_animal",
        "is_plant",
        "is_weed",
        "kind",
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
        data: dict[str, Any] | None,
        pos: tuple[int, int] | None = None,
        quadrant: str | None = None,
    ) -> None:
        self.x = x
        self.y = y
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

        if not data:
            self.empty = True
            self.kind = None
            self.is_plant = False
            self.is_weed = False
            self.is_animal = False
            self.animal = None
            self.crop = None
            self.watered = False
            self.yield_units = 0
            self.planted_day = None
            self.fed_today = False
            self.cared_today = False
            self.fertilizer_available = False
            self.consecutive_unfed = 0
            return

        self.empty = False
        if isinstance(data, dict):
            kind = data.get("kind")
            self.kind = kind
            if kind == "PLANT":
                self.is_plant = True
                self.is_weed = False
                self.is_animal = False
                self.animal = None
                self.crop = data.get("crop")
                self.watered = bool(data.get("watered_today", False))
                self.yield_units = int(data.get("yield_units", 0))
                self.planted_day = data.get("planted_day")
                self.fed_today = False
                self.cared_today = False
                self.fertilizer_available = False
                self.consecutive_unfed = 0
            elif kind == "WEED":
                self.is_plant = False
                self.is_weed = True
                self.is_animal = False
                self.animal = None
                self.crop = None
                self.watered = False
                self.yield_units = 0
                self.planted_day = None
                self.fed_today = False
                self.cared_today = False
                self.fertilizer_available = False
                self.consecutive_unfed = 0
            elif kind in ("PASTURE", "COOP") or "animal" in data:
                animal_name = data.get("animal")
                self.is_plant = False
                self.is_weed = False
                self.is_animal = bool(animal_name)
                self.animal = animal_name
                self.crop = None
                self.watered = False
                self.yield_units = int(data.get("yield_units", 0))
                self.planted_day = data.get("placed_day")
                self.fed_today = bool(data.get("fed_today", False))
                self.cared_today = bool(data.get("cared_today", False))
                self.fertilizer_available = bool(
                    data.get("fertilizer_available", False)
                )
                self.consecutive_unfed = int(data.get("consecutive_unfed", 0))
            else:
                self.is_plant = False
                self.is_weed = False
                self.is_animal = False
                self.animal = None
                self.crop = None
                self.watered = False
                self.yield_units = 0
                self.planted_day = None
                self.fed_today = False
                self.cared_today = False
                self.fertilizer_available = False
                self.consecutive_unfed = 0
        elif isinstance(data, str):
            self.kind = data
            self.is_plant = False
            self.is_weed = data == "WEED"
            self.is_animal = False
            self.animal = None
            self.crop = None
            self.watered = False
            self.yield_units = 0
            self.planted_day = None
            self.fed_today = False
            self.cared_today = False
            self.fertilizer_available = False
            self.consecutive_unfed = 0
        else:
            self.kind = None
            self.is_plant = False
            self.is_weed = False
            self.is_animal = False
            self.animal = None
            self.crop = None
            self.watered = False
            self.yield_units = 0
            self.planted_day = None
            self.fed_today = False
            self.cared_today = False
            self.fertilizer_available = False
            self.consecutive_unfed = 0

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
        if age < spec[0]:
            return False
        return spec[3] or self.yield_units >= spec[2] or age >= spec[1]


EMPTY_TILES: tuple[Tile, ...] = tuple(
    Tile(x, y, None, STATIC_POS[i], STATIC_QUADRANTS[i])
    for i, (x, y) in enumerate(STATIC_POS)
)


class Board:
    __slots__ = (
        "_animals",
        "_empty_unlocked",
        "_fertilizer_available",
        "_harvestable",
        "_needs_care",
        "_needs_feed",
        "_needs_water",
        "_tiles",
        "_weeds_unlocked",
        "size",
        "state",
    )

    def __init__(self, state: GameState) -> None:
        self.state = state
        self.size = state.board_size
        unlocked = state.unlocked_quadrants_set
        day = state.day

        tiles_list: list[Tile] = []
        empty_unlocked: list[Tile] = []
        weeds_unlocked: list[Tile] = []
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
                    tiles_list.append(tile)
                    if tile.quadrant in unlocked:
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
                    if is_unl:
                        empty_unlocked.append(tile)
                elif tile.is_plant:
                    if not tile.watered:
                        needs_water.append(tile)
                    if tile.is_ripe(day):
                        harvestable.append(tile)
                elif tile.is_weed:
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

        self._tiles = tuple(tiles_list)
        self._empty_unlocked = empty_unlocked
        self._weeds_unlocked = weeds_unlocked
        self._needs_water = needs_water
        self._harvestable = harvestable
        self._animals = animals
        self._needs_feed = needs_feed
        self._needs_care = needs_care
        self._fertilizer_available = fertilizer_available

    @property
    def empty_tiles_count(self) -> int:
        return len(self._empty_unlocked)

    def tile(self, x: int, y: int) -> Tile | None:
        if 0 <= x < 10 and 0 <= y < 10:
            return self._tiles[y * 10 + x]
        return None

    def get_tile(self, x: int, y: int) -> Tile | None:
        return self.tile(x, y)

    def all_tiles(self) -> tuple[Tile, ...]:
        return self._tiles

    def empty_tiles(self, only_unlocked: bool = True) -> list[Tile]:
        return self._empty_unlocked

    def weeds(self, only_unlocked: bool = True) -> list[Tile]:
        return self._weeds_unlocked

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
        best: Tile | None = None
        best_dist = 10**9
        for tile in tiles:
            if exclude_pos and tile.pos == exclude_pos:
                continue
            d = abs(tile.x - x) + abs(tile.y - y)
            if d < best_dist:
                best_dist = d
                best = tile
        return best

    def nearest_shed(self, x: int, y: int) -> tuple[int, int]:
        """Return nearest shed interaction coordinate, preferring unlocked quadrants."""
        best = (4, 4)
        best_dist = 10**9
        for sx, sy in SHED_ACCESS_TILES:
            if self.state.is_tile_unlocked(sx, sy) or (sx, sy) == (4, 4):
                d = abs(sx - x) + abs(sy - y)
                if d < best_dist:
                    best_dist = d
                    best = (sx, sy)
        return best
