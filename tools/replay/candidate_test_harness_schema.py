"""Pure in-memory candidate test harness schema/validator (Gate D).

This module implements the Gate D Record D17 Candidate Test Harness Contract as a
deterministic, fail-closed, pure in-memory validator over *already-loaded*
candidate test harness metadata. A harness record *declares* which candidate
governance invariants a future test harness is expected to cover, the candidate
subject references it pertains to, and its pure/in-memory authority boundary. It
validates that declaration only.

Validating harness metadata is not the same as executing anything: this module
runs no tests, treats no test as promotion evidence, reads no packages, resolves
no filesystem paths, performs no package discovery, mutates no baseline or
candidate evidence, executes no replay, generates no candidate evidence, and
runs no comparison, scoring, evaluation, or promotion. It opens no Unit 12 and
carries no runtime, broker, paper-trading, or live-trading authority.

Per D17 a future candidate test harness must prove deterministic candidate
artifact validation, candidate identity/version validation, replay input adapter
fail-closed behavior, baseline no-mutation enforcement, as-of enforcement,
reproducibility/integrity declaration enforcement, D14 ledger membership
compatibility, and broker/order/live-execution exclusion, and must remain
pure/in-memory until a separate future gate explicitly authorizes any
filesystem/package-read behavior. This schema certifies that a harness record
*declares* coverage of exactly that invariant set and *declares* that purity
boundary — it does not run the harness and does not relax the boundary.

Composition (behavior of composed modules is not modified): candidate identity
via candidate decision artifact governance; replay-input identity / run-id /
package-reference-string validation via the replay input adapter schema; linkage
identity via the candidate-vs-baseline linkage schema; baseline strategy identity
via Unit 8 baseline-vs-candidate comparison governance; as-of ordering via the
rule ``asof_timestamp_utc <= decision_timestamp_utc``.

Governance basis: Gate D Record D17 (Candidate Test Harness Contract) and the
candidate test harness schema readiness audit
(READY_FOR_SEPARATE_IMPLEMENTATION_GATE, narrow pure-schema scope only).
Implementing this validator does not advance Gate D: the active lane remains
STOP / NO ACTION and Gate D overall remains NOT COMPLETE -> PARKED. It does not
satisfy any precondition for candidate-evidence execution, which remains
UNIMPLEMENTED and UNAPPROVED.
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
from tools.replay.candidate_baseline_linkage_schema import (
    is_valid_candidate_baseline_link_identifier,
)
from tools.replay.baseline_candidate_comparison_governance import (
    is_valid_baseline_strategy_identifier,
)


CANDIDATE_TEST_HARNESS_SCHEMA = "candidate_test_harness_schema_in_memory_only"
CANDIDATE_TEST_HARNESS_SCHEMA_VERSION = "0.1-candidate-test-harness-schema"
SUPPORTED_CANDIDATE_TEST_HARNESS_SCHEMA_VERSIONS: tuple[str, ...] = (
    CANDIDATE_TEST_HARNESS_SCHEMA_VERSION,
)
CANDIDATE_TEST_HARNESS_SCHEMA_RESULT = "candidate_test_harness_schema_result"

CANDIDATE_TEST_HARNESS_ID_PREFIX = "candidate_test_harness_"
CANDIDATE_TEST_HARNESS_ID_MAX_LENGTH = 128
_IDENTIFIER_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

HARNESS_PURITY_STATUS_PURE_IN_MEMORY = "pure_in_memory"

# The fixed invariant vocabulary a candidate test harness record may declare,
# mirroring the Gate D Record D17 Candidate Test Harness Contract verbatim. A
# valid record must declare coverage of exactly this set.
KNOWN_EXPECTED_INVARIANTS: tuple[str, ...] = (
    "deterministic_candidate_artifact_validation",
    "candidate_identity_version_validation",
    "replay_input_adapter_fail_closed",
    "baseline_no_mutation_enforcement",
    "asof_enforcement",
    "reproducibility_integrity_declaration_enforcement",
    "d14_ledger_membership_compatibility",
    "broker_order_live_execution_exclusion",
)
_REQUIRED_INVARIANT_SET: frozenset[str] = frozenset(KNOWN_EXPECTED_INVARIANTS)

# Required scalar string fields (always present, non-empty).
CANDIDATE_TEST_HARNESS_REQUIRED_FIELDS: tuple[str, ...] = (
    "candidate_test_harness_id",
    "candidate_artifact_id",
    "replay_input_adapter_id",
    "candidate_baseline_link_id",
    "baseline_strategy_id",
    "run_id",
    "package_reference",
    "source_commit",
    "harness_purity_status",
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
    "no_filesystem_or_package_read_until_separate_gate",
)

# Markers that disqualify a harness record and fail closed if truthy. Includes
# explicit test-as-promotion-evidence markers: a test harness declaration must
# never assert that its tests constitute promotion evidence.
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
    "tests_as_promotion_evidence",
    "test_as_promotion_evidence",
    "tests_prove_promotion",
    "promotion_evidence",
)

# Broker / order-state / live-execution fields a harness record must not carry
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
    "test_execution",
    "tests_executed",
    "replay_execution",
    "comparison_execution",
    "scoring",
    "score",
    "scoring_authority",
    "evaluation_execution",
    "promotion",
    "promotion_authority",
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

CANDIDATE_TEST_HARNESS_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_required_field",
    "malformed_candidate_test_harness_id",
    "malformed_candidate_artifact_id",
    "malformed_replay_input_adapter_id",
    "malformed_candidate_baseline_link_id",
    "malformed_baseline_strategy_id",
    "malformed_run_id",
    "malformed_package_reference",
    "missing_source_commit",
    "missing_expected_invariants",
    "unknown_expected_invariant",
    "incomplete_invariant_coverage",
    "harness_purity_status_not_pure_in_memory",
    "filesystem_or_package_read_declared",
    "malformed_timestamp",
    "asof_after_decision_time",
    "missing_or_invalid_integrity_attestation",
    "missing_or_invalid_reproducibility_declaration",
    "missing_no_baseline_mutation_attestation",
    "production_approved_live_promoted_mutable_marker",
    "future_leaked_post_decision_marker",
    "test_as_promotion_evidence_marker",
    "broker_order_live_field_present",
    "authority_bearing_field_present",
    "malformed_record",
)

CANDIDATE_TEST_HARNESS_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "candidate_test_harness_metadata_validation_only",
    "declares_expected_invariant_coverage_only",
    "evidence_only",
    "non_authoritative",
    "no_test_execution",
    "no_tests_as_promotion_evidence",
    "pure_in_memory_until_separate_gate",
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
    "no_baseline_mutation",
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
class CandidateTestHarnessSchema:
    """Static governed candidate test harness schema and version."""

    version: str = CANDIDATE_TEST_HARNESS_SCHEMA_VERSION
    required_fields: tuple[str, ...] = CANDIDATE_TEST_HARNESS_REQUIRED_FIELDS
    expected_invariants: tuple[str, ...] = KNOWN_EXPECTED_INVARIANTS
    authority_boundary: tuple[str, ...] = CANDIDATE_TEST_HARNESS_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class CandidateTestHarnessFailClosedConditions:
    """Static fail-closed condition vocabulary for candidate test harness records."""

    conditions: tuple[str, ...] = CANDIDATE_TEST_HARNESS_FAIL_CLOSED_CONDITIONS


def is_valid_candidate_test_harness_identifier(identifier: object) -> bool:
    """Return True only for a well-formed candidate test harness id."""

    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(CANDIDATE_TEST_HARNESS_ID_PREFIX):
        return False
    if len(identifier) <= len(CANDIDATE_TEST_HARNESS_ID_PREFIX):
        return False
    if len(identifier) > CANDIDATE_TEST_HARNESS_ID_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(CANDIDATE_TEST_HARNESS_ID_PREFIX):]
    return all(char in _IDENTIFIER_BODY_CHARS for char in body)


def is_known_expected_invariant(value: object) -> bool:
    """Return True only for an exactly-known governed expected invariant name."""

    return isinstance(value, str) and value in _REQUIRED_INVARIANT_SET


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


def validate_candidate_test_harness(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded candidate test harness record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("harness record must be already-loaded metadata")

    _reject_forbidden_fields(record)

    for field in CANDIDATE_TEST_HARNESS_REQUIRED_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing required field: '{field}'")

    harness_id = record["candidate_test_harness_id"]
    if not is_valid_candidate_test_harness_identifier(harness_id):
        raise ValueError(f"malformed candidate test harness id: '{harness_id}'")

    candidate_artifact_id = record["candidate_artifact_id"]
    if not is_valid_candidate_artifact_identifier(candidate_artifact_id):
        raise ValueError(
            f"malformed candidate artifact id: '{candidate_artifact_id}'"
        )

    adapter_id = record["replay_input_adapter_id"]
    if not is_valid_replay_input_adapter_identifier(adapter_id):
        raise ValueError(f"malformed replay input adapter id: '{adapter_id}'")

    link_id = record["candidate_baseline_link_id"]
    if not is_valid_candidate_baseline_link_identifier(link_id):
        raise ValueError(f"malformed candidate baseline link id: '{link_id}'")

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

    _validate_expected_invariants(record)

    if record["harness_purity_status"] != HARNESS_PURITY_STATUS_PURE_IN_MEMORY:
        raise ValueError("harness_purity_status must be 'pure_in_memory'")

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
        harness_id=harness_id,
        candidate_artifact_id=candidate_artifact_id,
        replay_input_adapter_id=adapter_id,
        candidate_baseline_link_id=link_id,
        run_id=run_id,
    )


def _validate_expected_invariants(record: Mapping[str, Any]) -> None:
    """Require a non-empty, fully-covering, known-only expected-invariant set."""

    expected = record.get("expected_invariants")
    if not isinstance(expected, (list, tuple)) or not expected:
        raise ValueError("missing expected invariants")
    seen: set[str] = set()
    for invariant in expected:
        if not is_known_expected_invariant(invariant):
            raise ValueError(f"unknown expected invariant: '{invariant}'")
        seen.add(invariant)
    if seen != _REQUIRED_INVARIANT_SET:
        raise ValueError("incomplete expected invariant coverage")


def _reject_forbidden_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_MARKER_FIELDS:
        if record.get(field):
            raise ValueError(
                "production/approved/live/promoted/mutable, future/leaked/"
                "post-decision, or test-as-promotion-evidence marker present: "
                f"'{field}'"
            )
    for field in FORBIDDEN_BROKER_ORDER_FIELDS:
        if field in record:
            raise ValueError(f"broker/order/live field present: '{field}'")
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(
    *,
    harness_id: str,
    candidate_artifact_id: str,
    replay_input_adapter_id: str,
    candidate_baseline_link_id: str,
    run_id: str,
) -> dict[str, Any]:
    return {
        "result_type": CANDIDATE_TEST_HARNESS_SCHEMA_RESULT,
        "candidate_test_harness_schema_version": (
            CANDIDATE_TEST_HARNESS_SCHEMA_VERSION
        ),
        "candidate_test_harness_id": harness_id,
        "candidate_artifact_id": candidate_artifact_id,
        "replay_input_adapter_id": replay_input_adapter_id,
        "candidate_baseline_link_id": candidate_baseline_link_id,
        "run_id": run_id,
        "declares_full_invariant_coverage": True,
        "evidence_only": True,
        "non_authoritative": True,
        "test_execution": False,
        "tests_as_promotion_evidence": False,
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
        "authority_boundary": CANDIDATE_TEST_HARNESS_AUTHORITY_BOUNDARY,
    }
