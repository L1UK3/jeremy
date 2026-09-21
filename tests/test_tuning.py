"""Unit tests for hyperparameter optimization search spaces and trial sampling."""

from __future__ import annotations

from typing import Any

from simulation.tuning.objective import create_objective
from simulation.tuning.search_space import sample_parameters
from src.parameters import (
    DEFAULT_PARAMETERS,
    Parameters,
)


class MockTrial:
    """Mock Optuna Trial recording suggest calls and returning specified or midpoint values."""

    def __init__(self, overrides: dict[str, Any] | None = None) -> None:
        self.overrides = overrides or {}
        self.recorded_calls: list[tuple[str, str, dict[str, Any]]] = []

    def suggest_float(
        self,
        name: str,
        low: float,
        high: float,
        *,
        step: float | None = None,
        log: bool = False,
    ) -> float:
        self.recorded_calls.append(
            (
                "float",
                name,
                {"low": low, "high": high, "step": step, "log": log},
            )
        )
        if name in self.overrides:
            return float(self.overrides[name])
        return (low + high) / 2.0

    def suggest_int(
        self,
        name: str,
        low: int,
        high: int,
        *,
        step: int | None = None,
        log: bool = False,
    ) -> int:
        self.recorded_calls.append(
            ("int", name, {"low": low, "high": high, "step": step, "log": log})
        )
        if name in self.overrides:
            return int(self.overrides[name])
        return (low + high) // 2

    def suggest_categorical(self, name: str, choices: list[Any]) -> Any:
        self.recorded_calls.append(
            ("categorical", name, {"choices": list(choices)})
        )
        if name in self.overrides:
            return self.overrides[name]
        return choices[0]


def test_sample_parameters_bounds_and_validity() -> None:
    """sample_parameters samples valid parameters with proper bounds."""
    trial = MockTrial()
    params = sample_parameters(trial)
    assert isinstance(params, Parameters)
    assert len(trial.recorded_calls) >= 40
    for kind, _name, kwargs in trial.recorded_calls:
        if kind in ("float", "int"):
            assert kwargs["low"] < kwargs["high"]
        elif kind == "categorical":
            assert len(kwargs["choices"]) > 0


def test_sample_parameters_samples_all_registered_parameters() -> None:
    """sample_parameters queries the trial for every optimizable parameter."""
    trial = MockTrial(overrides={"land_cost_mult": 3.2, "dist_penalty": 1.5})
    params = sample_parameters(trial)

    assert params.procurement.land_cost_mult == 3.2
    assert params.dispatcher.dist_penalty == 1.5
    assert len(trial.recorded_calls) == 57


def test_sample_parameters_with_selective_groups() -> None:
    """sample_parameters with groups only samples active groups; others take base defaults."""
    trial = MockTrial(overrides={"land_cost_mult": 3.8})
    params = sample_parameters(trial, groups=["procurement"])

    assert params.procurement.land_cost_mult == 3.8
    # Dispatcher was not in groups, must have canonical default
    assert (
        params.dispatcher.dist_penalty
        == DEFAULT_PARAMETERS.dispatcher.dist_penalty
    )
    # Only procurement specs should have been sampled (9 parameters)
    assert len(trial.recorded_calls) == 9


def test_sample_parameters_inherits_from_custom_base() -> None:
    """sample_parameters inherits non-sampled group values from custom base."""
    custom_base = DEFAULT_PARAMETERS.clone_with(
        dist_penalty=4.25,
        land_cost_mult=1.1,
    )
    trial = MockTrial(overrides={"land_cost_mult": 3.5})
    params = sample_parameters(trial, groups=["procurement"], base=custom_base)

    # Sampled from trial
    assert params.procurement.land_cost_mult == 3.5
    # Inherited from custom base
    assert params.dispatcher.dist_penalty == 4.25


def test_create_objective_returns_callable() -> None:
    """create_objective constructs a callable Optuna objective function."""
    obj = create_objective(
        groups=["procurement"],
        steps=24,
        seats=[0],
        seeds=[42],
    )
    assert callable(obj)
