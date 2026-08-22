Episode replays and results from the [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) simulation competition, collected from the public episode API and refreshed daily. One episode is one 720-turn farming game (24 turns a day, 30 days).

The companion report [Kaggriculture Daily Replays](https://www.kaggle.com/code/georgymamarin/kaggriculture-daily-replays-the-live-meta-report) is built entirely from these files.

**Raw dumps or this?** Kaggle's official [daily episodes index](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index) ships ~21 GB of top replays daily: take that for bulk IL/RL. This is the analysis-ready complement: flat tables, pre-parsed features, one zstd parquet.

## Content

- `episodes.csv`: one row per episode: times, `state`, `type` (`EPISODE_TYPE_PUBLIC` = ladder, `EPISODE_TYPE_VALIDATION` = self-play, filter out), per seat `sub_N`, `team_N`, `bank_N`, `rating_N`.
- `agents.csv`: `episode_id`, `agent_index`, `submission_id`, `team_id`, `final_bank`, `rating_after`.
- `teams.csv`: `team_id` to `team_name`, `ladder_score`, `last_submission`. A leaderboard snapshot, so it names about half the teams in the episodes; the rest have dropped off it.
- `episode_features.csv`: one row per (episode, seat): `peak_crew`, `total_hires`, `first_land_day`, `tiles_planted`, `plants_*` (5 crops), `price_*_min`/`_max` (9 goods). Two columns come from the outcome itself, `final_money` (= `bank_N`) and `elbow_day`: keep both out of any feature set.
- `replays.parquet`: full replay of every episode here, `episode_id` plus `replay_json` as the CDN serves it. Zstd holds 801 GB of JSON in 3.4 GB (236x, from the parquet's column metadata); it grows daily, so take the size from the Data tab.
- `daily_stats.csv`: per UTC day: ladder games, active teams, median/p90/record winner's bank, `replay_coverage` (share of games *stored here* that day with a replay).
- `stream_hashes.csv`: per (episode, seat), sha256 of the action stream cut at turns 24/100/200/400/719. Equal values at turn N mean identical actions through turn N, so a shared opening is an observation, not a threshold. Suggested by destbreso; still backfilling, so older episodes can be missing.
- `state.json`, `README.md`, and the collector chain (`scrape.py`, `repack.py`, `teams.py`, `features.py`): everything reproduces from public endpoints.

Pull one replay (ids in `episode_features.csv` are guaranteed to have one):

```python
import pandas as pd, json, pyarrow.dataset as pads
base = "/kaggle/input/kaggriculture-episodes"
eid = pd.read_csv(f"{base}/episode_features.csv").episode_id.iloc[-1]
row = pads.dataset(f"{base}/replays.parquet").scanner(
    filter=pads.field("episode_id") == int(eid), batch_size=1).head(1)
replay = json.loads(row.column("replay_json")[0].as_py())
```

On completeness: coverage is per submission, not per day. The crawl services a few hundred submissions and everyone else lands here only as their opponent: 97% of stored episodes have a seat among the 300 submissions with the most rows here, and the twelve of those checked against the episode API hold 87-99.8% of their own games, while the median submission shows up twice. Daily totals are that sample, not the ladder's true volume. Every stored episode does have its replay.

The games belong to their players and to Kaggle; I only collect and reshape. Environment: [kaggle-environments](https://github.com/Kaggle/kaggle-environments).
Regress the bank on `episode_features.csv` to see what predicts winning, or train an imitation model on (observation, action) pairs from `replays.parquet` and judge it against the ladder's median.

New to the game? [Kaggriculture, Visualized](https://www.kaggle.com/code/georgymamarin/kaggriculture-visualized-what-every-crop-pays) draws every rule with a chart. Found a gap or built something on this? The discussion tab is open.
