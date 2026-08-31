import base64
import json
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "src" / "v2" / "trace.json"
OUT_PATH = ROOT / ".out" / "routes_encoded.py"


def _load_routes() -> dict[str, Any] | dict[int, Any]:
    if not ROUTES_PATH.exists():
        raise FileNotFoundError(f"Routes file not found at {ROUTES_PATH}")

    with open(ROUTES_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict):
        if all(k.isdigit() for k in raw.keys()):
            return {int(k): v for k, v in raw.items()}
        return raw
    return raw


def encode_routes() -> str:
    routes = _load_routes()
    json_bytes = json.dumps(routes, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(json_bytes, level=9)
    encoded = base64.b85encode(compressed).decode("ascii")

    code = f'''import base64
import json
import zlib

_MOVESETS = json.loads(
    zlib.decompress(
        base64.b85decode(
            "{encoded}"
        )
    ).decode("utf-8")
)
'''
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(code)

    return encoded


if __name__ == "__main__":
    encoded_str = encode_routes()
    routes_data = _load_routes()
    print(f"Encoded {len(routes_data)} paths into {OUT_PATH}")
    print(f"Base85 length: {len(encoded_str):,} chars")
