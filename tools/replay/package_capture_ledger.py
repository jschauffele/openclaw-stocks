"""Pure in-memory package capture ledger schema governance (Gate D D14).

This module defines the deterministic source-controlled package inventory /
capture ledger schema for future governed replay package evidence tracking. It
validates already-loaded ledger record metadata only. It reads no packages,
discovers no packages, creates no ledger entries, touches no filesystem, runs
no capture, computes no scores, performs no evaluation, and carries no
promotion, broker, strategy/risk/execution, paper-trading, or live-trading
authority.

The ledger schema supports D12 sufficiency reassessment by recording finalized,
immutable governed package evidence while preserving the D13 market-session
capture guard and the D12 exclusion rules. Market/session-ineligible and
market-closed-only packages may be recorded only as excluded/non-counting
evidence. Draft, incomplete, mutable, stale, mixed-run-id, hash-mismatch,
error-terminal, future-dated, leaked, or post-decision evidence fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.capture_eligibility_guard import is_market_session_reason


PACKAGE_CAPTURE_LEDGER = "package_capture_ledger_schema_in_memory_only"
PACKAGE_CAPTURE_LEDGER_VERSION = "0.1-package-capture-ledger"
SUPPORTED_PACKAGE_CAPTURE_LEDGER_VERSIONS: tuple[str, ...] = (
    PACKAGE_CAPTURE_LEDGER_VERSION,
)
PACKAGE_CAPTURE_LEDGER_RESULT = "package_capture_ledger_validation_result"

EVIDENCE_MEMBERSHIP_BASELINE = "baseline"
EVIDENCE_MEMBERSHIP_CANDIDATE = "candidate"
EVIDENCE_MEMBERSHIP_EXCLUDED = "excluded"
EVIDENCE_MEMBERSHIP_UNKNOWN = "unknown"
KNOWN_EVIDENCE_MEMBERSHIPS: tuple[str, ...] = (
    EVIDENCE_MEMBERSHIP_BASELINE,
    EVIDENCE_MEMBERSHIP_CANDIDATE,
    EVIDENCE_MEMBERSHIP_EXCLUDED,
    EVIDENCE_MEMBERSHIP_UNKNOWN,
)

SESSION_CLASS_REGULAR = "regular_session"
SESSION_CLASS_MARKET_CLOSED = "market_closed"
SESSION_CLASS_MARKET_HOLIDAY = "market_holiday_or_closed_day"
SESSION_CLASS_BEFORE_OPEN = "before_regular_session_open"
SESSION_CLASS_AFTER_CLOSE = "after_regular_session_close"
SESSION_CLASS_UNKNOWN = "unknown"
KNOWN_SESSION_CLASSES: tuple[str, ...] = (
    SESSION_CLASS_REGULAR,
    SESSION_CLASS_MARKET_CLOSED,
    SESSION_CLASS_MARKET_HOLIDAY,
    SESSION_CLASS_BEFORE_OPEN,
    SESSION_CLASS_AFTER_CLOSE,
    SESSION_CLASS_UNKNOWN,
)
MARKET_SESSION_INELIGIBLE_SESSION_CLASSES: tuple[str, ...] = (
    SESSION_CLASS_MARKET_CLOSED,
    SESSION_CLASS_MARKET_HOLIDAY,
    SESSION_CLASS_BEFORE_OPEN,
    SESSION_CLASS_AFTER_CLOSE,
)

TERMINAL_STATUS_OK = "ok"
TERMINAL_STATUS_BLOCKED = "blocked"
KNOWN_TERMINAL_STATUSES: tuple[str, ...] = (
    TERMINAL_STATUS_OK,
    TERMINAL_STATUS_BLOCKED,
)

DECISION_OUTCOME_SUBMITTED = "submitted"
DECISION_OUTCOME_DRY_RUN = "dry_run"
DECISION_OUTCOME_BLOCKED = "blocked"
DECISION_OUTCOME_HOLD = "hold"
DECISION_OUTCOME_NO_SIGNAL = "no_signal"
DECISION_OUTCOME_UNKNOWN = "unknown"
KNOWN_DECISION_OUTCOMES: tuple[str, ...] = (
    DECISION_OUTCOME_SUBMITTED,
    DECISION_OUTCOME_DRY_RUN,
    DECISION_OUTCOME_BLOCKED,
    DECISION_OUTCOME_HOLD,
    DECISION_OUTCOME_NO_SIGNAL,
    DECISION_OUTCOME_UNKNOWN,
)

DECLARATION_STATUS_DECLARED = "declared"
DECLARATION_STATUS_MISSING = "missing"
DECLARATION_STATUS_UNKNOWN = "unknown"
KNOWN_DECLARATION_STATUSES: tuple[str, ...] = (
    DECLARATION_STATUS_DECLARED,
    DECLARATION_STATUS_MISSING,
    DECLARATION_STATUS_UNKNOWN,
)

INTEGRITY_STATUS_ATTESTED = "attested"
INTEGRITY_STATUS_MISSING = "missing"
INTEGRITY_STATUS_MISMATCH = "mismatch"
KNOWN_INTEGRITY_ATTESTATION_STATUSES: tuple[str, ...] = (
    INTEGRITY_STATUS_ATTESTED,
    INTEGRITY_STATUS_MISSING,
    INTEGRITY_STATUS_MISMATCH,
)

INCLUSION_STATUS_INCLUDED = "included"
INCLUSION_STATUS_EXCLUDED = "excluded"
INCLUSION_STATUS_UNKNOWN = "unknown"
KNOWN_INCLUSION_STATUSES: tuple[str, ...] = (
    INCLUSION_STATUS_INCLUDED,
    INCLUSION_STATUS_EXCLUDED,
    INCLUSION_STATUS_UNKNOWN,
)

PACKAGE_CAPTURE_LEDGER_REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "package_sha256",
    "package_path_or_relative_reference",
    "capture_timestamp_utc",
    "source_commit",
    "session_class",
    "terminal_status",
    "terminal_reason",
    "decision_outcome",
    "evidence_membership",
    "strategy_id",
    "parameter_version",
    "reproducibility_declaration_status",
    "asof_declaration_status",
    "integrity_attestation_status",
    "inclusion_status",
    "exclusion_reason",
    "notes",
)

PACKAGE_CAPTURE_LEDGER_CONTROL_FIELDS: tuple[str, ...] = (
    "finalized",
    "immutable",
    "lifecycle_status",
    "run_id_aligned",
    "hash_verified",
    "complete_package_authority",
    "draft",
    "mutable",
    "stale",
    "mixed_run_id",
    "hash_mismatch",
    "future_dated",
    "leaked",
    "post_decision",
)

FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "package_read",
    "package_reads",
    "package_discovery",
    "package_capture_execution",
    "ledger_write",
    "ledger_persistence",
    "scoring",
    "score",
    "evaluation_execution",
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

PACKAGE_CAPTURE_LEDGER_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_package_capture_ledger_version",
    "unsupported_package_capture_ledger_version",
    "missing_required_ledger_field",
    "malformed_run_id",
    "malformed_package_sha256",
    "malformed_package_reference",
    "malformed_capture_timestamp_utc",
    "malformed_source_commit",
    "unknown_session_class",
    "unknown_terminal_status",
    "unknown_decision_outcome",
    "unknown_evidence_membership",
    "unknown_declaration_status",
    "unknown_integrity_attestation_status",
    "unknown_inclusion_status",
    "missing_exclusion_reason",
    "included_excluded_membership_conflict",
    "market_session_ineligible_not_excluded",
    "non_regular_session_count_attempt",
    "missing_finalized_immutable_package_marker",
    "draft_or_incomplete_package",
    "mutable_package_marker",
    "stale_package_marker",
    "mixed_run_id",
    "hash_mismatch",
    "error_terminal_package",
    "future_dated_or_leaked_or_post_decision_evidence",
    "missing_reproducibility_declaration",
    "missing_asof_declaration",
    "missing_integrity_attestation",
    "authority_bearing_field_present",
)

PACKAGE_CAPTURE_LEDGER_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "package_capture_ledger_schema_governance_only",
    "evidence_only",
    "non_authoritative",
    "source_controlled_records_only",
    "finalized_immutable_packages_only",
    "market_session_ineligible_excluded_from_sufficiency",
    "no_package_reads",
    "no_package_discovery",
    "no_package_capture_execution",
    "no_ledger_writes",
    "no_filesystem_reads",
    "no_scoring",
    "no_evaluation_execution",
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_approval",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class PackageCaptureLedgerSchema:
    """Static governed package capture ledger schema vocabulary."""

    version: str = PACKAGE_CAPTURE_LEDGER_VERSION
    required_fields: tuple[str, ...] = PACKAGE_CAPTURE_LEDGER_REQUIRED_FIELDS
    evidence_memberships: tuple[str, ...] = KNOWN_EVIDENCE_MEMBERSHIPS
    session_classes: tuple[str, ...] = KNOWN_SESSION_CLASSES
    inclusion_statuses: tuple[str, ...] = KNOWN_INCLUSION_STATUSES
    authority_boundary: tuple[str, ...] = PACKAGE_CAPTURE_LEDGER_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageCaptureLedgerFailClosedConditions:
    """Static fail-closed condition vocabulary for D14 ledger validation."""

    conditions: tuple[str, ...] = PACKAGE_CAPTURE_LEDGER_FAIL_CLOSED_CONDITIONS


def is_known_evidence_membership(value: object) -> bool:
    return isinstance(value, str) and value in KNOWN_EVIDENCE_MEMBERSHIPS


def is_known_session_class(value: object) -> bool:
    return isinstance(value, str) and value in KNOWN_SESSION_CLASSES


def is_known_inclusion_status(value: object) -> bool:
    return isinstance(value, str) and value in KNOWN_INCLUSION_STATUSES


def validate_package_capture_ledger_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded package capture ledger record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("package capture ledger record must be already-loaded metadata")

    _validate_version(record)
    _require_fields(record)
    _validate_identity_fields(record)
    _validate_vocabularies(record)
    _validate_finalized_immutable_package(record)
    _validate_exclusion_and_counting_rules(record)
    _reject_authority_fields(record)

    count_eligible = (
        record["inclusion_status"] == INCLUSION_STATUS_INCLUDED
        and record["evidence_membership"]
        in (EVIDENCE_MEMBERSHIP_BASELINE, EVIDENCE_MEMBERSHIP_CANDIDATE)
        and record["session_class"] == SESSION_CLASS_REGULAR
    )
    return {
        "result_type": PACKAGE_CAPTURE_LEDGER_RESULT,
        "package_capture_ledger_version": PACKAGE_CAPTURE_LEDGER_VERSION,
        "run_id": record["run_id"],
        "package_sha256": record["package_sha256"],
        "evidence_membership": record["evidence_membership"],
        "inclusion_status": record["inclusion_status"],
        "sufficiency_count_eligible": count_eligible,
        "market_session_ineligible_excluded": _is_market_session_excluded(record),
        "evidence_only": True,
        "non_authoritative": True,
        "package_reads": False,
        "package_discovery": False,
        "package_capture_execution": False,
        "ledger_writes": False,
        "filesystem_reads": False,
        "scoring": False,
        "evaluation_execution": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": PACKAGE_CAPTURE_LEDGER_AUTHORITY_BOUNDARY,
    }


def _validate_version(record: Mapping[str, Any]) -> None:
    version = record.get("package_capture_ledger_version")
    if not version:
        raise ValueError("missing package capture ledger version")
    if version not in SUPPORTED_PACKAGE_CAPTURE_LEDGER_VERSIONS:
        raise ValueError(f"unsupported package capture ledger version: '{version}'")


def _require_fields(record: Mapping[str, Any]) -> None:
    for field in PACKAGE_CAPTURE_LEDGER_REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"missing required ledger field: '{field}'")
    for field in PACKAGE_CAPTURE_LEDGER_CONTROL_FIELDS:
        if field not in record:
            raise ValueError(f"missing required ledger field: '{field}'")


def _validate_identity_fields(record: Mapping[str, Any]) -> None:
    run_id = record["run_id"]
    if not isinstance(run_id, str) or not run_id.startswith("run_"):
        raise ValueError("malformed run_id")
    package_sha256 = record["package_sha256"]
    if not isinstance(package_sha256, str) or len(package_sha256) != 64:
        raise ValueError("malformed package sha256")
    if not all(char in "0123456789abcdef" for char in package_sha256):
        raise ValueError("malformed package sha256")
    reference = record["package_path_or_relative_reference"]
    if not isinstance(reference, str) or not reference:
        raise ValueError("malformed package reference")
    if reference.startswith("/") or ".." in reference or "order_state" in reference:
        raise ValueError("malformed package reference")
    if not _is_utc_iso8601(record["capture_timestamp_utc"]):
        raise ValueError("malformed capture timestamp UTC")
    source_commit = record["source_commit"]
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise ValueError("malformed source commit")
    if not all(char in "0123456789abcdef" for char in source_commit):
        raise ValueError("malformed source commit")


def _validate_vocabularies(record: Mapping[str, Any]) -> None:
    if record["session_class"] not in KNOWN_SESSION_CLASSES:
        raise ValueError(f"unknown session class: '{record['session_class']}'")
    if record["terminal_status"] not in KNOWN_TERMINAL_STATUSES:
        if record["terminal_status"] == "error":
            raise ValueError("error-terminal package")
        raise ValueError(f"unknown terminal status: '{record['terminal_status']}'")
    if record["decision_outcome"] not in KNOWN_DECISION_OUTCOMES:
        raise ValueError(f"unknown decision outcome: '{record['decision_outcome']}'")
    if record["evidence_membership"] not in KNOWN_EVIDENCE_MEMBERSHIPS:
        raise ValueError(
            f"unknown evidence membership: '{record['evidence_membership']}'"
        )
    for field in (
        "reproducibility_declaration_status",
        "asof_declaration_status",
    ):
        if record[field] not in KNOWN_DECLARATION_STATUSES:
            raise ValueError(f"unknown declaration status: '{record[field]}'")
    if record["integrity_attestation_status"] not in KNOWN_INTEGRITY_ATTESTATION_STATUSES:
        raise ValueError(
            "unknown integrity attestation status: "
            f"'{record['integrity_attestation_status']}'"
        )
    if record["inclusion_status"] not in KNOWN_INCLUSION_STATUSES:
        raise ValueError(f"unknown inclusion status: '{record['inclusion_status']}'")


def _validate_finalized_immutable_package(record: Mapping[str, Any]) -> None:
    if record["finalized"] is not True or record["immutable"] is not True:
        raise ValueError("missing finalized immutable package marker")
    if record["lifecycle_status"] != "finalized":
        raise ValueError("missing finalized immutable package marker")
    if record["complete_package_authority"] is not True:
        raise ValueError("draft or incomplete package")
    if record["draft"]:
        raise ValueError("draft or incomplete package")
    if record["mutable"]:
        raise ValueError("mutable package marker")
    if record["stale"]:
        raise ValueError("stale package marker")
    if record["run_id_aligned"] is not True or record["mixed_run_id"]:
        raise ValueError("mixed run_id")
    if record["hash_verified"] is not True or record["hash_mismatch"]:
        raise ValueError("hash mismatch")
    if record["terminal_status"] == "error":
        raise ValueError("error-terminal package")
    if record["future_dated"] or record["leaked"] or record["post_decision"]:
        raise ValueError("future-dated, leaked, or post-decision evidence")
    if record["reproducibility_declaration_status"] != DECLARATION_STATUS_DECLARED:
        raise ValueError("missing reproducibility declaration")
    if record["asof_declaration_status"] != DECLARATION_STATUS_DECLARED:
        raise ValueError("missing as-of declaration")
    if record["integrity_attestation_status"] != INTEGRITY_STATUS_ATTESTED:
        raise ValueError("missing integrity attestation")


def _validate_exclusion_and_counting_rules(record: Mapping[str, Any]) -> None:
    membership = record["evidence_membership"]
    inclusion = record["inclusion_status"]
    excluded = inclusion == INCLUSION_STATUS_EXCLUDED
    if membership == EVIDENCE_MEMBERSHIP_EXCLUDED and not excluded:
        raise ValueError("included/excluded membership conflict")
    if excluded and not record["exclusion_reason"]:
        raise ValueError("missing exclusion reason")
    if _is_market_session_excluded(record) and not excluded:
        raise ValueError("market/session-ineligible package must be excluded")
    if inclusion == INCLUSION_STATUS_INCLUDED and record["session_class"] != (
        SESSION_CLASS_REGULAR
    ):
        raise ValueError("non-regular-session package cannot count")


def _is_market_session_excluded(record: Mapping[str, Any]) -> bool:
    return (
        record["session_class"] in MARKET_SESSION_INELIGIBLE_SESSION_CLASSES
        or is_market_session_reason(record["terminal_reason"])
    )


def _is_utc_iso8601(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 20:
        return False
    if value[4] != "-" or value[7] != "-" or value[10] != "T":
        return False
    if value[13] != ":" or value[16] != ":" or value[19] != "Z":
        return False
    digits = (
        value[0:4]
        + value[5:7]
        + value[8:10]
        + value[11:13]
        + value[14:16]
        + value[17:19]
    )
    return digits.isdigit()


def _reject_authority_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")
