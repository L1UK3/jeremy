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

| File / Subpackage                                            | Role & Invariants                                                                                                              |
| :----------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| [`src/main.py`](src/main.py)                                 | **Top-level entrypoint**. Exports `def agent(obs: dict) -> dict:`. Orchestrates routes, evaluators, scheduler, and strategies. |
| [`src/state.py`](src/state.py)                               | **State wrapper**. Typed `GameState.from_obs(obs)` dataclass for fast attribute access.                                        |
| [`src/board.py`](src/board.py)                               | **Spatial grid manager**. `Board` and `Tile` with `__slots__`, precomputed neighbor lookups, and fast spatial queries.         |
| [`src/economy.py`](src/economy.py)                           | **Financial calculator**. Calculates `crop_roi()`, `should_expand()`, and affordable hiring counts.                            |
| [`src/market.py`](src/market.py)                             | **Rolling market stats**. Single-pass price analysis and composite `sell_score()`.                                             |
| [`src/scheduler.py`](src/scheduler.py)                       | **Multi-unit task dispatcher**. Allocates spatial crop and chore jobs to farmer and hired farmhands.                           |
| [`src/controller.py`](src/controller.py)                     | **Lifecycle controller**. Manages phase transitions, crop selection, and quadrant expansion staging.                           |
| [`src/evaluators/`](src/evaluators/)                         | **Evaluator subpackage**. Evaluates livestock feeding/care, market trades, and quadrant expansions.                            |
| [`src/routes/`](src/routes/)                                 | **Scripted trajectories**. Replay-extracted traces for early-game opening and quadrant expansions.                             |
| [`src/strategies/`](src/strategies/)                         | **End-game liquidation**. Fast harvest and market liquidation pipeline for Days 29–30.                                         |
| [`simulation/episode.py`](simulation/episode.py)             | **Simulation harness**. Runs 720-turn matches between two agents and saves replay JSONs.                                       |
| [`scripts/build_submission.py`](scripts/build_submission.py) | **Packager**. Bundles modular `src/` tree into `.out/submission.py` and `.out/submission.tar.gz`.                              |

---

## 3. Mandatory Agent Rules & Constraints

1. **Native Action Dictionaries**: Return standard action dictionaries `{"farmer": [...], "hands": [...], "market": [...]}` directly.
2. **Never hardcode movements in dynamic phases**: Use `step_toward()` or `Scheduler` spatial job dispatch.
3. **Action Merging**: The engine processes 1 farmer action + up to 10 market orders per turn concurrently.
4. **Passability on Locked Tiles**: Units can walk across locked quadrants to access other areas or the shed. Tile actions (`PLANT`, `WATER`, `DIG`, `BUILD_*`) no-op on locked tiles.
5. **Shed Adjacency**: Shed interaction coordinates are `(4,4)`, `(5,4)`, `(4,5)`, and `(5,5)` on the $10 \times 10$ board.
6. **No bytecode in packages**: `build_submission.py` excludes all `__pycache__` and `.pyc` files.

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
python scripts/build_submission.py --build
python scripts/build_submission.py --bundle

# 3. Format and lint
ruff check .
ruff format .
```
