"""
Unpack and integrate the encoded model payload for the Kaggriculture agent.

Provides tools to decode, verify checksums, compile, execute in-memory,
and package deterministic submission archives.
"""

import base64
import gzip
import hashlib
import io
import tarfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Support imports whether running from src/ or project root
try:
    from package.payload import AGENT_B64
except ImportError:
    try:
        from src.package.payload import AGENT_B64
    except ImportError:
        from .payload import AGENT_B64

# Expected SHA256 checksums
EXPECTED_MAIN_SHA = "d39dba50793d9777c990347443bf0c481c78adaea86055f6f6b0600dcfcd9f2e"
EXPECTED_ARCHIVE_SHA = "a5f0e99ef483408fb524e7ae7c9c2df0c71fd849a30e4fcc54ef50fc166e3ee8"

_CACHED_AGENT: Callable[[dict], dict] | None = None


def get_payload_bytes(verify_checksum: bool = True) -> bytes:
    """
    Decode the base64-encoded agent payload and optionally verify its SHA256 checksum.
    """
    payload = base64.b64decode(AGENT_B64)
    if verify_checksum:
        actual_sha = hashlib.sha256(payload).hexdigest()
        if actual_sha != EXPECTED_MAIN_SHA:
            raise ValueError(
                f"Payload checksum mismatch: expected {EXPECTED_MAIN_SHA}, got {actual_sha}"
            )
    return payload


def get_payload_code(verify_checksum: bool = True) -> str:
    """Return decoded agent Python source code as string."""
    return get_payload_bytes(verify_checksum=verify_checksum).decode("utf-8")


def load_agent_from_payload(verify_checksum: bool = True) -> Callable[[dict], dict]:
    """
    Decode, compile, and execute the encoded model in an isolated namespace,
    returning the callable agent function. Cached after first load.
    """
    global _CACHED_AGENT
    if _CACHED_AGENT is not None:
        return _CACHED_AGENT

    code_bytes = get_payload_bytes(verify_checksum=verify_checksum)
    compiled_code = compile(code_bytes, "<encoded_model_payload>", "exec")

    scope: dict[str, Any] = {}
    exec(compiled_code, scope)

    if "agent" not in scope or not callable(scope["agent"]):
        raise AttributeError("Decoded payload does not contain a callable 'agent' entry point.")

    _CACHED_AGENT = scope["agent"]
    return _CACHED_AGENT


def unpack_to_file(
    target_path: Path | str = "submission.py",
    verify_checksum: bool = True,
) -> Path:
    """
    Decode and write the agent payload to a target .py file, verifying syntax and checksum.
    """
    target = Path(target_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = get_payload_bytes(verify_checksum=verify_checksum)
    compile(payload, str(target), "exec")

    target.write_bytes(payload)
    print(f"Unpacked payload to: {target}")
    print(f"  SHA256: {hashlib.sha256(payload).hexdigest()}")
    print(f"  Size  : {len(payload):,} bytes")
    return target


def create_deterministic_archive(
    output_tar: Path | str = "submission.tar.gz",
    verify_checksum: bool = True,
) -> Path:
    """
    Build a deterministic gzip tar archive with fixed metadata for a reproducible hash.
    """
    output_tar = Path(output_tar).resolve()
    output_tar.parent.mkdir(parents=True, exist_ok=True)

    payload = get_payload_bytes(verify_checksum=verify_checksum)

    with output_tar.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive_out:
                info = tarfile.TarInfo("main.py")
                info.size = len(payload)
                info.mode = 0o644
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                archive_out.addfile(info, io.BytesIO(payload))

    archive_bytes = output_tar.read_bytes()
    actual_sha = hashlib.sha256(archive_bytes).hexdigest()

    if verify_checksum and actual_sha != EXPECTED_ARCHIVE_SHA:
        raise ValueError(
            f"Archive checksum mismatch: expected {EXPECTED_ARCHIVE_SHA}, got {actual_sha}"
        )

    print(f"Created deterministic archive: {output_tar}")
    print(f"  main.py SHA256 : {hashlib.sha256(payload).hexdigest()}")
    print(f"  archive SHA256 : {actual_sha}")
    print(f"  Archive Size   : {len(archive_bytes):,} bytes")
    return output_tar


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Unpack and verify encoded model payload")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("submission.py"),
        help="Target output script path (default: submission.py)",
    )
    parser.add_argument(
        "--tar",
        type=Path,
        default=None,
        help="Also build deterministic submission.tar.gz archive at specified path",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the unpacked agent against starter in kaggle-environments",
    )

    args = parser.parse_args()

    _unpacked_path = unpack_to_file(target_path=args.output)

    if args.tar:
        create_deterministic_archive(output_tar=args.tar)

    if args.test:
        from kaggle_environments import make

        agent_fn = load_agent_from_payload()
        print("\nRunning validation test against 'starter'...")
        env = make("kaggriculture")
        env.run([agent_fn, "starter"])
        final = env.steps[-1]
        print(f"Result: Challenger={final[0].reward} ({final[0].status}) vs Starter={final[1].reward} ({final[1].status})")


if __name__ == "__main__":
    main()
