import json
import os
import logging
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso8601(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


def write_json_atomic(path: str, data: dict) -> None:
    temp_file = f"{path}.tmp"
    with open(temp_file, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(temp_file, path)


def setup_logging(log_file: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
