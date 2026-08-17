"""
Package submission script and bundle into submission.tar.gz archive.
"""

import argparse
import os
import sys
import tarfile
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
DEFAULT_OUT_PY = PROJECT_ROOT / "submission.py"
DEFAULT_OUT_TAR = PROJECT_ROOT / "submission.tar.gz"


def create_submission_archive(
    submission_path: Path | str | None = None,
    output_tar: Path | str | None = None,
    use_payload: bool = True,
    strategy: str = "model",
) -> tuple[Path, Path]:
    """
    Builds both submission.py and submission.tar.gz containing main.py for Kaggle competition upload.

    Returns:
      (submission_py_path, submission_tar_path)
    """
    if output_tar is None:
        out_tar = DEFAULT_OUT_TAR
    else:
        out_tar = Path(output_tar).resolve()

    if submission_path is None:
        out_py = DEFAULT_OUT_PY
    else:
        out_py = Path(submission_path).resolve()

    if use_payload or strategy in {"model", "payload"}:
        print("=" * 60)
        print("PACKAGING SUBMISSION FROM MODEL PAYLOAD")
        print("=" * 60)
        unpack_to_file(target_path=out_py, verify_checksum=True)
        tar_path = create_deterministic_archive(output_tar=out_tar, verify_checksum=True)
        return out_py, tar_path

    # Modular packaging
    if not out_py.exists():
        from package.bundle import build_submission

        print(f"Submission script not found at {out_py}, building from modular source...")
        build_submission(output_path=out_py, strategy=strategy, package_tar=False)

    def tar_filter(t: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if (
            "__pycache__" in t.name
            or t.name.endswith(".pyc")
            or os.path.basename(t.name).startswith(".")
        ):
            return None
        return t

    out_tar.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(out_tar, "w:gz") as tar:
        tar.add(
            str(out_py),
            arcname="main.py",
            filter=tar_filter,
        )

    print("=" * 60)
    print("PACKAGING SUCCESSFUL")
    print("=" * 60)
    print(f"  Output Script  : {out_py}")
    print(f"  Output Archive : {out_tar}")
    print(f"  Archive Size   : {out_tar.stat().st_size:,} bytes")
    print("=" * 60)
    return out_py, out_tar


def main():
    parser = argparse.ArgumentParser(
        description="Package submission.py and create submission.tar.gz"
    )
    parser.add_argument(
        "-s",
        "--source",
        type=Path,
        default=DEFAULT_OUT_PY,
        help=f"Path to submission.py (default: {DEFAULT_OUT_PY})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUT_TAR,
        help=f"Output tarball path (default: {DEFAULT_OUT_TAR})",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["model", "modular", "payload"],
        default="model",
        help="Strategy to generate submission.py if missing or building (default: model)",
    )
    parser.add_argument(
        "--modular",
        action="store_true",
        help="Use modular agent source files rather than model payload",
    )

    args = parser.parse_args()
    strategy = "modular" if args.modular else args.strategy

    create_submission_archive(
        submission_path=args.source,
        output_tar=args.output,
        use_payload=not args.modular and strategy in {"model", "payload"},
        strategy=strategy,
    )


if __name__ == "__main__":
    main()
