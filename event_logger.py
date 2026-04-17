import json
import logging
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = 1
DEFAULT_EVENTS_BASE_DIR = "./logs"

_CURRENT_RUN_ID: Optional[str] = None
_CURRENT_RUN_FILE: Optional[Path] = None
_EVENT_COUNTER = 0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso_z() -> str:
    return _utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _short_random_id() -> str:
    return secrets.token_hex(3)


def generate_run_id() -> str:
    return f"run_{_utc_now_iso_z()}_{_short_random_id()}"


def _run_file_path(base_dir: str, run_id: str) -> Path:
    return Path(base_dir) / f"{run_id}.jsonl"


def initialize_event_logger(
    run_id: str,
    base_dir: str = DEFAULT_EVENTS_BASE_DIR,
) -> Optional[str]:
    global _CURRENT_RUN_ID, _CURRENT_RUN_FILE, _EVENT_COUNTER

    run_file = _run_file_path(base_dir, run_id)

    try:
        run_file.parent.mkdir(parents=True, exist_ok=True)
        run_file.touch(exist_ok=True)
    except OSError:
        logging.getLogger(__name__).exception("Failed to initialize event log")
        return None

    _CURRENT_RUN_ID = run_id
    _CURRENT_RUN_FILE = run_file
    _EVENT_COUNTER = 0
    return run_id


def current_run_id() -> Optional[str]:
    return _CURRENT_RUN_ID


def log_event(
    event_type: str,
    stage: str,
    status: str,
    payload: dict,
) -> None:
    global _EVENT_COUNTER

    if _CURRENT_RUN_ID is None or _CURRENT_RUN_FILE is None:
        return

    _EVENT_COUNTER += 1
    event = {
        "schema_version": 1,
        "run_id": _CURRENT_RUN_ID,
        "event_id": f"evt_{_EVENT_COUNTER:04d}",
        "event_type": event_type,
        "stage": stage,
        "timestamp_utc": _utc_now_iso_z(),
        "status": status,
        "payload": payload if isinstance(payload, dict) else {},
    }

    try:
        with open(_CURRENT_RUN_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":"), sort_keys=False))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        logging.getLogger(__name__).exception("Failed to append event log record")
