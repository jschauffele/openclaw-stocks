"""Pure in-memory candidate-vs-baseline linkage schema/validator (Gate D).

This module implements the Gate D Record D17 Candidate-Vs-Baseline Linkage
Contract as a deterministic, fail-closed, pure in-memory validator over
*already-loaded* linkage metadata. A linkage record binds one candidate
decision artifact and its replay input adapter reference to the governed
baseline package/run scope used to generate the candidate evidence. Validating a
linkage here authorizes nothing: it reads no packages, resolves no filesystem
paths, performs no package discovery, mutates no baseline or candidate evidence,
executes no replay, generates no candidate evidence, and runs no comparison,
scoring, evaluation, or promotion. It opens no Unit 12 and carries no runtime,
broker, paper-trading, or live-trading authority.

Per D17 the linkage must reference the baseline package or run scope, must not
imply scoring or promotion authority, must not relabel baseline evidence as
candidate evidence, must not mutate or rewrite baseline packages, must preserve
baseline and candidate membership distinctions for D14 ledger records, and must
support future Unit 7 baseline-vs-candidate comparison governance *without*
executing comparison, scoring, evaluation, or promotion.

Composition (behavior of composed modules is not modified): candidate identity
via Unit candidate decision artifact governance; replay-input identity / run-id
/ package-reference-string validation via the replay input adapter schema;
baseline strategy identity via Unit 8 baseline-vs-candidate comparison
governance; evidence-membership vocabulary via the D14 package capture ledger;
as-of ordering via the rule ``asof_timestamp_utc <= decision_timestamp_utc``.

Governance basis: Gate D Record D17 (Candidate-Vs-Baseline Linkage Contract) and
the candidate-vs-baseline linkage schema readiness audit
(READY_FOR_SEPARATE_IMPLEMENTATION_GATE, narrow pure-schema scope only).
Implementing this validator does not advance Gate D: the active lane remains
STOP / NO ACTION and Gate D overall remains NOT COMPLETE -> PARKED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.candidate_decision_artifact import (
    is_valid_candidate_artifact_identifier,
)
from tools.replay.replay_input_adapter_schema import (
    is_valid_package_reference,
    is_valid_replay_input_adapter_identifier,
    is_valid_run_id,
)
from tools.replay.baseline_candidate_comparison_governance import (
    is_valid_baseline_strategy_identifier,
)
from tools.replay.package_capture_ledger import (
    EVIDENCE_MEMBERSHIP_BASELINE,
    EVIDENCE_MEMBERSHIP_CANDIDATE,
)


CANDIDATE_BASELINE_LINKAGE_SCHEMA = "candidate_baseline_linkage_schema_in_memory_only"
CANDIDATE_BASELINE_LINKAGE_SCHEMA_VERSION = "0.1-candidate-baseline-linkage-schema"
SUPPORTED_CANDIDATE_BASELINE_LINKAGE_SCHEMA_VERSIONS: tuple[str, ...] = (
    CANDIDATE_BASELINE_LINKAGE_SCHEMA_VERSION,
)
CANDIDATE_BASELINE_LINKAGE_SCHEMA_RESULT = "candidate_baseline_linkage_schema_result"

CANDIDATE_BASELINE_LINK_ID_PREFIX = "candidate_baseline_link_"
CANDIDATE_BASELINE_LINK_ID_MAX_LENGTH = 128
_IDENTIFIER_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

# Required scalar string fields (always present, non-empty).
CANDIDATE_BASELINE_LINKAGE_REQUIRED_FIELDS: tuple[str, ...] = (
    "candidate_baseline_link_id",
    "candidate_artifact_id",
    "replay_input_adapter_id",
    "baseline_package_reference",
    "baseline_strategy_id",
    "run_id",
    "package_reference",
    "source_commit",
    "candidate_evidence_membership",
    "baseline_evidence_membership",
    "asof_timestamp_utc",
    "decision_timestamp_utc",
)

# Declaration fields and the exact value each must carry.
REQUIRED_DECLARATIONS: tuple[tuple[str, str], ...] = (
    ("integrity_attestation_status", "attested"),
    ("reproducibility_declaration_status", "declared"),
)

# Boolean attestations that must be exactly True.
REQUIRED_TRUE_ATTESTATIONS: tuple[str, ...] = (
    "no_baseline_mutation_attestation",
)

# Markers that disqualify a linkage record and fail closed if truthy.
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

# Broker / order-state / live-execution fields a linkage record must not carry
# at all (presence — not merely truthiness — fails closed).
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
    "promotion",
    "promotion_authority",
    "comparison_execution",
    "evaluation_execution",
    "replay_execution",
    "candidate_generation",
    "package_reads",
    "package_writes",
    "package_discovery",
    "filesystem_reads",
    "path_resolution",
    "runtime_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

CANDIDATE_BASELINE_LINKAGE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_required_field",
    "malformed_candidate_baseline_link_id",
    "malformed_candidate_artifact_id",
    "malformed_replay_input_adapter_id",
    "malformed_baseline_package_reference",
    "malformed_baseline_strategy_id",
    "malformed_run_id",
    "malformed_package_reference",
    "missing_source_commit",
    "candidate_membership_not_candidate",
    "baseline_membership_not_baseline",
    "membership_not_distinct",
    "baseline_relabeled_as_candidate",
    "reference_carries_both_baseline_and_candidate_markers",
    "malformed_timestamp",
    "asof_after_decision_time",
    "missing_or_invalid_integrity_attestation",
    "missing_or_invalid_reproducibility_declaration",
    "missing_no_baseline_mutation_attestation",
    "production_approved_live_promoted_mutable_marker",
    "future_leaked_post_decision_marker",
    "broker_order_live_field_present",
    "authority_bearing_field_present",
    "malformed_record",
)

CANDIDATE_BASELINE_LINKAGE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "candidate_baseline_linkage_validation_only",
    "evidence_only",
    "non_authoritative",
    "preserves_d14_baseline_candidate_membership_distinction",
    "supports_future_comparison_without_executing_comparison",
    "baseline_and_candidate_membership_distinct",
    "no_relabel_baseline_as_candidate",
    "no_baseline_mutation",
    "asof_decision_time_ordering_enforced",
    "no_candidate_generation",
    "no_replay_execution",
    "no_comparison_execution",
    "no_scoring",
    "no_evaluation_execution",
    "no_promotion_or_strategy_promotion",
    "no_package_reads",
    "no_package_writes",
    "no_package_discovery",
    "no_filesystem_reads",
    "no_path_resolution",
    "no_unit_12",
    "no_runtime_authority",
    "no_broker_api_authority",
    "no_order_state_binding",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class CandidateBaselineLinkageSchema:
    """Static governed candidate-vs-baseline linkage schema and version."""

    version: str = CANDIDATE_BASELINE_LINKAGE_SCHEMA_VERSION
    required_fields: tuple[str, ...] = CANDIDATE_BASELINE_LINKAGE_REQUIRED_FIELDS
    authority_boundary: tuple[str, ...] = (
        CANDIDATE_BASELINE_LINKAGE_AUTHORITY_BOUNDARY
    )


@dataclass(frozen=True, slots=True)
class CandidateBaselineLinkageFailClosedConditions:
    """Static fail-closed condition vocabulary for linkage records."""

    conditions: tuple[str, ...] = (
        CANDIDATE_BASELINE_LINKAGE_FAIL_CLOSED_CONDITIONS
    )


def is_valid_candidate_baseline_link_identifier(identifier: object) -> bool:
    """Return True only for a well-formed candidate-vs-baseline linkage id."""

    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(CANDIDATE_BASELINE_LINK_ID_PREFIX):
        return False
    if len(identifier) <= len(CANDIDATE_BASELINE_LINK_ID_PREFIX):
        return False
    if len(identifier) > CANDIDATE_BASELINE_LINK_ID_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(CANDIDATE_BASELINE_LINK_ID_PREFIX):]
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


def validate_candidate_baseline_linkage(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded candidate-vs-baseline linkage, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("linkage record must be already-loaded metadata")

    _reject_forbidden_fields(record)

    for field in CANDIDATE_BASELINE_LINKAGE_REQUIRED_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing required field: '{field}'")

    link_id = record["candidate_baseline_link_id"]
    if not is_valid_candidate_baseline_link_identifier(link_id):
        raise ValueError(f"malformed candidate baseline link id: '{link_id}'")

    candidate_artifact_id = record["candidate_artifact_id"]
    if not is_valid_candidate_artifact_identifier(candidate_artifact_id):
        raise ValueError(
            f"malformed candidate artifact id: '{candidate_artifact_id}'"
        )

    adapter_id = record["replay_input_adapter_id"]
    if not is_valid_replay_input_adapter_identifier(adapter_id):
        raise ValueError(f"malformed replay input adapter id: '{adapter_id}'")

    baseline_package_reference = record["baseline_package_reference"]
    if not is_valid_package_reference(baseline_package_reference):
        raise ValueError(
            "malformed baseline package reference (reference string only): "
            f"'{baseline_package_reference}'"
        )

    baseline_strategy_id = record["baseline_strategy_id"]
    if not is_valid_baseline_strategy_identifier(baseline_strategy_id):
        raise ValueError(
            f"malformed baseline strategy id: '{baseline_strategy_id}'"
        )

    run_id = record["run_id"]
    if not is_valid_run_id(run_id):
        raise ValueError(f"malformed run_id: '{run_id}'")

    package_reference = record["package_reference"]
    if not is_valid_package_reference(package_reference):
        raise ValueError(
            f"malformed package reference (reference string only): '{package_reference}'"
        )

    _validate_membership_distinctness(record)

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
        link_id=link_id,
        candidate_artifact_id=candidate_artifact_id,
        replay_input_adapter_id=adapter_id,
        baseline_strategy_id=baseline_strategy_id,
        run_id=run_id,
    )


def _validate_membership_distinctness(record: Mapping[str, Any]) -> None:
    """Enforce distinct baseline/candidate membership; reject relabeling."""

    candidate_membership = record["candidate_evidence_membership"]
    baseline_membership = record["baseline_evidence_membership"]
    if candidate_membership != EVIDENCE_MEMBERSHIP_CANDIDATE:
        raise ValueError("candidate membership must be 'candidate'")
    if baseline_membership != EVIDENCE_MEMBERSHIP_BASELINE:
        raise ValueError("baseline membership must be 'baseline'")
    if candidate_membership == baseline_membership:
        raise ValueError("baseline and candidate membership must be distinct")
    # Anti-relabel: a reference must not carry both baseline and candidate markers.
    if record.get("baseline_is_candidate") or record.get("candidate_is_baseline"):
        raise ValueError("baseline evidence relabeled as candidate evidence")
    if record.get("is_baseline") and record.get("is_candidate"):
        raise ValueError(
            "reference carries both baseline and candidate markers"
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
    link_id: str,
    candidate_artifact_id: str,
    replay_input_adapter_id: str,
    baseline_strategy_id: str,
    run_id: str,
) -> dict[str, Any]:
    return {
        "result_type": CANDIDATE_BASELINE_LINKAGE_SCHEMA_RESULT,
        "candidate_baseline_linkage_schema_version": (
            CANDIDATE_BASELINE_LINKAGE_SCHEMA_VERSION
        ),
        "candidate_baseline_link_id": link_id,
        "candidate_artifact_id": candidate_artifact_id,
        "replay_input_adapter_id": replay_input_adapter_id,
        "baseline_strategy_id": baseline_strategy_id,
        "run_id": run_id,
        "baseline_candidate_membership_distinct": True,
        "evidence_only": True,
        "non_authoritative": True,
        "candidate_generation": False,
        "replay_execution": False,
        "comparison_execution": False,
        "scoring": False,
        "evaluation_execution": False,
        "promotion_authority": False,
        "package_reads": False,
        "package_writes": False,
        "package_discovery": False,
        "filesystem_reads": False,
        "path_resolution": False,
        "baseline_mutation": False,
        "unit_12": False,
        "runtime_authority": False,
        "broker_api_authority": False,
        "order_state_binding": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": CANDIDATE_BASELINE_LINKAGE_AUTHORITY_BOUNDARY,
    }
