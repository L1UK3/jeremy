# Reference: Agent API

This document provides the technical specification and API reference for the decision-making and planning modules in `src/agent/`.

---

## Module: `agent.planner`

### `class Planner`

Main heuristic planning coordinator that inspects game state, invokes domain evaluations, queues candidate actions in `Search`, and produces the final merged action for the turn.

```python
class Planner:
    def __init__(self, state: GameState) -> None: ...
```

#### Instance Attributes
* `state: GameState` — Current turn game state wrapper.
* `board: Board` — Spatial grid manager.
* `eco: Economy` — ROI and cost calculator.
* `search: Search` — Priority candidate action queue.

#### Methods

##### `add(score: float, action: Action) -> None`
Pushes a candidate action with an assigned numerical utility score to `self.search`.

##### `evaluate_market() -> None`
Evaluates market sales and purchases:
- Queues `SELL` if best crop inventory exists and price exceeds seed cost.
- Queues `BUY_SEED` if holding 0 seeds and balance is sufficient.

##### `evaluate_current_tile() -> None`
Inspects `self.state.current_tile`:
- If tile is a mature crop (`yield_units > 0`), queues `HARVEST` with score `100 + (units * price)`.
- If tile is an unwatered crop, queues `WATER` with score `80`.

##### `evaluate_planting() -> None`
Checks if `self.state.current_tile` is `None` (empty unlocked tile). If seeds for the highest-ROI crop are in storage, queues `PLANT <crop>` with score `60 + ROI`.

##### `evaluate_movement() -> None`
Finds nearest objective target on the board in priority order:
1. Harvestable plant (`score = 40`)
2. Plant needing water (`score = 30`)
3. Empty unlocked tile (`score = 20`)

##### `move_to(tile: Tile) -> Action`
Computes a single Manhattan step (`NORTH`, `SOUTH`, `EAST`, or `WEST`) from farmer position `(fx, fy)` toward `(tile.x, tile.y)`. Returns `ActionBuilder.pass_turn()` if already at destination.

##### `choose() -> Action`
Merges all candidate nodes in `self.search` using `ActionBuilder.merge()`.

##### `play() -> Action`
Runs the evaluation cycle (`evaluate_market`, `evaluate_current_tile`, `evaluate_planting`, `evaluate_movement`), dumps the top search candidates to stdout, and returns the merged `Action`.

---

## Module: `agent.search`

### `class Node`
A lightweight dataclass container storing scored candidate actions.

```python
@dataclass(slots=True)
class Node:
    score: float
    action: Action
    state: GameState | None = None
    parent: Any = None
```

---

### `class Search`
Priority candidate pool for accumulating, sorting, and pruning candidate actions.

```python
class Search:
    def __init__(self) -> None: ...
```

#### Methods

##### `clear() -> None`
Clears all registered nodes.

##### `add(score: float, action: Action, state: GameState | None = None, parent: Any = None) -> None`
Appends a new `Node` to `self.nodes`.

##### `empty() -> bool`
Returns `True` if `len(self.nodes) == 0`.

##### `best() -> Node | None`
Returns the node with maximum `score`, or `None` if empty.

##### `topk(k: int = 5) -> list[Node]`
Returns the top `k` nodes sorted in descending order by `score`.

##### `choose() -> Action | None`
Returns `best().action` or `None` if empty.

##### `dump() -> None`
Prints the top-5 scored actions to stdout for debugging.

---

## Module: `agent.scheduler`

### `class Job`
Dataclass representing a unit task assignment for multi-agent coordination.

```python
@dataclass(slots=True)
class Job:
    priority: float
    action: str
    target: tuple[int, int]
    actor: str = "farmer"
```

---

### `class Scheduler`
Multi-unit task allocation queue for assigning non-overlapping spatial tasks across the main farmer and hired farmhands.

```python
class Scheduler:
    def __init__(self, state: GameState) -> None: ...
```

#### Methods

##### `add_job(action: str, x: int, y: int, priority: float, actor: str = "farmer") -> None`
Adds a new job target to `self.jobs`.

##### `sort() -> None`
Sorts `self.jobs` in-place in descending order of `priority`.

##### `best() -> Job | None`
Returns the highest-priority job.

##### `assign() -> tuple[Job | None, list[Job]]`
Greedily dispatches jobs to units while ensuring no two units target the same `(x, y)` coordinate. Returns `(farmer_job, [hand_job_1, hand_job_2, ...])`.

##### `clear() -> None`
Empties the job queue.
