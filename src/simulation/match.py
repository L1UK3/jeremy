import contextlib
import importlib
import importlib.util
import io
import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Suppress noisy C-level OpenSpiel startup output during kaggle_environments import
try:
    _null_fd = os.open(os.devnull, os.O_WRONLY)
    _orig_stdout_fd = os.dup(1)
    _orig_stderr_fd = os.dup(2)
    os.dup2(_null_fd, 1)
    os.dup2(_null_fd, 2)
    from kaggle_environments import make
finally:
    try:
        os.dup2(_orig_stdout_fd, 1)
        os.dup2(_orig_stderr_fd, 2)
        os.close(_orig_stdout_fd)
        os.close(_orig_stderr_fd)
        os.close(_null_fd)
    except Exception:
        pass

from simulation.metrics import EpisodeResult

AgentType = Callable[[dict], dict] | str


def resolve_agent(agent: AgentType) -> Any:
    """
    Resolve an agent representation (callable, built-in string name, or module/file path)
    into a format suitable for kaggle-environments.
    """
    if callable(agent):
        return agent

    if isinstance(agent, str):
        # Built-in kaggle agents: "starter", "random", "pass"
        if agent.lower() in {"starter", "random", "pass"}:
            return agent.lower()

        # Check if file path exists (relative to cwd, src, or project root)
        src_path = Path(__file__).resolve().parent.parent
        root_path = src_path.parent
        for base in [Path.cwd(), src_path, root_path]:
            candidate = (
                Path(agent) if Path(agent).is_absolute() else (base / agent)
            )
            if candidate.exists() and candidate.suffix == ".py":
                try:
                    spec = importlib.util.spec_from_file_location(
                        "custom_agent_mod", candidate
                    )
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "agent"):
                            return mod.agent
                except Exception:
                    pass
                return str(candidate.resolve())

        # Check if module path e.g. "src.agent.agent" or "agent.agent"
        if "." in agent:
            try:
                mod_name, func_name = agent.rsplit(".", 1)
                mod = importlib.import_module(mod_name)
                return getattr(mod, func_name)
            except (ImportError, AttributeError):
                pass

        return agent

    return agent


def get_next_replay_path(replays_dir: Path) -> Path:
    """Get path for next sequentially numbered replay file in replays/ directory."""
    replays_dir.mkdir(parents=True, exist_ok=True)
    indices = [
        int(m.group(1))
        for p in replays_dir.glob("replay*.json")
        if (m := re.search(r"replay(\d+)\.json$", p.name))
    ]
    next_idx = max(indices, default=0) + 1
    return replays_dir / f"replay{next_idx}.json"


class Match:
    """
    Manages and executes a single 2-player Kaggriculture game between two agents.
    Measures per-turn latency, captures final scores, and provides replay export.
    """

    def __init__(
        self,
        agent1: AgentType,
        agent2: AgentType = "random",
        episode_idx: int = 0,
        seat: int = 0,
        debug: bool = False,
        configuration: dict | None = None,
    ) -> None:
        self.agent1_raw = agent1
        self.agent2_raw = agent2
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

    def _wrap_agent(self, agent_fn: Any, times_list: list[float]) -> Callable:
        def wrapped_agent(obs: dict) -> dict:
            t0 = time.perf_counter()
            act = agent_fn(obs)
            times_list.append(time.perf_counter() - t0)
            return act

        return wrapped_agent

    def run(self) -> EpisodeResult:
        """Run the match to completion and return EpisodeResult."""
        a1 = resolve_agent(self.agent1_raw)
        a2 = resolve_agent(self.agent2_raw)

        # Wrap callables to measure execution timing
        p1 = self._wrap_agent(a1, self.agent1_times) if callable(a1) else a1
        p2 = self._wrap_agent(a2, self.agent2_times) if callable(a2) else a2

        # Assign player seats based on seat rotation
        if self.seat == 0:
            players = [p1, p2]
        else:
            players = [p2, p1]

        with (
            contextlib.redirect_stderr(io.StringIO()),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.env = make(
                "kaggriculture",
                configuration=self.configuration,
                debug=self.debug,
            )

        self.env.run(players)
        final_state = self.env.steps[-1]

        p0_reward = (
            float(final_state[0].reward)
            if final_state[0].reward is not None
            else 0.0
        )
        p1_reward = (
            float(final_state[1].reward)
            if final_state[1].reward is not None
            else 0.0
        )
        p0_status = str(final_state[0].status)
        p1_status = str(final_state[1].status)

        if self.seat == 0:
            c_score = p0_reward
            b_score = p1_reward
            c_status = p0_status
            b_status = p1_status
            c_times = self.agent1_times
            b_times = self.agent2_times
        else:
            c_score = p1_reward
            b_score = p0_reward
            c_status = p1_status
            b_status = p0_status
            c_times = self.agent1_times
            b_times = self.agent2_times

        if c_score > b_score:
            winner = 0
        elif b_score > c_score:
            winner = 1
        else:
            winner = -1

        self.result = EpisodeResult(
            episode_idx=self.episode_idx,
            seat=self.seat,
            score_challenger=c_score,
            score_baseline=b_score,
            winner=winner,
            challenger_times=c_times,
            baseline_times=b_times,
            status_challenger=c_status,
            status_baseline=b_status,
        )
        return self.result

    def save_replay(self, output_path: str | Path | None = None) -> Path:
        """Save episode replay JSON file."""
        if self.env is None:
            raise RuntimeError("Cannot save replay before running the match.")

        if output_path is None:
            path = get_next_replay_path(Path("replays"))
        else:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

        replay_json = self.env.toJSON()
        path.write_text(json.dumps(replay_json, indent=2), encoding="utf-8")
        if self.result:
            self.result.replay_path = str(path.resolve())
        return path


class Simulator:
    """
    Backward-compatible simulator wrapper for single-threaded quick runs.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug

    def run(self, agent1, agent2="random", render=False):
        env = make("kaggriculture", debug=self.debug)
        env.run([resolve_agent(agent1), resolve_agent(agent2)])
        if render:
            try:
                env.render(mode="ipython", width=900, height=700)
            except Exception:
                pass
        return env

    def result(self, env):
        final = env.steps[-1]
        return [
            {"player": i, "reward": s.reward, "status": s.status}
            for i, s in enumerate(final)
        ]

    def winner(self, env):
        res = self.result(env)
        if len(res) < 2:
            return None
        if res[0]["reward"] > res[1]["reward"]:
            return 0
        if res[1]["reward"] > res[0]["reward"]:
            return 1
        return -1

    def evaluate(self, agent, opponent="random", episodes=20):
        _match_runner = Match(agent, opponent, debug=self.debug)
        rewards = []
        wins = 0
        losses = 0
        draws = 0

        for ep in range(episodes):
            m = Match(
                agent, opponent, episode_idx=ep, seat=ep % 2, debug=self.debug
            )
            res = m.run()
            rewards.append(res.score_challenger)
            if res.winner == 0:
                wins += 1
            elif res.winner == 1:
                losses += 1
            else:
                draws += 1

        return {
            "episodes": episodes,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": wins / episodes,
            "avg_reward": sum(rewards) / len(rewards) if rewards else 0.0,
            "max_reward": max(rewards) if rewards else 0.0,
            "min_reward": min(rewards) if rewards else 0.0,
        }

    def compare(self, agent_a, agent_b, episodes=20):
        a = self.evaluate(agent_a, opponent=agent_b, episodes=episodes)
        b = self.evaluate(agent_b, opponent=agent_a, episodes=episodes)
        return {"agent_a": a, "agent_b": b}
