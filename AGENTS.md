# AI Agent Instructions — Jeremy Kaggriculture

System manual and operational contract for AI coding agents modifying the **Jeremy** codebase.

---

## 1. Documentation Index

Consult these documents in [`docs/`](docs/index.md) before designing or changing code:

- **Rules & Mechanics**: [`docs/reference/game-rules-and-mechanics.md`](docs/reference/game-rules-and-mechanics.md) (crop/animal tables, price formulas, engine parameters)
- **Environment API**: [`docs/reference/environment-api.md`](docs/reference/environment-api.md) (`GameState`, `Board`, `Tile`, `Economy`, `Market`, `ActionBuilder`)
- **Agent API**: [`docs/reference/agent-api.md`](docs/reference/agent-api.md) (`Planner`, `Search`, `Scheduler`)
- **Heuristics Guide**: [`docs/how-to/implement-agent-heuristics.md`](docs/how-to/implement-agent-heuristics.md) (scoring and planner logic)
- **Benchmark Guide**: [`docs/how-to/benchmark-agents-and-plot.md`](docs/how-to/benchmark-agents-and-plot.md) (evaluation and tournament runs)
- **Submission Guide**: [`docs/how-to/build-submission-package.md`](docs/how-to/build-submission-package.md) (packaging `submission.tar.gz`)
- **Integration Status**: [`docs/environment-integration-status.md`](docs/environment-integration-status.md) (unimplemented / planned features tracker)

---

## 2. Core Architecture & File Responsibilities

| File | Role & Invariants |
| :--- | :--- |
| [`src/main.py`](src/main.py) | **Top-level entrypoint**. Exports `def agent(obs: dict) -> dict:`. Wraps `obs` in `GameState`, executes `Planner(state).play().to_dict()`. |
| [`src/agent/planner.py`](src/agent/planner.py) | **Decision loop**. Evaluates market, current tile, planting, and movement. Pushes scored candidate actions into `Search`. |
| [`src/agent/search.py`](src/agent/search.py) | **Candidate pool**. Stores `Node(score, action)`. `topk()` and `best()` prioritize actions. |
| [`src/agent/scheduler.py`](src/agent/scheduler.py) | **Multi-unit task dispatcher**. Allocates non-overlapping spatial jobs to farmer and hired farmhands. |
| [`src/environment/state.py`](src/environment/state.py) | **State wrapper**. Typed `GameState.from_obs(obs)` dataclass for fast attribute access. |
| [`src/environment/board.py`](src/environment/board.py) | **Spatial grid manager**. Yields `Tile` generators (`harvestable()`, `needs_water()`, `empty_tiles()`) and Manhattan `nearest()`. |
| [`src/environment/economy.py`](src/environment/economy.py) | **Financial calculator**. Calculates `crop_roi()`, `best_crop()`, and checks affordability. |
| [`src/environment/market.py`](src/environment/market.py) | **Rolling market stats**. 20-turn price window, trend tracking, and composite `sell_score()`. |
| [`src/environment/actions.py`](src/environment/actions.py) | **Action factory**. Static `ActionBuilder` methods and `ActionBuilder.merge()` logic. |
| [`src/simulation/episode.py`](src/simulation/episode.py) | **Simulation harness**. Runs 720-turn matches between two agents and saves replay JSONs. |
| [`src/utils/build.py`](src/utils/build.py) | **Packager**. Bundles `agent/`, `environment/`, and `main.py` into root of `submission.tar.gz`. |

---

## 3. Mandatory Agent Rules & Constraints

1. **Never write raw action dictionaries**: Always use [`ActionBuilder`](docs/reference/environment-api.md#class-actionbuilder) static methods (`ActionBuilder.water()`, `ActionBuilder.plant(crop)`, `ActionBuilder.sell(item, n)`).
2. **Never hardcode movements**: Use `Planner.move_to(tile)` or `Board.nearest()` Manhattan distance queries.
3. **Action Merging**: The engine processes 1 farmer action + up to 10 market orders per turn concurrently. Use `ActionBuilder.merge(*actions)` to combine them.
4. **Passability on Locked Tiles**: Units can walk across locked quadrants to access other areas or the shed. Only tile actions (`PLANT`, `WATER`, `DIG`, `BUILD_*`) no-op on locked tiles.
5. **Shed Adjacency**: Shed interaction coordinates are `(4,4)`, `(5,4)`, `(4,5)`, and `(5,5)` on the $10 \times 10$ board.
6. **No bytecode in packages**: `build.py` excludes all `__pycache__` and `.pyc` files.

---

## 4. Score Calibration Hierarchy

When pushing candidate actions to `self.search.add(score, action)`, adhere strictly to these utility ranges:

```
Score >= 100 : Immediate revenue       → ActionBuilder.harvest() [100 + (units * price)]
Score = 90   : Tile recovery          → ActionBuilder.dig() (clear weed underfoot)
Score = 80   : Plant maintenance      → ActionBuilder.water()
Score = 60+  : Capacity expansion     → ActionBuilder.plant(crop) [60 + crop_roi]
Score = 40-50: Concurrent market trade → ActionBuilder.sell() (50), ActionBuilder.buy_seed() (40)
Score = 20-40: Target repositioning   → Move to harvest (40), move to water (30), move to empty (20)
```

---

## 5. Idiomatic Pattern: Adding a Decision Rule

To add a new rule in [`src/agent/planner.py`](src/agent/planner.py):

```python
# 1. Query environment/board state
tile = self.state.current_tile
if isinstance(tile, dict) and tile.get("kind") == "WEED":
    # 2. Build action with ActionBuilder and score against calibration table
    self.add(90, ActionBuilder.dig())
```

---

## 6. Continuous Documentation Protocol

Every AI agent must follow this 3-step loop:

1. **Read**: Check [`docs/reference/`](docs/reference/) and [`docs/environment-integration-status.md`](docs/environment-integration-status.md) before writing code.
2. **Verify**: Ensure code matches the documented signatures and scoring hierarchy.
3. **Update**: Modify the corresponding documentation files under [`docs/`](docs/index.md) whenever you add, refactor, or adjust features.

---

## 7. Verification & Smoke Test Commands

Run from project root:

```bash
# 1. Run a 1-match smoke test simulation
python -c "
import sys; sys.path.insert(0, 'src')
from simulation.episode import Episode
ep = Episode(agent1='src/main.py', agent2='starter', debug=True)
res = ep.run()
print(f'Score: {res.score_challenger:,.2f} | Status: {res.status_challenger}')
assert res.status_challenger == 'DONE'
"

# 2. Build and verify submission package
python src/utils/build.py

# 3. Format and lint
ruff check .
ruff format .
```
