from board import Board, Tile, manhattan_distance, step_toward
from state import GameState


def test_manhattan_and_step():
    assert manhattan_distance(0, 0, 3, 4) == 7
    assert step_toward(0, 0, 3, 0) == "EAST"
    assert step_toward(3, 0, 0, 0) == "WEST"
    assert step_toward(0, 0, 0, 3) == "SOUTH"
    assert step_toward(0, 3, 0, 0) == "NORTH"


def test_tile_properties():
    t_empty = Tile(x=0, y=0, data=None)
    assert t_empty.empty is True
    assert t_empty.is_plant is False
    assert t_empty.is_weed is False

    t_weed = Tile(x=1, y=1, data="WEED")
    assert t_weed.is_weed is True

    t_plant = Tile(
        x=2,
        y=2,
        data={
            "kind": "PLANT",
            "crop": "MELON",
            "watered_today": False,
            "yield_units": 6,
        },
    )
    assert t_plant.is_plant is True
    assert t_plant.crop == "MELON"
    assert t_plant.watered is False
    assert t_plant.yield_units == 6


def test_board_indexing():
    obs = {
        "player": 0,
        "step": 0,
        "market": {"prices": {"WHEAT": 25}},
        "farms": [
            {
                "money": 3000,
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "tiles": [
                    [
                        {
                            "kind": "PLANT",
                            "crop": "WHEAT",
                            "watered_today": False,
                            "yield_units": 0,
                        }
                        if (x == 1 and y == 1)
                        else None
                        for x in range(10)
                    ]
                    for y in range(10)
                ],
            }
        ],
        "private": {"shed": {}, "seeds": {}},
    }
    state = GameState.from_obs(obs)
    board = Board(state)
    assert len(board.needs_water()) == 1
    assert board.empty_tiles_count == 24
