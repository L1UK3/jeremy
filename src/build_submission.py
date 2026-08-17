import os
from pathlib import Path
import tarfile

src_dir = Path(__file__).resolve().parent
root_dir = src_dir.parent


def build_submission() -> None:
    """Builds a submission tarball containing the necessary files.
    The tarball includes the following items:
    - main.py

    Output: submission.tar.gz - hidden files and __pycache__ directories are excluded."""
    out_tar = root_dir / "submission.tar.gz"

    # Locate the bundled submission file (in src/ or root)
    submission_src = src_dir / "submission.py"
    if not submission_src.exists():
        submission_src = root_dir / "submission.py"

    if not submission_src.exists():
        raise FileNotFoundError(
            f"Could not find submission.py in {src_dir} or {root_dir}. "
            "Please run 'python src/build.py' first."
        )

    def tar_filter(t: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if (
            "__pycache__" in t.name
            or t.name.endswith(".pyc")
            or os.path.basename(t.name).startswith(".")
        ):
            return None
        return t

    with tarfile.open(out_tar, "w:gz") as tar:
        # Add as main.py (Kaggle requirement for submission archives)
        tar.add(
            str(submission_src),
            arcname="main.py",
            filter=tar_filter,
        )

    print(f"Created {out_tar}")


if __name__ == "__main__":
    build_submission()
