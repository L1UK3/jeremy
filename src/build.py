"""
Build script entrypoint. Bundles agent modules into a standalone submission.py.

Usage:
    python src/build.py
    python src/build.py --test
    python src/build.py -o ./submission.py
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from package.bundle import main  # noqa: E402

if __name__ == "__main__":
    main()
