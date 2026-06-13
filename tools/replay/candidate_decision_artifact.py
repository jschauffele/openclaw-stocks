"""Pure in-memory candidate decision artifact schema + validator (Gate D D18).

This module implements the Gate D Record D17 Candidate Decision Artifact
Contract as a deterministic, fail-closed, pure in-memory validator over
already-loaded candidate decision artifact metadata. It generates no candidate
evidence, executes no replay, reads no packages, touches no filesystem, scores
nothing, evaluates nothing, and carries no scoring, promotion, replay,
package-read, package-write, runtime, broker, paper-trading, or live-trading
authority.

A candidate decision artifact is research metadata describing one deterministic
candidate decision. Validating an artifact here authorizes nothing: it neither
produces the artifact, reads any package, nor approves any downstream behavior.
Candidate identity composes with Unit 6 candidate strategy governance; as-of
ordering composes with the Unit 8 / D17 rule
`asof_timestamp_utc <= decision_timestamp_utc`. Broker/order/live fields,
production/approved/live/promoted/mutable markers, future/leaked/post-decision
evidence, and missing reproducibility / as-of / integrity / no-mutation /
no-broker-order-state declarations all fail closed.

Governance basis: Gate D Record D17 (candidate-evidence mechanism contract) and
the D18 implementation-readiness audit (READY_FOR_SEPARATE_IMPLEMENTATION_GATE,
narrow pure-schema scope only).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.candidate_strategy_governance import (
    is_valid_candidate_strategy_identifier,
)


CANDIDATE_DECISION_ARTIFACT = "candidate_decision_artifact_in_memory_only"
CANDIDATE_DECISION_ARTIFACT_VERSION = "0.1-candidate-decision-artifact"
SUPPORTED_CANDIDATE_DECISION_ARTIFACT_VERSIONS: tuple[str, ...] = (
    CANDIDATE_DECISION_ARTIFACT_VERSION,
)
CANDIDATE_DECISION_ARTIFACT_RESULT = "candidate_decision_artifact_result"

CANDIDATE_ARTIFACT_ID_PREFIX = "cand_artifact_"
CANDIDATE_ARTIFACT_ID_MAX_LENGTH = 128
_IDENTIFIER_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

# Required scalar string fields (always present, non-empty).
CANDIDATE_DECISION_ARTIFACT_REQUIRED_FIELDS: tuple[str, ...] = (
    "candidate_artifact_id",
    "candidate_strategy_id",
    "candidate_parameter_version",
    "source_commit",
    "decision_timestamp_utc",
    "asof_timestamp_utc",
    "decision_signal",
    "proposed_action",
    "decision_reason",
    "deterministic_inputs_reference",
)

# Declaration fields and the exact value each must carry.
REQUIRED_DECLARATIONS: tuple[tuple[str, str], ...] = (
    ("reproducibility_declaration_status", "declared"),
    ("asof_declaration_status", "declared"),
    ("integrity_attestation_status", "attested"),
)

# Boolean attestations that must be exactly True.
REQUIRED_TRUE_ATTESTATIONS: tuple[str, ...] = (
    "no_broker_order_state_binding",
    "no_mutation_attestation",
)

# Markers that disqualify a candidate artifact and fail closed if truthy.
FORBIDDEN_MARKER_FIELDS: tuple[str, ...] = (
    "production",
    "approved",
    "live",
    "promoted",
    "mutable",
    "mutable_evidence",
    "future_dated",
    "leaked",
    "post_decision",
)

# Broker / order-state / live-execution fields a candidate artifact must not
# carry at all (presence — not merely truthiness — fails closed).
FORBIDDEN_BROKER_ORDER_FIELDS: tuple[str, ...] = (
    "broker",
    "broker_api",
    "broker_api_authority",
    "alpaca",
    "ibkr",
    "tws",
    "order_submission",
    "order_cancellation",
    "order_state",
    "order_state_binding",
    "flatten",
    "cleanup",
    "paper_trading",
    "paper_trading_authority",
    "live_trading",
    "live_trading_authority",
)

# Fields that would imply downstream authority this schema must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "scoring_authority",
    "evaluation_execution",
    "replay_execution",
    "candidate_generation",
    "package_reads",
    "package_writes",
    "runtime_authority",
    "promotion_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
)

CANDIDATE_DECISION_ARTIFACT_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_required_field",
    "malformed_candidate_artifact_id",
    "malformed_candidate_strategy_id",
    "missing_input_reference",
    "malformed_timestamp",
    "asof_after_decision_time",
    "missing_or_invalid_reproducibility_declaration",
    "missing_or_invalid_asof_declaration",
    "missing_or_invalid_integrity_attestation",
    "missing_no_broker_order_state_binding",
    "missing_no_mutation_attestation",
    "production_approved_live_promoted_mutable_marker",
    "future_leaked_post_decision_marker",
    "broker_order_live_field_present",
    "authority_bearing_field_present",
    "malformed_record",
)

CANDIDATE_DECISION_ARTIFACT_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "candidate_decision_artifact_schema_validation_only",
    "evidence_only",
    "non_authoritative",
    "research_evidence_only",
    "candidate_distinct_from_baseline_and_production",
    "asof_decision_time_ordering_enforced",
    "no_candidate_generation",
    "no_replay_execution",
    "no_package_reads",
    "no_package_writes",
    "no_filesystem_reads",
    "no_scoring",
    "no_evaluation_execution",
    "no_comparison_execution",
    "no_runtime_authority",
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_order_state_binding",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class CandidateDecisionArtifactSchema:
    """Static governed candidate decision artifact schema and version."""

    version: str = CANDIDATE_DECISION_ARTIFACT_VERSION
    required_fields: tuple[str, ...] = CANDIDATE_DECISION_ARTIFACT_REQUIRED_FIELDS
    authority_boundary: tuple[str, ...] = (
        CANDIDATE_DECISION_ARTIFACT_AUTHORITY_BOUNDARY
    )


@dataclass(frozen=True, slots=True)
class CandidateDecisionArtifactFailClosedConditions:
    """Static fail-closed condition vocabulary for candidate decision artifacts."""

    conditions: tuple[str, ...] = (
        CANDIDATE_DECISION_ARTIFACT_FAIL_CLOSED_CONDITIONS
    )


def is_valid_candidate_artifact_identifier(identifier: object) -> bool:
    """Return True only for a well-formed candidate decision artifact id."""

    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(CANDIDATE_ARTIFACT_ID_PREFIX):
        return False
    if len(identifier) <= len(CANDIDATE_ARTIFACT_ID_PREFIX):
        return False
    if len(identifier) > CANDIDATE_ARTIFACT_ID_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(CANDIDATE_ARTIFACT_ID_PREFIX):]
    return all(char in _IDENTIFIER_BODY_CHARS for char in body)


def _is_utc_iso8601(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 20:
        return False
    if value[4] != "-" or value[7] != "-" or value[10] != "T":
        return False
    if value[13] != ":" or value[16] != ":" or value[19] != "Z":
        return False
    digits = (
        value[0:4] + value[5:7] + value[8:10]
        + value[11:13] + value[14:16] + value[17:19]
    )
    return digits.isdigit()


def validate_candidate_decision_artifact(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded candidate decision artifact, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError(
            "candidate decision artifact must be already-loaded metadata"
        )

    _reject_forbidden_fields(record)

    for field in CANDIDATE_DECISION_ARTIFACT_REQUIRED_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing required field: '{field}'")

    candidate_artifact_id = record["candidate_artifact_id"]
    if not is_valid_candidate_artifact_identifier(candidate_artifact_id):
        raise ValueError(
            f"malformed candidate artifact id: '{candidate_artifact_id}'"
        )

    candidate_strategy_id = record["candidate_strategy_id"]
    if not is_valid_candidate_strategy_identifier(candidate_strategy_id):
        raise ValueError(
            f"malformed candidate strategy id: '{candidate_strategy_id}'"
        )

    input_run_id = record.get("input_run_id")
    input_package_reference = record.get("input_package_reference")
    if not (
        (isinstance(input_run_id, str) and input_run_id)
        or (isinstance(input_package_reference, str) and input_package_reference)
    ):
        raise ValueError(
            "missing input reference: input_run_id or input_package_reference required"
        )

    baseline_package_reference = record.get("baseline_package_reference")
    if baseline_package_reference is not None and not (
        isinstance(baseline_package_reference, str) and baseline_package_reference
    ):
        raise ValueError("malformed baseline_package_reference")

    decision_ts = record["decision_timestamp_utc"]
    asof_ts = record["asof_timestamp_utc"]
    if not _is_utc_iso8601(decision_ts) or not _is_utc_iso8601(asof_ts):
        raise ValueError("malformed timestamp")
    if asof_ts > decision_ts:
        raise ValueError("as-of timestamp is after decision time")

    for field, expected in REQUIRED_DECLARATIONS:
        if record.get(field) != expected:
            raise ValueError(
                f"missing or invalid declaration: '{field}' must be '{expected}'"
            )

    for field in REQUIRED_TRUE_ATTESTATIONS:
        if record.get(field) is not True:
            raise ValueError(f"missing attestation: '{field}' must be True")

    return _governed_result(
        candidate_artifact_id=candidate_artifact_id,
        candidate_strategy_id=candidate_strategy_id,
    )


def _reject_forbidden_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_MARKER_FIELDS:
        if record.get(field):
            raise ValueError(
                "production/approved/live/promoted/mutable or future/leaked/"
                f"post-decision marker present: '{field}'"
            )
    for field in FORBIDDEN_BROKER_ORDER_FIELDS:
        if field in record:
            raise ValueError(f"broker/order/live field present: '{field}'")
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(
    *,
    candidate_artifact_id: str,
    candidate_strategy_id: str,
) -> dict[str, Any]:
    return {
        "result_type": CANDIDATE_DECISION_ARTIFACT_RESULT,
        "candidate_decision_artifact_version": CANDIDATE_DECISION_ARTIFACT_VERSION,
        "candidate_artifact_id": candidate_artifact_id,
        "candidate_strategy_id": candidate_strategy_id,
        "evidence_only": True,
        "non_authoritative": True,
        "research_evidence_only": True,
        "candidate_generation": False,
        "replay_execution": False,
        "comparison_execution": False,
        "scoring": False,
        "evaluation_execution": False,
        "package_reads": False,
        "package_writes": False,
        "filesystem_reads": False,
        "runtime_authority": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "order_state_binding": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": CANDIDATE_DECISION_ARTIFACT_AUTHORITY_BOUNDARY,
    }
