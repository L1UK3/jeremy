from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, NamedTuple

from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

if TYPE_CHECKING:
    from state import GameState

__all__ = [
    "SHED_ACCESS_TILES",
    "Board",
    "CropSpec",
    "Tile",
    "manhattan_distance",
    "step_toward",
]


class CropSpec(NamedTuple):
    """Immutable specifications for a crop's growth lifecycle."""

    first_yield_day: int
    max_yield_day: int
    max_yield: int
    ongoing: bool


CROP_SPECS: dict[str, CropSpec] = {
    crop: CropSpec(
        first_yield_day=int(data.get("first_yield_day", 0)),
        max_yield_day=int(data.get("max_yield_day", 0)),
        max_yield=int(data.get("max_yield", 0)),
        ongoing=bool(data.get("ongoing", False)),
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
    """Encapsulates a grid coordinate and parsed state attributes."""

    __slots__ = (
        "animal",
        "cared_today",
        "consecutive_unfed",
        "consecutive_unwatered",
        "crop",
        "empty",
        "empty_pasture",
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
        data: dict[str, Any] | str | None,
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

        # Baseline default attributes
        self.empty = False
        self.empty_pasture = False
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
        self.consecutive_unwatered = 0

        if not data:
            self.empty = True
            return

        if isinstance(data, dict):
            kind = data.get("kind")
            self.kind = kind
            if kind == "PLANT":
                self.is_plant = True
                self.crop = data.get("crop")
                self.watered = bool(data.get("watered_today", False))
                self.yield_units = int(data.get("yield_units", 0))
                self.planted_day = data.get("planted_day")
                self.consecutive_unwatered = int(
                    data.get("consecutive_unwatered", 0)
                )
            elif kind == "WEED":
                self.is_weed = True
            elif kind in ("PASTURE", "COOP") or "animal" in data:
                animal_name = data.get("animal")
                if animal_name:
                    self.is_animal = True
                    self.animal = animal_name
                    self.yield_units = int(data.get("yield_units", 0))
                    self.planted_day = data.get("placed_day")
                    self.fed_today = bool(data.get("fed_today", False))
                    self.cared_today = bool(data.get("cared_today", False))
                    self.fertilizer_available = bool(
                        data.get("fertilizer_available", False)
                    )
                    self.consecutive_unfed = int(
                        data.get("consecutive_unfed", 0)
                    )
                else:
                    self.empty_pasture = True
        elif isinstance(data, str):
            self.kind = data
            self.is_weed = data == "WEED"

    def distance(self, x: int, y: int) -> int:
        """Calculate Manhattan distance from this tile to coordinate (x, y)."""
        return abs(self.x - x) + abs(self.y - y)

    def age(self, current_day: int) -> int:
        """Calculate elapsed days since planting or placement."""
        return (
            current_day - self.planted_day
            if self.planted_day is not None
            else 0
        )

    def is_unlocked(self, unlocked_quadrants: Iterable[str]) -> bool:
        """Check if this tile resides in one of the unlocked quadrants."""
        return self.quadrant in unlocked_quadrants

    def is_ripe(self, current_day: int) -> bool:
        """Check if a plant has reached harvestable maturity or ongoing yield threshold."""
        if not (self.is_plant and self.yield_units > 0 and self.crop):
            return False
        spec = CROP_SPECS.get(self.crop)
        if spec is None:
            return False
        plant_age = self.age(current_day)
        if plant_age < spec.first_yield_day:
            return False
        return (
            spec.ongoing
            or self.yield_units >= spec.max_yield
            or plant_age >= spec.max_yield_day
        )


EMPTY_TILES: tuple[Tile, ...] = tuple(
    Tile(x, y, None, STATIC_POS[i], STATIC_QUADRANTS[i])
    for i, (x, y) in enumerate(STATIC_POS)
)


class Board:
    """Spatial grid indexer and categorized query manager for the farm board."""

    __slots__ = (
        "_animals",
        "_empty_all",
        "_empty_pastures_all",
        "_empty_pastures_unlocked",
        "_empty_unlocked",
        "_fertilizer_available",
        "_harvestable",
        "_needs_care",
        "_needs_feed",
        "_needs_water",
        "_needs_water_urgent",
        "_plants",
        "_tiles",
        "_weeds_all",
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
        empty_all: list[Tile] = []
        empty_unlocked: list[Tile] = []
        empty_pastures_all: list[Tile] = []
        empty_pastures_unlocked: list[Tile] = []
        weeds_all: list[Tile] = []
        weeds_unlocked: list[Tile] = []
        plants: list[Tile] = []
        needs_water: list[Tile] = []
        needs_water_urgent: list[Tile] = []
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
                    empty_all.append(tile)
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
                    empty_all.append(tile)
                    if is_unl:
                        empty_unlocked.append(tile)
                elif tile.empty_pasture:
                    empty_pastures_all.append(tile)
                    if is_unl:
                        empty_pastures_unlocked.append(tile)
                elif tile.is_weed:
                    weeds_all.append(tile)
                    if is_unl:
                        weeds_unlocked.append(tile)
                elif tile.is_plant:
                    plants.append(tile)
                    if not tile.watered:
                        needs_water.append(tile)
                        if tile.consecutive_unwatered >= 1:
                            needs_water_urgent.append(tile)
                    if tile.is_ripe(day):
                        harvestable.append(tile)
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
        self._empty_all = empty_all
        self._empty_unlocked = empty_unlocked
        self._empty_pastures_all = empty_pastures_all
        self._empty_pastures_unlocked = empty_pastures_unlocked
        self._weeds_all = weeds_all
        self._weeds_unlocked = weeds_unlocked
        self._plants = plants
        self._needs_water = needs_water
        self._needs_water_urgent = needs_water_urgent
        self._harvestable = harvestable
        self._animals = animals
        self._needs_feed = needs_feed
        self._needs_care = needs_care
        self._fertilizer_available = fertilizer_available

    @property
    def empty_tiles_count(self) -> int:
        """Count of empty tiles on currently unlocked quadrants."""
        return len(self._empty_unlocked)

    def tile(self, x: int, y: int) -> Tile | None:
        """Get Tile at coordinate (x, y) or None if out of bounds."""
        if 0 <= x < 10 and 0 <= y < 10:
            return self._tiles[y * 10 + x]
        return None

    def get_tile(self, x: int, y: int) -> Tile | None:
        """Alias for tile(x, y)."""
        return self.tile(x, y)

    def all_tiles(self) -> tuple[Tile, ...]:
        """Return all 100 tiles across the board."""
        return self._tiles

    def empty_tiles(self, only_unlocked: bool = True) -> list[Tile]:
        """Return empty tiles, optionally filtering to unlocked quadrants only."""
        return self._empty_unlocked if only_unlocked else self._empty_all

    def empty_pastures(self, only_unlocked: bool = True) -> list[Tile]:
        """Return empty pasture/coop tiles awaiting animal placement."""
        return (
            self._empty_pastures_unlocked
            if only_unlocked
            else self._empty_pastures_all
        )

    def weeds(self, only_unlocked: bool = True) -> list[Tile]:
        """Return weed tiles, optionally filtering to unlocked quadrants only."""
        return self._weeds_unlocked if only_unlocked else self._weeds_all

    def plants(self) -> list[Tile]:
        """Return active plant tiles."""
        return self._plants

    def crops(self, crop: str) -> list[Tile]:
        """Return plant tiles of a specific crop."""
        return [t for t in self._plants if t.crop == crop]

    def harvestable(self, crop: str | None = None) -> list[Tile]:
        """Return mature plant tiles (and ready animal yields), optionally filtered by crop."""
        if crop is None:
            return self._harvestable
        return [t for t in self._harvestable if t.crop == crop]

    def needs_water(self) -> list[Tile]:
        """Return active plant tiles that have not been watered today."""
        return self._needs_water

    def needs_water_urgent(self) -> list[Tile]:
        """Return plant tiles with consecutive_unwatered >= 1 facing imminent death."""
        return self._needs_water_urgent

    def animals(self) -> list[Tile]:
        """Return all pasture and coop tiles containing animals."""
        return self._animals

    def needs_feed(self) -> list[Tile]:
        """Return animal tiles that have not been fed today."""
        return self._needs_feed

    def needs_care(self) -> list[Tile]:
        """Return animal tiles that have not been cared for today."""
        return self._needs_care

    def has_fertilizer_tiles(self) -> list[Tile]:
        """Return animal tiles with ready-to-collect fertilizer."""
        return self._fertilizer_available

    def nearest(self, tiles: Iterable[Tile]) -> Tile | None:
        """Return the closest tile to the farmer from a collection of tiles."""
        fx, fy = self.state.farmer
        return self.nearest_to(fx, fy, tiles)

    def nearest_other(self, tiles: Iterable[Tile]) -> Tile | None:
        """Return the closest tile to the farmer, excluding the farmer's current coordinate."""
        fx, fy = self.state.farmer
        return self.nearest_to(fx, fy, tiles, exclude_pos=(fx, fy))

    def nearest_to(
        self,
        x: int,
        y: int,
        tiles: Iterable[Tile],
        exclude_pos: tuple[int, int] | None = None,
    ) -> Tile | None:
        """Find the tile in `tiles` closest to coordinate (x, y) via Manhattan distance."""
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
