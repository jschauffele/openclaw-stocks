from pathlib import Path
import sys

try:
    from event_reader import read_event_log
except ImportError:
    from event_reader import read_run_events as read_event_log

from run_reconstructor import reconstruct_run


def main() -> None:
    try:
        log_dir = Path("./logs")
        log_files = [path for path in log_dir.glob("*.jsonl") if path.is_file()]

        if not log_files:
            raise FileNotFoundError("No log files found in ./logs")

        latest_log = max(log_files, key=lambda path: path.stat().st_mtime)

        events = read_event_log(str(latest_log))
        summary = reconstruct_run(events)
        event_types = [event.get("event_type") for event in events]

        print(f"EVENT COUNT: {len(events)}")
        print(f"EVENT TYPES: {event_types}")
        print(f"SUMMARY: {summary}")
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
