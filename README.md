# Jeremy — Kaggriculture AI Agent & Simulation Framework

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Documentation: Diataxis](https://img.shields.io/badge/docs-Diátaxis-brightgreen.svg)](docs/index.md)

**Jeremy** is a high-performance Python framework for building, simulating, benchmarking, and deploying competitive AI agents for the [Kaggle Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) multi-agent farming simulation environment. It is naturally named after a lovely farmer called Jeremy.

<img src="https://i2-prod.manchestereveningnews.co.uk/article34141179.ece/ALTERNATES/s1200f/0_clarkson.jpg" width="75%" height="auto">

---

## Architecture Overview

```
jeremy/
├── pyproject.toml              # Build & dependency spec (pytest, ruff, pythonpath = ["src"])
├── ruff.toml                   # Code formatting & linter rules
├── AGENTS.md                   # AI Agent manual & operational invariants
├── README.md                   # Project overview & quickstart
├── scripts/
│   ├── build_submission.py     # Bundler creating standalone .out/submission.py & submission.tar.gz
│   └── data_analysis.py        # Replay dataset analyzer
├── src/                        # Core agent package
│   ├── __init__.py             # Public top-level exports (__all__)
│   ├── main.py                 # Top-level Kaggle entrypoint: agent(obs)
│   ├── state.py                # GameState observation parser & typed dataclass
│   ├── board.py                # Spatial Board grid indexing & Tile properties (__slots__)
│   ├── economy.py              # Financial models, crop ROI calculators, and hiring thresholds
│   ├── market.py               # Rolling price window, trend indicators, and sell scoring
│   ├── scheduler.py            # Multi-unit spatial task & chore job dispatcher
│   ├── controller.py           # Lifecycle phase controller & crop selection
│   ├── evaluators/             # Subpackage: Decision evaluators
│   │   ├── __init__.py         # Evaluator exports
│   │   ├── expansion.py        # Land expansion logic (Day ≥ 8, Day ≥ 22)
│   │   ├── livestock.py        # Animal chore routines (feed, care, fertilizer, harvest)
│   ├── routes.json             # Scripted opening (turns 0–23) & expansion trajectories
│   └── strategies/             # Subpackage: Endgame algorithms
│       ├── __init__.py         # Strategy exports
│       └── explosion.py        # Days 29–30 fast harvest & market liquidation pipeline
├── tests/                      # Unit & integration test suite (pytest)
│   ├── __init__.py
│   ├── test_state.py           # GameState parsing & shed adjacency tests
│   ├── test_board.py           # Spatial queries & Tile attribute tests
│   ├── test_economy.py         # ROI calculations & hiring affordability tests
│   ├── test_agent.py           # Agent callback signature & action contract tests
│   └── test_submission.py      # Simulation integration test against baseline
├── data/                       # Kaggle API episode crawler & dataset generator
│   ├── scrape.py               # Public ladder replay scraper
│   ├── repack.py               # Parquet dataset generator
│   ├── teams.py                # Leaderboard team metadata sync
│   └── features.py             # Match feature extraction
└── simulation/                 # Simulation & tournament evaluation harness
    ├── episode.py              # 720-turn match execution & replay saver
    └── base/                   # Baseline agent benchmarks (c95, v16, v46)
```

---

## Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/jeremy.git
cd jeremy

# Install dependencies via uv (recommended)
uv sync

# Or using standard pip in a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -e .
```

### 2. Run Test Suite

```bash
# Run unit and integration tests
uv run pytest
```

### 3. Run a Local Test Simulation

```bash
# Run a 720-turn head-to-head match against the starter agent
uv run python -c "
from simulation.episode import Episode
ep = Episode(agent1='src/main.py', agent2='starter', debug=True)
res = ep.run()
print(f'Score: {res.score_challenger:,.2f} vs {res.score_baseline:,.2f} | Status: {res.status_challenger}')
"
```

### 4. Build Standalone Submission Package

```bash
# Compile and bundle into .out/submission.py and .out/submission.tar.gz
uv run python scripts/build_submission.py --build --bundle
```

---

## Documentation

Full developer and architecture documentation is structured under [`docs/`](docs/index.md):

- **[Developer Onboarding Tutorial](docs/tutorials/onboarding.md)**: Step-by-step onboarding, environment verification, and first simulation match.
- **How-To Guides**:
    - **[Implement Agent Heuristics](docs/how-to/implement-agent-heuristics.md)**: Adding decision rules, querying the board, and scoring candidates.
    - **[Benchmark Agents & Plot Results](docs/how-to/benchmark-agents-and-plot.md)**: Multi-game head-to-head tournaments with alternating seat positions.
    - **[Build & Validate Submission Package](docs/how-to/build-submission-package.md)**: Tarball creation, smoke testing, and Kaggle CLI submission.
    - **[Scrape & Process Ladder Replays](docs/how-to/scrape-and-process-replays.md)**: Mining public replays into Parquet feature tables.
- **Reference Specifications**:
    - **[Game Rules & Mechanics Reference](docs/reference/game-rules-and-mechanics.md)**: Official crop/animal stats, bonus watering windows, town shops, price formulas, and engine parameters.
    - **[Agent API Reference](docs/reference/agent-api.md)**: Method contracts for `Planner`, `Search`, `Node`, `Scheduler`, and `Job`.
    - **[Environment API Reference](docs/reference/environment-api.md)**: API specification for `GameState`, `Board`, `Tile`, `Economy`, `Market`, and `ActionBuilder`.
    - **[Archive Pipeline Reference](docs/reference/archive-pipeline.md)**: Dataset schemas for `replays.parquet`, `episodes.csv`, `episode_features.csv`, etc.
- **Explanation Deep-Dives**:
    - **[System Architecture](docs/explanation/system-architecture.md)**: Subsystem boundaries, design philosophy, and execution flow.
    - **[Decision Cycle & Economic Model](docs/explanation/decision-cycle-and-economic-model.md)**: Mechanics of the 720-turn game loop, action merging, and ROI math.

---

## Game Rules Summary

Kaggriculture is a 2-player simultaneous farming simulation spanning 30 days (24 turns/day = 720 turns):

- **Board**: $10 \times 10$ grid divided into four $5 \times 5$ quadrants (`NW` starts unlocked; `NE`, `SW`, `SE` cost \$1k, \$2k, \$4k).
- **Crops**: Wheat, Carrot, Tomato (ongoing), Strawberry (ongoing), Melon. Watering during the bonus window ($\ge \lceil \text{max\_yield\_day}/2 \rceil$) adds $+1$ harvestable yield/day ($+2$ if fertilized).
- **Animals**: Goose (eggs), Cow (milk), Sheep (wool). Fed wheat daily; `CARE` banks yield bonuses for next harvest; `COLLECT_FERTILIZER` yields 1 fertilizer/day.
- **Decay & Survival**: 2 consecutive unwatered/unfed days turn plants to weeds or cause animals to escape. Crops decay after max lifespan.
- **Market**: Dynamic pricing based on global inventory $I$ relative to $I_0 = 10,000$. Gluts drop prices toward \$1; scarcity raises prices. Town shops unlock every 3 days and consume market supply.
- **Win Condition**: Player with the most coins in the bank at turn 720 wins.

For exhaustive formulas, tables, and mechanics, see [`docs/reference/game-rules-and-mechanics.md`](docs/reference/game-rules-and-mechanics.md).

---

## License & Attribution

Game environment and engine provided by [kaggle-environments](https://github.com/Kaggle/kaggle-environments).
