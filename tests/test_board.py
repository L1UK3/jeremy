from src.board import Board, CropSpec, Tile, manhattan_distance, step_toward
from src.state import GameState


def test_manhattan_and_step():
    assert manhattan_distance(0, 0, 3, 4) == 7
    assert step_toward(0, 0, 3, 0) == "EAST"
    assert step_toward(3, 0, 0, 0) == "WEST"
    assert step_toward(0, 0, 0, 3) == "SOUTH"
    assert step_toward(0, 3, 0, 0) == "NORTH"
    assert step_toward(2, 2, 2, 2) == "PASS"


def test_cropspec_namedtuple():
    spec = CropSpec(
        first_yield_day=4, max_yield_day=8, max_yield=6, ongoing=False
    )
    assert spec.first_yield_day == 4
    assert spec.max_yield_day == 8
    assert spec.max_yield == 6
    assert spec.ongoing is False


def test_tile_properties_and_methods():
    t_empty = Tile(x=0, y=0, data=None)
    assert t_empty.empty is True
    assert t_empty.is_plant is False
    assert t_empty.is_weed is False
    assert t_empty.is_animal is False
    assert t_empty.distance(3, 4) == 7
    assert t_empty.age(5) == 0
    assert t_empty.is_unlocked(["NW", "NE"]) is True
    assert t_empty.is_unlocked(["SE"]) is False

    t_weed = Tile(x=1, y=1, data="WEED")
    assert t_weed.is_weed is True
    assert t_weed.empty is False

    t_plant = Tile(
        x=2,
        y=2,
        data={
            "kind": "PLANT",
            "crop": "MELON",
            "planted_day": 2,
            "watered_today": False,
            "yield_units": 6,
        },
    )
    assert t_plant.is_plant is True
    assert t_plant.crop == "MELON"
    assert t_plant.watered is False
    assert t_plant.yield_units == 6
    assert t_plant.age(5) == 3
    # MELON first yield day is 10 (planted day 2 -> day 11 is age 9 < 10, day 12 is age 10 >= 10)
    assert t_plant.is_ripe(11) is False
    assert t_plant.is_ripe(12) is True

    # Ongoing crop test (TOMATO: first yield day 8, ongoing=True)
    t_tomato = Tile(
        x=3,
        y=3,
        data={
            "kind": "PLANT",
            "crop": "TOMATO",
            "planted_day": 1,
            "watered_today": True,
            "yield_units": 1,
        },
    )
    assert t_tomato.is_ripe(8) is False  # age 7 < 8
    assert t_tomato.is_ripe(9) is True  # age 8 >= 8 and yield_units > 0

    # Animal tile test
    t_animal = Tile(
        x=4,
        y=4,
        data={
            "kind": "COOP",
            "animal": "GOOSE",
            "placed_day": 0,
            "yield_units": 2,
            "fed_today": False,
            "cared_today": True,
            "fertilizer_available": True,
            "consecutive_unfed": 1,
        },
    )
    assert t_animal.is_animal is True
    assert t_animal.animal == "GOOSE"
    assert t_animal.fed_today is False
    assert t_animal.cared_today is True
    assert t_animal.fertilizer_available is True
    assert t_animal.consecutive_unfed == 1


def test_board_indexing_and_queries():
    tiles_grid: list[list[dict | str | None]] = [
        [None for _ in range(10)] for _ in range(10)
    ]
    # Plant at (1, 1) NW
    tiles_grid[1][1] = {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": False,
        "yield_units": 0,
    }
    # Weed at (2, 2) NW
    tiles_grid[2][2] = {"kind": "WEED"}
    # Weed at (8, 8) SE (locked quadrant)
    tiles_grid[8][8] = {"kind": "WEED"}
    # Animal at (0, 0) NW
    tiles_grid[0][0] = {
        "kind": "PASTURE",
        "animal": "COW",
        "placed_day": 0,
        "yield_units": 1,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": True,
        "consecutive_unfed": 0,
    }

    obs = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "market": {"prices": {"WHEAT": 25, "MILK": 60, "FERTILIZER": 40}},
        "farms": [
            {
                "money": 3000,
                "farmer": [1, 0],
                "hands": [[0, 1]],
                "unlocked_quadrants": ["NW"],
                "tiles": tiles_grid,
            }
        ],
        "private": {"shed": {}, "seeds": {}},
    }
    state = GameState.from_obs(obs)
    board = Board(state)

    # Basic counts
    assert len(board.needs_water()) == 1
    assert len(board.plants()) == 1
    assert len(board.crops("WHEAT")) == 1
    assert len(board.crops("CARROT")) == 0

    # Unlocked vs all filtering
    assert len(board.weeds(only_unlocked=True)) == 1
    assert len(board.weeds(only_unlocked=False)) == 2
    assert board.empty_tiles_count == 22
    assert len(board.empty_tiles(only_unlocked=True)) == 22
    assert len(board.empty_tiles(only_unlocked=False)) == 96

    # Animal and Pasture queries
    assert len(board.animals()) == 1
    assert len(board.empty_pastures()) == 0
    assert len(board.needs_feed()) == 1
    assert len(board.needs_care()) == 1
    assert len(board.has_fertilizer_tiles()) == 1
    assert len(board.needs_water_urgent()) == 0

    # Nearest navigation helpers
    all_plants = board.plants()
    nearest_plant = board.nearest(all_plants)
    assert nearest_plant is not None
    assert nearest_plant.pos == (1, 1)

    nearest_other = board.nearest_other([board.tile(1, 0), board.tile(1, 1)])
    assert nearest_other is not None
    assert nearest_other.pos == (1, 1)

    # Coordinate indexing & out of bounds
    assert board.tile(1, 1) is not None
    assert board.tile(10, 10) is None
    assert board.tile(-1, 0) is None
    assert board.get_tile(0, 0) is not None

    # Nearest shed
    shed_coord = board.nearest_shed(0, 0)
    assert shed_coord == (4, 4)
