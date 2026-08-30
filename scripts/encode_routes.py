import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "src" / "routes.json"


def _load_routes() -> dict[int, dict]:
    if not ROUTES_PATH.exists():
        raise FileNotFoundError(f"Routes file not found at {ROUTES_PATH}")

    with open(ROUTES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


ROUTES: dict[int, dict] = _load_routes()

with open(ROOT / ".out" / "routes_encoded.py", "w", encoding="utf-8") as f:
    f.write(
        f"""import base64
import json
import zlib

_ACTIONS = json.loads(zlib.decompress(base64.b85decode("{base64.b85encode(json.dumps(ROUTES).encode('utf-8')).decode('utf-8')}")).decode('utf-8'))
"""
    )
