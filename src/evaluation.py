"""
Evaluation script for benchmarking Kaggriculture agents.

Usage:
    python src/evaluation.py
    python src/evaluation.py --episodes 20 --workers 4 --baseline starter
    python src/evaluation.py --challenger src/submission.py --baseline random --plot
"""

import argparse
import sys
from pathlib import Path

# Ensure src directory and src/agent are in sys.path
src_dir = Path(__file__).resolve().parent
agent_dir = src_dir / "agent"
for p in (src_dir, agent_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from simulation import evaluate_agents  # noqa: E402


def plot_scores_over_time(summary, output_path: str | None = None) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping plot.")
        return

    episodes = range(1, summary.episodes + 1)
    plt.figure(figsize=(10, 5))
    plt.plot(
        episodes,
        summary.challenger_scores,
        marker="o",
        label="Challenger",
        color="#2563eb",
    )
    plt.plot(
        episodes,
        summary.baseline_scores,
        marker="s",
        label="Baseline",
        color="#dc2626",
    )
    plt.title("Scores per Episode (Alternating Seats)")
    plt.xlabel("Episode")
    plt.ylabel("Final Bank / Score")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved plot to {output_path}")
    else:
        plt.show()


def plot_score_distribution(summary, output_path: str | None = None) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping plot.")
        return

    plt.figure(figsize=(8, 5))
    plt.hist(
        summary.challenger_scores,
        alpha=0.6,
        bins=10,
        label="Challenger",
        color="#2563eb",
    )
    plt.hist(
        summary.baseline_scores,
        alpha=0.6,
        bins=10,
        label="Baseline",
        color="#dc2626",
    )
    plt.title("Score Distribution")
    plt.xlabel("Final Bank / Score")
    plt.ylabel("Frequency")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved histogram to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Parallel Evaluation Harness for Kaggriculture Agents"
    )
    parser.add_argument(
        "--challenger",
        "-c",
        type=str,
        default="agent.agent",
        help="Challenger agent callable or file path (default: agent.agent)",
    )
    parser.add_argument(
        "--baseline",
        "-b",
        type=str,
        default="starter",
        help="Baseline agent ('starter', 'random', 'pass', or file path, default: starter)",
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
        help="Number of parallel worker processes (default: min(os.cpu_count(), 8))",
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
        "--plot",
        action="store_true",
        help="Render and display score distribution plots",
    )
    parser.add_argument(
        "--save-plot",
        type=str,
        default=None,
        help="Path to save score distribution chart image",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable kaggle-environments debug logging",
    )

    args = parser.parse_args()

    summary = evaluate_agents(
        agent1=args.challenger,
        agent2=args.baseline,
        num_episodes=args.episodes,
        num_workers=args.workers,
        auto_save_failures=True,
        save_all_replays=args.save_all,
        replays_dir=args.replays_dir,
        debug=args.debug,
    )

    if args.plot or args.save_plot:
        plot_scores_over_time(summary, output_path=args.save_plot)
        plot_score_distribution(summary)


if __name__ == "__main__":
    main()
