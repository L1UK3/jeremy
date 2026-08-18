# Tutorial: Developer Onboarding

This tutorial guides you through setting up your local development environment, understanding the repository layout, and running your first local simulation match between your agent and a baseline agent.

---

## Learning Objectives

By the end of this tutorial, you will:
1. Have a working Python 3.12+ environment with required simulation packages.
2. Understand where key subsystems live inside `src/`.
3. Run a complete 720-turn match using [`simulation.episode.Episode`](file:///d:/Projects/jeremy/src/simulation/episode.py).
4. Inspect the match result scores and replay JSON.

---

## Step 1: Set Up Your Development Environment

Ensure you have Python 3.12 or higher installed.

### Using `uv` (Recommended)

```bash
# Sync dependencies from pyproject.toml and uv.lock
uv sync
```

### Using standard `venv` and `pip`

```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install project and dependencies
pip install -e .
```

If you intend to use local GPU acceleration or custom local PyTorch builds, install from [`requirements.local.txt`](file:///d:/Projects/jeremy/requirements.local.txt):

```bash
pip install -r requirements.local.txt
```

---

## Step 2: Explore the Project Structure

The project code is centralized inside the [`src/`](file:///d:/Projects/jeremy/src) directory:

```
src/
├── agent/            # Decision-making logic, planner, priority search, task scheduler
├── environment/      # High-performance environment state wrappers and action builders
├── simulation/       # Head-to-head match runner and episode manager
├── archive/          # Kaggle API episode scraper, dataset repackager, feature extraction
├── utils/            # Packaging (build.py), plotting (plot.py), and progress indicators
└── main.py           # Kaggle entrypoint agent(obs) callback
```

---

## Step 3: Run Your First Simulation

Create a test script `test_match.py` in your project root or run the following snippet in Python:

```python
from simulation.episode import Episode

# Initialize a match between your agent and the built-in random agent
episode = Episode(
    agent1="src/main.py",      # Your agent entrypoint
    agent2="random",           # Baseline opponent ("random", "pass", or "starter")
    episode_idx=0,
    seat=0,                    # 0: Your agent is Seat 0 (P0); 1: Seat 1 (P1)
    debug=True
)

print("Starting match simulation (720 turns)...")
result = episode.run()

print("\n--- Match Results ---")
print(f"Challenger Final Bank : ${result.score_challenger:,.2f}")
print(f"Baseline Final Bank   : ${result.score_baseline:,.2f}")
print(f"Winner (0=Challenger, 1=Baseline, -1=Tie): {result.winner}")

# Save the match replay to disk
replay_file = episode.save_replay("replays/test_replay.json")
print(f"Replay saved to: {replay_file}")
```

Run the script:

```bash
python test_match.py
```

---

## Step 4: Verify Output, Replays, and Visualizer

When the simulation completes, you should observe:
1. `result.score_challenger` reflecting the coins earned by your agent at step 720.
2. `result.status_challenger` set to `"DONE"`.
3. A JSON file written to `replays/test_replay.json` containing the full turn-by-turn state history.

### Optional: Interactive Notebook Rendering

If you are developing inside a Jupyter or Kaggle notebook, you can render the visualizer widget directly:

```python
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env.run(["src/main.py", "starter"])
env.render(mode="ipython", width=1200, height=800)
```

---

## Next Steps

Now that your environment is running:
- Learn how to modify the decision loop in [How-To: Implement Agent Heuristics](../how-to/implement-agent-heuristics.md).
- Learn how to run automated multi-game tournaments in [How-To: Benchmark Agents & Plot Results](../how-to/benchmark-agents-and-plot.md).
- Review the class contracts in [Agent API Reference](../reference/agent-api.md).
