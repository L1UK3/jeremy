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
