from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from kaggle_environments import make

AgentType = str | Callable[[dict, dict | None], dict]
WinnerType = Literal["challenger", "baseline", "tie"]


@dataclass(slots=True)
class EpisodeResult:
    episode_idx: int
    seat: int
    winner: WinnerType
    score_challenger: float
    score_baseline: float
    duration_sec: float = 0.0
    status_challenger: str = "DONE"
    status_baseline: str = "DONE"
    error_challenger: str | None = None
    error_baseline: str | None = None
    turns: int = 720
    challenger_inventory: dict[str, int] = field(default_factory=dict)
    replay_path: str | None = None
    env: Any = None


def run_episode(
    challenger: Any = "src/main.py",
    baseline: Any = "starter",
    seat: int = 0,
    episode_idx: int = 0,
    seed: int | None = None,
    steps: int = 720,
    debug: bool = False,
    save_replay_path: Path | str | None = None,
    replay_format: Literal["html", "json"] = "html",
    keep_env: bool = False,
    configuration: dict | None = None,
) -> EpisodeResult:
    """Runs a single 2-player Kaggriculture game and returns an EpisodeResult."""
    config: dict[str, Any] = {"episodeSteps": steps, **(configuration or {})}
    if seed is not None:
        config["seed"] = seed

    env = make("kaggriculture", configuration=config, debug=debug)
    agents = [challenger, baseline] if seat == 0 else [baseline, challenger]

    start_time = time.perf_counter()
    env.run(agents)
    duration_sec = time.perf_counter() - start_time

    final_step = env.steps[-1]
    p_chal, p_base = final_step[seat], final_step[1 - seat]

    c_score = float(p_chal.get("reward") or 0.0)
    b_score = float(p_base.get("reward") or 0.0)

    winner: WinnerType = (
        "challenger"
        if c_score > b_score
        else ("baseline" if b_score > c_score else "tie")
    )

    c_obs = p_chal.get("observation") or {}
    c_shed = (
        c_obs.get("private", {}).get("shed", {})
        if isinstance(c_obs, dict)
        else {}
    )

    replay_str: str | None = None
    if save_replay_path:
        out_path = Path(save_replay_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if replay_format == "json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(env.toJSON(), f)
        else:
            out_path.write_text(env.render(mode="html"), encoding="utf-8")
        replay_str = str(out_path.resolve())

    return EpisodeResult(
        episode_idx=episode_idx,
        seat=seat,
        winner=winner,
        score_challenger=c_score,
        score_baseline=b_score,
        duration_sec=duration_sec,
        status_challenger=str(p_chal.get("status", "DONE")),
        status_baseline=str(p_base.get("status", "DONE")),
        error_challenger=p_chal.get("error") or c_obs.get("error"),
        error_baseline=p_base.get("error"),
        turns=len(env.steps),
        challenger_inventory=c_shed,
        replay_path=replay_str,
        env=env if keep_env else None,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Kaggriculture episode.")
    parser.add_argument(
        "--challenger",
        type=str,
        default="src/main.py",
        help="Path to the challenger agent (default: src/main.py)",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="starter",
        help="Path to the baseline agent (default: starter)",
    )
    parser.add_argument(
        "--replay_path",
        type=str,
        help="Path to save the replay (JSON or HTML format)",
    )
    parser.add_argument(
        "--seat",
        type=int,
        default=0,
        help="Seat of challenger (0 or 1)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=720,
        help="Episode steps (default: 720)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Game random seed",
    )

    parsed = parser.parse_args()
    res = run_episode(
        challenger=parsed.challenger,
        baseline=parsed.baseline,
        seat=parsed.seat,
        steps=parsed.steps,
        seed=parsed.seed,
        save_replay_path=parsed.replay_path,
    )
    print(
        f"Episode {res.episode_idx} (Seat {res.seat}) in {res.duration_sec:.2f}s | "
        f"Winner: {res.winner} | Score: {res.score_challenger:.0f} vs {res.score_baseline:.0f}"
    )
