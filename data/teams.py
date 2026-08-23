#!/usr/bin/env python3
"""Writes teams.csv: team_id -> team name and current ladder score.

Episode rows carry team ids only, so charts built on them are unreadable
without this join. Names come from the public leaderboard, paged through
until it stops returning new rows.
"""
import csv
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE.parent / ".out"
OUT = OUT_DIR / "teams.csv"


def leaderboard_rows():
    seen, rows, token = set(), [], None
    while True:
        cmd = ["kaggle", "competitions", "leaderboard", "kaggriculture", "-s", "-v"]
        if token:
            cmd += ["--page-token", token]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
        token = next(
            (line.split("= ")[1].strip() for line in out if line.startswith("Next Page Token")),
            None,
        )
        body = [line for line in out if not line.startswith("Next Page Token") and line.strip()]
        if not body:
            break
        reader = csv.DictReader(body)
        fresh = [r for r in reader if r.get("teamId") and r["teamId"] not in seen]
        for r in fresh:
            seen.add(r["teamId"])
            rows.append(r)
        if not fresh or not token:
            break
    return rows


rows = leaderboard_rows()
OUT_DIR.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["team_id", "team_name", "ladder_score", "last_submission"])
    for r in rows:
        w.writerow([r["teamId"], r["teamName"], r.get("score"), r.get("submissionDate")])
print(f"teams.csv: {len(rows)} teams")
