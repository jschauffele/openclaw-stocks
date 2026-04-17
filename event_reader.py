import json
from typing import Any


def read_run_events(file_path: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    break

                if isinstance(event, dict):
                    events.append(event)
                else:
                    break
    except (OSError, UnicodeDecodeError):
        return []

    return events


def read_event_log(file_path: str) -> list[dict[str, Any]]:
    return read_run_events(file_path)
