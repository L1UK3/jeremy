# Jeremy Kaggriculture Framework Documentation

Welcome to the internal engineering documentation for the **Jeremy** Kaggriculture project. This documentation is organized according to the [Diátaxis framework](https://diataxis.fr/) across four distinct quadrants.

---

## Documentation Map

```
docs/
├── tutorials/
│   └── onboarding.md                             # Step-by-step developer onboarding
├── how-to/
│   ├── implement-agent-heuristics.md             # Writing and integrating new planner rules
│   ├── benchmark-agents-and-plot.md              # Running multi-game benchmarks and plotting
│   ├── build-submission-package.md               # Bundling and smoke-testing submissions
│   └── scrape-and-process-replays.md             # Scraping ladder games and dataset mining
├── reference/
│   ├── game-rules-and-mechanics.md               # Official parameters, object tables, pricing curves
│   ├── agent-api.md                              # API contracts: Planner, Search, Scheduler
│   ├── environment-api.md                        # API contracts: GameState, Board, Economy, Actions
│   └── archive-pipeline.md                       # CLI flags and dataset Parquet/CSV schemas
└── explanation/
    ├── system-architecture.md                    # Engine design and subsystem decoupling
    └── decision-cycle-and-economic-model.md      # Action resolution, scoring, and ROI math
```

---

## Quadrants Overview

### 1. [Tutorials](tutorials/onboarding.md) (Learning-Oriented)
Practical, end-to-end walkthroughs for new developers getting started on the team.
* **[Developer Onboarding](tutorials/onboarding.md)**: Set up the Python 3.12 environment, run a baseline 720-turn simulation, and inspect output replays.

### 2. [How-To Guides](how-to/) (Problem-Oriented)
Task-focused recipes to solve specific engineering and development problems.
* **[Implement Agent Heuristics](how-to/implement-agent-heuristics.md)**: Add new decision logic, query board tiles, and score candidate actions.
* **[Benchmark Agents & Plot Results](how-to/benchmark-agents-and-plot.md)**: Execute head-to-head agent tournaments with alternating seats and plot score distributions.
* **[Build & Validate Submission Package](how-to/build-submission-package.md)**: Package codebase artifacts into `submission.tar.gz` and run local environment smoke tests.
* **[Scrape & Process Ladder Replays](how-to/scrape-and-process-replays.md)**: Scrape top ladder matches from the Kaggle API, repack replays into Parquet, and compute behavioral feature matrices.

### 3. [Reference](reference/) (Information-Oriented)
Technical descriptions of classes, functions, contracts, and schemas.
* **[Game Rules & Mechanics Reference](reference/game-rules-and-mechanics.md)**: Official crop/animal stats, bonus watering windows, town shops, price formulas, and engine parameters.
* **[Agent API Reference](reference/agent-api.md)**: Full API specification for `Planner`, `Search`, `Node`, `Scheduler`, and `Job`.
* **[Environment API Reference](reference/environment-api.md)**: Full API specification for `GameState`, `Board`, `Tile`, `Economy`, `Market`, `ActionBuilder`, and observation schemas.
* **[Archive Pipeline & Dataset Reference](reference/archive-pipeline.md)**: Detailed schema definitions for CSV/Parquet dataset files and CLI tool parameters.

### 4. [Explanation](explanation/) (Understanding-Oriented)
Conceptual discussions on architecture, mechanics, and design rationale.
* **[System Architecture](explanation/system-architecture.md)**: Design philosophy, subsystem boundaries, and execution pipeline.
* **[Decision Cycle & Economic Model](explanation/decision-cycle-and-economic-model.md)**: Mechanics of the 720-turn game loop, action merging, ROI calculations, and market pricing curves.
