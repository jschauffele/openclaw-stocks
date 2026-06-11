"""Pure in-memory source path ingestion governance contract for replay.

This module validates already-loaded metadata describing a source path
candidate. It does not resolve paths, read files, stat the filesystem,
canonicalize from disk, ingest runtime artifacts, discover artifacts, copy
artifacts, capture runtime output, evaluate or promote strategies, call broker
APIs, authorize execution, approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.source_paths import KNOWN_SOURCE_PATH_FAMILIES
from tools.replay.integrity_validation import VALID_REDACTION_STATUS


SOURCE_PATH_INGESTION_AUTHORITY = "source_path_ingestion_authority_metadata_only"
SOURCE_PATH_INGESTION_RESULT = "source_path_ingestion_result"
GOVERNED_SOURCE_PATH = "governed_source_path"
UNGOVERNED_SOURCE_PATH = "ungoverned_source_path"
FORBIDDEN_ABSOLUTE_PATH_INGESTION = "forbidden_absolute_path_ingestion"
FORBIDDEN_PATH_TRAVERSAL_INGESTION = "forbidden_path_traversal_ingestion"
FORBIDDEN_ARBITRARY_PATH_INGESTION = "forbidden_arbitrary_path_ingestion"

SOURCE_PATH_INGESTION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "no_filesystem_reads",
    "no_path_resolution",
    "no_file_path_reads",
    "no_source_path_discovery",
    "no_artifact_copying",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

SOURCE_PATH_INGESTION_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "missing_source_reference",
    "missing_path_family",
    "missing_path_value",
    "missing_provenance",
    "missing_redaction_status",
    "not_approved",
    "absolute_path_value",
    "path_traversal_marker",
    "unknown_path_family",
    "forbidden_arbitrary_path_ingestion",
    "invalid_redaction_status",
)

SOURCE_PATH_INGESTION_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "approved_source_reference_present",
    "known_path_family_explicit",
    "provenance_present_and_valid",
    "redaction_status_present_and_valid",
    "approved_flag_explicit_and_true",
    "no_absolute_path_ingestion",
    "no_path_traversal",
    "no_arbitrary_path_discovery",
    "no_runtime_log_access",
    "no_artifact_copying",
    "no_runtime_capture",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
    "no_paper_live_authority",
)

_PATH_TRAVERSAL_MARKERS: tuple[str, ...] = ("..", "//", "~")


@dataclass(frozen=True, slots=True)
class SourcePathIngestionAuthority:
    """Static source path ingestion authority vocabulary."""

    name: str = SOURCE_PATH_INGESTION_AUTHORITY
    authority_boundary: tuple[str, ...] = SOURCE_PATH_INGESTION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class SourcePathIngestionInput:
    """Already-loaded path metadata eligible for ingestion governance check."""

    canonical_run_id: str
    source_reference: str
    path_family: str
    path_value: str
    provenance: str
    redaction_status: str
    approved: bool = False


@dataclass(frozen=True, slots=True)
class SourcePathIngestionResult:
    """Result of a source path ingestion governance check."""

    result_type: str = SOURCE_PATH_INGESTION_RESULT
    governed: bool = False


def validate_source_path_ingestion(
    input_data: Mapping[str, Any],
) -> list[str]:
    """Validate source path ingestion governance over already-loaded metadata.

    Returns a list of failure messages. Empty list means the metadata passes
    all ingestion governance checks. No filesystem access is performed.
    """

    failures: list[str] = []

    canonical_run_id = input_data.get("canonical_run_id", "")
    if not canonical_run_id:
        failures.append("missing canonical_run_id")

    source_reference = input_data.get("source_reference", "")
    if not source_reference:
        failures.append("missing source_reference")

    path_family = input_data.get("path_family", "")
    if not path_family:
        failures.append("missing path_family")
    elif path_family not in KNOWN_SOURCE_PATH_FAMILIES:
        failures.append(f"unknown path_family: '{path_family}'")

    path_value = input_data.get("path_value", "")
    if not path_value:
        failures.append("missing path_value")
    else:
        if _is_absolute_path(path_value):
            failures.append(
                f"absolute path value rejected as ungoverned: '{path_value[:32]}'"
            )
        for marker in _PATH_TRAVERSAL_MARKERS:
            if marker in path_value:
                failures.append(
                    f"path traversal marker '{marker}' in path_value"
                )
                break

    provenance = input_data.get("provenance", "")
    if not provenance:
        failures.append("missing provenance")

    redaction_status = input_data.get("redaction_status", "")
    if not redaction_status:
        failures.append("missing redaction_status")
    elif redaction_status not in VALID_REDACTION_STATUS:
        failures.append(f"invalid redaction_status: '{redaction_status}'")

    approved = input_data.get("approved", False)
    if approved is not True:
        failures.append("approved is not True: path ingestion not approved")

    return failures


def _is_absolute_path(value: str) -> bool:
    return value.startswith("/") or (
        len(value) >= 3 and value[1] == ":" and value[2] in ("/", "\\")
    )
