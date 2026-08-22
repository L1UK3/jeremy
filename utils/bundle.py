"""
Bundle agent source files into submission.tar.gz.
"""

import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
OUTPUT_TAR = ROOT / "submission.tar.gz"

FILES = [
    "agent",
    "environment",
    "main.py",
]


def build_submission() -> None:
    """Build submission.tar.gz."""
    OUTPUT_TAR.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
        for file in FILES:
            path = SRC_DIR / file
            if path.exists():
                tar.add(
                    path,
                    arcname=file,
                    filter=lambda ti: None if "__pycache__" in ti.name else ti,
                )

    print(f"  Output Archive : {OUTPUT_TAR}")
    print(f"  Created        : {OUTPUT_TAR.stat().st_mtime}")
    print(f"  Archive Size   : {OUTPUT_TAR.stat().st_size:,} bytes")


if __name__ == "__main__":
    build_submission()
