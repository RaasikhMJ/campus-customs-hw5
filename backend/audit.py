"""Append-only desk log. output/audit_trail.json grows. It is never replaced by a shorter file."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT_PATH = HERE.parent / "output" / "audit_trail.json"
_LOCK = threading.Lock()
_LIMIT = 400


def _clip(text: str) -> str:
    text = " ".join((text or "").split())
    if len(text) <= _LIMIT:
        return text
    return text[: _LIMIT - 1] + "…"


def _short(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return _clip(json.dumps(value, default=str))
    return _clip(str(value))


def _load(now: str) -> list:
    if not AUDIT_PATH.is_file() or AUDIT_PATH.stat().st_size == 0:
        return []
    raw = AUDIT_PATH.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return parsed
    return [
        {
            "time": now,
            "agent": "audit",
            "step": "kept_previous_file",
            "detail": _clip(raw),
        }
    ]


def append_step(step: dict) -> None:
    """Add one loop step to the end of the trail. Earlier steps stay."""

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    row = dict(step)
    row.setdefault("time", now)
    for key in ("detail", "args", "result"):
        if key in row and not isinstance(row[key], str):
            row[key] = _short(row[key])
        elif key in row:
            row[key] = _clip(row[key])
    with _LOCK:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = _load(now) + [row]
        temporary = AUDIT_PATH.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(AUDIT_PATH)


def tool_returns(result) -> list[dict]:
    """Tool name, arguments, and return value from one finished agent loop."""

    args_by_id: dict[str, str] = {}
    rows: list[dict] = []
    for message in result.new_messages():
        for part in getattr(message, "parts", ()):
            kind = getattr(part, "part_kind", "")
            name = getattr(part, "tool_name", "") or ""
            call_id = getattr(part, "tool_call_id", "") or name
            if kind == "tool-call":
                args = getattr(part, "args", "")
                if hasattr(part, "args_as_dict"):
                    try:
                        args = part.args_as_dict()
                    except Exception:
                        args = getattr(part, "args", "")
                args_by_id[call_id] = _short(args)
            elif kind == "tool-return":
                rows.append(
                    {
                        "tool": name,
                        "args": args_by_id.get(call_id, ""),
                        "result": _short(getattr(part, "content", None)),
                    }
                )
    return rows
