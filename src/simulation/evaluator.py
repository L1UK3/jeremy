import argparse
import os
import sys
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# Ensure src directory and src/agent are in sys.path
src_dir = Path(__file__).resolve().parent.parent
agent_dir = src_dir / "agent"
for p in (src_dir, agent_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.simulation.episode import AgentType, Match  # noqa: E402
from simulation.metrics import EpisodeResult, EvaluationSummary  # noqa: E402
from simulation.progress import progress  # noqa: E402


def _worker_run_episode(
    challenger_spec: str | Callable,
    baseline_spec: str | Callable,
    episode_idx: int,
    seat: int,
    debug: bool,
    auto_save_failures: bool,
    save_all_replays: bool,
    replays_dir_str: str | None,
) -> EpisodeResult:
    """Worker function executed in parallel child processes."""
    # Add src and src/agent to sys.path in worker process if not present
    for p in (src_dir, agent_dir):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    replays_dir = Path(replays_dir_str) if replays_dir_str else Path("replays")

    match = Match(
        agent1=challenger_spec,
        agent2=baseline_spec,
        episode_idx=episode_idx,
        seat=seat,
        debug=debug,
    )
    result = match.run()

    # Save replay if requested or if failure/loss occurred
    should_save = save_all_replays or (
        auto_save_failures and (result.is_error or result.winner == 1)
    )

    if should_save:
        try:
            filename = f"replay_ep{episode_idx + 1}_seat{seat}_{'loss' if result.winner == 1 else 'error' if result.is_error else 'game'}.json"
            out_file = replays_dir / filename
            match.save_replay(out_file)
            result.replay_path = str(out_file.resolve())
        except Exception as e:
            sys.stderr.write(
                f"\nFailed to save replay for ep {episode_idx + 1}: {e}\n"
            )

    return result


class Evaluator:
    """
    High-performance parallel evaluation engine for Kaggriculture agents.
    Manages multi-core processing, seat balancing, latency metrics, and replay logging.
    """

    def __init__(
        self,
        challenger: AgentType,
        baseline: AgentType = "starter",
        num_episodes: int = 10,
        num_workers: int | None = None,
        auto_save_failures: bool = True,
        save_all_replays: bool = False,
        replays_dir: str | Path = "replays",
        debug: bool = False,
    ) -> None:
        self.challenger = challenger
        self.baseline = baseline
        self.num_episodes = max(1, num_episodes)
        self.num_workers = (
            num_workers
            if num_workers is not None
            else min(os.cpu_count() or 1, 8)
        )
        self.auto_save_failures = auto_save_failures
        self.save_all_replays = save_all_replays
        self.replays_dir = Path(replays_dir)
        self.debug = debug

    def run(self) -> EvaluationSummary:
        """Run all evaluation episodes and return computed summary."""
        tasks = []
        for i in range(self.num_episodes):
            seat = (
                i % 2
            )  # 50/50 seat alternation to eliminate first-player bias
            tasks.append(
                (
                    self.challenger,
                    self.baseline,
                    i,
                    seat,
                    self.debug,
                    self.auto_save_failures,
                    self.save_all_replays,
                    str(self.replays_dir),
                )
            )

        results: list[EpisodeResult] = []
        saved_replays: list[str] = []

        print(
            f"Evaluating {self.num_episodes} episodes across {self.num_workers} worker(s)..."
        )
        print(f"  Challenger: {self.challenger}")
        print(f"  Baseline  : {self.baseline}")
        print("  Seat Mode : Alternating (50% Seat 0, 50% Seat 1)\n")

        prog = progress(self.num_episodes, text="Simulating matches")
        next(prog)

        if self.num_workers > 1 and self.num_episodes > 1:
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {
                    executor.submit(_worker_run_episode, *t): t[2]
                    for t in tasks
                }
                for fut in as_completed(futures):
                    res = fut.result()
                    results.append(res)
                    if res.replay_path:
                        saved_replays.append(res.replay_path)
                    try:
                        next(prog)
                    except StopIteration:
                        pass
        else:
            # Sequential execution
            for t in tasks:
                res = _worker_run_episode(*t)
                results.append(res)
                if res.replay_path:
                    saved_replays.append(res.replay_path)
                try:
                    next(prog)
                except StopIteration:
                    pass

        # Sort results back into original episode order
        results.sort(key=lambda r: r.episode_idx)

        summary = EvaluationSummary.from_results(
            results, saved_replays=saved_replays
        )
        return summary


def evaluate_agents(
    agent1: AgentType,
    agent2: AgentType = "starter",
    num_episodes: int = 10,
    num_workers: int | None = None,
    auto_save_failures: bool = True,
    save_all_replays: bool = False,
    replays_dir: str | Path = "replays",
    debug: bool = False,
) -> EvaluationSummary:
    """Convenience function to evaluate two agents and print the summary."""
    evaluator = Evaluator(
        challenger=agent1,
        baseline=agent2,
        num_episodes=num_episodes,
        num_workers=num_workers,
        auto_save_failures=auto_save_failures,
        save_all_replays=save_all_replays,
        replays_dir=replays_dir,
        debug=debug,
    )
    summary = evaluator.run()
    c_name = str(agent1.__name__) if callable(agent1) else str(agent1)
    b_name = str(agent2.__name__) if callable(agent2) else str(agent2)
    summary.print_summary(challenger_name=c_name, baseline_name=b_name)
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Parallel Evaluator for Kaggriculture Agents"
    )
    parser.add_argument(
        "--challenger",
        "-c",
        type=str,
        default="agent.agent",
        help="Path or module to challenger agent (default: agent.agent)",
    )
    parser.add_argument(
        "--baseline",
        "-b",
        type=str,
        default="starter",
        help="Baseline agent ('starter', 'random', 'pass', or file path)",
    )
    parser.add_argument(
        "--episodes",
        "-n",
        type=int,
        default=10,
        help="Number of episodes to evaluate (default: 10)",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of parallel worker processes (default: min(CPU count, 8))",
    )
    parser.add_argument(
        "--save-all",
        action="store_true",
        help="Save replay JSON for all episodes (not just losses/errors)",
    )
    parser.add_argument(
        "--replays-dir",
        type=str,
        default="replays",
        help="Directory to store replay JSON files",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable kaggle-environments debug logging",
    )

    args = parser.parse_args()

    evaluate_agents(
        agent1=args.challenger,
        agent2=args.baseline,
        num_episodes=args.episodes,
        num_workers=args.workers,
        auto_save_failures=True,
        save_all_replays=args.save_all,
        replays_dir=args.replays_dir,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
