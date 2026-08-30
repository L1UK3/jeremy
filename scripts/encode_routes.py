import base64
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "src" / "routes.json"
OUT_PATH = ROOT / ".out" / "routes_encoded.py"


def _load_routes() -> dict[int, dict]:
    if not ROUTES_PATH.exists():
        raise FileNotFoundError(f"Routes file not found at {ROUTES_PATH}")

    with open(ROUTES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def encode_routes() -> str:
    routes = _load_routes()
    json_bytes = json.dumps(routes, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(json_bytes, level=9)
    encoded = base64.b85encode(compressed).decode("ascii")

    code = f'''import base64
import json
import zlib

_ROUTES: dict[int, dict] = {{
    int(k): v
    for k, v in json.loads(
        zlib.decompress(
            base64.b85decode(
                "{encoded}"
            )
        ).decode("utf-8")
    ).items()
}}
'''
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(code)

    return encoded


if __name__ == "__main__":
    encoded_str = encode_routes()
    print(f"Encoded {len(_load_routes())} routes into {OUT_PATH}")
    print(f"Base85 length: {len(encoded_str)} chars")
