import os
import tarfile

utils_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(utils_dir)
root_dir = os.path.dirname(src_dir)


def build_submission() -> None:
    """Builds a submission tarball containing the necessary files.
    The tarball includes the following items:
    - main.py

    Output: submission.tar.gz - hidden files and __pycache__ directories are excluded."""
    out_tar = os.path.join(root_dir, "submission.tar.gz")

    items = ["main.py"]

    def tar_filter(t: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if (
            "__pycache__" in t.name
            or t.name.endswith(".pyc")
            or os.path.basename(t.name).startswith(".")
        ):
            return None
        return t

    with tarfile.open(out_tar, "w:gz") as tar:
        for item in items:
            item_path = os.path.join(src_dir, item)
            if os.path.exists(item_path):
                tar.add(
                    item_path,
                    arcname=item,
                    filter=tar_filter,
                )

    print(f"Created {out_tar}")


if __name__ == "__main__":
    build_submission()
