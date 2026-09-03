import argparse
import json
from pathlib import Path

import kaggle_environments
import pandas as pd
import pyarrow.dataset as pads

df = pd.read_csv(".out/episode_features.csv")

# Filter top 5% highest scoring games
TOP_PERFORMERS = df[df["final_money"] >= df["final_money"].quantile(0.95)]

print("=== WINNING STRATEGY PROFILE (TOP 5%) ===")
print(f"Mean Final Bank   : ${TOP_PERFORMERS['final_money'].mean():,.2f}")
print(f"Mean Peak Crew    : {TOP_PERFORMERS['peak_crew'].mean():.1f} workers")
print(f"Mean Total Hires  : {TOP_PERFORMERS['total_hires'].mean():.1f} hires")
print(
    f"First Land Day    : Day {TOP_PERFORMERS['first_land_day'].median():.0f}"
)
print(f"Mean Wheat Plants : {TOP_PERFORMERS['plants_wheat'].mean():.1f}")
print(f"Mean Melon Plants : {TOP_PERFORMERS['plants_melon'].mean():.1f}")


def get_top_eps(df, n=10):
    """Get the top n episodes by final_money."""
    return (
        df.sort_values("final_money", ascending=False)
        .drop_duplicates("episode_id")
        .head(n)
    )


def main(n=10):
    top_eps = get_top_eps(df, n=n)

    out_dir = Path(".out/highest_scoring_replays")
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = pads.dataset(".out/replays.parquet", format="parquet")

    for _, row in top_eps.iterrows():
        ep_id = int(row["episode_id"])
        score = row["final_money"]
        json_path = out_dir / f"{ep_id}.json"

        # Query the single matching row from parquet
        scanner = dataset.scanner(
            filter=pads.field("episode_id") == ep_id, batch_size=1
        )
        batch = scanner.head(1)
        if batch.num_rows == 0:
            print(f"Episode {ep_id} not found in replays.parquet")
            continue

        raw_json = batch.column("replay_json")[0].as_py()
        replay = json.loads(raw_json)
        print(
            f"Loaded Episode {ep_id} (Score: ${score:,.2f}, {len(replay['steps'])} turns)"
        )

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(replay, f, indent=2)

    replay_dir = Path(".out/highest_scoring_replays")

    # Convert all JSON replays in the directory to HTML
    for json_file in replay_dir.glob("*.json"):
        html_file = json_file.with_suffix(".html")

        print(f"Rendering {json_file.name} as {html_file.name}")
        with open(json_file, encoding="utf-8") as f:
            replay = json.load(f)

        env = kaggle_environments.make(
            "kaggriculture",
            steps=replay["steps"],
            configuration=replay.get("configuration", {}),
        )

        html_content = env.render(mode="html")
        html_file.write_text(html_content, encoding="utf-8")
        print(f"Saved: {html_file}")


if __name__ == "__main__":
    args = argparse.ArgumentParser(
        description="Analyze top scoring episodes and render replays."
    )

    args.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top episodes to analyze (default: 10)",
    )

    args = args.parse_args()

    main(args.top_n)
