import json
from pathlib import Path
from typing import Any

TRACE_FILE = Path(__file__).resolve().parent / "trace.json"
TRACE: dict[str, list[dict[str, Any]]] = (
    json.loads(TRACE_FILE.read_text(encoding="utf-8"))
    if TRACE_FILE.is_file()
    else {}
)
