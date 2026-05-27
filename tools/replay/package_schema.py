"""Schema constants for in-memory replay package envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ENVELOPE_SECTIONS: tuple[str, ...] = (
    "package_identity",
    "schema",
    "source_control",
    "run_identity",
    "replay_window",
    "environment_classification",
    "package_status",
    "configuration_references",
    "market_input_references",
    "strategy_decision_references",
    "portfolio_risk_snapshot_references",
    "broker_visible_state_references",
    "reconciliation_risk_references",
    "event_order_references",
    "attribution",
    "integrity",
    "immutability",
    "authority_boundary",
    "out_of_scope",
)

REPLAY_PACKAGE_SCHEMA_VERSION = "0.1-planning"
SCHEMA_STATUS = "scaffold_in_memory_only"
SECTION_STATUS_PRESENT = "present"
SECTION_STATUS_ABSENT = "absent"

AUTHORITY_BOUNDARY: dict[str, bool] = {
    "evidence_only": True,
    "non_authoritative": True,
    "no_runtime_mutation": True,
    "no_execution_authority": True,
    "no_broker_authority": True,
    "no_strategy_behavior_change": True,
    "no_secret_material": True,
}

OUT_OF_SCOPE: dict[str, bool] = {
    "file_path_artifact_ingestion": True,
    "artifact_writer": True,
    "storage": True,
    "hashing_integrity_enforcement": True,
    "runtime_capture": True,
    "runtime_integration": True,
    "broker_live_api_work": True,
    "alpaca_calls": True,
    "ibkr_tws_work": True,
    "credential_or_env_handling": True,
    "strategy_behavior_changes": True,
    "replay_based_promotion_decisions": True,
}


@dataclass(frozen=True, slots=True)
class ReplayInputBundle:
    """Already-loaded replay inputs supplied by a caller."""

    events: list[dict[str, Any]]
    run_report: dict[str, Any] | None = None
    observations: list[dict[str, Any]] | None = None
    order_state: dict[str, Any] | None = None
    runtime_visibility: dict[str, Any] | None = None


def absent_section(reason: str = "not_supplied") -> dict[str, Any]:
    return {
        "status": SECTION_STATUS_ABSENT,
        "reason": reason,
    }


def present_section(**references: Any) -> dict[str, Any]:
    return {
        "status": SECTION_STATUS_PRESENT,
        **references,
    }
