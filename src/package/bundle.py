"""
Bundle agent source files or encoded model payload into submission.py and package submission.tar.gz.
"""

import argparse
import os
import re
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

# Ensure src/ is on sys.path
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from package.unpack import (  # noqa: E402
    create_deterministic_archive,
    unpack_to_file,
)

PROJECT_ROOT = src_dir.parent
DEFAULT_SRC_DIR = src_dir / "agent"
DEFAULT_OUTPUT_PY = PROJECT_ROOT / "submission.py"
DEFAULT_OUTPUT_TAR = PROJECT_ROOT / "submission.tar.gz"

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


def create_tar_from_file(
    source_py: Path,
    output_tar: Path = DEFAULT_OUTPUT_TAR,
) -> Path:
    """Package a Python script as main.py into a submission.tar.gz archive."""
    output_tar = Path(output_tar).resolve()
    output_tar.parent.mkdir(parents=True, exist_ok=True)

    def tar_filter(t: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if (
            "__pycache__" in t.name
            or t.name.endswith(".pyc")
            or os.path.basename(t.name).startswith(".")
        ):
            return None
        return t

    with tarfile.open(output_tar, "w:gz") as tar:
        tar.add(str(source_py), arcname="main.py", filter=tar_filter)

    print(f"\n[+] Created archive : {output_tar}")
    print(f"    Bundled Source  : {source_py} -> main.py")
    print(f"    Archive Size    : {output_tar.stat().st_size:,} bytes")
    return output_tar


def build_submission(
    src_dir: Path | str = DEFAULT_SRC_DIR,
    output_path: Path | str | None = None,
    output_tar: Path | str | None = None,
    modules: list[str] = DEFAULT_MODULES,
    strategy: str = "model",
    include_banners: bool = True,
    package_tar: bool = True,
) -> tuple[Path, Path | None]:
    """
    Build standalone submission.py and package submission.tar.gz archive.

    Strategies:
      - 'model' / 'payload': Unpacks the high-performing encoded consensus model payload.
      - 'modular': Bundles modular source files from src/agent/.

    Returns:
      (submission_py_path, submission_tar_path)
    """
    if output_path is None:
        output_py = DEFAULT_OUTPUT_PY
    else:
        output_py = Path(output_path).resolve()

    if output_tar is None:
        target_tar = DEFAULT_OUTPUT_TAR
    else:
        target_tar = Path(output_tar).resolve()

    print("=" * 60)
    print(f"BUILDING SUBMISSION (Strategy: {strategy})")
    print(f"  Target Script  : {output_py}")
    if package_tar:
        print(f"  Target Archive : {target_tar}")
    print("=" * 60)

    if strategy in {"model", "payload"}:
        unpack_to_file(target_path=output_py, verify_checksum=True)

        tar_path = None
        if package_tar:
            tar_path = create_deterministic_archive(
                output_tar=target_tar, verify_checksum=True
            )
        return output_py, tar_path

    # Modular build
    src_dir = Path(src_dir).resolve()
    internal_modules = {Path(m).stem for m in modules}

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
            merged_body.append(
                f"\n# ===================== {module} ====================="
            )
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

    output_py.parent.mkdir(parents=True, exist_ok=True)

    with output_py.open("w", encoding="utf-8") as f:
        f.write(header)
        for imp in sorted(all_imports):
            f.write(imp + "\n")
        f.write("\n")
        for line in merged_body:
            f.write(line + "\n")

    # Verify syntax compilation
    output_code = output_py.read_text(encoding="utf-8")
    compile(output_code, output_py.name, "exec")

    line_count = len(output_code.splitlines())
    file_size = output_py.stat().st_size

    print("-" * 60)
    print("SCRIPT BUILD SUCCESSFUL")
    print(f"  Output Script : {output_py}")
    print(f"  Modules Total : {len(modules)}")
    print(f"  Total Imports : {len(all_imports)}")
    print(f"  Lines of Code : {line_count:,}")
    print(f"  File Size     : {file_size:,} bytes")
    print("-" * 60)

    tar_path = None
    if package_tar:
        tar_path = create_tar_from_file(
            source_py=output_py, output_tar=target_tar
        )

    return output_py, tar_path


def test_submission(
    submission_path: Path, opponent: str = "starter", debug: bool = True
) -> None:
    """Run a quick validation match against an opponent using kaggle_environments."""
    print(f"\nRunning test simulation against '{opponent}'...")
    try:
        from kaggle_environments import make
    except ImportError:
        print(
            "Warning: kaggle_environments is not installed in the active environment. Skipping test."
        )
        return

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
    parser = argparse.ArgumentParser(
        description="Bundle submission.py and package submission.tar.gz"
    )
    parser.add_argument(
        "--strategy",
        "-s",
        type=str,
        choices=["model", "modular", "payload"],
        default="model",
        help="Build strategy: 'model' (unpacks encoded consensus payload) or 'modular' (bundles src/agent/ files)",
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=DEFAULT_SRC_DIR,
        help=f"Source directory for modular build (default: {DEFAULT_SRC_DIR})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PY,
        help=f"Output submission.py path (default: {DEFAULT_OUTPUT_PY})",
    )
    parser.add_argument(
        "-t",
        "--tar",
        type=Path,
        default=DEFAULT_OUTPUT_TAR,
        help=f"Output submission.tar.gz path (default: {DEFAULT_OUTPUT_TAR})",
    )
    parser.add_argument(
        "--no-tar",
        action="store_true",
        help="Skip creating the submission.tar.gz archive",
    )
    parser.add_argument(
        "--no-banners",
        action="store_true",
        help="Do not include module section header comments in output (modular mode only)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test game with kaggle_environments after building",
    )

    args = parser.parse_args()

    out_py, _out_tar = build_submission(
        src_dir=args.src_dir,
        output_path=args.output,
        output_tar=args.tar,
        strategy=args.strategy,
        include_banners=not args.no_banners,
        package_tar=not args.no_tar,
    )

    if args.test:
        test_submission(out_py)


if __name__ == "__main__":
    main()
