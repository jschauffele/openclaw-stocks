"""Pure in-memory source reference vocabulary for replay prerequisites.

This module defines governed source reference name identity only. It does not
read files, ingest paths, discover artifacts, copy artifacts, capture runtime
output, evaluate or promote strategies, call broker APIs, authorize execution,
approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_REF_EVENT_JSONL = "event_jsonl"
SOURCE_REF_LAST_RUN_REPORT = "last_run_report"
SOURCE_REF_ORDER_STATE = "order_state"
SOURCE_REF_OBSERVATIONS = "observations"
SOURCE_REF_RUNTIME_VISIBILITY = "runtime_visibility"

KNOWN_SOURCE_REFERENCES: tuple[str, ...] = (
    SOURCE_REF_EVENT_JSONL,
    SOURCE_REF_LAST_RUN_REPORT,
    SOURCE_REF_ORDER_STATE,
    SOURCE_REF_OBSERVATIONS,
    SOURCE_REF_RUNTIME_VISIBILITY,
)

UNKNOWN_SOURCE_REFERENCE = "unknown_source_reference"
MISSING_SOURCE_REFERENCE = "missing_source_reference"
AMBIGUOUS_SOURCE_REFERENCE = "ambiguous_source_reference"
MISSING_RUN_ID = "missing_run_id"
MIXED_RUN_ID = "mixed_run_id"
STALE_ARTIFACT = "stale_artifact"
MISSING_PROVENANCE = "missing_provenance"
MISSING_REDACTION_STATUS = "missing_redaction_status"
INVALID_REDACTION_STATUS = "invalid_redaction_status"
SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"

ABSENT_SOURCE_REFERENCE_DECLARATION = "absent_source_reference_declaration"
NOT_APPLICABLE_SOURCE_REFERENCE_DECLARATION = (
    "not_applicable_source_reference_declaration"
)

SOURCE_REFERENCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    UNKNOWN_SOURCE_REFERENCE,
    MISSING_SOURCE_REFERENCE,
    AMBIGUOUS_SOURCE_REFERENCE,
    MISSING_RUN_ID,
    MIXED_RUN_ID,
    STALE_ARTIFACT,
    MISSING_PROVENANCE,
    MISSING_REDACTION_STATUS,
    INVALID_REDACTION_STATUS,
    SENSITIVE_DATA_EXPOSURE,
)

SOURCE_REFERENCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "evidence_only",
    "non_authoritative",
    "no_filesystem_reads",
    "no_runtime_artifact_reads",
    "no_arbitrary_path_discovery",
    "no_source_path_ingestion",
    "no_artifact_copying",
    "no_runtime_capture",
    "no_package_writing",
    "no_package_finalization",
    "no_evaluation_or_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_paper_trading_approval",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class SourceReferenceVocabulary:
    """Static governed source reference vocabulary."""

    known_references: tuple[str, ...] = KNOWN_SOURCE_REFERENCES
    authority_boundary: tuple[str, ...] = SOURCE_REFERENCE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class AbsentSourceReferenceDeclaration:
    """Explicit absent source reference declaration vocabulary."""

    name: str = ABSENT_SOURCE_REFERENCE_DECLARATION


@dataclass(frozen=True, slots=True)
class NotApplicableSourceReferenceDeclaration:
    """Explicit not-applicable source reference declaration vocabulary."""

    name: str = NOT_APPLICABLE_SOURCE_REFERENCE_DECLARATION


@dataclass(frozen=True, slots=True)
class SourceReferenceFailClosedConditions:
    """Static fail-closed condition vocabulary for source references."""

    conditions: tuple[str, ...] = SOURCE_REFERENCE_FAIL_CLOSED_CONDITIONS
