"""Pure in-memory storage lifecycle metadata helper.

This module builds storage lifecycle and finalization metadata from
already-built package creation and filesystem/storage authority records only.
It does not touch the filesystem, create directories, read files, write files,
assert package completeness, capture runtime data, evaluate strategies, or
authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


STORAGE_IMPLEMENTATION = "storage_implementation_metadata_only"
STORAGE_LIFECYCLE_IMPLEMENTATION = "storage_lifecycle_metadata_only"
DRAFT_STORAGE_RECORD = "draft_storage_record"
FINALIZED_STORAGE_RECORD = "finalized_storage_record"
STORAGE_FINALIZATION_RESULT = "storage_finalization_result"
IMMUTABILITY_MARKER = "immutability_marker"
LINEAGE_REFERENCE = "lineage_reference"
INVALIDATION_REFERENCE = "invalidation_reference"
SUPERSESSION_REFERENCE = "supersession_reference"
NO_OVERWRITE_ENFORCEMENT_VOCABULARY = "no_overwrite_enforcement_vocabulary"
STORAGE_WRITER_METADATA_INPUT = "storage_writer_metadata_input"
STORAGE_WRITER_METADATA_RESULT = "storage_writer_metadata_result"

STORAGE_LIFECYCLE_STATES: tuple[str, ...] = (
    "draft",
    "finalized",
    "invalidated",
    "superseded",
)

STORAGE_IMPLEMENTATION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "evidence_only",
    "non_authoritative",
    "no_actual_filesystem_reads",
    "no_actual_filesystem_writes",
    "no_package_directory_creation",
    "no_package_completeness",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class StorageImplementation:
    """Static storage implementation metadata vocabulary."""

    name: str = STORAGE_IMPLEMENTATION
    authority_boundary: tuple[str, ...] = STORAGE_IMPLEMENTATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class StorageLifecycleImplementation:
    """Static lifecycle metadata vocabulary."""

    states: tuple[str, ...] = STORAGE_LIFECYCLE_STATES


@dataclass(frozen=True, slots=True)
class DraftStorageRecord:
    """Draft storage metadata vocabulary."""

    lifecycle_status: str = "draft"


@dataclass(frozen=True, slots=True)
class FinalizedStorageRecord:
    """Finalized storage metadata vocabulary."""

    lifecycle_status: str = "finalized"


@dataclass(frozen=True, slots=True)
class StorageFinalizationResult:
    """Storage finalization result metadata vocabulary."""

    result_type: str = STORAGE_FINALIZATION_RESULT


@dataclass(frozen=True, slots=True)
class ImmutabilityMarker:
    """Immutability marker metadata vocabulary."""

    name: str = IMMUTABILITY_MARKER


@dataclass(frozen=True, slots=True)
class LineageReference:
    """Lineage reference metadata vocabulary."""

    name: str = LINEAGE_REFERENCE


@dataclass(frozen=True, slots=True)
class InvalidationReference:
    """Invalidation reference metadata vocabulary."""

    name: str = INVALIDATION_REFERENCE


@dataclass(frozen=True, slots=True)
class SupersessionReference:
    """Supersession reference metadata vocabulary."""

    name: str = SUPERSESSION_REFERENCE


@dataclass(frozen=True, slots=True)
class NoOverwriteEnforcementVocabulary:
    """No-overwrite rule metadata vocabulary."""

    name: str = NO_OVERWRITE_ENFORCEMENT_VOCABULARY


@dataclass(frozen=True, slots=True)
class StorageWriterMetadataInput:
    """Already-loaded metadata eligible for storage lifecycle records."""

    canonical_run_id: str
    package_creation_result: Mapping[str, Any]
    filesystem_storage_authority_result: Mapping[str, Any]
    package_identity: Mapping[str, Any]
    storage_root: str
    package_path: str
    package_directory: str
    lifecycle_status: str
    provenance: str
    redaction_status: str
    source_reference: str
    known_source_references: tuple[str, ...]
    input_run_ids: tuple[str, ...]
    package_completeness_authority: bool
    attempted_complete_replay_package_authority: bool = False
    overwrite_attempt: bool = False
    symlink_status: str = "not_symlink"
    repo_relative: bool = True
    sensitive_data_status: str = "clear"
    runtime_dependent: bool = False
    evaluation_dependent: bool = False
    broker_dependent: bool = False


@dataclass(frozen=True, slots=True)
class StorageWriterMetadataResult:
    """Storage writer metadata result vocabulary."""

    result_type: str = STORAGE_WRITER_METADATA_RESULT
    authority_boundary: tuple[str, ...] = STORAGE_IMPLEMENTATION_AUTHORITY_BOUNDARY


def build_draft_storage_record(
    storage_input: StorageWriterMetadataInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build a draft storage metadata record in memory."""

    normalized = _normalize_storage_input(storage_input)
    if normalized.lifecycle_status != "draft":
        raise ValueError("draft storage records require draft lifecycle status")
    return _build_storage_record(DRAFT_STORAGE_RECORD, normalized)


def build_finalized_storage_record(
    storage_input: StorageWriterMetadataInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build a finalized storage metadata record in memory."""

    normalized = _normalize_storage_input(storage_input)
    if normalized.lifecycle_status != "finalized":
        raise ValueError("finalized storage records require finalized lifecycle status")
    return _build_storage_record(FINALIZED_STORAGE_RECORD, normalized)


def build_storage_finalization_result(
    storage_input: StorageWriterMetadataInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build a non-authoritative finalization result metadata record."""

    return build_finalized_storage_record(storage_input)


def invalidate_storage_record(
    storage_input: StorageWriterMetadataInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build invalidation lineage metadata in memory."""

    normalized = _normalize_storage_input(storage_input)
    if normalized.lifecycle_status != "invalidated":
        raise ValueError("invalidation records require invalidated lifecycle status")
    return _build_storage_record(INVALIDATION_REFERENCE, normalized)


def supersede_storage_record(
    storage_input: StorageWriterMetadataInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build supersession lineage metadata in memory."""

    normalized = _normalize_storage_input(storage_input)
    if normalized.lifecycle_status != "superseded":
        raise ValueError("supersession records require superseded lifecycle status")
    return _build_storage_record(SUPERSESSION_REFERENCE, normalized)


def _build_storage_record(
    record_type: str,
    storage_input: StorageWriterMetadataInput,
) -> dict[str, Any]:
    _validate_storage_input(storage_input)
    return {
        "record_type": record_type,
        "result_type": STORAGE_WRITER_METADATA_RESULT,
        "canonical_run_id": storage_input.canonical_run_id,
        "package_identity": dict(storage_input.package_identity),
        "storage_root": storage_input.storage_root,
        "package_path": storage_input.package_path,
        "package_directory": storage_input.package_directory,
        "lifecycle_status": storage_input.lifecycle_status,
        "immutability_marker": IMMUTABILITY_MARKER,
        "lineage_reference": LINEAGE_REFERENCE,
        "no_overwrite_rule": NO_OVERWRITE_ENFORCEMENT_VOCABULARY,
        "package_creation_result": dict(storage_input.package_creation_result),
        "filesystem_storage_authority_result": dict(
            storage_input.filesystem_storage_authority_result
        ),
        "provenance": storage_input.provenance,
        "redaction_status": storage_input.redaction_status,
        "source_reference": storage_input.source_reference,
        "append_only_lineage": True,
        "correction_lineage": True,
        "invalidation_lineage": record_type == INVALIDATION_REFERENCE,
        "supersession_lineage": record_type == SUPERSESSION_REFERENCE,
        "derived_reports_distinct_from_immutable_evidence": True,
        "evidence_only": True,
        "non_authoritative": True,
        "actual_filesystem_reads": False,
        "actual_filesystem_writes": False,
        "package_directory_creation": False,
        "package_completeness": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "live_trading_authority": False,
        "authority_boundary": STORAGE_IMPLEMENTATION_AUTHORITY_BOUNDARY,
    }


def _normalize_storage_input(
    storage_input: StorageWriterMetadataInput | Mapping[str, Any],
) -> StorageWriterMetadataInput:
    if isinstance(storage_input, StorageWriterMetadataInput):
        return storage_input
    if not isinstance(storage_input, Mapping):
        raise TypeError("storage implementation input must be already-loaded metadata")
    return StorageWriterMetadataInput(**storage_input)


def _validate_storage_input(storage_input: StorageWriterMetadataInput) -> None:
    _validate_package_and_authority_inputs(storage_input)
    _validate_storage_identity(storage_input)
    _validate_path_identity(storage_input)
    _validate_metadata(storage_input)
    _reject_downstream_dependencies(storage_input)


def _validate_package_and_authority_inputs(
    storage_input: StorageWriterMetadataInput,
) -> None:
    if not isinstance(storage_input.filesystem_storage_authority_result, Mapping):
        raise ValueError("filesystem/storage authority result is required")
    authority_result = storage_input.filesystem_storage_authority_result
    if authority_result.get("evidence_only") is not True:
        raise ValueError("filesystem/storage authority result must be valid")
    if authority_result.get("actual_filesystem_writes") is not False:
        raise ValueError("filesystem/storage authority result must be metadata-only")
    if not isinstance(storage_input.package_creation_result, Mapping):
        raise ValueError("package creation result is required")
    package_creation_result = storage_input.package_creation_result
    if package_creation_result.get("evidence_only") is not True:
        raise ValueError("package creation result is required")
    if package_creation_result.get("package_completeness") is not False:
        raise ValueError("package creation result must not be package completeness")
    if not isinstance(storage_input.package_identity, Mapping):
        raise ValueError("package identity is required")
    if not storage_input.package_identity.get("package_id"):
        raise ValueError("package identity is required")
    if storage_input.package_completeness_authority is not False:
        raise ValueError("package completeness authority remains separate")
    if storage_input.attempted_complete_replay_package_authority:
        raise ValueError("storage output cannot become complete replay package authority")


def _validate_storage_identity(storage_input: StorageWriterMetadataInput) -> None:
    if not storage_input.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not storage_input.storage_root:
        raise ValueError("storage root is required")
    if not storage_input.package_path:
        raise ValueError("package path is required")
    if not storage_input.package_directory:
        raise ValueError("package directory is required")
    authority_result = storage_input.filesystem_storage_authority_result
    if storage_input.storage_root != authority_result.get("storage_root"):
        raise ValueError("unknown or unapproved storage root")
    if storage_input.package_path != authority_result.get("package_path"):
        raise ValueError("unknown or unapproved package path")
    if storage_input.package_directory != authority_result.get("package_directory"):
        raise ValueError("unknown or unapproved package directory")
    if storage_input.lifecycle_status not in STORAGE_LIFECYCLE_STATES:
        raise ValueError("unknown lifecycle status")
    for run_id in storage_input.input_run_ids:
        if run_id != storage_input.canonical_run_id:
            raise ValueError("mixed run_id storage input")


def _validate_path_identity(storage_input: StorageWriterMetadataInput) -> None:
    for value in (
        storage_input.storage_root,
        storage_input.package_path,
        storage_input.package_directory,
    ):
        if _has_absolute_path_shape(value):
            raise ValueError("absolute path injection")
        if _has_path_traversal_shape(value):
            raise ValueError("path traversal")
    if storage_input.symlink_status != "not_symlink":
        raise ValueError("symlink ambiguity")
    if storage_input.repo_relative is not True:
        raise ValueError("non-repo path ambiguity")
    if storage_input.overwrite_attempt:
        raise ValueError("attempted overwrite")


def _validate_metadata(storage_input: StorageWriterMetadataInput) -> None:
    if not isinstance(storage_input.provenance, str):
        raise ValueError("malformed provenance")
    if not storage_input.provenance:
        raise ValueError("missing provenance")
    if not storage_input.redaction_status:
        raise ValueError("missing redaction status")
    if storage_input.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if storage_input.source_reference not in storage_input.known_source_references:
        raise ValueError("unknown source references")
    if storage_input.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")


def _reject_downstream_dependencies(storage_input: StorageWriterMetadataInput) -> None:
    if storage_input.runtime_dependent:
        raise ValueError("runtime-dependent storage input")
    if storage_input.evaluation_dependent:
        raise ValueError("evaluation-dependent storage input")
    if storage_input.broker_dependent:
        raise ValueError("broker-dependent storage input")


def _has_absolute_path_shape(value: str) -> bool:
    return (
        value.startswith("/")
        or value.startswith("~")
        or value.startswith("\\")
        or "://" in value
    )


def _has_path_traversal_shape(value: str) -> bool:
    parts = value.replace("\\", "/").split("/")
    return ".." in parts
