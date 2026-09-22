from __future__ import annotations

import argparse
import sys
import types
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

_dummy = types.ModuleType(
    "kaggle_environments.envs.open_spiel_env.open_spiel_env"
)
_dummy.ENV_REGISTRY = {}
_dummy.LAZY_ENV_LOADERS = {}
sys.modules["kaggle_environments.envs.open_spiel_env.open_spiel_env"] = _dummy

from kaggle_environments import make

AgentType = str | Callable[[dict, dict | None], dict]
WinnerType = Literal["challenger", "baseline", "tie"]
DEFAULT_REPLAY_DIR = Path(".out/replays")


@dataclass(slots=True)
class EpisodeResult:
    episode_idx: int
    winner: WinnerType
    score_challenger: float
    score_baseline: float
    challenger_final_inventory: dict[str, int] = field(default_factory=dict)
    replay_path: str | None = None
    env: Any = None


def run_episode(
    challenger: str = "src/main.py",
    baseline: str = "starter",
    seat: int = 0,
    steps: int = 720,
    keep_env: bool = False,
    seed: int | None = None,
) -> EpisodeResult:
    """Runs a single 2-player Kaggriculture game and returns an EpisodeResult."""
    config: dict[str, Any] = {"episodeSteps": steps}
    if seed is not None:
        config["seed"] = seed
    env: Any = make(
        "kaggriculture", configuration=config, debug=False
    )
    agents: list[str] = (
        [challenger, baseline] if seat == 0 else [baseline, challenger]
    )

    env.run(agents)

    final_step: list[dict[str, Any]] = env.steps[-1]
    p_chal: dict[str, Any] = final_step[seat]
    p_base: dict[str, Any] = final_step[1 - seat]

    c_score: float = float(p_chal.get("reward") or 0.0)
    b_score: float = float(p_base.get("reward") or 0.0)

    winner: WinnerType = (
        "challenger"
        if c_score > b_score
        else ("baseline" if b_score > c_score else "tie")
    )

    c_obs: dict[str, Any] = p_chal.get("observation") or {}
    c_shed: dict[str, int] = (
        c_obs.get("private", {}).get("shed", {})
        if isinstance(c_obs, dict)
        else {}
    )

    episode_idx: int = 0

    out_path: Path = DEFAULT_REPLAY_DIR / f"episode_{episode_idx}.html"

    if out_path.exists():
        while out_path.exists():
            episode_idx += 1
            out_path = DEFAULT_REPLAY_DIR / f"episode_{episode_idx}.html"

    DEFAULT_REPLAY_DIR.mkdir(parents=True, exist_ok=True)

    out_path.write_text(env.render(mode="html"), encoding="utf-8")

    return EpisodeResult(
        episode_idx=episode_idx,
        winner=winner,
        score_challenger=c_score,
        score_baseline=b_score,
        challenger_final_inventory=c_shed,
        replay_path=out_path.as_posix(),
        env=env if keep_env else None,
    )


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Run a Kaggriculture episode."
    )
    parser.add_argument(
        "--challenger",
        type=str,
        default="src/main.py",
        help="Path to the challenger agent (default: src/main.py)",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="simulation/base/main.py",
        help="Path to the baseline agent (default: starter)",
    )

    parsed: argparse.Namespace = parser.parse_args()
    result: EpisodeResult = run_episode(
        challenger=parsed.challenger,
        baseline=parsed.baseline,
    )

    msg: str = (
        f"Episode {result.episode_idx} | "
        f"Winner: {result.winner} | "
        f"Score: {result.score_challenger:.0f} vs {result.score_baseline:.0f} \n"
        f"Replay path: {result.replay_path}\n\n"
        f"Challenger final inventory: {result.challenger_final_inventory}"
    )

    print(msg)
