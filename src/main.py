
import base64
import gzip
import hashlib
import io
import tarfile
from pathlib import Path

from src.model import AGENT_B64

# Expected checksums for the decoded agent script and the final packaged archive
EXPECTED_MAIN_SHA = "d39dba50793d9777c990347443bf0c481c78adaea86055f6f6b0600dcfcd9f2e"
EXPECTED_ARCHIVE_SHA = "a5f0e99ef483408fb524e7ae7c9c2df0c71fd849a30e4fcc54ef50fc166e3ee8"

# Decode the agent payload, verify it compiles and matches the expected hash, then write it to disk
payload = base64.b64decode(AGENT_B64)
compile(payload, "main.py", "exec")
assert hashlib.sha256(payload).hexdigest() == EXPECTED_MAIN_SHA
Path("main.py").write_bytes(payload)

# Pack main.py into a deterministic gzip tar archive with fixed metadata for a reproducible hash
with Path("submission.tar.gz").open("wb") as raw:
    with gzip.GzipFile(filename = "", mode = "wb", fileobj = raw, mtime = 0) as compressed:
        with tarfile.open(fileobj = compressed, mode = "w") as archive_out:
            info = tarfile.TarInfo("main.py")
            info.size = len(payload)
            info.mode = 0o644
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive_out.addfile(info, io.BytesIO(payload))

# Verify the archive hash and that it extracts back to the exact same payload
archive_bytes = Path("submission.tar.gz").read_bytes()
assert hashlib.sha256(archive_bytes).hexdigest() == EXPECTED_ARCHIVE_SHA
with tarfile.open("submission.tar.gz", "r:gz") as archive_in:
    assert archive_in.getnames() == ["main.py"]
    assert archive_in.extractfile("main.py").read() == payload

print("main.py:", EXPECTED_MAIN_SHA)
print("submission.tar.gz:", EXPECTED_ARCHIVE_SHA)
