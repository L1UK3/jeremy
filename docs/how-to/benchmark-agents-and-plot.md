# How-To: Benchmark Agents & Plot Results

This guide shows how to run statistical head-to-head evaluation benchmarks between two agent versions and plot performance metrics.

---

## Why Benchmark with Alternating Seats?

In Kaggriculture, Player 0 (Seat 0) and Player 1 (Seat 1) execute market orders and movements simultaneously, but certain quadrant layouts and tiebreakers can introduce subtle positional bias. Benchmarks must alternate seat assignments across an even number of games.

---

## Step 1: Writing an Evaluation Runner

Create an evaluation script `run_benchmark.py`:

```python
from dataclasses import dataclass, field
from simulation.episode import Episode
from utils.progress import progress
from utils.plot import plot_scores_over_time, plot_score_distribution


@dataclass
class BenchmarkSummary:
    episodes: int
    challenger_scores: list[float] = field(default_factory=list)
    baseline_scores: list[float] = field(default_factory=list)
    challenger_wins: int = 0
    baseline_wins: int = 0
    draws: int = 0


def run_tournament(
    challenger: str = "src/main.py",
    baseline: str = "starter",
    num_episodes: int = 10,
) -> BenchmarkSummary:
    summary = BenchmarkSummary(episodes=num_episodes)

    print(f"\nRunning {num_episodes}-game benchmark: {challenger} vs {baseline}")
    for i in progress(num_episodes, text="Simulating Matches"):
        # Alternate seat position: 0 for even games, 1 for odd games
        seat = i % 2

        ep = Episode(
            agent1=challenger,
            agent2=baseline,
            episode_idx=i,
            seat=seat,
            debug=False,
        )
        res = ep.run()

        summary.challenger_scores.append(res.score_challenger)
        summary.baseline_scores.append(res.score_baseline)

        if res.winner == 0:
            summary.challenger_wins += 1
        elif res.winner == 1:
            summary.baseline_wins += 1
        else:
            summary.draws += 1

    return summary
```

---

## Step 2: Running and Reporting Results

Add reporting and plotting logic at the bottom of `run_benchmark.py`:

```python
if __name__ == "__main__":
    summary = run_tournament(
        challenger="src/main.py",
        baseline="starter",
        num_episodes=20,
    )

    c_avg = sum(summary.challenger_scores) / len(summary.challenger_scores)
    b_avg = sum(summary.baseline_scores) / len(summary.baseline_scores)
    win_rate = (summary.challenger_wins / summary.episodes) * 100

    print("\n" + "=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Total Matches       : {summary.episodes}")
    print(f"Challenger Wins     : {summary.challenger_wins} ({win_rate:.1f}%)")
    print(f"Baseline Wins       : {summary.baseline_wins}")
    print(f"Draws               : {summary.draws}")
    print(f"Challenger Mean Bank: ${c_avg:,.2f}")
    print(f"Baseline Mean Bank  : ${b_avg:,.2f}")
    print("=" * 50)

    # Save visual plots to artifacts/replays directory
    plot_scores_over_time(summary, output_path="docs/benchmark_timeline.png")
    plot_score_distribution(summary, output_path="docs/benchmark_dist.png")
```

---

## Step 3: Executing the Benchmark

Run the benchmark script from your shell:

```bash
python run_benchmark.py
```

Console output with real-time ETA:
```
Simulating Matches: 60% (12/20) | ETA: 14.2s
```

---

## Step 4: Interpreting Benchmark Visualizations

* **Score Over Time Plot (`benchmark_timeline.png`)**:
  Shows game-by-game bank trajectories. Stability across both even and odd episode indices indicates consistency across both Seat 0 and Seat 1.
* **Score Distribution Histogram (`benchmark_dist.png`)**:
  Shows variance and separation between challenger and baseline distributions. Bimodal distributions can indicate sensitivity to initial crop seeds or shop unlock draws.
