from typing import Any


def get_last_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not events:
        return None
    return events[-1]


def get_event_by_type(
    events: list[dict[str, Any]],
    event_type: str,
) -> dict[str, Any] | None:
    for event in events:
        if event.get("event_type") == event_type:
            return event
    return None


def get_all_events_by_type(
    events: list[dict[str, Any]],
    event_type: str,
) -> list[dict[str, Any]]:
    return [event for event in events if event.get("event_type") == event_type]
