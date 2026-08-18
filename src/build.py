"""
Bundle agent source files into submission.tar.gz.
"""

import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "src" / "agent"
OUTPUT_TAR = ROOT / "submission.tar.gz"


def build_submission() -> None:
    """Build submission.tar.gz."""
    OUTPUT_TAR.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
        tar.add(AGENT_DIR, arcname="agent   ")

    print(f"  Output Archive : {OUTPUT_TAR}")
    print(f"  Created        : {OUTPUT_TAR.stat().st_mtime}")
    print(f"  Archive Size   : {OUTPUT_TAR.stat().st_size:,} bytes")


if __name__ == "__main__":
    build_submission()
