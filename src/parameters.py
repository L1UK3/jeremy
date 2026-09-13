"""Centralized agent runtime hyperparameter configuration and parsing."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar

_logger = logging.getLogger(__name__)

EMBEDDED_PARAMS_JSON: str | None = None

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

    reserved_animal_tiles: int = 6
    seed_fallback_crop: str = "WHEAT"
    expansion_day_ne: int = 7
    expansion_day_sw: int = 11
    actions_per_hand: float = 8.0
    max_daily_hires: int = 12


@dataclass(frozen=True, slots=True)
class DispatcherParams:
    """Hyperparameters governing chore priorities and spatial scheduling."""

    prio_feed_urgent: float = 350.0
    prio_water_urgent: float = 300.0
    prio_drop_shed: float = 260.0
    prio_harvest_premium: float = 250.0
    prio_place_animal: float = 245.0
    prio_pickup_animal: float = 240.0
    prio_build_structure: float = 220.0
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
    reserved_animal_tiles: int = 6


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

    Provides serialization, dictionary conversion, and partial overrides.
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

    @classmethod
    def from_trial(
        cls,
        trial: Any,
        groups: Sequence[str] | None = None,
        base: Parameters | None = None,
    ) -> Parameters:
        """Sample hyperparameters from an Optuna trial."""
        from simulation.tuning.search_space import sample_parameters

        return sample_parameters(trial, groups=groups, base=base)


# =============================================================================
# Parameter Auto-Discovery & Loading
# =============================================================================


def load_parameters(
    source: Path | str | dict[str, Any] | None = None,
) -> Parameters:
    """Load and parse Parameters following the agreed resolution precedence:

    1. Explicit `source` argument (dict, JSON string, or Path to JSON file)
    2. Environment variable `JEREMY_PARAMS_PATH` (file path) or `JEREMY_PARAMS_JSON` (raw JSON)
    3. File adjacent to `parameters.py` (`Path(__file__).parent / "parameters.json"`)
    4. Working directory `./parameters.json` (`Path.cwd() / "parameters.json"`)
    5. Injected module payload `EMBEDDED_PARAMS_JSON`
    6. Canonical `Parameters()` dataclass defaults

    If any candidate JSON file or payload is corrupted or invalid, logs a warning
    and gracefully continues down the fallback chain.
    """
    if source is not None:
        try:
            if isinstance(source, dict):
                return Parameters.from_dict(source)
            return Parameters.from_json(source)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from explicit source: %s", e
            )

    env_path = os.environ.get("JEREMY_PARAMS_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            try:
                return Parameters.from_json(p)
            except Exception as e:
                _logger.warning(
                    "Failed to load parameters from JEREMY_PARAMS_PATH (%s): %s",
                    p,
                    e,
                )

    env_json = os.environ.get("JEREMY_PARAMS_JSON")
    if env_json:
        try:
            return Parameters.from_json(env_json)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from JEREMY_PARAMS_JSON: %s", e
            )

    adjacent_path = Path(__file__).parent / "parameters.json"
    if adjacent_path.is_file():
        try:
            return Parameters.from_json(adjacent_path)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from adjacent file (%s): %s",
                adjacent_path,
                e,
            )

    file_attr = globals().get("__file__")
    adjacent_path = (
        Path(file_attr).parent / "parameters.json" if file_attr else None
    )
    if adjacent_path and adjacent_path.is_file():
        try:
            return Parameters.from_json(adjacent_path)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from adjacent file (%s): %s",
                adjacent_path,
                e,
            )

    cwd_path = Path.cwd() / "parameters.json"
    if cwd_path.is_file() and cwd_path.resolve() != adjacent_path.resolve():
        try:
            return Parameters.from_json(cwd_path)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from cwd (%s): %s", cwd_path, e
            )

    if EMBEDDED_PARAMS_JSON:
        try:
            return Parameters.from_json(EMBEDDED_PARAMS_JSON)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from EMBEDDED_PARAMS_JSON: %s", e
            )

    if EMBEDDED_PARAMS_JSON:
        try:
            return Parameters.from_json(EMBEDDED_PARAMS_JSON)
        except Exception as e:
            _logger.warning(
                "Failed to load parameters from EMBEDDED_PARAMS_JSON: %s", e
            )

    return Parameters()


# Canonical default instance, resolved at module load
DEFAULT_PARAMETERS: Parameters = load_parameters()


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
    "EMBEDDED_PARAMS_JSON",
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
    "load_parameters",
    "set_active_parameters",
    "use_parameters",
]
