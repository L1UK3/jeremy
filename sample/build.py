import re
from datetime import UTC, datetime
from pathlib import Path

MODEL_DIR = Path("/kaggle/input/models/jek1wantaufik/buddy/scikitlearn/agric/2")

OUTPUT = Path("/kaggle/working/submission.py")

MODULES = [
    "state.py",
    "board.py",
    "actions.py",
    "economy.py",
    "market.py",
    "scheduler.py",
    "search.py",
    "planner.py",
    "agent.py",
]

HEADER = f"""# ==========================================================
# AUTO GENERATED SUBMISSION
# Generated : {datetime.now(UTC).isoformat()}
# Source    : {MODEL_DIR}
# ==========================================================

"""

internal_modules = {Path(m).stem for m in MODULES}


def split_source(text):

    imports = []
    body = []

    blank = False

    for line in text.splitlines():
        s = line.strip()

        if s.startswith("from "):
            m = re.match(
                r"from\s+([A-Za-z0-9_]+)\s+import",
                s,
            )

            if m and m.group(1) in internal_modules:
                continue

            if line not in imports:
                imports.append(line)
            continue

        if s.startswith("import "):
            if line not in imports:
                imports.append(line)
            continue

        if s == "":
            if blank:
                continue
            blank = True
        else:
            blank = False

        body.append(line.rstrip())

    while body and body[-1] == "":
        body.pop()

    return imports, body


all_imports = []
seen_imports = set()
merged = []

print("=" * 60)
print("Building submission.py")
print("=" * 60)

for module in MODULES:
    path = MODEL_DIR / module

    if not path.exists():
        raise FileNotFoundError(path)

    print(f"✓ {module}")

    imports, body = split_source(path.read_text(encoding="utf-8"))

    for imp in imports:
        if imp not in seen_imports:
            seen_imports.add(imp)
            all_imports.append(imp)

    merged.extend(body)
    merged.append("")

while merged and merged[-1] == "":
    merged.pop()

with OUTPUT.open("w", encoding="utf-8") as f:
    f.write(HEADER)

    for imp in sorted(all_imports):
        f.write(imp + "\n")

    f.write("\n")

    for line in merged:
        f.write(line + "\n")

compile(
    OUTPUT.read_text(encoding="utf-8"),
    "submission.py",
    "exec",
)

print()
print("=" * 60)
print("SUCCESS")
print("=" * 60)
print(f"Output  : {OUTPUT}")
print(f"Modules : {len(MODULES)}")
print(f"Imports : {len(all_imports)}")
print(f"Lines   : {len(OUTPUT.read_text(encoding='utf-8').splitlines()):,}")
print(f"Size    : {OUTPUT.stat().st_size:,} bytes")

from kaggle_environments import make

from sample.buddy.agent import agent

env = make("kaggriculture", debug=True)
env.run([agent, "random"])

print(env.steps[-1][0].status)
print(env.steps[-1][0].reward)
