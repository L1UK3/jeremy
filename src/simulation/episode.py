import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kaggle_environments import make


@dataclass(slots=True)
class EpisodeResult:
    episode_idx: int
    seat: int
    score_challenger: float
    score_baseline: float
    winner: int
    status_challenger: str = "DONE"
    status_baseline: str = "DONE"
    replay_path: str | None = None


class Episode:
    """
    Manages and executes a single 2-player Kaggriculture game between two agents.
    """

    def __init__(
        self,
        agent1: str | Callable = "agent.agent",
        agent2: str | Callable = "agent.agent",
        episode_idx: int = 0,
        seat: int = 0,
        debug: bool = False,
        configuration: dict | None = None,
    ) -> None:
        self.agent1 = agent1
        self.agent2 = agent2
        self.episode_idx = episode_idx
        self.seat = (
            seat  # 0: agent1 is P0, agent2 is P1; 1: agent1 is P1, agent2 is P0
        )
        self.debug = debug
        self.configuration = configuration or {"episodeSteps": 720}

        self.agent1_times: list[float] = []
        self.agent2_times: list[float] = []
        self.env: Any = None
        self.result: EpisodeResult | None = None

    def run(self) -> EpisodeResult:
        """Run the match and return the EpisodeResult."""
        self.env = make(
            "kaggriculture", configuration=self.configuration, debug=self.debug
        )
        # Place challenger in the correct seat
        agents = (
            [self.agent1, self.agent2]
            if self.seat == 0
            else [self.agent2, self.agent1]
        )
        self.env.run(agents)
        p_challenger = self.env.steps[-1][self.seat]
        p_baseline = self.env.steps[-1][1 - self.seat]
        c_score = float(p_challenger.reward or 0.0)
        b_score = float(p_baseline.reward or 0.0)
        winner = 0 if c_score > b_score else (1 if b_score > c_score else -1)
        self.result = EpisodeResult(
            episode_idx=self.episode_idx,
            seat=self.seat,
            score_challenger=c_score,
            score_baseline=b_score,
            winner=winner,
            status_challenger=str(p_challenger.status),
            status_baseline=str(p_baseline.status),
        )
        return self.result

    def save_replay(self, output_path: str | Path | None = None) -> Path:
        """Save episode replay JSON file."""
        if self.env is None:
            raise RuntimeError("Cannot save replay before running the match.")

        path = Path(
            output_path or f"replays/replay_ep{self.episode_idx + 1}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.env.toJSON(), indent=2), encoding="utf-8"
        )

        if self.result:
            self.result.replay_path = str(path.resolve())
        return path
