"""Pure in-memory source path family vocabulary for replay prerequisites.

This module defines governed source path family name identity only. It does not
read files, resolve paths, ingest artifacts, discover runtime outputs, copy
artifacts, capture runtime data, evaluate or promote strategies, call broker
APIs, authorize execution, approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_PATH_FAMILY_EVENT_JSONL = "logs/{run_id}.jsonl"
SOURCE_PATH_FAMILY_LAST_RUN_REPORT = "last_run_report.json"
SOURCE_PATH_FAMILY_PER_RUN_REPORT = "run_reports/{run_id}.json"
SOURCE_PATH_FAMILY_ORDER_STATE = "order_state.json"
SOURCE_PATH_FAMILY_OBSERVATIONS = "observations/{run_id}.json"
SOURCE_PATH_FAMILY_RUNTIME_VISIBILITY = "runtime_visibility/{run_id}.json"

KNOWN_SOURCE_PATH_FAMILIES: tuple[str, ...] = (
    SOURCE_PATH_FAMILY_EVENT_JSONL,
    SOURCE_PATH_FAMILY_LAST_RUN_REPORT,
    SOURCE_PATH_FAMILY_PER_RUN_REPORT,
    SOURCE_PATH_FAMILY_ORDER_STATE,
    SOURCE_PATH_FAMILY_OBSERVATIONS,
    SOURCE_PATH_FAMILY_RUNTIME_VISIBILITY,
)

UNKNOWN_SOURCE_PATH = "unknown_source_path"
MISSING_SOURCE_PATH = "missing_source_path"
AMBIGUOUS_SOURCE_PATH = "ambiguous_source_path"
UNRESOLVABLE_SOURCE_PATH = "unresolvable_source_path"
FORBIDDEN_ABSOLUTE_PATH = "forbidden_absolute_path"
FORBIDDEN_ARBITRARY_PATH = "forbidden_arbitrary_path"
FORBIDDEN_PATH_TRAVERSAL = "forbidden_path_traversal"
FORBIDDEN_FILESYSTEM_READ = "forbidden_filesystem_read"

ABSENT_SOURCE_PATH_DECLARATION = "absent_source_path_declaration"
NOT_APPLICABLE_SOURCE_PATH_DECLARATION = "not_applicable_source_path_declaration"

SOURCE_PATH_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    UNKNOWN_SOURCE_PATH,
    MISSING_SOURCE_PATH,
    AMBIGUOUS_SOURCE_PATH,
    UNRESOLVABLE_SOURCE_PATH,
    FORBIDDEN_ABSOLUTE_PATH,
    FORBIDDEN_ARBITRARY_PATH,
    FORBIDDEN_PATH_TRAVERSAL,
    FORBIDDEN_FILESYSTEM_READ,
)

SOURCE_PATH_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "evidence_only",
    "non_authoritative",
    "no_filesystem_reads",
    "no_path_resolution",
    "no_absolute_path_ingestion",
    "no_arbitrary_path_discovery",
    "no_runtime_artifact_reads",
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
class SourcePathVocabulary:
    """Static governed source path family vocabulary."""

    known_path_families: tuple[str, ...] = KNOWN_SOURCE_PATH_FAMILIES
    authority_boundary: tuple[str, ...] = SOURCE_PATH_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class AbsentSourcePathDeclaration:
    """Explicit absent source path declaration vocabulary."""

    name: str = ABSENT_SOURCE_PATH_DECLARATION


@dataclass(frozen=True, slots=True)
class NotApplicableSourcePathDeclaration:
    """Explicit not-applicable source path declaration vocabulary."""

    name: str = NOT_APPLICABLE_SOURCE_PATH_DECLARATION


@dataclass(frozen=True, slots=True)
class SourcePathFailClosedConditions:
    """Static fail-closed condition vocabulary for source paths."""

    conditions: tuple[str, ...] = SOURCE_PATH_FAIL_CLOSED_CONDITIONS
