"""Pure in-memory package completeness validation helper.

This module validates already-built replay package evidence only. It does not
touch the filesystem, create directories, capture runtime data, evaluate or
promote strategies, call broker APIs, authorize execution, or authorize live
trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS
from tools.replay.storage_implementation import STORAGE_LIFECYCLE_STATES


PACKAGE_COMPLETENESS = "package_completeness_in_memory_only"
COMPLETE_REPLAY_PACKAGE = "complete_replay_package_metadata_only"
PACKAGE_COMPLETENESS_AUTHORITY = "package_completeness_authority_metadata_only"
PACKAGE_COMPLETENESS_RESULT = "package_completeness_result"
PACKAGE_COMPLETENESS_VALIDATION = "package_completeness_validation"
COMPLETE_PACKAGE_EVIDENCE = "complete_package_evidence"
COMPLETE_PACKAGE_ELIGIBILITY = "complete_package_eligibility"
COMPLETE_REPLAY_PACKAGE_AUTHORITY = "complete_replay_package_authority_metadata_only"
COMPLETENESS_MANIFEST_CHECK = "completeness_manifest_check"
COMPLETENESS_HASH_CHECK = "completeness_hash_check"
COMPLETENESS_INTEGRITY_CHECK = "completeness_integrity_check"
COMPLETENESS_STORAGE_CHECK = "completeness_storage_check"
COMPLETENESS_PROVENANCE_CHECK = "completeness_provenance_check"
COMPLETENESS_REDACTION_CHECK = "completeness_redaction_check"
COMPLETENESS_SOURCE_REFERENCE_CHECK = "completeness_source_reference_check"

PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "evidence_only",
    "non_authoritative_beyond_package_completeness_metadata",
    "no_actual_filesystem_reads",
    "no_actual_filesystem_writes",
    "no_package_directory_creation",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)

PACKAGE_COMPLETENESS_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "package_identity_present",
    "draft_package_creation_result_present",
    "manifest_present",
    "canonical_bytes_present",
    "hash_records_present",
    "integrity_validation_result_present_and_valid",
    "storage_implementation_result_present",
    "storage_lifecycle_state_acceptable_for_completeness_review",
    "provenance_present_and_valid",
    "redaction_status_present_and_valid",
    "source_references_present_and_known",
    "no_sensitive_data_exposure",
    "no_stale_inputs",
    "no_mixed_run_id_evidence",
    "no_malformed_package_evidence",
)

PACKAGE_COMPLETENESS_FAIL_CLOSED_BOUNDARIES: tuple[str, ...] = (
    "missing_package_identity",
    "missing_package_creation_result",
    "missing_manifest",
    "missing_canonical_bytes",
    "missing_hash_records",
    "missing_integrity_validation_result",
    "failed_integrity_validation_result",
    "missing_storage_implementation_result",
    "failed_storage_implementation_result",
    "missing_storage_lifecycle_state",
    "invalid_storage_lifecycle_state",
    "missing_provenance",
    "malformed_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
    "missing_source_references",
    "unknown_source_references",
    "sensitive_data_exposure",
    "stale_inputs",
    "malformed_inputs",
    "mixed_run_id",
    "runtime_dependent_inputs",
    "evaluation_dependent_inputs",
    "broker_dependent_inputs",
    "actual_filesystem_writer_dependency_before_explicit_writer_authority",
    "package_completeness_as_evaluation_approval",
    "package_completeness_as_execution_permission",
    "package_completeness_as_live_trading_authority",
)

ACCEPTABLE_COMPLETENESS_LIFECYCLE_STATES: tuple[str, ...] = ("finalized",)


@dataclass(frozen=True, slots=True)
class PackageCompleteness:
    """Static package completeness vocabulary."""

    name: str = PACKAGE_COMPLETENESS
    authority_boundary: tuple[str, ...] = PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class CompleteReplayPackage:
    """Static complete replay package metadata vocabulary."""

    name: str = COMPLETE_REPLAY_PACKAGE


@dataclass(frozen=True, slots=True)
class PackageCompletenessAuthority:
    """Static package completeness authority vocabulary."""

    name: str = PACKAGE_COMPLETENESS_AUTHORITY
    authority_boundary: tuple[str, ...] = PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageCompletenessResult:
    """Static package completeness result vocabulary."""

    result_type: str = PACKAGE_COMPLETENESS_RESULT
    authority_boundary: tuple[str, ...] = PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageCompletenessValidation:
    """Static package completeness validation vocabulary."""

    name: str = PACKAGE_COMPLETENESS_VALIDATION


@dataclass(frozen=True, slots=True)
class CompletePackageEvidence:
    """Already-loaded evidence eligible for package completeness review."""

    canonical_run_id: str
    package_identity: Mapping[str, Any]
    package_creation_result: Mapping[str, Any]
    manifest: Mapping[str, Any]
    canonical_bytes: bytes
    hash_records: tuple[Mapping[str, Any], ...]
    integrity_validation_result: Mapping[str, Any]
    storage_implementation_result: Mapping[str, Any]
    storage_lifecycle_state: str
    provenance: str
    redaction_status: str
    source_references: tuple[str, ...]
    known_source_references: tuple[str, ...]
    input_run_ids: tuple[str, ...]
    sensitive_data_status: str = "clear"
    stale_input: bool = False
    malformed_input: bool = False
    runtime_dependent: bool = False
    evaluation_dependent: bool = False
    broker_dependent: bool = False
    filesystem_writer_dependent: bool = False
    attempted_evaluation_approval: bool = False
    attempted_execution_permission: bool = False
    attempted_live_trading_authority: bool = False


@dataclass(frozen=True, slots=True)
class CompletePackageEligibility:
    """Static complete package eligibility vocabulary."""

    prerequisites: tuple[str, ...] = PACKAGE_COMPLETENESS_PREREQUISITES


@dataclass(frozen=True, slots=True)
class CompleteReplayPackageAuthority:
    """Static complete replay package authority metadata vocabulary."""

    name: str = COMPLETE_REPLAY_PACKAGE_AUTHORITY
    authority_boundary: tuple[str, ...] = PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class CompletenessManifestCheck:
    """Static manifest check vocabulary."""

    name: str = COMPLETENESS_MANIFEST_CHECK


@dataclass(frozen=True, slots=True)
class CompletenessHashCheck:
    """Static hash check vocabulary."""

    name: str = COMPLETENESS_HASH_CHECK


@dataclass(frozen=True, slots=True)
class CompletenessIntegrityCheck:
    """Static integrity check vocabulary."""

    name: str = COMPLETENESS_INTEGRITY_CHECK


@dataclass(frozen=True, slots=True)
class CompletenessStorageCheck:
    """Static storage check vocabulary."""

    name: str = COMPLETENESS_STORAGE_CHECK


@dataclass(frozen=True, slots=True)
class CompletenessProvenanceCheck:
    """Static provenance check vocabulary."""

    name: str = COMPLETENESS_PROVENANCE_CHECK


@dataclass(frozen=True, slots=True)
class CompletenessRedactionCheck:
    """Static redaction check vocabulary."""

    name: str = COMPLETENESS_REDACTION_CHECK


@dataclass(frozen=True, slots=True)
class CompletenessSourceReferenceCheck:
    """Static source-reference check vocabulary."""

    name: str = COMPLETENESS_SOURCE_REFERENCE_CHECK


def build_package_completeness_result(
    evidence: CompletePackageEvidence | Mapping[str, Any],
) -> dict[str, Any]:
    """Build package completeness metadata from already-loaded evidence."""

    normalized = _normalize_evidence(evidence)
    _validate_evidence(normalized)
    return {
        "result_type": PACKAGE_COMPLETENESS_RESULT,
        "validation_type": PACKAGE_COMPLETENESS_VALIDATION,
        "canonical_run_id": normalized.canonical_run_id,
        "package_identity": dict(normalized.package_identity),
        "package_creation_result": dict(normalized.package_creation_result),
        "manifest": dict(normalized.manifest),
        "canonical_bytes": normalized.canonical_bytes,
        "hash_records": tuple(dict(record) for record in normalized.hash_records),
        "integrity_validation_result": dict(normalized.integrity_validation_result),
        "storage_implementation_result": dict(normalized.storage_implementation_result),
        "storage_lifecycle_state": normalized.storage_lifecycle_state,
        "provenance": normalized.provenance,
        "redaction_status": normalized.redaction_status,
        "source_references": tuple(normalized.source_references),
        "package_completeness": True,
        "package_completeness_authority": True,
        "complete_replay_package_authority": True,
        "evidence_only": True,
        "non_authoritative_beyond_package_completeness_metadata": True,
        "actual_filesystem_reads": False,
        "actual_filesystem_writes": False,
        "package_directory_creation": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "live_trading_authority": False,
        "prerequisites": PACKAGE_COMPLETENESS_PREREQUISITES,
        "fail_closed_boundaries": PACKAGE_COMPLETENESS_FAIL_CLOSED_BOUNDARIES,
        "authority_boundary": PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY,
    }


def validate_package_completeness(
    evidence: CompletePackageEvidence | Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for package completeness validation over in-memory evidence."""

    return build_package_completeness_result(evidence)


def assert_package_complete(
    evidence: CompletePackageEvidence | Mapping[str, Any],
) -> dict[str, Any]:
    """Return package completeness metadata or fail closed."""

    return build_package_completeness_result(evidence)


def _normalize_evidence(
    evidence: CompletePackageEvidence | Mapping[str, Any],
) -> CompletePackageEvidence:
    if isinstance(evidence, CompletePackageEvidence):
        return evidence
    if not isinstance(evidence, Mapping):
        raise TypeError("package completeness evidence must be already-loaded metadata")
    return CompletePackageEvidence(**evidence)


def _validate_evidence(evidence: CompletePackageEvidence) -> None:
    _reject_forbidden_dependencies(evidence)
    _validate_run_identity(evidence)
    _validate_package_creation(evidence)
    _validate_manifest(evidence)
    _validate_canonical_bytes(evidence)
    _validate_hash_records(evidence)
    _validate_integrity(evidence)
    _validate_storage(evidence)
    _validate_metadata(evidence)


def _reject_forbidden_dependencies(evidence: CompletePackageEvidence) -> None:
    if evidence.malformed_input:
        raise ValueError("malformed package evidence")
    if evidence.stale_input:
        raise ValueError("stale package completeness input")
    if evidence.runtime_dependent:
        raise ValueError("runtime-dependent package completeness input")
    if evidence.evaluation_dependent:
        raise ValueError("evaluation-dependent package completeness input")
    if evidence.broker_dependent:
        raise ValueError("broker-dependent package completeness input")
    if evidence.filesystem_writer_dependent:
        raise ValueError("actual filesystem writer dependency before writer authority")
    if evidence.attempted_evaluation_approval:
        raise ValueError("package completeness is not evaluation approval")
    if evidence.attempted_execution_permission:
        raise ValueError("package completeness is not execution permission")
    if evidence.attempted_live_trading_authority:
        raise ValueError("package completeness is not live trading authority")


def _validate_run_identity(evidence: CompletePackageEvidence) -> None:
    if not evidence.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not isinstance(evidence.package_identity, Mapping):
        raise ValueError("package identity is required")
    if not evidence.package_identity.get("package_id"):
        raise ValueError("package identity is required")
    if evidence.package_identity.get("canonical_run_id") != evidence.canonical_run_id:
        raise ValueError("mixed run_id package evidence")
    for run_id in evidence.input_run_ids:
        if run_id != evidence.canonical_run_id:
            raise ValueError("mixed run_id package evidence")


def _validate_package_creation(evidence: CompletePackageEvidence) -> None:
    result = evidence.package_creation_result
    if not isinstance(result, Mapping) or not result:
        raise ValueError("package creation result is required")
    if result.get("evidence_only") is not True:
        raise ValueError("package creation result is required")
    if result.get("package_completeness") is not False:
        raise ValueError("draft package creation is not package completeness")
    if result.get("canonical_run_id") != evidence.canonical_run_id:
        raise ValueError("mixed run_id package evidence")
    result_identity = result.get("package_identity")
    if not isinstance(result_identity, Mapping):
        raise ValueError("package identity is required")
    if result_identity.get("package_id") != evidence.package_identity.get("package_id"):
        raise ValueError("malformed package evidence")


def _validate_manifest(evidence: CompletePackageEvidence) -> None:
    if not isinstance(evidence.manifest, Mapping) or not evidence.manifest:
        raise ValueError("manifest is required")
    if evidence.manifest.get("canonical_run_id") != evidence.canonical_run_id:
        raise ValueError("mixed run_id package evidence")


def _validate_canonical_bytes(evidence: CompletePackageEvidence) -> None:
    if not isinstance(evidence.canonical_bytes, bytes) or not evidence.canonical_bytes:
        raise ValueError("canonical bytes are required")


def _validate_hash_records(evidence: CompletePackageEvidence) -> None:
    if not evidence.hash_records:
        raise ValueError("hash records are required")
    for hash_record in evidence.hash_records:
        if not isinstance(hash_record, Mapping):
            raise TypeError("hash records must be already-loaded metadata")
        if not hash_record.get("digest"):
            raise ValueError("hash records are required")
        metadata = hash_record.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("malformed provenance")
        if metadata.get("canonical_run_id") != evidence.canonical_run_id:
            raise ValueError("mixed run_id package evidence")


def _validate_integrity(evidence: CompletePackageEvidence) -> None:
    result = evidence.integrity_validation_result
    if not isinstance(result, Mapping) or not result:
        raise ValueError("integrity validation result is required")
    if result.get("integrity_status") != "valid":
        raise ValueError("integrity validation result must be valid")
    if result.get("hash_match") is not True:
        raise ValueError("integrity validation result must be valid")


def _validate_storage(evidence: CompletePackageEvidence) -> None:
    result = evidence.storage_implementation_result
    if not isinstance(result, Mapping) or not result:
        raise ValueError("storage implementation result is required")
    if result.get("evidence_only") is not True:
        raise ValueError("storage implementation result must be valid")
    if result.get("actual_filesystem_writes") is not False:
        raise ValueError("storage implementation result must be metadata-only")
    if result.get("package_completeness") is not False:
        raise ValueError("storage implementation is not package completeness")
    if result.get("canonical_run_id") != evidence.canonical_run_id:
        raise ValueError("mixed run_id package evidence")
    if not evidence.storage_lifecycle_state:
        raise ValueError("storage lifecycle state is required")
    if evidence.storage_lifecycle_state not in STORAGE_LIFECYCLE_STATES:
        raise ValueError("unknown lifecycle status")
    if evidence.storage_lifecycle_state not in ACCEPTABLE_COMPLETENESS_LIFECYCLE_STATES:
        raise ValueError("storage lifecycle state is not complete")
    if result.get("lifecycle_status") != evidence.storage_lifecycle_state:
        raise ValueError("malformed package evidence")


def _validate_metadata(evidence: CompletePackageEvidence) -> None:
    if not isinstance(evidence.provenance, str):
        raise ValueError("malformed provenance")
    if not evidence.provenance:
        raise ValueError("missing provenance")
    if not evidence.redaction_status:
        raise ValueError("missing redaction status")
    if evidence.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if evidence.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")
    if not evidence.source_references:
        raise ValueError("unknown source references")
    known_references = set(evidence.known_source_references)
    if not known_references:
        raise ValueError("unknown source references")
    for source_reference in evidence.source_references:
        if source_reference not in known_references:
            raise ValueError("unknown source references")
