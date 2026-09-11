"""Unit and integration tests for parameters.py configuration module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dispatcher import generate_jobs
from src.environment.board import Board
from src.environment.state import GameState
from src.main import make_agent
from src.parameters import (
    DEFAULT_PARAMETERS,
    DispatcherParams,
    MarketMakerParams,
    Parameters,
    ProcurementParams,
    get_active_parameters,
    load_parameters,
    use_parameters,
)

# =============================================================================
# Baseline Consistency & Invariant Tests
# =============================================================================


def test_default_parameters_match_domain_constants() -> None:
    """Canonical defaults in DEFAULT_PARAMETERS must mirror agent specifications."""
    p = DEFAULT_PARAMETERS
    assert p.procurement.land_cost_mult == 2.0
    assert p.procurement.land_min_crew == 3
    assert p.procurement.max_hire_hour == 2
    assert p.procurement.feed_buffer_mult == 2
    assert p.procurement.max_animals == 2
    assert p.procurement.reserved_animal_tiles == 2
    assert p.procurement.seed_fallback_crop == "WHEAT"

    assert p.dispatcher.prio_feed_urgent == 350.0
    assert p.dispatcher.prio_water_urgent == 300.0
    assert p.dispatcher.prio_drop_shed == 260.0
    assert p.dispatcher.prio_harvest_premium == 250.0
    assert p.dispatcher.prio_place_animal == 245.0
    assert p.dispatcher.prio_pickup_animal == 240.0
    assert p.dispatcher.prio_build_structure == 220.0
    assert p.dispatcher.prio_feed == 200.0
    assert p.dispatcher.prio_care == 180.0
    assert p.dispatcher.prio_water_bonus == 160.0
    assert p.dispatcher.prio_harvest_base == 150.0
    assert p.dispatcher.prio_dig_weed == 140.0
    assert p.dispatcher.prio_water == 120.0
    assert p.dispatcher.prio_plant_base == 75.0
    assert p.dispatcher.prio_plant_cascade == 65.0
    assert p.dispatcher.prio_fertilize == 70.0
    assert p.dispatcher.prio_collect_fertilizer == 60.0
    assert p.dispatcher.dist_penalty == 2.0
    assert p.dispatcher.reserved_animal_tiles == 2

    assert p.market_maker.glut_weight_melon == 3.5
    assert p.market_maker.glut_weight_strawberry == 2.0
    assert p.market_maker.sort_sells is True
    assert p.market_maker.sort_key == "impact"
    assert p.market_maker.shed_pressure == 80
    assert p.market_maker.ramp_start == 576
    assert p.market_maker.ramp_end == 716

    assert p.predation.front_run_discount == 0.85
    assert p.predation.corner_wheat_buy_qty == 5
    assert p.weed_repair.weed_repair_cutoff_step == 672
    assert p.explosion.explosion_step == 712
    assert p.explosion.pre_terminal_step == 672
    assert p.debt_manager.opening_strategy == "feed5"
    assert p.clone_detector.clone_distance_high == 1


# =============================================================================
# Serialization & Conversion Tests
# =============================================================================


def test_dict_serialization_round_trip() -> None:
    """Round-trip conversion between flat/nested dicts and Parameters."""
    custom = Parameters(
        procurement=ProcurementParams(land_cost_mult=3.5, land_min_crew=4),
        dispatcher=DispatcherParams(dist_penalty=3.0, prio_dig_weed=180.0),
        market_maker=MarketMakerParams(shed_pressure=90),
    )

    flat = custom.to_dict(flat=True)
    assert flat["land_cost_mult"] == 3.5
    assert flat["land_min_crew"] == 4
    assert flat["dist_penalty"] == 3.0
    assert flat["prio_dig_weed"] == 180.0
    assert flat["shed_pressure"] == 90

    reconstructed_from_flat = Parameters.from_dict(flat)
    assert reconstructed_from_flat.procurement.land_cost_mult == 3.5
    assert reconstructed_from_flat.dispatcher.dist_penalty == 3.0
    assert reconstructed_from_flat.market_maker.shed_pressure == 90

    nested = custom.to_dict(flat=False)
    assert nested["procurement"]["land_cost_mult"] == 3.5
    reconstructed_from_nested = Parameters.from_dict(nested)
    assert reconstructed_from_nested == custom


def test_json_serialization_round_trip(tmp_path: Path) -> None:
    """Serialization to JSON string and file round-trips cleanly."""
    custom = Parameters(
        procurement=ProcurementParams(land_cost_mult=2.7),
        market_maker=MarketMakerParams(ramp_start=500),
    )
    json_file = tmp_path / "params.json"
    custom.to_json(json_file)

    loaded = Parameters.from_json(json_file)
    assert loaded.procurement.land_cost_mult == 2.7
    assert loaded.market_maker.ramp_start == 500

    raw_json = custom.to_json()
    loaded_str = Parameters.from_json(raw_json)
    assert loaded_str == custom


def test_clone_with_modifications() -> None:
    """clone_with applies flat and grouped overrides without mutating original."""
    base = DEFAULT_PARAMETERS
    modified = base.clone_with(
        land_cost_mult=1.5,
        dist_penalty=4.0,
    )
    assert modified.procurement.land_cost_mult == 1.5
    assert modified.dispatcher.dist_penalty == 4.0
    # Original remains unchanged
    assert base.procurement.land_cost_mult == 2.0
    assert base.dispatcher.dist_penalty == 2.0


# =============================================================================
# Parameter Auto-Discovery & Loading Tests
# =============================================================================


def test_load_parameters_explicit_source(tmp_path: Path) -> None:
    """Explicit source argument (dict, JSON string, or Path) takes highest precedence."""
    custom_dict = {"land_cost_mult": 3.75, "dist_penalty": 4.5}
    p1 = load_parameters(source=custom_dict)
    assert p1.procurement.land_cost_mult == 3.75
    assert p1.dispatcher.dist_penalty == 4.5

    custom_json = json.dumps(custom_dict)
    p2 = load_parameters(source=custom_json)
    assert p2.procurement.land_cost_mult == 3.75

    file_path = tmp_path / "custom.json"
    file_path.write_text(custom_json, encoding="utf-8")
    p3 = load_parameters(source=file_path)
    assert p3.procurement.land_cost_mult == 3.75


def test_load_parameters_from_env_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """JEREMY_PARAMS_PATH env var loads parameters from specified path."""
    p_file = tmp_path / "env_params.json"
    p_file.write_text(json.dumps({"land_cost_mult": 3.9}), encoding="utf-8")

    monkeypatch.setenv("JEREMY_PARAMS_PATH", str(p_file))
    loaded = load_parameters()
    assert loaded.procurement.land_cost_mult == 3.9


def test_load_parameters_from_env_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """JEREMY_PARAMS_JSON env var loads parameters from inline JSON string."""
    monkeypatch.setenv("JEREMY_PARAMS_JSON", json.dumps({"dist_penalty": 4.8}))
    loaded = load_parameters()
    assert loaded.dispatcher.dist_penalty == 4.8


def test_load_parameters_from_embedded_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EMBEDDED_PARAMS_JSON is parsed when injected for standalone builds."""
    monkeypatch.setattr(
        "src.parameters.EMBEDDED_PARAMS_JSON",
        json.dumps({"glut_weight_melon": 4.9}),
    )
    loaded = load_parameters()
    assert loaded.market_maker.glut_weight_melon == 4.9


def test_load_parameters_corrupt_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Corrupted JSON sources gracefully fall back down the chain to defaults."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{corrupt: json}", encoding="utf-8")

    monkeypatch.setenv("JEREMY_PARAMS_PATH", str(bad_file))
    # Should not raise, falls back to defaults
    loaded = load_parameters()
    assert loaded == Parameters()


# =============================================================================
# Runtime Context & Agent Integration Tests
# =============================================================================


def test_scoped_context_isolation() -> None:
    """use_parameters isolates parameter changes within context block."""
    assert get_active_parameters() == DEFAULT_PARAMETERS

    trial_params = DEFAULT_PARAMETERS.clone_with(dist_penalty=5.0)
    with use_parameters(trial_params):
        assert get_active_parameters().dispatcher.dist_penalty == 5.0

    # Restores after exit
    assert get_active_parameters().dispatcher.dist_penalty == 2.0


def test_make_agent_closure() -> None:
    """make_agent returns an executable agent closure bound to custom parameters."""
    custom_params = DEFAULT_PARAMETERS.clone_with(dist_penalty=4.5)
    custom_agent = make_agent(custom_params)

    obs = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [2, 2],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [7, 7],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": {},
            "seeds": {"WHEAT": 5},
            "inventories": [{}],
        },
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
    }

    act = custom_agent(obs)
    assert "farmer" in act
    assert "market" in act
    assert "hands" in act


def test_dispatcher_respects_custom_dispatcher_params() -> None:
    """generate_jobs priority matches custom DispatcherParams passed explicitly."""
    obs = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [0, 0],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            }
        ],
        "private": {
            "shed": {},
            "seeds": {"WHEAT": 10},
            "inventories": [{}],
        },
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
    }
    state = GameState.from_obs(obs)
    board = Board(state)

    custom_dp = DispatcherParams(prio_plant_base=999.0)
    jobs = generate_jobs(state, board, target_crop="WHEAT", params=custom_dp)
    plant_jobs = [j for j in jobs if j.action == "PLANT"]
    assert len(plant_jobs) > 0
    assert plant_jobs[0].priority == 999.0


def test_reserved_animal_tiles_hyperparameter_override() -> None:
    """Configuring reserved_animal_tiles dynamically adjusts excluded plant tiles."""
    obs = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [
            {
                "money": 3000,
                "tiles": [[None for _ in range(10)] for _ in range(10)],
                "farmer": [0, 0],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            }
        ],
        "private": {
            "shed": {},
            "seeds": {"WHEAT": 100},
            "inventories": [{}],
        },
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
    }
    state = GameState.from_obs(obs)
    board = Board(state)

    # Override with 3 reserved tiles: (3, 4), (4, 3), (3, 3)
    custom_dp = DispatcherParams(reserved_animal_tiles=3)
    jobs = generate_jobs(state, board, target_crop="WHEAT", params=custom_dp)
    plant_targets = {j.target for j in jobs if j.action == "PLANT"}

    assert (3, 4) not in plant_targets
    assert (4, 3) not in plant_targets
    assert (3, 3) not in plant_targets

    # With 1 reserved tile: only (3, 4) is reserved; (4, 3) and (3, 3) are planted
    custom_dp_1 = DispatcherParams(reserved_animal_tiles=1)
    jobs_1 = generate_jobs(
        state, board, target_crop="WHEAT", params=custom_dp_1
    )
    plant_targets_1 = {j.target for j in jobs_1 if j.action == "PLANT"}

    assert (3, 4) not in plant_targets_1
    assert (4, 3) in plant_targets_1
    assert (3, 3) in plant_targets_1
