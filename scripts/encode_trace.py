import base64
import json
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "src" / "trace.json"
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

TRACE = json.loads(
    zlib.decompress(
        base64.b85decode(
            "{encoded}"
        )
    ).decode("utf-8")
)
'''
    return code


def decode_routes(encoded_str: str) -> dict[str, Any] | dict[int, Any]:
    try:
        compressed = base64.b85decode(encoded_str)
    except Exception:
        compressed = base64.b64decode(encoded_str)
    json_bytes = zlib.decompress(compressed)
    return json.loads(json_bytes.decode("utf-8"))


def write_encoded_routes_to_file(
    content: Any, out_path: Path | str = OUT_PATH
) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        if isinstance(content, dict | list):
            json.dump(content, f, indent=2)
        else:
            f.write(str(content))
    print(f"Wrote to {out_path}")


def main():
    encoded_str = encode_routes()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(encoded_str)
    print(f"Encoded {len(encoded_str)} paths into {OUT_PATH}")
    print(f"Base85 length: {len(encoded_str):,} chars")


if __name__ == "__main__":
    main()
