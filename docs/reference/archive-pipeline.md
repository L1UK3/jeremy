# Reference: Archive Pipeline & Datasets

This document provides schema specifications and command-line usage references for the dataset archive pipeline located in `src/archive/`.

---

## Dataset Schema Specifications

### 1. `episodes.csv`
One row per crawled episode.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `int64` | Unique Kaggle match episode identifier. |
| `create_time` | `string (ISO 8601)` | Match start timestamp UTC. |
| `end_time` | `string (ISO 8601)` | Match completion timestamp UTC. |
| `state` | `string` | Completion state (`"COMPLETE"`, `"ERROR"`). |
| `type` | `string` | `"EPISODE_TYPE_PUBLIC"` (ladder) or `"EPISODE_TYPE_VALIDATION"` (self-play check). |
| `sub_0`, `sub_1` | `int64` | Submission ID for Player 0 and Player 1. |
| `team_0`, `team_1` | `int64` | Team ID for Player 0 and Player 1. |
| `bank_0`, `bank_1` | `float64` | Final coin balance (reward) at step 720. |
| `rating_0`, `rating_1`| `float64` | Post-match skill rating score. |

---

### 2. `agents.csv`
Per-agent view of match outcomes (two rows per episode).

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `int64` | Foreign key to `episodes.csv`. |
| `agent_index` | `int32` | Seat index (`0` or `1`). |
| `submission_id` | `int64` | Submission ID. |
| `team_id` | `int64` | Team ID. |
| `final_bank` | `float64` | Final score. |
| `rating_after` | `float64` | Updated rating after episode completion. |

---

### 3. `teams.csv`
Leaderboard snapshot mapping team IDs to names.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `team_id` | `int64` | Primary key team identifier. |
| `team_name` | `string` | Kaggle display team name. |
| `ladder_score` | `float64` | Public leaderboard skill score. |
| `last_submission` | `string` | Timestamp of latest submission. |

---

### 4. `episode_features.csv`
Per-seat strategic feature vector extracted from full turn trajectories.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `int64` | Episode identifier. |
| `agent_index` | `int32` | Seat index (`0` or `1`). |
| `peak_crew` | `int32` | Max simultaneous workers active in a single day. |
| `total_hires` | `int32` | Cumulative farmhands hired over 30 days. |
| `first_land_day` | `int32` | Day number of first quadrant purchase (`-1` if never). |
| `tiles_planted` | `int32` | Total crop planting operations. |
| `plants_wheat` | `int32` | Total wheat plantings. |
| `plants_carrot` | `int32` | Total carrot plantings. |
| `plants_tomato` | `int32` | Total tomato plantings. |
| `plants_strawberry`| `int32` | Total strawberry plantings. |
| `plants_melon` | `int32` | Total melon plantings. |
| `price_<item>_min` | `int32` | Minimum market price observed for `<item>`. |
| `price_<item>_max` | `int32` | Maximum market price observed for `<item>`. |
| `final_money` | `float64` | Match outcome (final bank). |
| `elbow_day` | `int32` | Day when bank crossed 10% of final balance. |

---

### 5. `stream_hashes.csv`
Action-stream SHA-256 fingerprint checkpoints to detect strategy cloning and common openings.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `int64` | Match identifier. |
| `agent_index` | `int32` | Seat index (`0` or `1`). |
| `h24`, `h100`, `h200`, `h400`, `h719` | `string (16 hex)` | SHA-256 slice prefix of serialized actions up to turn N. |
| `turns` | `int32` | Total turns survived. |

---

### 6. `replays.parquet`
Consolidated Zstandard-compressed Parquet store.

| Field Name | Arrow Data Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `int64` | Match identifier. |
| `replay_json`| `string (utf-8)` | Full replay JSON (720 turns, observations, actions, rewards). |

---

## Script & CLI Reference

### `src/archive/scrape.py`
```bash
python scrape.py [--max-new N]
```
* **Description**: Queries `https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes` starting from `SEED_SUBMISSIONS`, downloading gzipped replays to `raw/{id}.json.gz`.
* **Flags**:
  * `--max-new`: Limit count of new episodes fetched in run (default: unlimited).

### `src/archive/repack.py`
```bash
python repack.py
```
* **Description**: Iterates through `raw/*.json.gz`, parses raw payloads, and writes consolidated `replays.parquet` with Zstandard level 19 compression.

### `src/archive/teams.py`
```bash
python teams.py
```
* **Description**: Pulls leaderboard snapshot and generates `teams.csv`.

### `src/archive/features.py`
```bash
python features.py
```
* **Description**: Processes `replays.parquet` or `raw/*.json.gz` to output `episode_features.csv` and `stream_hashes.csv`.
