"""Centralized agent hyperparameter configuration and Optuna tuning interface."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar


# =============================================================================
# Subsystem Parameter Groups
# =============================================================================


@dataclass(frozen=True, slots=True)
class ProcurementParams:
    """Hyperparameters governing asset procurement and land expansion."""

    land_cost_mult: float = 2.0
    land_min_crew: int = 3
    max_hire_hour: int = 2
    feed_buffer_mult: int = 2
    feed_target_buffer: int = 2
    max_animals: int = 2
    seed_fallback_crop: str = "WHEAT"


@dataclass(frozen=True, slots=True)
class DispatcherParams:
    """Hyperparameters governing chore priorities and spatial scheduling."""

    prio_feed_urgent: float = 350.0
    prio_water_urgent: float = 300.0
    prio_drop_shed: float = 260.0
    prio_harvest_premium: float = 250.0
    prio_feed: float = 200.0
    prio_care: float = 180.0
    prio_water_bonus: float = 160.0
    prio_harvest_base: float = 150.0
    prio_dig_weed: float = 140.0
    prio_water: float = 120.0
    prio_plant_base: float = 75.0
    prio_plant_cascade: float = 65.0
    prio_fertilize: float = 70.0
    prio_collect_fertilizer: float = 60.0
    dist_penalty: float = 2.0
    harvest_crop_yield_threshold: int = 4
    crop_weight_threshold: float = 0.15
    last_water_day: int = 28


@dataclass(frozen=True, slots=True)
class MarketMakerParams:
    """Hyperparameters governing market sell orders and price liquidation."""

    glut_weight_melon: float = 3.5
    glut_weight_strawberry: float = 2.0
    glut_weight_milk: float = 2.0
    glut_weight_wool: float = 3.2
    sort_sells: bool = True
    sort_key: str = "impact"
    sells_first: bool = True
    race_weight: float = 0.0
    shed_pressure: int = 80
    ramp_start: int = 576
    ramp_end: int = 716
    front_run_horizon: int = 1
    early_terminal: int = 0


@dataclass(frozen=True, slots=True)
class PredationParams:
    """Hyperparameters governing opponent counter-strategies."""

    front_run_discount: float = 0.85
    corner_wheat_buy_qty: int = 5
    surplus_wheat_mult: int = 2


@dataclass(frozen=True, slots=True)
class WeedRepairParams:
    """Hyperparameters governing reactive weed clearing."""

    weed_repair_cutoff_step: int = 672


@dataclass(frozen=True, slots=True)
class ExplosionParams:
    """Hyperparameters governing final-turn liquidation."""

    explosion_step: int = 712
    pre_terminal_step: int = 672
    terminal_glut_weight_melon: float = 3.6
    terminal_glut_weight_wool: float = 3.2
    terminal_glut_weight_milk: float = 2.0
    terminal_glut_weight_strawberry: float = 2.0
    terminal_glut_weight_egg: float = 1.5
    terminal_glut_weight_tomato: float = 1.3


@dataclass(frozen=True, slots=True)
class DebtManagerParams:
    """Hyperparameters governing opening sequence liquidity."""

    opening_strategy: str = "feed5"


@dataclass(frozen=True, slots=True)
class CloneDetectorParams:
    """Hyperparameters governing public farm clone detection thresholds."""

    clone_distance_high: int = 1
    clone_distance_medium: int = 4


# =============================================================================
# Composite Root Parameters Container
# =============================================================================


@dataclass(frozen=True, slots=True)
class Parameters:
    """Complete agent configuration composite.

    Provides serialization, Optuna search space sampling, and partial overrides.
    """

    procurement: ProcurementParams = field(default_factory=ProcurementParams)
    dispatcher: DispatcherParams = field(default_factory=DispatcherParams)
    market_maker: MarketMakerParams = field(default_factory=MarketMakerParams)
    predation: PredationParams = field(default_factory=PredationParams)
    weed_repair: WeedRepairParams = field(default_factory=WeedRepairParams)
    explosion: ExplosionParams = field(default_factory=ExplosionParams)
    debt_manager: DebtManagerParams = field(default_factory=DebtManagerParams)
    clone_detector: CloneDetectorParams = field(
        default_factory=CloneDetectorParams
    )

    GROUPS: ClassVar[tuple[str, ...]] = (
        "procurement",
        "dispatcher",
        "market_maker",
        "predation",
        "weed_repair",
        "explosion",
        "debt_manager",
        "clone_detector",
    )

    @classmethod
    def from_trial(
        cls, trial: Any, groups: tuple[str, ...] | list[str] | None = None
    ) -> Parameters:
        """Sample candidate hyperparameters from an Optuna Trial."""
        active = set(groups) if groups is not None else None

        def in_group(g: str) -> bool:
            return active is None or g in active

        return cls(
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
                )
                if in_group("procurement")
                else ProcurementParams()
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
                else DispatcherParams()
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
                    ramp_start=trial.suggest_int(
                        "ramp_start", 480, 648, step=24
                    ),
                    ramp_end=trial.suggest_int("ramp_end", 672, 718, step=2),
                    front_run_horizon=trial.suggest_int(
                        "front_run_horizon", 1, 5
                    ),
                    early_terminal=trial.suggest_int("early_terminal", 0, 10),
                )
                if in_group("market_maker")
                else MarketMakerParams()
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
                else PredationParams()
            ),
            weed_repair=(
                WeedRepairParams(
                    weed_repair_cutoff_step=trial.suggest_int(
                        "weed_repair_cutoff_step", 600, 700, step=24
                    ),
                )
                if in_group("weed_repair")
                else WeedRepairParams()
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
                else ExplosionParams()
            ),
            debt_manager=(
                DebtManagerParams(
                    opening_strategy=trial.suggest_categorical(
                        "opening_strategy", ["feed5", "fast_expand", "passive"]
                    ),
                )
                if in_group("debt_manager")
                else DebtManagerParams()
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
                else CloneDetectorParams()
            ),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Parameters:
        """Construct Parameters from a flat or nested dictionary."""
        groups = {
            "procurement": ProcurementParams,
            "dispatcher": DispatcherParams,
            "market_maker": MarketMakerParams,
            "predation": PredationParams,
            "weed_repair": WeedRepairParams,
            "explosion": ExplosionParams,
            "debt_manager": DebtManagerParams,
            "clone_detector": CloneDetectorParams,
        }
        field_to_group = {
            f: g
            for g, g_cls in groups.items()
            for f in g_cls.__dataclass_fields__
        }

        nested: dict[str, dict[str, Any]] = {g: {} for g in groups}

        for g in groups:
            if isinstance(data.get(g), dict):
                nested[g].update(data[g])

        for k, v in data.items():
            if k in groups:
                continue
            prefixed = False
            for sep in ("__", "."):
                if sep in k:
                    prefix, name = k.split(sep, 1)
                    if prefix in nested:
                        nested[prefix][name] = v
                        prefixed = True
                        break
            if not prefixed and k in field_to_group:
                nested[field_to_group[k]][k] = v

        return cls(**{g: groups[g](**vals) for g, vals in nested.items()})

    def to_dict(self, flat: bool = True) -> dict[str, Any]:
        """Convert parameters to dictionary (flat or nested)."""
        nested = {g: asdict(getattr(self, g)) for g in self.GROUPS}
        if not flat:
            return nested
        return {k: v for g_dict in nested.values() for k, v in g_dict.items()}

    def to_json(self, path: str | Path | None = None, indent: int = 2) -> str:
        """Serialize configuration to a JSON string or file."""
        text = json.dumps(self.to_dict(flat=False), indent=indent)
        if path is not None:
            Path(path).write_text(text, encoding="utf-8")
        return text

    @classmethod
    def from_json(cls, source: str | Path) -> Parameters:
        """Load configuration from a JSON file path or string."""
        if isinstance(source, Path) or (
            isinstance(source, str) and not source.strip().startswith("{")
        ):
            p = Path(source)
            if p.is_file():
                return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))
        return cls.from_dict(json.loads(str(source)))

    def clone_with(self, **kwargs: Any) -> Parameters:
        """Return a copy of Parameters with updated values."""
        d = self.to_dict(flat=False)
        for k, v in kwargs.items():
            if k in d:
                if isinstance(v, dict):
                    d[k].update(v)
                elif hasattr(v, "__dataclass_fields__"):
                    d[k] = asdict(v)
            else:
                for group_vals in d.values():
                    if k in group_vals:
                        group_vals[k] = v
                        break
        return Parameters.from_dict(d)


# Canonical default instance
DEFAULT_PARAMETERS: Parameters = Parameters()


# =============================================================================
# Scoped Runtime Context
# =============================================================================

_ACTIVE_PARAMETERS: Parameters | None = None


def get_active_parameters() -> Parameters:
    """Retrieve the currently active Parameters instance."""
    return (
        _ACTIVE_PARAMETERS
        if _ACTIVE_PARAMETERS is not None
        else DEFAULT_PARAMETERS
    )


def set_active_parameters(params: Parameters | None) -> None:
    """Set the globally active Parameters instance."""
    global _ACTIVE_PARAMETERS
    _ACTIVE_PARAMETERS = params


@contextmanager
def use_parameters(params: Parameters):
    """Context manager for temporary execution with specific Parameters."""
    global _ACTIVE_PARAMETERS
    previous = _ACTIVE_PARAMETERS
    _ACTIVE_PARAMETERS = params
    try:
        yield params
    finally:
        _ACTIVE_PARAMETERS = previous


__all__ = [
    "DEFAULT_PARAMETERS",
    "CloneDetectorParams",
    "DebtManagerParams",
    "DispatcherParams",
    "ExplosionParams",
    "MarketMakerParams",
    "Parameters",
    "PredationParams",
    "ProcurementParams",
    "WeedRepairParams",
    "get_active_parameters",
    "set_active_parameters",
    "use_parameters",
]

