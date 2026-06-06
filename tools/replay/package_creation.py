"""Pure in-memory draft package creation helper for replay prerequisites.

This module assembles draft package evidence from already-loaded governed
inputs only. It does not assert package completeness, create finalized
packages, create directories, touch the filesystem, store artifacts, capture
runtime data, evaluate strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


PACKAGE_CREATION = "draft_package_creation_in_memory_only"
PACKAGE_BUILDER_TYPES = "draft_package_builder_types"
PACKAGE_CREATION_MODULE = "package_creation"
DRAFT_REPLAY_PACKAGE = "draft_replay_package"
DRAFT_PACKAGE_ASSEMBLY = "draft_package_assembly"
PACKAGE_CREATION_INPUT = "package_creation_input"
PACKAGE_CREATION_RESULT = "package_creation_result"

PACKAGE_CREATION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "draft_only",
    "in_memory_only",
    "evidence_only",
    "non_authoritative",
    "no_package_completeness",
    "no_finalized_storage",
    "no_filesystem_reads",
    "no_filesystem_writes",
    "no_package_directories",
    "no_storage_finalization_immutability",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class PackageBuilderInput:
    """Already-loaded inputs eligible for draft package assembly."""

    canonical_run_id: str
    package_identity: Mapping[str, Any]
    manifest: Mapping[str, Any]
    canonical_bytes: bytes
    hash_records: tuple[Mapping[str, Any], ...]
    integrity_validation_result: Mapping[str, Any]
    provenance: str
    redaction_status: str
    source_references: tuple[str, ...]
    known_source_references: tuple[str, ...]
    input_run_ids: tuple[str, ...]
    sensitive_data_status: str = "clear"
    stale_input: bool = False
    runtime_dependent: bool = False
    filesystem_dependent: bool = False
    evaluation_dependent: bool = False
    malformed_input: bool = False


@dataclass(frozen=True, slots=True)
class PackageCreationInput(PackageBuilderInput):
    """Package creation input vocabulary."""


@dataclass(frozen=True, slots=True)
class DraftReplayPackage:
    """Non-authoritative draft package output vocabulary."""

    package_type: str = DRAFT_REPLAY_PACKAGE
    lifecycle_status: str = "draft"
    authority_boundary: tuple[str, ...] = PACKAGE_CREATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class DraftPackageAssembly:
    """Draft-only assembly vocabulary."""

    assembly_type: str = DRAFT_PACKAGE_ASSEMBLY


@dataclass(frozen=True, slots=True)
class PackageCreation:
    """Static package creation vocabulary."""

    name: str = PACKAGE_CREATION
    authority_boundary: tuple[str, ...] = PACKAGE_CREATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageBuilder:
    """Static package builder vocabulary."""

    name: str = PACKAGE_BUILDER_TYPES
    input_model: str = PACKAGE_CREATION_INPUT
    output_model: str = DRAFT_REPLAY_PACKAGE


@dataclass(frozen=True, slots=True)
class PackageBuilderOutput:
    """Draft package builder output vocabulary."""

    output_model: str = DRAFT_REPLAY_PACKAGE
    authority_boundary: tuple[str, ...] = PACKAGE_CREATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageCreationResult:
    """Package creation result vocabulary."""

    result_type: str = PACKAGE_CREATION_RESULT
    authority_boundary: tuple[str, ...] = PACKAGE_CREATION_AUTHORITY_BOUNDARY


def build_draft_package(
    package_input: PackageBuilderInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build a non-authoritative draft package from already-loaded inputs."""

    normalized = _normalize_package_input(package_input)
    _validate_package_input(normalized)
    return {
        "package_type": DRAFT_REPLAY_PACKAGE,
        "assembly_type": DRAFT_PACKAGE_ASSEMBLY,
        "lifecycle_status": "draft",
        "canonical_run_id": normalized.canonical_run_id,
        "package_identity": dict(normalized.package_identity),
        "manifest": dict(normalized.manifest),
        "canonical_bytes": normalized.canonical_bytes,
        "hash_records": tuple(dict(record) for record in normalized.hash_records),
        "integrity_validation_result": dict(normalized.integrity_validation_result),
        "provenance": normalized.provenance,
        "redaction_status": normalized.redaction_status,
        "source_references": tuple(normalized.source_references),
        "evidence_only": True,
        "non_authoritative": True,
        "package_completeness": False,
        "finalized_storage": False,
        "filesystem_reads": False,
        "filesystem_writes": False,
        "package_directories": False,
        "storage_finalization_immutability": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "live_trading_authority": False,
        "authority_boundary": PACKAGE_CREATION_AUTHORITY_BOUNDARY,
    }


def assemble_draft_package(
    package_input: PackageBuilderInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for draft package assembly."""

    return build_draft_package(package_input)


def create_draft_package(
    package_input: PackageBuilderInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for draft-only in-memory package creation."""

    return build_draft_package(package_input)


def _normalize_package_input(
    package_input: PackageBuilderInput | Mapping[str, Any],
) -> PackageBuilderInput:
    if isinstance(package_input, PackageBuilderInput):
        return package_input
    if not isinstance(package_input, Mapping):
        raise TypeError("package creation input must be already-loaded metadata")
    return PackageBuilderInput(**package_input)


def _validate_package_input(package_input: PackageBuilderInput) -> None:
    if package_input.malformed_input:
        raise ValueError("malformed package creation input")
    if not package_input.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not isinstance(package_input.package_identity, Mapping):
        raise TypeError("package identity is required")
    if not package_input.package_identity.get("package_id"):
        raise ValueError("package identity is required")
    if package_input.package_identity.get("canonical_run_id") != (
        package_input.canonical_run_id
    ):
        raise ValueError("mixed run_id package input")
    if not isinstance(package_input.manifest, Mapping) or not package_input.manifest:
        raise ValueError("manifest is required")
    if package_input.manifest.get("canonical_run_id") != package_input.canonical_run_id:
        raise ValueError("mixed run_id package input")
    if not isinstance(package_input.canonical_bytes, bytes) or not (
        package_input.canonical_bytes
    ):
        raise ValueError("canonical bytes are required")
    if not package_input.hash_records:
        raise ValueError("hash records are required")
    if not isinstance(package_input.integrity_validation_result, Mapping):
        raise ValueError("integrity validation result is required")
    if package_input.integrity_validation_result.get("integrity_status") != "valid":
        raise ValueError("integrity validation result must be valid")
    if package_input.integrity_validation_result.get("hash_match") is not True:
        raise ValueError("integrity validation result must be valid")
    _validate_metadata(package_input)
    _validate_hash_records(package_input)
    _reject_forbidden_dependencies(package_input)


def _validate_metadata(package_input: PackageBuilderInput) -> None:
    if not isinstance(package_input.provenance, str):
        raise ValueError("malformed provenance")
    if not package_input.provenance:
        raise ValueError("missing provenance")
    if not package_input.redaction_status:
        raise ValueError("missing redaction status")
    if package_input.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if package_input.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")
    if not package_input.source_references:
        raise ValueError("unknown source references")
    known_references = set(package_input.known_source_references)
    if not known_references:
        raise ValueError("unknown source references")
    for source_reference in package_input.source_references:
        if source_reference not in known_references:
            raise ValueError("unknown source references")
    for run_id in package_input.input_run_ids:
        if run_id != package_input.canonical_run_id:
            raise ValueError("mixed run_id package input")


def _validate_hash_records(package_input: PackageBuilderInput) -> None:
    for hash_record in package_input.hash_records:
        if not isinstance(hash_record, Mapping):
            raise TypeError("hash records must be already-loaded metadata")
        if not hash_record.get("digest"):
            raise ValueError("hash records are required")
        metadata = hash_record.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("malformed provenance")
        if metadata.get("canonical_run_id") != package_input.canonical_run_id:
            raise ValueError("mixed run_id package input")


def _reject_forbidden_dependencies(package_input: PackageBuilderInput) -> None:
    if package_input.stale_input:
        raise ValueError("stale package creation input")
    if package_input.runtime_dependent:
        raise ValueError("runtime-dependent package creation input")
    if package_input.filesystem_dependent:
        raise ValueError("filesystem-dependent package creation input")
    if package_input.evaluation_dependent:
        raise ValueError("evaluation-dependent package creation input")
