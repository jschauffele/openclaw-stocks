from typing import Any

from simple_query import get_event_by_type, get_last_event


def _payload(event: dict[str, Any] | None) -> dict[str, Any]:
    if not event:
        return {}
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _first_present(payload: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def reconstruct_run(events: list[dict[str, Any]]) -> dict[str, Any]:
    run_started = get_event_by_type(events, "run_started")
    decision_made = get_event_by_type(events, "decision_made")
    order_submitted = get_event_by_type(events, "order_submitted")
    run_completed = get_event_by_type(events, "run_completed")
    last_event = get_last_event(events)

    run_started_payload = _payload(run_started)
    decision_payload = _payload(decision_made)
    submitted_payload = _payload(order_submitted)
    completed_payload = _payload(run_completed)
    last_payload = _payload(last_event)

    run_id = None
    if run_started and run_started.get("run_id") is not None:
        run_id = run_started.get("run_id")
    elif last_event and last_event.get("run_id") is not None:
        run_id = last_event.get("run_id")

    final_event_type = None
    if last_event:
        final_event_type = last_event.get("event_type")

    final_decision = _first_present(
        decision_payload,
        ["final_decision", "decision", "action", "final_action"],
    )

    symbol = (
        _first_present(submitted_payload, ["symbol"])
        or _first_present(decision_payload, ["symbol"])
        or _first_present(run_started_payload, ["symbol"])
    )

    qty = (
        _first_present(submitted_payload, ["qty", "quantity"])
        or _first_present(decision_payload, ["qty", "quantity"])
    )

    order_submitted_flag = order_submitted is not None

    error = (
        _first_present(completed_payload, ["error", "error_reason"])
        or _first_present(last_payload, ["error", "error_reason"])
    )

    if run_completed is not None:
        run_status = "completed"
    elif error is not None:
        run_status = "error"
    elif last_event is not None:
        run_status = "interrupted"
    else:
        run_status = "missing"

    if final_decision is None and order_submitted_flag:
        final_decision = "submit_order"

    return {
        "run_id": run_id,
        "run_status": run_status,
        "final_event_type": final_event_type,
        "final_decision": final_decision,
        "symbol": symbol,
        "qty": qty,
        "order_submitted": order_submitted_flag,
        "error": error,
    }
