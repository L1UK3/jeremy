# How-To: Build & Validate Submission Package

This guide details how to bundle agent source files into a valid `submission.tar.gz` archive and smoke-test it against the Kaggle environment engine before submitting to the leaderboard.

---

## Submission Format Requirements

Kaggle requires a `.tar.gz` archive containing:
1. `main.py` at the root of the archive exposing an `agent(obs)` function.
2. Supporting modules placed alongside `main.py` (e.g. `agent/`, `environment/`).
3. Exclusion of byte-compiled `.pyc` and `__pycache__` directories.

---

## Step 1: Generate `submission.tar.gz`

Execute the automated packager in [`src/utils/build.py`](file:///d:/Projects/jeremy/src/utils/build.py):

```bash
python src/utils/build.py
```

Expected output:
```
  Output Archive : D:\Projects\jeremy\submission.tar.gz
  Created        : 1723984210.0
  Archive Size   : 14,280 bytes
```

---

## Step 2: Verify Archive Contents

Inspect the internal directory layout of the generated tarball to verify paths are rooted correctly:

### In PowerShell
```powershell
tar -tzf submission.tar.gz
```

### Expected Directory Listing
```
main.py
agent/
agent/__init__.py
agent/planner.py
agent/scheduler.py
agent/search.py
environment/
environment/__init__.py
environment/actions.py
environment/board.py
environment/economy.py
environment/market.py
environment/state.py
```

> [!IMPORTANT]
> `main.py` MUST reside at the top level of the archive, NOT inside a nested `src/` folder. [`src/utils/build.py`](file:///d:/Projects/jeremy/src/utils/build.py) automatically strips the `src/` prefix during packaging.

---

## Step 3: Run Local Smoke Test on the Archive

Because `kaggle_environments` executes `.py` entrypoints directly during local testing, verify your packaged archive by extracting it to a clean temporary test folder:

```python
import tempfile
import tarfile
from kaggle_environments import make

with tempfile.TemporaryDirectory() as tmp_dir:
    # Extract the generated tar.gz
    with tarfile.open("submission.tar.gz", "r:gz") as tar:
        tar.extractall(tmp_dir)

    # Run the extracted entrypoint
    entrypoint = f"{tmp_dir}/main.py"
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
    env.run([entrypoint, "random"])

    final_step = env.steps[-1]
    challenger_status = final_step[0].status
    challenger_reward = final_step[0].reward

    print(f"Status: {challenger_status}")
    print(f"Reward: ${challenger_reward:,.2f}")
    assert challenger_status == "DONE", f"Agent failed with status {challenger_status}"
    print("Smoke test passed successfully!")
```

---

## Step 4: Configure Kaggle CLI Credentials

If you haven't set up the Kaggle CLI:

```bash
pip install kaggle
```

Place your Kaggle API token in `~/.kaggle/access_token`:
```bash
# Recommended on Linux/macOS
mkdir -p ~/.kaggle
nano ~/.kaggle/access_token
chmod 600 ~/.kaggle/access_token

# Or set as environment variable
export KAGGLE_API_TOKEN="your_token_here"
```

Verify authentication and joined competitions:
```bash
kaggle competitions list --group entered
```

---

## Step 5: Submit to Kaggle Leaderboard

Submit your packaged `submission.tar.gz` archive:

```bash
kaggle competitions submit kaggriculture -f submission.tar.gz -m "v1.2: Heuristic planner with weed digging"
```

---

## Step 6: Monitor Submissions & Debug Episodes

### 1. Check Submission Status
```bash
kaggle competitions submissions kaggriculture
```
Take note of your `<SUBMISSION_ID>`.

### 2. List Match Episodes
View all games played by your submission on the ladder:
```bash
# Formatted table
kaggle competitions episodes <SUBMISSION_ID>

# CSV output for scripting
kaggle competitions episodes <SUBMISSION_ID> -v
```

### 3. Download Episode Replays
Download the complete replay JSON for offline inspection or local visualizer playback:
```bash
kaggle competitions replay <EPISODE_ID> -p ./replays
```

### 4. Download Execution Logs
Fetch standard output / standard error logs to debug runtime exceptions or verify search decisions:
```bash
# Logs for Player 0 (Seat 0)
kaggle competitions logs <EPISODE_ID> 0 -p ./logs

# Logs for Player 1 (Seat 1)
kaggle competitions logs <EPISODE_ID> 1 -p ./logs
```

### 5. Check Leaderboard Standings
```bash
kaggle competitions leaderboard kaggriculture -s
```
