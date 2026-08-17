from dataclasses import dataclass


@dataclass(slots=True)
class Tile:
    x: int
    y: int
    data: object

    @property
    def empty(self):
        return self.data is None

    @property
    def is_plant(self):
        return (
            isinstance(self.data, dict)
            and self.data.get("kind") == "PLANT"
        )

    @property
    def crop(self):
        if self.is_plant:
            return self.data["crop"]
        return None

    @property
    def watered(self):
        if self.is_plant:
            return self.data.get("watered_today", False)
        return False

    @property
    def yield_units(self):
        if self.is_plant:
            return self.data.get("yield_units", 0)
        return 0

    @property
    def planted_day(self):
        if self.is_plant:
            return self.data.get("planted_day")
        return None

    def distance(self, x, y):
        return abs(self.x - x) + abs(self.y - y)


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

    def crops(self, crop):
        for tile in self.plants():
            if tile.crop == crop:
                yield tile

    def harvestable(self):
        for tile in self.plants():
            if tile.yield_units > 0:
                yield tile

    def needs_water(self):
        for tile in self.plants():
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
