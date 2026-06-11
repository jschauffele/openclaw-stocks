"""Pure in-memory runtime capture coordination contract for replay.

This module validates whether already-loaded metadata satisfies prerequisites
for a future capture implementation. It does not execute capture, read files,
ingest paths, discover artifacts, copy artifacts, write packages, or perform
filesystem-backed persistence. It does not capture runtime output, evaluate or
promote strategies, call broker APIs, authorize execution, approve paper
trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


RUNTIME_CAPTURE_AUTHORITY = "runtime_capture_authority_metadata_only"
RUNTIME_CAPTURE_RESULT = "runtime_capture_result"
CAPTURE_ELIGIBILITY_RESULT = "capture_eligibility_result"
CAPTURE_PREREQUISITE_RESULT = "capture_prerequisite_result"

_CAPTURE_ELIGIBLE_COMPLETION_STATUSES: tuple[str, ...] = ("ok", "blocked")
_ALL_KNOWN_COMPLETION_STATUSES: tuple[str, ...] = ("ok", "blocked", "error")

RUNTIME_CAPTURE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "no_filesystem_reads",
    "no_runtime_artifact_reads",
    "no_file_path_ingestion",
    "no_source_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_discovery",
    "no_package_writing",
    "no_storage_finalization",
    "no_runtime_capture_execution",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

RUNTIME_CAPTURE_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "terminal_completion_present",
    "terminal_completion_status_capture_eligible",
    "run_id_aligned",
    "source_artifact_authority_valid",
    "runtime_artifact_discovery_valid",
    "source_path_ingestion_valid",
    "provenance_present",
    "redaction_status_present",
    "package_creation_authority_present",
    "storage_finalization_authority_present",
    "no_filesystem_reads",
    "no_runtime_artifact_reads",
    "no_artifact_copying",
    "no_runtime_capture_execution",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
    "no_paper_live_authority",
)

RUNTIME_CAPTURE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "terminal_completion_not_present",
    "terminal_completion_status_error_not_capture_eligible",
    "terminal_completion_status_unknown",
    "run_id_not_aligned",
    "source_artifact_authority_invalid",
    "runtime_artifact_discovery_invalid",
    "source_path_ingestion_invalid",
    "provenance_missing",
    "redaction_status_missing",
    "package_creation_authority_missing",
    "storage_finalization_authority_missing",
    "missing_terminal_completion",
    "mixed_run_id",
    "stale_artifact",
    "malformed_artifact",
    "missing_absent_or_not_applicable_declaration",
    "missing_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
    "sensitive_data_exposure",
)


@dataclass(frozen=True, slots=True)
class RuntimeCaptureAuthority:
    """Static runtime capture authority vocabulary."""

    name: str = RUNTIME_CAPTURE_AUTHORITY
    authority_boundary: tuple[str, ...] = RUNTIME_CAPTURE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class RuntimeCaptureInput:
    """Already-loaded metadata eligible for capture prerequisite validation."""

    canonical_run_id: str
    terminal_completion_present: bool
    terminal_completion_status: str
    run_id_aligned: bool
    source_artifact_authority_valid: bool
    runtime_artifact_discovery_valid: bool
    source_path_ingestion_valid: bool
    provenance_present: bool
    redaction_status_present: bool
    package_creation_authority_present: bool
    storage_finalization_authority_present: bool


@dataclass(frozen=True, slots=True)
class RuntimeCapturePrerequisiteCheck:
    """Result of a runtime capture prerequisite validation."""

    result_type: str = CAPTURE_PREREQUISITE_RESULT
    prerequisites_met: bool = False


@dataclass(frozen=True, slots=True)
class RuntimeCaptureEligibilityResult:
    """Result of a runtime capture eligibility determination."""

    result_type: str = CAPTURE_ELIGIBILITY_RESULT
    eligible: bool = False


def validate_runtime_capture_prerequisites(
    input_data: Mapping[str, Any],
) -> list[str]:
    """Validate runtime capture prerequisites over already-loaded metadata.

    Returns a list of failure messages. Empty list means all prerequisites
    are satisfied. No filesystem access is performed. No capture is executed.
    """

    failures: list[str] = []

    canonical_run_id = input_data.get("canonical_run_id", "")
    if not canonical_run_id:
        failures.append("missing canonical_run_id")

    terminal_completion_present = input_data.get("terminal_completion_present", False)
    if terminal_completion_present is not True:
        failures.append("terminal_completion_present is not True")

    terminal_completion_status = input_data.get("terminal_completion_status", "")
    if not terminal_completion_status:
        failures.append("missing terminal_completion_status")
    elif terminal_completion_status not in _ALL_KNOWN_COMPLETION_STATUSES:
        failures.append(
            f"unknown terminal_completion_status: '{terminal_completion_status}'"
        )
    elif terminal_completion_status == "error":
        failures.append(
            "terminal_completion_status 'error' is not capture-eligible"
        )

    run_id_aligned = input_data.get("run_id_aligned", False)
    if run_id_aligned is not True:
        failures.append("run_id_aligned is not True")

    source_artifact_authority_valid = input_data.get(
        "source_artifact_authority_valid", False
    )
    if source_artifact_authority_valid is not True:
        failures.append("source_artifact_authority_valid is not True")

    runtime_artifact_discovery_valid = input_data.get(
        "runtime_artifact_discovery_valid", False
    )
    if runtime_artifact_discovery_valid is not True:
        failures.append("runtime_artifact_discovery_valid is not True")

    source_path_ingestion_valid = input_data.get("source_path_ingestion_valid", False)
    if source_path_ingestion_valid is not True:
        failures.append("source_path_ingestion_valid is not True")

    provenance_present = input_data.get("provenance_present", False)
    if provenance_present is not True:
        failures.append("provenance_present is not True")

    redaction_status_present = input_data.get("redaction_status_present", False)
    if redaction_status_present is not True:
        failures.append("redaction_status_present is not True")

    package_creation_authority_present = input_data.get(
        "package_creation_authority_present", False
    )
    if package_creation_authority_present is not True:
        failures.append("package_creation_authority_present is not True")

    storage_finalization_authority_present = input_data.get(
        "storage_finalization_authority_present", False
    )
    if storage_finalization_authority_present is not True:
        failures.append("storage_finalization_authority_present is not True")

    return failures
