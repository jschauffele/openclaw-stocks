"""Pure in-memory runtime artifact instance contract for replay.

This module defines runtime artifact metadata status vocabulary, eligibility
vocabulary, absent/not-applicable declarations, provenance requirements,
redaction requirements, and fail-closed validation. It does not discover, read,
stat, copy, or inspect real artifacts. It does not capture runtime output,
evaluate or promote strategies, call broker APIs, authorize execution, approve
paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


RUNTIME_ARTIFACT_AUTHORITY = "runtime_artifact_authority_metadata_only"
RUNTIME_ARTIFACT_RESULT = "runtime_artifact_result"

JSONL_EVENT_STREAM = "jsonl_event_stream"
LAST_RUN_REPORT = "last_run_report"
ORDER_STATE = "order_state"
OBSERVATIONS = "observations"
RUNTIME_VISIBILITY = "runtime_visibility"

RUNTIME_ARTIFACT_TYPES: tuple[str, ...] = (
    JSONL_EVENT_STREAM,
    LAST_RUN_REPORT,
    ORDER_STATE,
    OBSERVATIONS,
    RUNTIME_VISIBILITY,
)

RUNTIME_ARTIFACT_ELIGIBLE = "eligible"
RUNTIME_ARTIFACT_ABSENT = "absent"
RUNTIME_ARTIFACT_NOT_APPLICABLE = "not_applicable"
RUNTIME_ARTIFACT_STALE = "stale"
RUNTIME_ARTIFACT_MALFORMED = "malformed"
RUNTIME_ARTIFACT_MIXED_RUN_ID = "mixed_run_id"
RUNTIME_ARTIFACT_AMBIGUOUS = "ambiguous"
RUNTIME_ARTIFACT_UNKNOWN = "unknown"
RUNTIME_ARTIFACT_BLOCKED_SENSITIVE = "blocked_sensitive"

RUNTIME_ARTIFACT_VALID_STATUSES: tuple[str, ...] = (
    RUNTIME_ARTIFACT_ELIGIBLE,
    RUNTIME_ARTIFACT_ABSENT,
    RUNTIME_ARTIFACT_NOT_APPLICABLE,
    RUNTIME_ARTIFACT_STALE,
    RUNTIME_ARTIFACT_MALFORMED,
    RUNTIME_ARTIFACT_MIXED_RUN_ID,
    RUNTIME_ARTIFACT_AMBIGUOUS,
    RUNTIME_ARTIFACT_UNKNOWN,
    RUNTIME_ARTIFACT_BLOCKED_SENSITIVE,
)

RUNTIME_ARTIFACT_FAIL_CLOSED_STATUSES: tuple[str, ...] = (
    RUNTIME_ARTIFACT_STALE,
    RUNTIME_ARTIFACT_MALFORMED,
    RUNTIME_ARTIFACT_MIXED_RUN_ID,
    RUNTIME_ARTIFACT_AMBIGUOUS,
    RUNTIME_ARTIFACT_UNKNOWN,
    RUNTIME_ARTIFACT_BLOCKED_SENSITIVE,
)

RUNTIME_ARTIFACT_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "no_filesystem_reads",
    "no_runtime_artifact_reads",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_discovery",
    "no_runtime_capture",
    "no_package_writing",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

RUNTIME_ARTIFACT_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "unknown_artifact_type",
    "missing_status",
    "unknown_status",
    "stale_artifact",
    "malformed_artifact",
    "mixed_run_id_artifact",
    "ambiguous_artifact",
    "unknown_artifact",
    "blocked_sensitive_artifact",
    "absent_without_absent_reason",
    "not_applicable_without_not_applicable_reason",
    "missing_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
)

RUNTIME_ARTIFACT_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "known_artifact_type_explicit",
    "artifact_status_explicit_and_valid",
    "provenance_present_and_valid",
    "redaction_status_present_and_valid",
    "absent_reason_present_when_absent",
    "not_applicable_reason_present_when_not_applicable",
    "no_filesystem_reads",
    "no_runtime_artifact_reads",
    "no_artifact_copying",
    "no_runtime_capture",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
    "no_paper_live_authority",
)


@dataclass(frozen=True, slots=True)
class RuntimeArtifactAuthority:
    """Static runtime artifact authority vocabulary."""

    name: str = RUNTIME_ARTIFACT_AUTHORITY
    authority_boundary: tuple[str, ...] = RUNTIME_ARTIFACT_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class RuntimeArtifactInstance:
    """Already-loaded metadata describing one runtime artifact instance."""

    canonical_run_id: str
    artifact_type: str
    status: str
    provenance: str
    redaction_status: str
    absent_reason: str | None = None
    not_applicable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeArtifactValidationResult:
    """Result of runtime artifact metadata validation."""

    result_type: str = RUNTIME_ARTIFACT_RESULT
    valid: bool = False


def validate_runtime_artifact(
    input_data: Mapping[str, Any],
) -> list[str]:
    """Validate runtime artifact metadata over already-loaded input.

    Returns a list of failure messages. Empty list means the metadata passes
    all artifact governance checks. No filesystem access is performed.
    """

    failures: list[str] = []

    canonical_run_id = input_data.get("canonical_run_id", "")
    if not canonical_run_id:
        failures.append("missing canonical_run_id")

    artifact_type = input_data.get("artifact_type", "")
    if not artifact_type:
        failures.append("missing artifact_type")
    elif artifact_type not in RUNTIME_ARTIFACT_TYPES:
        failures.append(f"unknown artifact_type: '{artifact_type}'")

    status = input_data.get("status", "")
    if not status:
        failures.append("missing status")
    elif status not in RUNTIME_ARTIFACT_VALID_STATUSES:
        failures.append(f"unknown status: '{status}'")
    elif status in RUNTIME_ARTIFACT_FAIL_CLOSED_STATUSES:
        failures.append(f"fail-closed status: '{status}'")
    elif status == RUNTIME_ARTIFACT_ABSENT:
        absent_reason = input_data.get("absent_reason") or ""
        if not absent_reason:
            failures.append("absent status requires absent_reason")
    elif status == RUNTIME_ARTIFACT_NOT_APPLICABLE:
        not_applicable_reason = input_data.get("not_applicable_reason") or ""
        if not not_applicable_reason:
            failures.append("not_applicable status requires not_applicable_reason")

    provenance = input_data.get("provenance", "")
    if not provenance:
        failures.append("missing provenance")

    redaction_status = input_data.get("redaction_status", "")
    if not redaction_status:
        failures.append("missing redaction_status")
    elif redaction_status not in VALID_REDACTION_STATUS:
        failures.append(f"invalid redaction_status: '{redaction_status}'")

    return failures
