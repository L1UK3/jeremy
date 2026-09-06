"""Single episode simulation runner for Kaggriculture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from kaggle_environments import make


def run_episode(
    challenger: Any = "main.py",
    baseline: Any = "starter",
    seat: int = 0,
    replay_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run a 2-player Kaggriculture game and return match summary statistics."""

    env = make("kaggriculture")
    agents = [challenger, baseline] if seat == 0 else [baseline, challenger]

    env.run(agents)

    final_step = env.steps[-1]
    p_chal, p_base = final_step[seat], final_step[1 - seat]
    c_score = float(p_chal.get("reward") or 0.0)
    b_score = float(p_base.get("reward") or 0.0)

    if c_score > b_score:
        winner = "1"
    elif b_score > c_score:
        winner = "2"
    else:
        winner = "0"

    if replay_path:
        out = Path(replay_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix.lower() == ".json":
            out.write_text(json.dumps(env.toJSON()), encoding="utf-8")
        elif out.suffix.lower() == ".html":
            out.write_text(env.render(mode="html"), encoding="utf-8")
        else:
            raise ValueError(f"Unsupported replay file extension: {out.suffix}")

    return {
        "winner": winner,
        "score_challenger": c_score,
        "score_baseline": b_score,
    }


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Run a Kaggriculture episode.")
    args.add_argument(
        "--challenger",
        type=str,
        default="main.py",
        help="Path to the challenger agent (default: main.py)",
    )
    args.add_argument(
        "--baseline",
        type=str,
        default="starter",
        help="Path to the baseline agent (default: starter)",
    )

    args.add_argument(
        "--replay_path",
        type=str,
        help="Path to save the replay (JSON or HTML format)",
    )

    res = run_episode()
    print(
        f"Winner: {res['winner']} | Score: {res['score_challenger']:.0f} vs {res['score_baseline']:.0f}"
    )
