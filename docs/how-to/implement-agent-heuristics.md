# How-To: Implement Agent Heuristics

This guide explains how to add and customize decision-making heuristics in the agent planner using the modular `src/agent/heuristics/` pipeline, search queue, board queries, and action builders.

---

## The Decision Pipeline

The agent executes a pipeline of registered `Heuristic` evaluators on each turn:

```mermaid
flowchart TD
    A[Observation Callback agent obs] --> B[GameState.from_obs]
    B --> C[Planner.play]
    C --> D[MarketHeuristic]
    C --> E[FarmingHeuristic]
    C --> F[MovementHeuristic]
    C --> G[ExpansionHeuristic]
    D & E & F & G --> H[Search candidate priority queue]
    H --> I[ActionBuilder.merge top candidates]
    I --> J[Return Action Dict to Kaggle Engine]
```

---

## Step 1: Defining a Custom Heuristic Function

Write a standalone function taking `planner`. Use score constants from [`agent.heuristics.scores`](file:///c:/Users/Luke%20Enness/Projects/jeremy/src/agent/heuristics/scores.py) to avoid magic numbers.

```python
from agent.heuristics.movement import move_to
from agent.heuristics.scores import SCORE_DIG_WEED, SCORE_MOVE_EMPTY
from environment.actions import ActionBuilder


def evaluate_weed_patrol(planner) -> None:
    """Clear weeds underfoot or seek out nearest weeds on farm."""
    tile = planner.state.current_tile
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        planner.add(SCORE_DIG_WEED, ActionBuilder.dig())
        return

    # Move toward nearest weed if idle
    weeds = [
        t
        for t in planner.board.all_tiles()
        if isinstance(t.data, dict) and t.data.get("kind") == "WEED"
    ]
    if nearest_weed := planner.board.nearest(weeds):
        planner.add(SCORE_MOVE_EMPTY - 5.0, move_to(planner, nearest_weed))
```

---

## Step 2: Calling from `Planner`

Call your custom heuristic directly inside `Planner.play()`:

```python
def play(self) -> Action:
    evaluate_market(self)
    evaluate_farming(self)
    evaluate_movement(self)
    evaluate_weed_patrol(self)
    evaluate_expansion(self)
    return self.choose()
```

---

## Step 4: Scoring Priority Calibration

Candidates are ranked by `score` in [`agent.search.Search`](file:///d:/Projects/jeremy/src/agent/search.py). When scoring actions, adhere to this calibration hierarchy:

| Action Type | Typical Score Range | Rationale |
| :--- | :--- | :--- |
| **Harvest Peak Crop** | `100 + (units * price)` | Realizing immediate revenue takes top precedence. |
| **Dig Weed Underfoot** | `90` | Frees up productive tile immediately. |
| **Water Thirsty Crop** | `80` | Prevents plant decay and ensures yield bonus. |
| **Plant Seed** | `60 + ROI` | Expands productive capacity on vacant tile. |
| **Sell Produce Order** | `50` | Concurrent market order; processed without blocking farmer move. |
| **Buy Seed Order** | `40` | Prepares inventory for next planting cycle. |
| **Move to Harvestable** | `40` | Closes distance to high-value harvest target. |
| **Move to Water Target** | `30` | Closes distance to unwatered crop. |
| **Move to Empty Tile** | `20` | Repositions farmer toward available soil. |

---

## Step 5: Validating Your Changes

Run a quick test episode to confirm your new heuristic executes without errors:

```bash
python -c "
from simulation.episode import Episode
ep = Episode(agent1='src/main.py', agent2='starter', debug=True)
result = ep.run()
print('Score:', result.score_challenger, 'Status:', result.status_challenger)
"
```
