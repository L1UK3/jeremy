"""Unit tests for unified spatial dispatcher with shed hauling and adaptive harvests."""

from __future__ import annotations

from typing import Any

from src.dispatcher import (
    ALL_CANDIDATE_ANIMAL_TILES,
    BUILD_COOP,
    BUILD_PASTURE,
    DROP_SHED,
    PICKUP_ANIMAL,
    PLACE,
    RESERVED_ANIMAL_TILES,
    Job,
    _quadrant_animal_tiles,
    assign_jobs,
    generate_jobs,
    get_animal_plot_candidates,
    get_animal_reserved_tiles,
    job_to_action,
    schedule_tasks,
)
from src.environment.board import SHED_ACCESS_TILES, Board
from src.environment.state import GameState


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


def test_animal_reserved_tiles_scale_with_max_animals() -> None:
    """Reserved animal tiles scale dynamically with max_animals."""
    assert ALL_CANDIDATE_ANIMAL_TILES[:2] == ((3, 4), (4, 3))
    assert get_animal_reserved_tiles(1) == frozenset({(3, 4)})
    assert get_animal_reserved_tiles(2) == frozenset({(3, 4), (4, 3)})
    assert get_animal_reserved_tiles(3) == frozenset({(3, 4), (4, 3), (3, 3)})
    assert get_animal_reserved_tiles(4) == frozenset(
        {(3, 4), (4, 3), (3, 3), (2, 4)}
    )
    assert get_animal_reserved_tiles(0) == frozenset()


def test_animal_plot_candidates_interleave_unlocked_quadrants() -> None:
    """Animal plots are allocated evenly in deterministic quadrant order."""
    assert get_animal_plot_candidates(
        frozenset({"NW", "NE", "SW"}), max_animals=6
    ) == (
        (3, 4),
        (6, 4),
        (3, 5),
        (4, 3),
        (5, 3),
        (4, 6),
    )


def test_generate_jobs_balances_multiple_animal_structures() -> None:
    """Multiple structures planned together use the least-loaded quadrant."""
    obs = make_obs(
        unlocked_quadrants=["NW", "NE", "SW"],
        shed={"GOOSE": 1, "COW": 1, "SHEEP": 1},
        money=3000,
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(
        state,
        board,
        target_animal="GOOSE",
        max_animals=6,
    )
    structure_jobs = [
        job
        for job in jobs
        if job.action in (BUILD_COOP, BUILD_PASTURE)
    ]

    assert [job.target for job in structure_jobs] == [
        (3, 4),
        (6, 4),
        (3, 5),
    ]


def test_generate_jobs_build_coop_for_goose() -> None:
    """Targeted GOOSE or GOOSE in shed generates BUILD_COOP on reserved tile."""
    # Targeted GOOSE
    obs = make_obs(money=1000)
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_animal="GOOSE")
    coop_jobs = [j for j in jobs if j.action == BUILD_COOP]
    assert len(coop_jobs) == 1
    assert coop_jobs[0].target == (3, 4)
    assert coop_jobs[0].item == "GOOSE"
    assert coop_jobs[0].priority == 220.0

    # GOOSE in shed
    obs_shed = make_obs(money=1000, shed={"GOOSE": 1})
    state_shed = GameState.from_obs(obs_shed)
    board_shed = Board(state_shed)

    jobs_shed = generate_jobs(state_shed, board_shed, target_animal="NONE")
    coop_jobs_shed = [j for j in jobs_shed if j.action == BUILD_COOP]
    assert len(coop_jobs_shed) == 1
    assert coop_jobs_shed[0].target == (3, 4)


def test_generate_jobs_build_pasture_for_cow_and_sheep() -> None:
    """Targeted COW or SHEEP generates BUILD_PASTURE on reserved tile."""
    # COW
    obs_cow = make_obs(money=1000)
    state_cow = GameState.from_obs(obs_cow)
    board_cow = Board(state_cow)

    jobs_cow = generate_jobs(state_cow, board_cow, target_animal="COW")
    pasture_jobs_cow = [j for j in jobs_cow if j.action == BUILD_PASTURE]
    assert len(pasture_jobs_cow) == 1
    assert pasture_jobs_cow[0].target == (3, 4)
    assert pasture_jobs_cow[0].item == "COW"

    # SHEEP
    obs_sheep = make_obs(money=1000)
    state_sheep = GameState.from_obs(obs_sheep)
    board_sheep = Board(state_sheep)

    jobs_sheep = generate_jobs(state_sheep, board_sheep, target_animal="SHEEP")
    pasture_jobs_sheep = [j for j in jobs_sheep if j.action == BUILD_PASTURE]
    assert len(pasture_jobs_sheep) == 1
    assert pasture_jobs_sheep[0].target == (3, 4)
    assert pasture_jobs_sheep[0].item == "SHEEP"


def test_generate_jobs_no_duplicate_structure_when_empty_exists() -> None:
    """When an empty matching structure already exists, do not build another."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[4][3] = {"kind": "COOP"}  # empty coop at (3, 4)

    obs = make_obs(tiles=tiles, money=1000)
    state = GameState.from_obs(obs)
    board = Board(state)

    # With empty coop available, targeted GOOSE should not generate another BUILD_COOP
    jobs = generate_jobs(state, board, target_animal="GOOSE")
    assert not any(j.action == BUILD_COOP for j in jobs)


def test_job_to_action_build_structure() -> None:
    """job_to_action navigates toward target and executes BUILD_COOP / BUILD_PASTURE safely."""
    # Away from target: step toward
    job = Job(priority=220.0, action="BUILD_COOP", target=(3, 4), item="GOOSE")
    obs = make_obs(farmer=(1, 4))
    state = GameState.from_obs(obs)
    board = Board(state)

    act_step = job_to_action(job, 1, 4, state=state, board=board)
    assert act_step == ["EAST"]

    # At target with empty tile: execute action
    act_build = job_to_action(job, 3, 4, state=state, board=board)
    assert act_build == ["BUILD_COOP"]

    # At target with occupied tile: return PASS for safety
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[4][3] = {"kind": "WEED"}
    obs_blocked = make_obs(farmer=(3, 4), tiles=tiles)
    state_blocked = GameState.from_obs(obs_blocked)
    board_blocked = Board(state_blocked)

    act_blocked = job_to_action(
        job, 3, 4, state=state_blocked, board=board_blocked
    )
    assert act_blocked == ["PASS"]


def test_generate_jobs_pickup_animal_when_shed_has_animal_and_empty_structure() -> (
    None
):
    """PICKUP_ANIMAL job emitted when animal in shed and matching empty structure exists."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[4][3] = {"kind": "COOP"}  # empty coop at (3, 4)

    obs = make_obs(tiles=tiles, shed={"GOOSE": 1})
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board)
    pickup_jobs = [j for j in jobs if j.action == PICKUP_ANIMAL]
    assert len(pickup_jobs) == 1
    assert pickup_jobs[0].item == "GOOSE"
    assert pickup_jobs[0].target in SHED_ACCESS_TILES


def test_generate_jobs_place_animal_when_worker_holds_animal() -> None:
    """PLACE chore job emitted targeting unoccupied structure when worker carries animal."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[3][4] = {"kind": "PASTURE"}  # empty pasture at (4, 3)

    obs = make_obs(tiles=tiles, inventories=[{"COW": 1}])
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board)
    place_jobs = [j for j in jobs if j.action == PLACE]
    assert len(place_jobs) == 1
    assert place_jobs[0].target == (4, 3)
    assert place_jobs[0].item == "COW"


def test_job_to_action_pickup_animal_drops_backpack_first() -> None:
    """Worker assigned to animal retrieval empties backpack via DROP before PICKUP."""
    job = Job(priority=240.0, action=PICKUP_ANIMAL, target=(4, 4), item="GOOSE")

    # Worker at (4, 4) with carried items: must DROP first
    obs_loaded = make_obs(farmer=(4, 4), inventories=[{"WHEAT": 2}])
    state_loaded = GameState.from_obs(obs_loaded)
    act_drop = job_to_action(job, 4, 4, state=state_loaded, u_idx=0)
    assert act_drop == ["DROP"]

    # Worker at (4, 4) with empty backpack: PICKUP 1 animal
    obs_empty = make_obs(farmer=(4, 4), inventories=[{}], shed={"GOOSE": 1})
    state_empty = GameState.from_obs(obs_empty)
    act_pickup = job_to_action(job, 4, 4, state=state_empty, u_idx=0)
    assert act_pickup == ["PICKUP", "GOOSE", 1]


def test_job_to_action_place_animal_at_structure() -> None:
    """Worker emits PLACE <animal> when arriving at unoccupied matching structure."""
    job = Job(priority=245.0, action=PLACE, target=(3, 4), item="GOOSE")

    # Away from structure: step toward
    obs_away = make_obs(farmer=(4, 4))
    state_away = GameState.from_obs(obs_away)
    act_step = job_to_action(job, 4, 4, state=state_away)
    assert act_step == ["WEST"]

    # At structure: PLACE animal
    obs_at = make_obs(farmer=(3, 4))
    state_at = GameState.from_obs(obs_at)
    act_place = job_to_action(job, 3, 4, state=state_at)
    assert act_place == ["PLACE", "GOOSE"]


def test_job_to_action_feed_wheat_pickup_route() -> None:
    """Worker with 0 carried wheat routes via shed to pick up wheat before feeding."""
    job = Job(priority=200.0, action="FEED", target=(3, 4), item="GOOSE")

    # Worker has wheat: steps toward animal
    obs_has_wheat = make_obs(farmer=(2, 4), inventories=[{"WHEAT": 1}])
    state_has_wheat = GameState.from_obs(obs_has_wheat)
    board_has_wheat = Board(state_has_wheat)
    act_step = job_to_action(
        job, 2, 4, state=state_has_wheat, board=board_has_wheat, u_idx=0
    )
    assert act_step == ["EAST"]

    # Worker has wheat and at animal: feeds
    act_feed = job_to_action(
        job, 3, 4, state=state_has_wheat, board=board_has_wheat, u_idx=0
    )
    assert act_feed == ["FEED"]

    # Worker has NO wheat and at shed: picks up wheat
    obs_no_wheat_at_shed = make_obs(
        farmer=(4, 4), inventories=[{}], shed={"WHEAT": 5}
    )
    state_no_wheat_at_shed = GameState.from_obs(obs_no_wheat_at_shed)
    board_no_wheat_at_shed = Board(state_no_wheat_at_shed)
    act_pickup_wheat = job_to_action(
        job,
        4,
        4,
        state=state_no_wheat_at_shed,
        board=board_no_wheat_at_shed,
        u_idx=0,
    )
    assert act_pickup_wheat == ["PICKUP", "WHEAT", 1]


def test_assign_jobs_place_restricted_to_worker_holding_animal() -> None:
    """Only the worker holding the animal can be assigned to PLACE."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[4][3] = {"kind": "COOP"}

    # Farmer has empty inventory at (0, 0); Hand 0 holds GOOSE at (4, 4)
    obs = make_obs(
        farmer=(0, 0),
        hands=[[4, 4]],
        tiles=tiles,
        inventories=[{}, {"GOOSE": 1}],
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    farmer_act, hands_acts = schedule_tasks(state, board)
    # Hand 0 should receive the PLACE job toward (3, 4) -> step WEST
    assert hands_acts[0] == ["WEST"]
    # Farmer should not receive PLACE
    assert farmer_act != ["WEST"]


def test_quadrant_animal_tiles_center_reflection() -> None:
    """_quadrant_animal_tiles reflects across (4.5, 4.5) axis for all quadrants."""
    assert _quadrant_animal_tiles("NW") == ((3, 4), (4, 3), (3, 3), (2, 4))
    assert _quadrant_animal_tiles("NE") == ((6, 4), (5, 3), (6, 3), (7, 4))
    assert _quadrant_animal_tiles("SW") == ((3, 5), (4, 6), (3, 6), (2, 5))
    assert _quadrant_animal_tiles("SE") == ((6, 5), (5, 6), (6, 6), (7, 5))


def test_animal_plot_candidates_all_four_quadrants_round_robin() -> None:
    """All four quadrants interleave reflected slots adjacent to the center drop."""
    candidates = get_animal_plot_candidates(
        frozenset({"NW", "NE", "SW", "SE"}), max_animals=8
    )
    assert candidates == (
        # Slot 0 round robin
        (3, 4),
        (6, 4),
        (3, 5),
        (6, 5),
        # Slot 1 round robin
        (4, 3),
        (5, 3),
        (4, 6),
        (5, 6),
    )


def test_animal_reserved_tiles_target_animals_capped() -> None:
    """get_animal_reserved_tiles caps reservations to min(target_animals, plot_quota)."""
    # 0 target animals reserves nothing
    assert get_animal_reserved_tiles(target_animals=0) == frozenset()
    assert (
        get_animal_reserved_tiles(
            unlocked_quadrants=frozenset({"NW", "NE"}), target_animals=0
        )
        == frozenset()
    )

    # 1 target animal reserves exactly 1 candidate tile
    res_1 = get_animal_reserved_tiles(
        unlocked_quadrants=frozenset({"NW", "NE"}), target_animals=1
    )
    assert res_1 == frozenset({(3, 4)})

    # 2 target animals across 2 quadrants reserves slot 0 of NW and NE
    res_2 = get_animal_reserved_tiles(
        unlocked_quadrants=frozenset({"NW", "NE"}), target_animals=2
    )
    assert res_2 == frozenset({(3, 4), (6, 4)})

    # Target exceeding quadrant quota (2 per quadrant) is capped at plot_quota
    res_capped = get_animal_reserved_tiles(
        unlocked_quadrants=frozenset({"NW"}), target_animals=5
    )
    assert res_capped == frozenset({(3, 4), (4, 3)})
    assert len(res_capped) == 2


def test_empty_candidate_tiles_available_for_planting_when_target_low() -> None:
    """Candidate tiles beyond target_animals are unreserved and get crop plant jobs."""
    obs = make_obs(
        unlocked_quadrants=["NW"],
        seeds={"CARROT": 25},
        money=1000,
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    # With target_animals=1, (3, 4) is reserved, but (4, 3) must NOT be reserved
    jobs = generate_jobs(
        state,
        board,
        target_crop="CARROT",
        target_animal="NONE",
        target_animals=1,
    )
    plant_targets = {j.target for j in jobs if j.action == "PLANT"}
    assert (3, 4) not in plant_targets
    assert (4, 3) in plant_targets

    # With target_animals=0, neither (3, 4) nor (4, 3) is reserved; both get planted
    jobs_zero = generate_jobs(
        state,
        board,
        target_crop="CARROT",
        target_animal="NONE",
        target_animals=0,
    )
    plant_targets_zero = {j.target for j in jobs_zero if j.action == "PLANT"}
    assert (3, 4) in plant_targets_zero
    assert (4, 3) in plant_targets_zero


def test_generate_jobs_skips_crop_occupied_candidate_fallback() -> None:
    """When preferred candidate tile has a growing crop, structure job falls back to next empty candidate."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    # Preferred candidate (3, 4) has a growing crop
    tiles[4][3] = {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": True,
        "consecutive_unwatered": 0,
        "yield_units": 0,
        "max_lifespan_step": 100,
        "fertilized_until_day": 0,
    }

    obs = make_obs(
        unlocked_quadrants=["NW"],
        shed={"GOOSE": 1},
        tiles=tiles,
        money=1000,
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_animal="NONE", max_animals=2)
    coop_jobs = [j for j in jobs if j.action == BUILD_COOP]
    assert len(coop_jobs) == 1
    # Skipped occupied (3, 4), targeted next empty candidate (4, 3)
    assert coop_jobs[0].target == (4, 3)
    assert coop_jobs[0].item == "GOOSE"


def test_generate_jobs_multiple_crop_occupied_fallback_across_candidates() -> None:
    """When multiple candidates have crops, structure job finds subsequent empty candidate."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    # Both slot 0 (3, 4) and slot 1 (4, 3) are occupied by crops
    for cx, cy in ((3, 4), (4, 3)):
        tiles[cy][cx] = {
            "kind": "PLANT",
            "crop": "CARROT",
            "planted_day": 1,
            "watered_today": True,
            "consecutive_unwatered": 0,
            "yield_units": 0,
            "max_lifespan_step": 100,
            "fertilized_until_day": 0,
        }

    obs = make_obs(
        unlocked_quadrants=["NW"],
        shed={"COW": 1},
        tiles=tiles,
        money=1000,
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    jobs = generate_jobs(state, board, target_animal="NONE")
    pasture_jobs = [j for j in jobs if j.action == BUILD_PASTURE]
    assert len(pasture_jobs) == 1
    # Skipped (3, 4) and (4, 3), fell back to slot 2 (3, 3)
    assert pasture_jobs[0].target == (3, 3)
    assert pasture_jobs[0].item == "COW"


def test_farmer_priority_over_hands_for_candidate_chores() -> None:
    """Farmer prioritizes high-utility field chores before allocating remaining chores to hands."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[2][0] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "planted_day": 0,
        "watered_today": True,
        "consecutive_unwatered": 0,
        "yield_units": 3,
        "max_lifespan_step": 100,
        "fertilized_until_day": 0,
    }

    # Farmer is at (0, 0); Hand is at (0, 1) - closer to (0, 2)
    obs = make_obs(
        day=5,
        farmer=(0, 0),
        hands=[[0, 1]],
        tiles=tiles,
        prices={"CARROT": 20},
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    farmer_act, hands_acts = schedule_tasks(state, board)
    # Farmer gets prioritized for the harvest job at (0, 2)
    assert farmer_act == ["SOUTH"]
    # Hand does not steal the chore
    assert hands_acts[0] != ["SOUTH"]


def test_idle_farmer_repositions_toward_center_drop() -> None:
    """When no field chores exist, an idle farmer steps toward the Center Drop instead of emitting PASS."""
    obs = make_obs(
        farmer=(0, 0),
        unlocked_quadrants=["NW"],
        seeds={},
        money=0,
    )
    state = GameState.from_obs(obs)
    board = Board(state)

    farmer_act, _ = schedule_tasks(state, board)
    assert farmer_act != ["PASS"]
    # Stepping toward Center Drop (4, 4) from (0, 0)
    assert farmer_act in (["EAST"], ["SOUTH"])

