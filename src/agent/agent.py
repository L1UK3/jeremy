"""
Main agent entrypoint.
Integrates the high-performing encoded consensus model policy with fallback
to the modular rule-based heuristics planner.
"""

import importlib
from collections.abc import Callable

from planner import Planner
from state import GameState

_model_agent: Callable[[dict], dict] | None = None


def _get_model_agent() -> Callable[[dict], dict] | None:
    global _model_agent
    if _model_agent is None:
        for mod_name in ("package.unpack", "src.package.unpack", "unpack"):
            try:
                mod = importlib.import_module(mod_name)
                fn = getattr(mod, "load_agent_from_payload", None)
                if fn and callable(fn):
                    _model_agent = fn() # type: ignore
                    break
            except Exception:
                pass
    return _model_agent


def agent(obs: dict) -> dict:
    """Main agent callback for Kaggriculture."""
    model = _get_model_agent()
    if model is not None:
        try:
            return model(obs)
        except Exception:
            pass

    # Heuristic planner fallback
    state = GameState.from_obs(obs)
    planner = Planner(state)
    return planner.play().to_dict()
