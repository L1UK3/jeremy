from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class EpisodeResult:
    episode_idx: int
    seat: int  # 0 or 1 (seat occupied by challenger)
    score_challenger: float
    score_baseline: float
    winner: int  # 0: challenger won, 1: baseline won, -1: tie
    challenger_times: list[float] = field(default_factory=list)
    baseline_times: list[float] = field(default_factory=list)
    status_challenger: str = "DONE"
    status_baseline: str = "DONE"
    replay_path: str | None = None

    @property
    def is_error(self) -> bool:
        return (
            self.status_challenger == "ERROR" or self.status_baseline == "ERROR"
        )


@dataclass(slots=True)
class EvaluationSummary:
    episodes: int
    wins: int
    losses: int
    ties: int
    win_rate: float

    challenger_scores: list[float]
    baseline_scores: list[float]

    challenger_mean: float
    challenger_sem: float
    challenger_median: float
    challenger_std: float
    challenger_min: float
    challenger_max: float

    baseline_mean: float
    baseline_sem: float
    baseline_median: float
    baseline_std: float
    baseline_min: float
    baseline_max: float

    challenger_latency_mean_ms: float
    challenger_latency_p50_ms: float
    challenger_latency_p95_ms: float
    challenger_latency_max_ms: float

    baseline_latency_mean_ms: float
    baseline_latency_p50_ms: float
    baseline_latency_p95_ms: float
    baseline_latency_max_ms: float

    errors: list[tuple[int, str, str]]
    saved_replays: list[str]

    @classmethod
    def from_results(
        cls,
        results: list[EpisodeResult],
        saved_replays: list[str] | None = None,
    ) -> "EvaluationSummary":
        n = len(results)
        if n == 0:
            raise ValueError("Cannot summarize empty results.")

        c_scores = np.array([r.score_challenger for r in results], dtype=float)
        b_scores = np.array([r.score_baseline for r in results], dtype=float)

        wins = int(np.sum(c_scores > b_scores))
        losses = int(np.sum(c_scores < b_scores))
        ties = int(np.sum(c_scores == b_scores))
        win_rate = (wins / n) * 100.0

        c_sem = float(np.std(c_scores, ddof=1) / np.sqrt(n)) if n > 1 else 0.0
        b_sem = float(np.std(b_scores, ddof=1) / np.sqrt(n)) if n > 1 else 0.0

        # Latencies
        all_c_times = []
        all_b_times = []
        for r in results:
            all_c_times.extend(r.challenger_times)
            all_b_times.extend(r.baseline_times)

        c_arr_ms = (
            np.array(all_c_times) * 1000.0 if all_c_times else np.array([0.0])
        )
        b_arr_ms = (
            np.array(all_b_times) * 1000.0 if all_b_times else np.array([0.0])
        )

        errors = [
            (r.episode_idx, r.status_challenger, r.status_baseline)
            for r in results
            if r.is_error
        ]

        replays = saved_replays or [
            r.replay_path for r in results if r.replay_path
        ]

        return cls(
            episodes=n,
            wins=wins,
            losses=losses,
            ties=ties,
            win_rate=win_rate,
            challenger_scores=c_scores.tolist(),
            baseline_scores=b_scores.tolist(),
            challenger_mean=float(np.mean(c_scores)),
            challenger_sem=c_sem,
            challenger_median=float(np.median(c_scores)),
            challenger_std=float(np.std(c_scores, ddof=1)) if n > 1 else 0.0,
            challenger_min=float(np.min(c_scores)),
            challenger_max=float(np.max(c_scores)),
            baseline_mean=float(np.mean(b_scores)),
            baseline_sem=b_sem,
            baseline_median=float(np.median(b_scores)),
            baseline_std=float(np.std(b_scores, ddof=1)) if n > 1 else 0.0,
            baseline_min=float(np.min(b_scores)),
            baseline_max=float(np.max(b_scores)),
            challenger_latency_mean_ms=float(np.mean(c_arr_ms)),
            challenger_latency_p50_ms=float(np.percentile(c_arr_ms, 50)),
            challenger_latency_p95_ms=float(np.percentile(c_arr_ms, 95)),
            challenger_latency_max_ms=float(np.max(c_arr_ms)),
            baseline_latency_mean_ms=float(np.mean(b_arr_ms)),
            baseline_latency_p50_ms=float(np.percentile(b_arr_ms, 50)),
            baseline_latency_p95_ms=float(np.percentile(b_arr_ms, 95)),
            baseline_latency_max_ms=float(np.max(b_arr_ms)),
            errors=errors,
            saved_replays=replays,
        )

    def print_summary(
        self,
        challenger_name: str = "Challenger",
        baseline_name: str = "Baseline",
    ) -> None:
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Total Episodes : {self.episodes}")
        print(f"Outcome        : {self.wins}W - {self.losses}L - {self.ties}T")
        print(f"Win Rate       : {self.win_rate:.1f}%")
        print("-" * 60)
        print(f"{challenger_name} Stats:")
        print(
            f"  Mean Score   : {self.challenger_mean:.2f} (± {self.challenger_sem:.2f} SEM)"
        )
        print(f"  Median Score : {self.challenger_median:.2f}")
        print(f"  Std Dev      : {self.challenger_std:.2f}")
        print(
            f"  Min / Max    : {self.challenger_min:.2f} / {self.challenger_max:.2f}"
        )
        print(
            f"  Latency (ms) : Mean: {self.challenger_latency_mean_ms:.2f} | "
            f"p50: {self.challenger_latency_p50_ms:.2f} | "
            f"p95: {self.challenger_latency_p95_ms:.2f} | "
            f"Max: {self.challenger_latency_max_ms:.2f}"
        )
        print("-" * 60)
        print(f"{baseline_name} Stats:")
        print(
            f"  Mean Score   : {self.baseline_mean:.2f} (± {self.baseline_sem:.2f} SEM)"
        )
        print(f"  Median Score : {self.baseline_median:.2f}")
        print(f"  Std Dev      : {self.baseline_std:.2f}")
        print(
            f"  Min / Max    : {self.baseline_min:.2f} / {self.baseline_max:.2f}"
        )
        print(
            f"  Latency (ms) : Mean: {self.baseline_latency_mean_ms:.2f} | "
            f"p50: {self.baseline_latency_p50_ms:.2f} | "
            f"p95: {self.baseline_latency_p95_ms:.2f} | "
            f"Max: {self.baseline_latency_max_ms:.2f}"
        )
        print("=" * 60)

        if self.errors:
            print(
                f"WARNING: {len(self.errors)} episodes finished in an ERROR state:"
            )
            for ep_idx, c_stat, b_stat in self.errors[:5]:
                print(
                    f"  Episode {ep_idx}: Challenger={c_stat}, Baseline={b_stat}"
                )
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more.")
        else:
            print("No environment errors detected.")

        if self.saved_replays:
            print(
                f"\nSaved {len(self.saved_replays)} replay(s) for inspection:"
            )
            for r in self.saved_replays[:5]:
                print(f"  {r}")
            if len(self.saved_replays) > 5:
                print(f"  ... and {len(self.saved_replays) - 5} more.")
        print()
