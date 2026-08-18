"""
Bundle agent source files into submission.py and submission.tar.gz.
"""

import re
import tarfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "src" / "agent"
OUTPUT_PY = ROOT / "submission.py"
OUTPUT_TAR = ROOT / "submission.tar.gz"

DEFAULT_MODULES = [
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


def clean_source(
    text: str, internal_modules: set[str]
) -> tuple[list[str], list[str]]:
    """
    Extract external imports and cleaned body lines from a source module.

    - Internal module imports (e.g. `from state import ...` or `from .state import ...`) are stripped.
    - Standard/third-party imports are extracted and deduplicated.
    - Consecutive blank lines and trailing line spaces are collapsed.
    """
    imports: list[str] = []
    body: list[str] = []
    blank = False

    for line in text.splitlines():
        s = line.strip()

        # Only extract top-level (unindented) imports
        if line.startswith("from "):
            m = re.match(
                r"from\s+(?:\.?agent\.)?\.?([A-Za-z0-9_]+)\s+import", s
            )
            if m and m.group(1) in internal_modules:
                continue
            if line not in imports:
                imports.append(line)
            continue

        if line.startswith("import "):
            m = re.match(r"import\s+(?:\.?agent\.)?\.?([A-Za-z0-9_]+)", s)
            if m and m.group(1) in internal_modules:
                continue
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

    # Trim trailing blank lines
    while body and body[-1] == "":
        body.pop()

    return imports, body


def build_submission(modules: list[str] = DEFAULT_MODULES) -> None:
    """Bundle modular source files from src/agent/ into submission.py."""
    print("Building submission.py from modules:")
    internal_modules = {Path(m).stem for m in modules}
    all_imports: list[str] = []
    seen_imports: set[str] = set()
    merged_body: list[str] = []

    for module in modules:
        path = AGENT_DIR / module
        if not path.exists():
            raise FileNotFoundError(f"Required module not found: {path}")

        print(f"  [+] Bundling: {module}")
        imports, body = clean_source(
            path.read_text(encoding="utf-8"), internal_modules
        )

        for imp in imports:
            if imp not in seen_imports:
                seen_imports.add(imp)
                all_imports.append(imp)

        merged_body.append(
            f"\n# ===================== {module} ====================="
        )
        merged_body.extend(body)
        merged_body.append("")

    header = (
        f"# ==========================================================\n"
        f"# AUTO GENERATED SUBMISSION\n"
        f"# Generated : {datetime.now(UTC).isoformat()}\n"
        f"# Source    : {AGENT_DIR}\n"
        f"# Do not edit manually.\n"
        f"# ==========================================================\n\n"
    )

    content = (
        header
        + "\n".join(sorted(all_imports))
        + "\n\n"
        + "\n".join(merged_body)
    )
    OUTPUT_PY.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PY.write_text(content, encoding="utf-8")

    # Validate syntax
    compile(content, OUTPUT_PY.name, "exec")

    print(f"  Output Script : {OUTPUT_PY}")
    print(f"  Modules Total : {len(modules)}")
    print(f"  Total Imports : {len(all_imports)}")
    print(f"  Lines of Code : {len(content.splitlines()):,}")
    print(f"  File Size     : {OUTPUT_PY.stat().st_size:,} bytes")


def package_submission() -> None:
    """Package submission.py (renamed to main.py) into submission.tar.gz."""
    OUTPUT_TAR.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
        tar.add(OUTPUT_PY, arcname="main.py")

    print(f"  Output Archive : {OUTPUT_TAR}")
    print(f"  Archive Size   : {OUTPUT_TAR.stat().st_size:,} bytes")


if __name__ == "__main__":
    build_submission(DEFAULT_MODULES)
    package_submission()
