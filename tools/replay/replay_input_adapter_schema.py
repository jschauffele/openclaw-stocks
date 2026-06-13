"""Pure in-memory replay input adapter schema/validator (Gate D, post-D18).

This module implements the Gate D Record D17 Replay Input Adapter Contract as a
deterministic, fail-closed, pure in-memory validator over *already-loaded*
replay input adapter metadata/references. It reads no packages, resolves no
filesystem paths, performs no package discovery, executes no replay, generates
no candidate evidence, compares nothing, scores nothing, evaluates nothing,
promotes nothing, and opens no Unit 12. It carries no scoring, promotion,
replay, package-read, package-write, runtime, broker, paper-trading, or
live-trading authority.

A replay input adapter reference is research metadata describing one immutable
governed replay input: its run scope, its package hash reference, and the as-of
decision-time ordering under which its evidence may be exposed. Validating a
reference here authorizes nothing: it neither reads any package, resolves any
path, discovers any artifact, nor executes any replay. The package reference is
validated strictly as a reference *string* (never a filesystem path): path-like
values are rejected so this module can never be mistaken for a path resolver.

Per D17 the adapter must consume immutable governed inputs only, never mutate
baseline packages, preserve original ``run_id`` and package hash references,
expose only as-of decision-time evidence, reject future/leaked/post-decision
evidence, reject broker/order-state/API/live-execution fields, and fail closed
on missing identity, version, integrity, reproducibility, as-of, run-scope, or
package-reference metadata.

Governance basis: Gate D Record D17 (Replay Input Adapter Contract) and the
replay-input-adapter schema readiness audit (READY_FOR_SEPARATE_IMPLEMENTATION_
GATE, narrow pure-schema scope only). Implementing this validator does not
advance Gate D: the active lane remains STOP / NO ACTION and Gate D overall
remains NOT COMPLETE -> PARKED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REPLAY_INPUT_ADAPTER_SCHEMA = "replay_input_adapter_schema_in_memory_only"
REPLAY_INPUT_ADAPTER_SCHEMA_VERSION = "0.1-replay-input-adapter-schema"
SUPPORTED_REPLAY_INPUT_ADAPTER_SCHEMA_VERSIONS: tuple[str, ...] = (
    REPLAY_INPUT_ADAPTER_SCHEMA_VERSION,
)
REPLAY_INPUT_ADAPTER_SCHEMA_RESULT = "replay_input_adapter_schema_result"

REPLAY_INPUT_ADAPTER_ID_PREFIX = "replay_input_"
REPLAY_INPUT_ADAPTER_ID_MAX_LENGTH = 128
RUN_ID_PREFIX = "run_"
PACKAGE_REFERENCE_MAX_LENGTH = 256
_IDENTIFIER_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

# Adapter-input-version values this schema accepts (the schema does not version
# the adapter runtime; it only certifies the declared input contract version).
SUPPORTED_INPUT_ADAPTER_VERSIONS: tuple[str, ...] = ("1.0",)

# Required scalar string fields (always present, non-empty).
REPLAY_INPUT_ADAPTER_REQUIRED_FIELDS: tuple[str, ...] = (
    "replay_input_adapter_id",
    "run_id",
    "package_reference",
    "input_adapter_version",
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

# Markers that disqualify an adapter reference and fail closed if truthy.
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

# Broker / order-state / live-execution fields an adapter reference must not
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
    "comparison_execution",
    "replay_execution",
    "candidate_generation",
    "package_reads",
    "package_writes",
    "package_discovery",
    "filesystem_reads",
    "path_resolution",
    "runtime_authority",
    "promotion_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
)

REPLAY_INPUT_ADAPTER_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_required_field",
    "malformed_replay_input_adapter_id",
    "malformed_run_id",
    "malformed_package_reference",
    "package_reference_is_path_like",
    "unsupported_input_adapter_version",
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

REPLAY_INPUT_ADAPTER_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "replay_input_adapter_reference_validation_only",
    "evidence_only",
    "non_authoritative",
    "immutable_governed_input_reference_only",
    "package_reference_is_reference_string_not_path",
    "asof_decision_time_ordering_enforced",
    "no_candidate_generation",
    "no_replay_execution",
    "no_package_reads",
    "no_package_writes",
    "no_package_discovery",
    "no_filesystem_reads",
    "no_path_resolution",
    "no_baseline_mutation",
    "no_scoring",
    "no_evaluation_execution",
    "no_comparison_execution",
    "no_unit_12",
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
class ReplayInputAdapterSchema:
    """Static governed replay input adapter schema and version."""

    version: str = REPLAY_INPUT_ADAPTER_SCHEMA_VERSION
    required_fields: tuple[str, ...] = REPLAY_INPUT_ADAPTER_REQUIRED_FIELDS
    authority_boundary: tuple[str, ...] = REPLAY_INPUT_ADAPTER_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class ReplayInputAdapterFailClosedConditions:
    """Static fail-closed condition vocabulary for replay input adapter refs."""

    conditions: tuple[str, ...] = REPLAY_INPUT_ADAPTER_FAIL_CLOSED_CONDITIONS


def is_valid_replay_input_adapter_identifier(identifier: object) -> bool:
    """Return True only for a well-formed replay input adapter id."""

    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(REPLAY_INPUT_ADAPTER_ID_PREFIX):
        return False
    if len(identifier) <= len(REPLAY_INPUT_ADAPTER_ID_PREFIX):
        return False
    if len(identifier) > REPLAY_INPUT_ADAPTER_ID_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(REPLAY_INPUT_ADAPTER_ID_PREFIX):]
    return all(char in _IDENTIFIER_BODY_CHARS for char in body)


def is_valid_run_id(run_id: object) -> bool:
    """Return True only for a well-formed run-scope identifier."""

    if not isinstance(run_id, str):
        return False
    if not run_id.startswith(RUN_ID_PREFIX):
        return False
    if len(run_id) <= len(RUN_ID_PREFIX):
        return False
    return ".." not in run_id and "/" not in run_id and "\\" not in run_id


def is_valid_package_reference(reference: object) -> bool:
    """Return True only for a non-empty package *reference string* (not a path).

    Path-like values (containing a path separator or parent traversal) are
    rejected so this schema can never be used to resolve a filesystem path.
    """

    if not isinstance(reference, str) or not reference:
        return False
    if reference != reference.strip():
        return False
    if len(reference) > PACKAGE_REFERENCE_MAX_LENGTH:
        return False
    return ".." not in reference and "/" not in reference and "\\" not in reference


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


def validate_replay_input_adapter_reference(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded replay input adapter reference, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError(
            "replay input adapter reference must be already-loaded metadata"
        )

    _reject_forbidden_fields(record)

    for field in REPLAY_INPUT_ADAPTER_REQUIRED_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing required field: '{field}'")

    adapter_id = record["replay_input_adapter_id"]
    if not is_valid_replay_input_adapter_identifier(adapter_id):
        raise ValueError(
            f"malformed replay input adapter id: '{adapter_id}'"
        )

    run_id = record["run_id"]
    if not is_valid_run_id(run_id):
        raise ValueError(f"malformed run_id: '{run_id}'")

    package_reference = record["package_reference"]
    if not is_valid_package_reference(package_reference):
        raise ValueError(
            f"malformed package reference (reference string only): '{package_reference}'"
        )

    input_adapter_version = record["input_adapter_version"]
    if input_adapter_version not in SUPPORTED_INPUT_ADAPTER_VERSIONS:
        raise ValueError(
            f"unsupported input_adapter_version: '{input_adapter_version}'"
        )

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
        adapter_id=adapter_id,
        run_id=run_id,
        package_reference=package_reference,
        input_adapter_version=input_adapter_version,
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
    adapter_id: str,
    run_id: str,
    package_reference: str,
    input_adapter_version: str,
) -> dict[str, Any]:
    return {
        "result_type": REPLAY_INPUT_ADAPTER_SCHEMA_RESULT,
        "replay_input_adapter_schema_version": REPLAY_INPUT_ADAPTER_SCHEMA_VERSION,
        "replay_input_adapter_id": adapter_id,
        "run_id": run_id,
        "package_reference": package_reference,
        "input_adapter_version": input_adapter_version,
        "evidence_only": True,
        "non_authoritative": True,
        "immutable_governed_input_reference_only": True,
        "candidate_generation": False,
        "replay_execution": False,
        "comparison_execution": False,
        "scoring": False,
        "evaluation_execution": False,
        "package_reads": False,
        "package_writes": False,
        "package_discovery": False,
        "filesystem_reads": False,
        "path_resolution": False,
        "baseline_mutation": False,
        "unit_12": False,
        "runtime_authority": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "order_state_binding": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": REPLAY_INPUT_ADAPTER_AUTHORITY_BOUNDARY,
    }
