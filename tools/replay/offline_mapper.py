"""In-memory offline mapper for replay package envelopes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from tools.replay.package_schema import (
    AUTHORITY_BOUNDARY,
    ENVELOPE_SECTIONS,
    OUT_OF_SCOPE,
    REPLAY_PACKAGE_SCHEMA_VERSION,
    SCHEMA_STATUS,
    SECTION_STATUS_ABSENT,
    SECTION_STATUS_PRESENT,
    absent_section,
    present_section,
)


def build_replay_package(
    *,
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None = None,
    observations: list[dict[str, Any]] | None = None,
    order_state: dict[str, Any] | None = None,
    runtime_visibility: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an in-memory replay package envelope from already-loaded inputs."""

    copied_events = _copy_events(events)
    copied_report = _copy_optional_dict(run_report)
    copied_observations = _copy_optional_events(observations)
    copied_order_state = _copy_optional_dict(order_state)
    copied_runtime_visibility = _copy_optional_dict(runtime_visibility)

    section_statuses = _section_statuses(
        events=copied_events,
        run_report=copied_report,
        observations=copied_observations,
        order_state=copied_order_state,
        runtime_visibility=copied_runtime_visibility,
    )
    run_id_alignment = _run_id_alignment(
        events=copied_events,
        run_report=copied_report,
        observations=copied_observations,
        order_state=copied_order_state,
        runtime_visibility=copied_runtime_visibility,
    )

    package = {
        "package_identity": _package_identity(copied_events, copied_report),
        "schema": {
            "replay_package_schema_version": REPLAY_PACKAGE_SCHEMA_VERSION,
            "schema_status": SCHEMA_STATUS,
        },
        "source_control": absent_section(),
        "run_identity": _run_identity(copied_events, copied_report),
        "replay_window": absent_section(),
        "environment_classification": absent_section(),
        "package_status": {
            "status": _overall_status(section_statuses, run_id_alignment),
            "section_statuses": section_statuses,
            "run_id_alignment": run_id_alignment,
        },
        "configuration_references": _configuration_references(copied_report),
        "market_input_references": _market_input_references(copied_events),
        "strategy_decision_references": _strategy_decision_references(
            copied_events,
            copied_report,
        ),
        "portfolio_risk_snapshot_references": _portfolio_risk_references(
            copied_report,
            copied_order_state,
        ),
        "broker_visible_state_references": _broker_visible_state_references(
            copied_report,
            copied_runtime_visibility,
        ),
        "reconciliation_risk_references": _reconciliation_risk_references(
            copied_events,
            copied_report,
            copied_observations,
        ),
        "event_order_references": _event_order_references(copied_events),
        "attribution": absent_section(),
        "integrity": absent_section("deferred_until_integrity_gate"),
        "immutability": absent_section("deferred_until_storage_gate"),
        "authority_boundary": deepcopy(AUTHORITY_BOUNDARY),
        "out_of_scope": deepcopy(OUT_OF_SCOPE),
    }
    return {section: package[section] for section in ENVELOPE_SECTIONS}


def _copy_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        raise TypeError("events must be a list of dictionaries")
    if not all(isinstance(event, dict) for event in events):
        raise TypeError("events must be a list of dictionaries")
    return deepcopy(events)


def _copy_optional_events(
    observations: list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    if observations is None:
        return None
    return _copy_events(observations)


def _copy_optional_dict(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError("optional replay inputs must be dictionaries")
    return deepcopy(value)


def _package_identity(
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
) -> dict[str, Any]:
    run_id = _run_id(events, run_report)
    if run_id is None:
        return absent_section("run_id_not_supplied")
    return present_section(package_id=None, run_id=run_id)


def _run_identity(
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
) -> dict[str, Any]:
    run_id = _run_id(events, run_report)
    if run_id is None:
        return absent_section("run_id_not_supplied")
    return present_section(
        run_id=run_id,
        trigger_source=(run_report or {}).get("trigger_source"),
        runtime_entrypoint=None,
    )


def _configuration_references(
    run_report: dict[str, Any] | None,
) -> dict[str, Any]:
    if run_report is None:
        return absent_section()
    return present_section(run_report=run_report)


def _market_input_references(events: list[dict[str, Any]]) -> dict[str, Any]:
    market_events = [
        event
        for event in events
        if event.get("event_type") == "data"
        and event.get("stage") == "market_input_captured"
    ]
    if not market_events:
        return absent_section("market_input_event_not_supplied")
    return present_section(events=market_events)


def _strategy_decision_references(
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
) -> dict[str, Any]:
    strategy_events = [
        event for event in events if event.get("event_type") == "strategy"
    ]
    if not strategy_events and run_report is None:
        return absent_section("strategy_reference_not_supplied")
    return present_section(events=strategy_events, run_report=run_report)


def _portfolio_risk_references(
    run_report: dict[str, Any] | None,
    order_state: dict[str, Any] | None,
) -> dict[str, Any]:
    if run_report is None and order_state is None:
        return absent_section("portfolio_risk_reference_not_supplied")
    return present_section(run_report=run_report, order_state=order_state)


def _broker_visible_state_references(
    run_report: dict[str, Any] | None,
    runtime_visibility: dict[str, Any] | None,
) -> dict[str, Any]:
    if run_report is None and runtime_visibility is None:
        return absent_section("broker_visible_reference_not_supplied")
    return present_section(
        run_report=run_report,
        runtime_visibility=runtime_visibility,
    )


def _reconciliation_risk_references(
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
    observations: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    reconciliation_events = [
        event
        for event in events
        if event.get("event_type") in {"position", "risk", "order"}
    ]
    if not reconciliation_events and run_report is None and observations is None:
        return absent_section("reconciliation_risk_reference_not_supplied")
    return present_section(
        events=reconciliation_events,
        run_report=run_report,
        observations=observations,
    )


def _event_order_references(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return absent_section("events_not_supplied")
    return present_section(events=events)


def _section_statuses(
    *,
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
    observations: list[dict[str, Any]] | None,
    order_state: dict[str, Any] | None,
    runtime_visibility: dict[str, Any] | None,
) -> dict[str, str]:
    return {
        "events": _status(bool(events)),
        "run_report": _status(run_report is not None),
        "observations": _status(observations is not None),
        "order_state": _status(order_state is not None),
        "runtime_visibility": _status(runtime_visibility is not None),
    }


def _status(is_present: bool) -> str:
    if is_present:
        return SECTION_STATUS_PRESENT
    return SECTION_STATUS_ABSENT


def _overall_status(
    section_statuses: dict[str, str],
    run_id_alignment: dict[str, Any],
) -> str:
    if all(
        status == SECTION_STATUS_PRESENT for status in section_statuses.values()
    ) and run_id_alignment["aligned"]:
        return "complete"
    return "incomplete"


def _run_id_alignment(
    *,
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
    observations: list[dict[str, Any]] | None,
    order_state: dict[str, Any] | None,
    runtime_visibility: dict[str, Any] | None,
) -> dict[str, Any]:
    event_run_ids = _run_ids_from_events(events)
    canonical_run_id = _event_stream_run_id(events)
    mismatches: dict[str, Any] = {}

    if len(event_run_ids) > 1:
        mismatches["events"] = sorted(event_run_ids)

    if canonical_run_id is not None:
        _record_mismatch(
            mismatches,
            "run_report",
            _run_id_from_dict(run_report),
            canonical_run_id,
        )
        _record_mismatch(
            mismatches,
            "order_state",
            _run_id_from_dict(order_state),
            canonical_run_id,
        )
        _record_event_mismatches(
            mismatches,
            "observations",
            observations,
            canonical_run_id,
        )
        _record_mismatch(
            mismatches,
            "runtime_visibility",
            _run_id_from_dict(runtime_visibility),
            canonical_run_id,
        )

    return {
        "aligned": bool(canonical_run_id) and not mismatches,
        "canonical_run_id": canonical_run_id,
        "mismatches": mismatches,
    }


def _record_mismatch(
    mismatches: dict[str, Any],
    section: str,
    section_run_id: str | None,
    canonical_run_id: str,
) -> None:
    if section_run_id is not None and section_run_id != canonical_run_id:
        mismatches[section] = section_run_id


def _record_event_mismatches(
    mismatches: dict[str, Any],
    section: str,
    events: list[dict[str, Any]] | None,
    canonical_run_id: str,
) -> None:
    if events is None:
        return
    section_run_ids = _run_ids_from_events(events)
    mismatched_run_ids = section_run_ids - {canonical_run_id}
    if mismatched_run_ids:
        mismatches[section] = sorted(mismatched_run_ids)


def _run_ids_from_events(events: list[dict[str, Any]]) -> set[str]:
    return {str(event["run_id"]) for event in events if event.get("run_id")}


def _run_id_from_dict(value: dict[str, Any] | None) -> str | None:
    if value is not None and value.get("run_id"):
        return str(value["run_id"])
    return None


def _event_stream_run_id(events: list[dict[str, Any]]) -> str | None:
    for event in events:
        if event.get("run_id"):
            return str(event["run_id"])
    return None


def _run_id(
    events: list[dict[str, Any]],
    run_report: dict[str, Any] | None,
) -> str | None:
    event_run_id = _event_stream_run_id(events)
    if event_run_id is not None:
        return event_run_id
    return _run_id_from_dict(run_report)
