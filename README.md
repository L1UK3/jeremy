# Jeremy — Kaggriculture AI Agent & Simulation Framework

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Documentation: Diataxis](https://img.shields.io/badge/docs-Diátaxis-brightgreen.svg)](docs/index.md)

**Jeremy** is a high-performance Python framework for building, simulating, benchmarking, and deploying competitive AI agents for the [Kaggle Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) multi-agent farming simulation environment. It is naturally named after a lovely farmer called Jeremy.

<img src="https://i2-prod.manchestereveningnews.co.uk/article34141179.ece/ALTERNATES/s1200f/0_clarkson.jpg" width="75%" height="auto">

---

## Architecture Overview

```
src/
├── agent/            # Decision-making logic, heuristic planner, priority search queue, job scheduler
│   ├── planner.py    # Main turn coordinator and domain evaluations
│   ├── search.py     # Priority candidate queue (Node, Search)
│   └── scheduler.py  # Multi-unit spatial task assignment for farmer and hired farmhands
├── environment/      # High-performance environment wrappers, state parsers, and action builders
│   ├── state.py      # Typed GameState observation parser
│   ├── board.py      # Spatial Board grid queries and Tile distance calculators
│   ├── economy.py    # Economic models, crop ROI calculators, and financial thresholds
│   ├── market.py     # Rolling price statistics, trend indicators, and sell score rankings
│   └── actions.py    # Action dataclass and ActionBuilder static factory
├── simulation/       # Head-to-head match runner and tournament evaluator
│   └── episode.py    # 720-turn episode execution, reward extraction, and replay saver
├── archive/          # Kaggle API episode crawler, dataset repackager, and feature extraction
│   ├── scrape.py     # Public ladder game scraper
│   ├── repack.py     # Zstandard Parquet dataset generator (replays.parquet)
│   ├── teams.py      # Leaderboard team metadata sync
│   └── features.py   # Strategic match feature extraction
├── utils/            # Packaging and visualization utilities
│   ├── build.py      # Automated packager for submission.tar.gz
│   ├── plot.py       # Matplotlib score trajectory and distribution charts
│   └── progress.py   # Real-time CLI progress bar generator
└── main.py           # Kaggle entrypoint agent(obs) callback
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


### 2. Run a Local Test Simulation

```bash
# run 700 games against a baseline agent
python src/simulation/episode.py
```

### 3. Build Submission Package

```bash
# Package into submission.tar.gz
python src/utils/build.py
```

---

## Documentation

Full developer and architecture documentation is structured under [`docs/`](docs/index.md):

* **[Developer Onboarding Tutorial](docs/tutorials/onboarding.md)**: Step-by-step onboarding, environment verification, and first simulation match.
* **How-To Guides**:
  * **[Implement Agent Heuristics](docs/how-to/implement-agent-heuristics.md)**: Adding decision rules, querying the board, and scoring candidates.
  * **[Benchmark Agents & Plot Results](docs/how-to/benchmark-agents-and-plot.md)**: Multi-game head-to-head tournaments with alternating seat positions.
  * **[Build & Validate Submission Package](docs/how-to/build-submission-package.md)**: Tarball creation, smoke testing, and Kaggle CLI submission.
  * **[Scrape & Process Ladder Replays](docs/how-to/scrape-and-process-replays.md)**: Mining public replays into Parquet feature tables.
* **Reference Specifications**:
  * **[Game Rules & Mechanics Reference](docs/reference/game-rules-and-mechanics.md)**: Official crop/animal stats, bonus watering windows, town shops, price formulas, and engine parameters.
  * **[Agent API Reference](docs/reference/agent-api.md)**: Method contracts for `Planner`, `Search`, `Node`, `Scheduler`, and `Job`.
  * **[Environment API Reference](docs/reference/environment-api.md)**: API specification for `GameState`, `Board`, `Tile`, `Economy`, `Market`, and `ActionBuilder`.
  * **[Archive Pipeline Reference](docs/reference/archive-pipeline.md)**: Dataset schemas for `replays.parquet`, `episodes.csv`, `episode_features.csv`, etc.
* **Explanation Deep-Dives**:
  * **[System Architecture](docs/explanation/system-architecture.md)**: Subsystem boundaries, design philosophy, and execution flow.
  * **[Decision Cycle & Economic Model](docs/explanation/decision-cycle-and-economic-model.md)**: Mechanics of the 720-turn game loop, action merging, and ROI math.

---

## Game Rules Summary

Kaggriculture is a 2-player simultaneous farming simulation spanning 30 days (24 turns/day = 720 turns):

* **Board**: $10 \times 10$ grid divided into four $5 \times 5$ quadrants (`NW` starts unlocked; `NE`, `SW`, `SE` cost \$1k, \$2k, \$4k).
* **Crops**: Wheat, Carrot, Tomato (ongoing), Strawberry (ongoing), Melon. Watering during the bonus window ($\ge \lceil \text{max\_yield\_day}/2 \rceil$) adds $+1$ harvestable yield/day ($+2$ if fertilized).
* **Animals**: Goose (eggs), Cow (milk), Sheep (wool). Fed wheat daily; `CARE` banks yield bonuses for next harvest; `COLLECT_FERTILIZER` yields 1 fertilizer/day.
* **Decay & Survival**: 2 consecutive unwatered/unfed days turn plants to weeds or cause animals to escape. Crops decay after max lifespan.
* **Market**: Dynamic pricing based on global inventory $I$ relative to $I_0 = 10,000$. Gluts drop prices toward \$1; scarcity raises prices. Town shops unlock every 3 days and consume market supply.
* **Win Condition**: Player with the most coins in the bank at turn 720 wins.

For exhaustive formulas, tables, and mechanics, see [`docs/reference/game-rules-and-mechanics.md`](docs/reference/game-rules-and-mechanics.md).

---

## License & Attribution

Game environment and engine provided by [kaggle-environments](https://github.com/Kaggle/kaggle-environments).
