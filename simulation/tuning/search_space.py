"""Optuna trial sampling routines for agent hyperparameters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.parameters import (
    CloneDetectorParams,
    DebtManagerParams,
    DispatcherParams,
    ExplosionParams,
    MarketMakerParams,
    Parameters,
    PlotAllocationParams,
    PredationParams,
    ProcurementParams,
    WeedRepairParams,
)


def sample_parameters(
    trial: Any,
    groups: Sequence[str] | None = None,
    base: Parameters | None = None,
) -> Parameters:
    """Sample candidate hyperparameters from an Optuna Trial.

    Active groups are sampled according to their search spaces.
    Non-sampled groups inherit their configuration from `base`
    (or default to `Parameters()` if `base` is not provided).
    """
    active = set(groups) if groups is not None else None
    base_params = base if base is not None else Parameters()

    def in_group(g: str) -> bool:
        return active is None or g in active

    return Parameters(
        procurement=(
            ProcurementParams(
                land_cost_mult=trial.suggest_float(
                    "land_cost_mult", 1.0, 4.0, step=0.1
                ),
                land_min_crew=trial.suggest_int("land_min_crew", 1, 6),
                max_hire_hour=trial.suggest_int("max_hire_hour", 0, 6),
                feed_buffer_mult=trial.suggest_int("feed_buffer_mult", 1, 5),
                feed_target_buffer=trial.suggest_int(
                    "feed_target_buffer", 0, 6
                ),
                max_animals=trial.suggest_int("max_animals", 1, 4),
                seed_fallback_crop=trial.suggest_categorical(
                    "seed_fallback_crop", ["WHEAT", "CARROT"]
                ),
                actions_per_hand=trial.suggest_float(
                    "actions_per_hand", 4.0, 12.0, step=1.0
                ),
                max_daily_hires=trial.suggest_int("max_daily_hires", 4, 16),
            )
            if in_group("procurement")
            else base_params.procurement
        ),
        dispatcher=(
            DispatcherParams(
                prio_feed_urgent=trial.suggest_float(
                    "prio_feed_urgent", 200.0, 500.0, step=10.0
                ),
                prio_water_urgent=trial.suggest_float(
                    "prio_water_urgent", 200.0, 450.0, step=10.0
                ),
                prio_drop_shed=trial.suggest_float(
                    "prio_drop_shed", 150.0, 400.0, step=10.0
                ),
                prio_harvest_premium=trial.suggest_float(
                    "prio_harvest_premium", 150.0, 350.0, step=10.0
                ),
                prio_feed=trial.suggest_float(
                    "prio_feed", 100.0, 300.0, step=10.0
                ),
                prio_care=trial.suggest_float(
                    "prio_care", 100.0, 250.0, step=10.0
                ),
                prio_water_bonus=trial.suggest_float(
                    "prio_water_bonus", 100.0, 250.0, step=10.0
                ),
                prio_harvest_base=trial.suggest_float(
                    "prio_harvest_base", 80.0, 220.0, step=10.0
                ),
                prio_dig_weed=trial.suggest_float(
                    "prio_dig_weed", 80.0, 200.0, step=10.0
                ),
                prio_water=trial.suggest_float(
                    "prio_water", 60.0, 180.0, step=10.0
                ),
                prio_plant_base=trial.suggest_float(
                    "prio_plant_base", 30.0, 150.0, step=5.0
                ),
                prio_plant_cascade=trial.suggest_float(
                    "prio_plant_cascade", 30.0, 120.0, step=5.0
                ),
                prio_fertilize=trial.suggest_float(
                    "prio_fertilize", 30.0, 120.0, step=5.0
                ),
                prio_collect_fertilizer=trial.suggest_float(
                    "prio_collect_fertilizer", 20.0, 100.0, step=5.0
                ),
                dist_penalty=trial.suggest_float(
                    "dist_penalty", 0.5, 5.0, step=0.25
                ),
                harvest_crop_yield_threshold=trial.suggest_int(
                    "harvest_crop_yield_threshold", 2, 5
                ),
                crop_weight_threshold=trial.suggest_float(
                    "crop_weight_threshold", 0.05, 0.40, step=0.05
                ),
                last_water_day=trial.suggest_int("last_water_day", 26, 29),
            )
            if in_group("dispatcher")
            else base_params.dispatcher
        ),
        market_maker=(
            MarketMakerParams(
                glut_weight_melon=trial.suggest_float(
                    "glut_weight_melon", 1.0, 5.0, step=0.25
                ),
                glut_weight_strawberry=trial.suggest_float(
                    "glut_weight_strawberry", 1.0, 4.0, step=0.25
                ),
                glut_weight_milk=trial.suggest_float(
                    "glut_weight_milk", 1.0, 4.0, step=0.25
                ),
                glut_weight_wool=trial.suggest_float(
                    "glut_weight_wool", 1.0, 5.0, step=0.25
                ),
                sort_sells=trial.suggest_categorical(
                    "sort_sells", [True, False]
                ),
                sort_key=trial.suggest_categorical(
                    "sort_key", ["impact", "unit_price", "revenue"]
                ),
                sells_first=trial.suggest_categorical(
                    "sells_first", [True, False]
                ),
                race_weight=trial.suggest_float(
                    "race_weight", 0.0, 1.0, step=0.1
                ),
                shed_pressure=trial.suggest_int(
                    "shed_pressure", 50, 95, step=5
                ),
                ramp_start=trial.suggest_int("ramp_start", 480, 648, step=24),
                ramp_end=trial.suggest_int("ramp_end", 672, 718, step=2),
                front_run_horizon=trial.suggest_int("front_run_horizon", 1, 5),
                early_terminal=trial.suggest_int("early_terminal", 0, 10),
            )
            if in_group("market_maker")
            else base_params.market_maker
        ),
        predation=(
            PredationParams(
                front_run_discount=trial.suggest_float(
                    "front_run_discount", 0.70, 0.95, step=0.05
                ),
                corner_wheat_buy_qty=trial.suggest_int(
                    "corner_wheat_buy_qty", 1, 10
                ),
                surplus_wheat_mult=trial.suggest_int(
                    "surplus_wheat_mult", 1, 4
                ),
            )
            if in_group("predation")
            else base_params.predation
        ),
        weed_repair=(
            WeedRepairParams(
                weed_repair_cutoff_step=trial.suggest_int(
                    "weed_repair_cutoff_step", 600, 700, step=24
                ),
            )
            if in_group("weed_repair")
            else base_params.weed_repair
        ),
        explosion=(
            ExplosionParams(
                explosion_step=trial.suggest_int(
                    "explosion_step", 700, 718, step=2
                ),
                pre_terminal_step=trial.suggest_int(
                    "pre_terminal_step", 624, 700, step=24
                ),
                terminal_glut_weight_melon=trial.suggest_float(
                    "terminal_glut_weight_melon", 1.0, 5.0, step=0.2
                ),
                terminal_glut_weight_wool=trial.suggest_float(
                    "terminal_glut_weight_wool", 1.0, 5.0, step=0.2
                ),
                terminal_glut_weight_milk=trial.suggest_float(
                    "terminal_glut_weight_milk", 1.0, 4.0, step=0.2
                ),
                terminal_glut_weight_strawberry=trial.suggest_float(
                    "terminal_glut_weight_strawberry", 1.0, 4.0, step=0.2
                ),
                terminal_glut_weight_egg=trial.suggest_float(
                    "terminal_glut_weight_egg", 1.0, 3.0, step=0.1
                ),
                terminal_glut_weight_tomato=trial.suggest_float(
                    "terminal_glut_weight_tomato", 1.0, 3.0, step=0.1
                ),
            )
            if in_group("explosion")
            else base_params.explosion
        ),
        debt_manager=(
            DebtManagerParams(
                opening_strategy=trial.suggest_categorical(
                    "opening_strategy", ["feed5", "fast_expand", "passive"]
                ),
            )
            if in_group("debt_manager")
            else base_params.debt_manager
        ),
        clone_detector=(
            CloneDetectorParams(
                clone_distance_high=trial.suggest_int(
                    "clone_distance_high", 0, 3
                ),
                clone_distance_medium=trial.suggest_int(
                    "clone_distance_medium", 3, 7
                ),
            )
            if in_group("clone_detector")
            else base_params.clone_detector
        ),
        plot_allocation=(
            PlotAllocationParams(
                animals_per_quadrant=trial.suggest_int(
                    "animals_per_quadrant", 1, 9
                ),
            )
            if in_group("plot_allocation")
            else base_params.plot_allocation
        ),
    )
