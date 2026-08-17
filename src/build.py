"""
Build Kaggle submission.py from modular source files.

Combines individual module files into a single standalone submission script,
deduplicating external/standard library imports and removing intra-project
relative imports. Also validates compilation syntax and supports optional
test execution.

Usage:
    python build.py
    python build.py --output ../submission.py
    python build.py --test
"""

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_SRC_DIR = Path(__file__).resolve().parent

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


def clean_source(text: str, internal_modules: set[str]) -> tuple[list[str], list[str]]:
    """
    Extract external imports and cleaned body lines from a source module.

    - Internal module imports (e.g. `from state import ...`) are stripped.
    - Standard/third-party imports are extracted and deduplicated.
    - Consecutive blank lines and trailing line spaces are collapsed.
    """
    imports: list[str] = []
    body: list[str] = []
    blank = False

    for line in text.splitlines():
        s = line.strip()

        if s.startswith("from "):
            m = re.match(r"from\s+([A-Za-z0-9_]+)\s+import", s)
            if m and m.group(1) in internal_modules:
                continue
            if line not in imports:
                imports.append(line)
            continue

        if s.startswith("import "):
            m = re.match(r"import\s+([A-Za-z0-9_]+)", s)
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


def build_submission(
    src_dir: Path = DEFAULT_SRC_DIR,
    output_path: Path | None = None,
    modules: list[str] = MODULES,
    include_banners: bool = True,
) -> Path:
    """Combine modular Python files into a single standalone submission script."""
    if output_path is None:
        output_path = src_dir / "submission.py"
    else:
        output_path = Path(output_path)

    internal_modules = {Path(m).stem for m in modules}

    print("=" * 60)
    print("Building submission.py")
    print(f"Source Directory : {src_dir}")
    print(f"Target Output    : {output_path}")
    print("=" * 60)

    # Verify all module files exist before building
    for module in modules:
        path = src_dir / module
        if not path.exists():
            raise FileNotFoundError(f"Required module not found: {path}")

    all_imports: list[str] = []
    seen_imports: set[str] = set()
    merged_body: list[str] = []

    for module in modules:
        path = src_dir / module
        print(f"  [+] Bundling: {module}")

        text = path.read_text(encoding="utf-8")
        imports, body = clean_source(text, internal_modules)

        for imp in imports:
            if imp not in seen_imports:
                seen_imports.add(imp)
                all_imports.append(imp)

        if include_banners:
            merged_body.append(f"\n# ===================== {module} =====================")
        merged_body.extend(body)
        merged_body.append("")

    while merged_body and merged_body[-1] == "":
        merged_body.pop()

    now_utc = datetime.now(UTC).isoformat()
    header = f"""# ==========================================================
# AUTO GENERATED SUBMISSION
# Generated : {now_utc}
# Source    : {src_dir}
# Do not edit manually.
# ==========================================================

"""

    # Ensure output parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(header)
        for imp in sorted(all_imports):
            f.write(imp + "\n")
        f.write("\n")
        for line in merged_body:
            f.write(line + "\n")

    # Verify syntax compilation
    output_code = output_path.read_text(encoding="utf-8")
    compile(output_code, output_path.name, "exec")

    line_count = len(output_code.splitlines())
    file_size = output_path.stat().st_size

    print("=" * 60)
    print("BUILD SUCCESSFUL")
    print("=" * 60)
    print(f"Output File   : {output_path.resolve()}")
    print(f"Modules Total : {len(modules)}")
    print(f"Total Imports : {len(all_imports)}")
    print(f"Lines of Code : {line_count:,}")
    print(f"File Size     : {file_size:,} bytes")
    print("=" * 60)

    return output_path


def test_submission(submission_path: Path, opponent: str = "random", debug: bool = True) -> None:
    """Run a quick validation match against an opponent using kaggle_environments."""
    print(f"\nRunning test simulation against '{opponent}'...")
    try:
        from kaggle_environments import make
    except ImportError:
        print("Warning: kaggle_environments is not installed in the active environment. Skipping test.")
        return

    # Execute submission code in an isolated namespace to extract agent function
    code = submission_path.read_text(encoding="utf-8")
    namespace = {}
    exec(code, namespace)

    if "agent" not in namespace:
        raise ValueError(f"No 'agent' function found in {submission_path}")

    env = make("kaggriculture", debug=debug)
    env.run([namespace["agent"], opponent])

    final = env.steps[-1]
    print("Simulation Finished.")
    for i, s in enumerate(final):
        print(f"  Player {i}: status={s.status}, reward={s.reward}")


def main():
    parser = argparse.ArgumentParser(description="Build and validate Kaggle submission.py")
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=DEFAULT_SRC_DIR,
        help="Source directory containing module files (default: src directory of this script)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output submission.py path (default: <src-dir>/submission.py)",
    )
    parser.add_argument(
        "--no-banners",
        action="store_true",
        help="Do not include module section header comments in output",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test game with kaggle_environments after building",
    )

    args = parser.parse_args()

    out = build_submission(
        src_dir=args.src_dir,
        output_path=args.output,
        include_banners=not args.no_banners,
    )

    if args.test:
        test_submission(out)


if __name__ == "__main__":
    main()
