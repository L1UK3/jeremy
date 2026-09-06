"""Unit tests for unified spatial dispatcher with shed hauling and adaptive harvests."""

from __future__ import annotations

from typing import Any

from dispatcher import (
    DROP_SHED,
    RESERVED_ANIMAL_TILES,
    Job,
    assign_jobs,
    generate_jobs,
    job_to_action,
    schedule_tasks,
)
from environment.board import SHED_ACCESS_TILES, Board
from environment.state import GameState


def make_obs(
    step: int = 0,
    day: int = 0,
    hour: int = 0,
    money: int = 3000,
    farmer: tuple[int, int] = (2, 2),
    hands: list[list[int]] | None = None,
    shed: dict[str, int] | None = None,
    seeds: dict[str, int] | None = None,
    inventories: list[dict[str, int]] | None = None,
    tiles: list[list[Any]] | None = None,
    unlocked_quadrants: list[str] | None = None,
    prices: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Construct an observation dict for dispatcher unit testing."""
    if tiles is None:
        tiles = [[None for _ in range(10)] for _ in range(10)]
    quads = unlocked_quadrants or ["NW"]
    default_prices = {
        "WHEAT": 25,
        "CARROT": 35,
        "TOMATO": 60,
        "STRAWBERRY": 120,
        "MELON": 250,
        "MILK": 160,
        "WOOL": 200,
    }
    if prices:
        default_prices.update(prices)

    invs = inventories if inventories is not None else [{}]

    return {
        "player": 0,
        "step": step,
        "day": day,
        "hour": hour,
        "farms": [
            {
                "money": money,
                "tiles": tiles,
                "farmer": list(farmer),
                "hands": hands or [],
                "unlocked_quadrants": quads,
                "hires_today": len(hands or []),
            },
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [2, 2],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": shed or {},
            "seeds": seeds or {},
            "inventories": invs,
        },
        "market": {
            "inventory": {
                "WHEAT": 800,
                "CARROT": 600,
                "TOMATO": 400,
                "STRAWBERRY": 200,
                "MELON": 150,
                "MILK": 150,
                "WOOL": 150,
            },
            "prices": default_prices,
        },
        "town": {
            "unlocked_shops": ["BAKERY"],
        },
    }


def test_reserved_animal_tiles_constants() -> None:
    """Shed-adjacent tiles (3, 4) and (4, 3) must be reserved for animals."""
    assert RESERVED_ANIMAL_TILES == frozenset({(3, 4), (4, 3)})
    assert DROP_SHED == 260.0


def test_reserved_animal_tiles_excluded_from_planting() -> None:
    """Planting chores must never target the reserved animal tiles (3, 4) or (4, 3)."""
    obs = make_obs(seeds={"WHEAT": 100})
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_crop="WHEAT")
    plant_targets = {j.target for j in jobs if j.action == "PLANT"}

    assert (3, 4) not in plant_targets
    assert (4, 3) not in plant_targets
    # Other NW tiles (e.g. (0, 0)) should be present
    assert (0, 0) in plant_targets


def test_planting_prioritizes_target_crop_and_cascades() -> None:
    """Planting jobs prioritize target_crop and cascade to secondary seeds (like Wheat) if unstocked."""
    # Scenario A: Target crop MELON has only 2 seeds, Wheat has 3 seeds
    obs = make_obs(seeds={"MELON": 2, "WHEAT": 3})
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_crop="MELON")
    plant_jobs = [j for j in jobs if j.action == "PLANT"]

    assert len(plant_jobs) == 5
    melon_jobs = [j for j in plant_jobs if j.item == "MELON"]
    wheat_jobs = [j for j in plant_jobs if j.item == "WHEAT"]

    assert len(melon_jobs) == 2
    assert len(wheat_jobs) == 3

    # Scenario B: Target crop MELON is completely unstocked (0 seeds), cascades to WHEAT
    obs_b = make_obs(seeds={"MELON": 0, "WHEAT": 4})
    state_b = GameState.from_obs(obs_b)
    board_b = Board(state_b)

    jobs_b = generate_jobs(state_b, board_b, target_crop="MELON")
    plant_jobs_b = [j for j in jobs_b if j.action == "PLANT"]

    assert len(plant_jobs_b) == 4
    assert all(j.item == "WHEAT" for j in plant_jobs_b)


def test_drop_shed_chore_emitted_when_carrying_ge_3() -> None:
    """Units carrying >= 3 items emit a DROP_SHED chore with priority 260.0."""
    obs = make_obs(
        hour=5,
        farmer=(2, 4),
        inventories=[{"WHEAT": 3}],
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board)
    drop_jobs = [j for j in jobs if j.action == "DROP_SHED"]

    assert len(drop_jobs) == 1
    assert drop_jobs[0].priority == 260.0
    # Nearest shed tile from (2, 4) should be (4, 4)
    assert drop_jobs[0].target == (4, 4)

    # Moving toward shed
    act = job_to_action(drop_jobs[0], 2, 4, state=state, board=board)
    assert act == ["EAST"]

    # When standing at shed access tile (4, 4), emits ["DROP"]
    act_at_shed = job_to_action(drop_jobs[0], 4, 4, state=state, board=board)
    assert act_at_shed == ["DROP"]


def test_drop_shed_chore_emitted_at_late_hour() -> None:
    """Units carrying produce at hour >= 20 emit a DROP_SHED chore."""
    # Hour 20 with 1 tomato -> should emit DROP_SHED
    obs_late = make_obs(
        hour=20,
        farmer=(4, 5),
        inventories=[{"TOMATO": 1}],
    )
    state_late = GameState.from_obs(obs_late)
    board_late = Board(state_late)

    jobs_late = generate_jobs(state_late, board_late)
    drop_jobs_late = [j for j in jobs_late if j.action == "DROP_SHED"]
    assert len(drop_jobs_late) == 1
    assert drop_jobs_late[0].priority == 260.0
    assert drop_jobs_late[0].target in SHED_ACCESS_TILES

    # Hour 19 with 1 tomato (< 3 items) -> should NOT emit DROP_SHED
    obs_early = make_obs(
        hour=19,
        farmer=(4, 5),
        inventories=[{"TOMATO": 1}],
    )
    state_early = GameState.from_obs(obs_early)
    board_early = Board(state_early)

    jobs_early = generate_jobs(state_early, board_early)
    drop_jobs_early = [j for j in jobs_early if j.action == "DROP_SHED"]
    assert len(drop_jobs_early) == 0


def test_one_time_crops_watered_through_bonus_window_when_solvent() -> None:
    """One-time crops are watered through bonus windows and harvested only at crop_age >= max_yield_day when money >= 50."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    # Wheat planted on day 0. At day 2: crop_age = 2 (first_yield_day). max_yield_day is 4.
    tiles[0][0] = {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": False,
        "yield_units": 1,
        "consecutive_unwatered": 0,
    }

    obs_day2 = make_obs(
        day=2,
        money=500,  # Solvent (> 50)
        tiles=tiles,
    )
    state_day2 = GameState.from_obs(obs_day2)
    board_day2 = Board(state_day2)

    jobs_day2 = generate_jobs(state_day2, board_day2)
    tile_jobs_day2 = [j for j in jobs_day2 if j.target == (0, 0)]

    # Must be watered, NOT harvested
    assert any(j.action == "WATER" for j in tile_jobs_day2)
    assert not any(j.action == "HARVEST" for j in tile_jobs_day2)

    # Fast forward to day 4 (max_yield_day)
    obs_day4 = make_obs(
        day=4,
        money=500,
        tiles=tiles,
    )
    state_day4 = GameState.from_obs(obs_day4)
    board_day4 = Board(state_day4)

    jobs_day4 = generate_jobs(state_day4, board_day4)
    tile_jobs_day4 = [j for j in jobs_day4 if j.target == (0, 0)]

    # At day 4, it is mature and must be harvested
    assert any(j.action == "HARVEST" for j in tile_jobs_day4)
    harvest_job = next(j for j in tile_jobs_day4 if j.action == "HARVEST")
    # Standing on tile emits ["HARVEST"]
    assert job_to_action(
        harvest_job, 0, 0, state=state_day4, board=board_day4
    ) == ["HARVEST"]


def test_emergency_early_harvest_when_cash_starved() -> None:
    """One-time crops harvest early at first_yield_day if money < 50 and unplanted tiles exist."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    # Wheat at first_yield_day (day 2), unwatered today
    tiles[0][0] = {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": False,
        "yield_units": 1,
        "consecutive_unwatered": 0,
    }
    # Unplanted tile exists at (1, 1)

    # Cash-starved: money = 30 (< 50)
    obs_broke = make_obs(
        day=2,
        money=30,
        tiles=tiles,
    )
    state_broke = GameState.from_obs(obs_broke)
    board_broke = Board(state_broke)

    jobs_broke = generate_jobs(state_broke, board_broke)
    tile_jobs_broke = [j for j in jobs_broke if j.target == (0, 0)]

    # Emergency early harvest triggered!
    assert any(j.action == "HARVEST" for j in tile_jobs_broke)

    # If all tiles were planted (no unplanted tiles exist), no emergency harvest even if money < 50
    tiles_full = [
        [
            {
                "kind": "PLANT",
                "crop": "WHEAT",
                "planted_day": 0,
                "watered_today": True,
                "yield_units": 1,
            }
            for _ in range(10)
        ]
        for _ in range(10)
    ]
    tiles_full[0][0]["watered_today"] = False

    obs_no_empty = make_obs(
        day=2,
        money=30,
        tiles=tiles_full,
    )
    state_no_empty = GameState.from_obs(obs_no_empty)
    board_no_empty = Board(state_no_empty)

    jobs_no_empty = generate_jobs(state_no_empty, board_no_empty)
    tile_jobs_no_empty = [j for j in jobs_no_empty if j.target == (0, 0)]
    assert not any(j.action == "HARVEST" for j in tile_jobs_no_empty)


def test_assign_jobs_coordinates_farmer_and_hands_without_duplicate_tiles() -> (
    None
):
    """assign_jobs coordinates farmer and hands from a single job pool without duplicate assignments."""
    obs = make_obs(
        farmer=(0, 0),
        hands=[[2, 2], [4, 4]],
    )
    state = GameState.from_obs(obs)

    jobs = [
        Job(priority=150.0, action="HARVEST", target=(2, 2), item="WHEAT"),
        Job(priority=140.0, action="DIG", target=(4, 4)),
        Job(priority=120.0, action="WATER", target=(0, 0)),
    ]

    farmer_act, hands_acts = assign_jobs(state, jobs)

    # Worker positions:
    # Farmer at (0, 0)
    # Hand 0 at (2, 2)
    # Hand 1 at (4, 4)
    # Optimal matching:
    # Farmer -> (0, 0) [WATER]
    # Hand 0 -> (2, 2) [HARVEST]
    # Hand 1 -> (4, 4) [DIG]
    assert farmer_act == ["WATER"]
    assert hands_acts[0] == ["HARVEST"]
    assert hands_acts[1] == ["DIG"]


def test_drop_shed_in_multi_agent_coordination() -> None:
    """When a hand carries 3 items, it is assigned DROP_SHED while farmer does fieldwork."""
    obs = make_obs(
        farmer=(0, 0),
        hands=[[3, 4]],
        inventories=[{}, {"WHEAT": 3}],  # Hand 0 has 3 wheat
        seeds={"WHEAT": 10},
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    farmer_act, hands_acts = schedule_tasks(state, board)

    # Farmer has empty backpack -> does not drop shed, does field work (e.g. plants/waters)
    assert farmer_act != ["DROP"]

    # Hand 0 is at (3, 4) with 3 wheat -> nearest shed is (4, 4), steps EAST
    assert hands_acts[0] == ["EAST"]


def test_bonus_window_watering_priority() -> None:
    """Crops inside their bonus window receive WATER_BONUS priority (160.0)."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    # Wheat planted day 0. At day 2: bonus window starts (ceil(4/2) = 2).
    tiles[0][0] = {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": False,
        "yield_units": 1,
        "consecutive_unwatered": 0,
    }
    # Melon planted day 0. At day 2: age 2 < bonus_start (ceil(12/2) = 6).
    tiles[0][1] = {
        "kind": "PLANT",
        "crop": "MELON",
        "planted_day": 0,
        "watered_today": False,
        "yield_units": 0,
        "consecutive_unwatered": 0,
    }

    obs = make_obs(day=2, money=1000, tiles=tiles)
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board)
    wheat_water = next(
        j for j in jobs if j.target == (0, 0) and j.action == "WATER"
    )
    melon_water = next(
        j for j in jobs if j.target == (1, 0) and j.action == "WATER"
    )

    # Wheat is in bonus window -> 160.0
    assert wheat_water.priority == 160.0
    # Melon is before bonus window -> 120.0
    assert melon_water.priority == 120.0


def test_cascade_planting_priority_lower_than_target() -> None:
    """Target crop planting has PLANT_BASE (75.0) while cascade has PLANT_CASCADE (65.0)."""
    obs = make_obs(seeds={"MELON": 1, "WHEAT": 1})
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_crop="MELON")
    melon_job = next(
        j for j in jobs if j.action == "PLANT" and j.item == "MELON"
    )
    wheat_job = next(
        j for j in jobs if j.action == "PLANT" and j.item == "WHEAT"
    )

    assert melon_job.priority == 75.0
    assert wheat_job.priority == 65.0


def test_late_hour_drop_only_for_produce() -> None:
    """At hour >= 20, carried produce triggers DROP_SHED but 1 fertilizer alone does not."""
    # 1 fertilizer at hour 21 -> carried < 3 and not produce -> NO drop
    obs_fert = make_obs(hour=21, inventories=[{"FERTILIZER": 1}])
    state_fert = GameState.from_obs(obs_fert)
    board_fert = Board(state_fert)
    jobs_fert = generate_jobs(state_fert, board_fert)
    assert not any(j.action == "DROP_SHED" for j in jobs_fert)

    # 1 egg (animal produce) at hour 21 -> triggers drop
    obs_egg = make_obs(hour=21, inventories=[{"EGG": 1}])
    state_egg = GameState.from_obs(obs_egg)
    board_egg = Board(state_egg)
    jobs_egg = generate_jobs(state_egg, board_egg)
    assert any(j.action == "DROP_SHED" for j in jobs_egg)
