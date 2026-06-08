"""Pure in-memory draft manifest builder for replay prerequisites.

This module builds draft manifest dictionaries from already-loaded, governed
metadata only. It does not create packages, create directories, touch the
filesystem, compute hashes, validate integrity, store artifacts, capture
runtime data, evaluate strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from tools.replay import hashing
from tools.replay import integrity
from tools.replay import package_layout as package_layout_rules
from tools.replay.manifest_schema import (
    MANIFEST_LIFECYCLE_STATUS,
    MANIFEST_REQUIRED_FIELDS,
    MANIFEST_SCHEMA_VERSION,
)


MANIFEST_GENERATION = "draft_manifest_generation_in_memory_only"
MANIFEST_BUILDER = "draft_manifest_builder_in_memory_only"
DRAFT_MANIFEST = "draft_manifest"
MANIFEST_INPUT = "manifest_input"
MANIFEST_FIELD_ELIGIBILITY = "required_optional_future_field_eligibility"
MANIFEST_PROVENANCE_ELIGIBILITY = "provenance_required"
MANIFEST_REDACTION_ELIGIBILITY = "redaction_status_required"
MANIFEST_RUN_ID_ALIGNMENT = "single_run_id_required"
MANIFEST_SOURCE_REFERENCE_ELIGIBILITY = "known_source_references_required"
MANIFEST_PACKAGE_IDENTITY_ELIGIBILITY = "package_identity_rules_required"
MANIFEST_PACKAGE_LAYOUT_ELIGIBILITY = "package_layout_rules_required"
MANIFEST_INTEGRITY_STATUS_PLACEHOLDER = "integrity_status_metadata_only"

MANIFEST_GENERATION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "draft_only",
    "in_memory_only",
    "evidence_only",
    "non_authoritative",
    "no_package_creation",
    "no_filesystem_access",
    "no_hash_computation",
    "no_integrity_validation",
    "no_storage_finalization",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class ManifestFieldEligibility:
    """Static field eligibility vocabulary for draft manifests."""

    required_fields: tuple[str, ...] = MANIFEST_REQUIRED_FIELDS


@dataclass(frozen=True, slots=True)
class ManifestProvenanceEligibility:
    """Static provenance eligibility vocabulary."""

    required: bool = True


@dataclass(frozen=True, slots=True)
class ManifestRedactionEligibility:
    """Static redaction eligibility vocabulary."""

    required: bool = True


@dataclass(frozen=True, slots=True)
class ManifestRunIdAlignment:
    """Static run identifier alignment vocabulary."""

    required: bool = True


@dataclass(frozen=True, slots=True)
class ManifestSourceReferenceEligibility:
    """Static source-reference eligibility vocabulary."""

    known_references_required: bool = True


@dataclass(frozen=True, slots=True)
class ManifestPackageIdentityEligibility:
    """Static package identity eligibility vocabulary."""

    required: bool = True


@dataclass(frozen=True, slots=True)
class ManifestPackageLayoutEligibility:
    """Static package layout eligibility vocabulary."""

    required: bool = True


@dataclass(frozen=True, slots=True)
class ManifestIntegrityStatusPlaceholder:
    """Static inert integrity/hash vocabulary placeholder for draft manifests."""

    integrity_status: str = integrity.INTEGRITY_STATUS[0]
    hash_algorithm: str = hashing.HASH_ALGORITHM
    hash_version: str = hashing.HASH_VERSION


@dataclass(frozen=True, slots=True)
class ManifestInput:
    """Already-loaded metadata eligible for draft manifest generation."""

    canonical_run_id: str
    created_at: str
    package_identity: Mapping[str, Any]
    package_layout_metadata: Mapping[str, Any]
    source_artifact_references: tuple[Mapping[str, Any], ...]
    section_status: Mapping[str, str]
    section_provenance: Mapping[str, str]
    section_redaction_status: Mapping[str, str]
    section_source_reference: Mapping[str, str]
    package_id: str | None = None
    package_schema_version: str = "0.1-planning"
    manifest_schema_version: str = MANIFEST_SCHEMA_VERSION
    lifecycle_status: str = MANIFEST_LIFECYCLE_STATUS[0]
    lifecycle_reason: str = "draft_manifest_generation_only"
    integrity_status: str = integrity.INTEGRITY_STATUS[0]
    hash_algorithm: str = hashing.HASH_ALGORITHM
    hash_version: str = hashing.HASH_VERSION


@dataclass(frozen=True, slots=True)
class DraftManifest:
    """Non-authoritative draft manifest output."""

    fields: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ManifestGeneration:
    """Static draft manifest generation vocabulary."""

    name: str = MANIFEST_GENERATION
    authority_boundary: tuple[str, ...] = MANIFEST_GENERATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class ManifestBuilder:
    """Static draft manifest builder vocabulary."""

    name: str = MANIFEST_BUILDER
    output_model: str = DRAFT_MANIFEST


def build_draft_manifest(manifest_input: ManifestInput | Mapping[str, Any]) -> dict[str, Any]:
    """Build a non-authoritative draft manifest from already-loaded metadata."""

    normalized = _normalize_manifest_input(manifest_input)
    _validate_manifest_input(normalized)
    package_id = _manifest_package_id(normalized)
    return {
        "canonical_run_id": normalized.canonical_run_id,
        "package_id": package_id,
        "package_identity": dict(normalized.package_identity),
        "package_layout": dict(normalized.package_layout_metadata),
        "package_schema_version": normalized.package_schema_version,
        "manifest_schema_version": normalized.manifest_schema_version,
        "lifecycle_status": normalized.lifecycle_status,
        "lifecycle_reason": normalized.lifecycle_reason,
        "created_at": normalized.created_at,
        "integrity_status": normalized.integrity_status,
        "hash_algorithm": normalized.hash_algorithm,
        "hash_version": normalized.hash_version,
        "source_artifact_references": tuple(normalized.source_artifact_references),
        "section_status": dict(normalized.section_status),
        "section_provenance": dict(normalized.section_provenance),
        "section_redaction_status": dict(normalized.section_redaction_status),
        "section_source_reference": dict(normalized.section_source_reference),
        "evidence_only": True,
        "non_authoritative": True,
        "authority_boundary": MANIFEST_GENERATION_AUTHORITY_BOUNDARY,
    }


def build_in_memory_manifest(
    manifest_input: ManifestInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for building a draft manifest in memory."""

    return build_draft_manifest(manifest_input)


def _normalize_manifest_input(
    manifest_input: ManifestInput | Mapping[str, Any],
) -> ManifestInput:
    if isinstance(manifest_input, ManifestInput):
        return manifest_input
    if not isinstance(manifest_input, Mapping):
        raise TypeError("manifest input must be already-loaded metadata")
    return ManifestInput(**manifest_input)


def _validate_manifest_input(manifest_input: ManifestInput) -> None:
    if not manifest_input.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if manifest_input.lifecycle_status != "draft":
        raise ValueError("draft manifests require draft lifecycle status")
    _reject_filesystem_dependent_input(manifest_input)
    _validate_package_identity_and_layout(manifest_input)
    _check_integrity_placeholder(manifest_input)
    _validate_source_artifact_references(manifest_input)
    _validate_sections(manifest_input)
    _validate_run_id_alignment(manifest_input)


def _manifest_package_id(manifest_input: ManifestInput) -> str:
    package_id = manifest_input.package_identity.get(package_layout_rules.PACKAGE_ID)
    if not isinstance(package_id, str) or not package_id:
        raise ValueError("package_id is required")
    return package_id


def _validate_package_identity_and_layout(manifest_input: ManifestInput) -> None:
    if not package_layout_rules.package_identity_is_complete(
        manifest_input.package_identity
    ):
        raise ValueError("package identity is required")
    if manifest_input.package_identity.get(package_layout_rules.CANONICAL_RUN_ID) != (
        manifest_input.canonical_run_id
    ):
        raise ValueError("package identity run_id must align")
    package_id = manifest_input.package_identity.get(package_layout_rules.PACKAGE_ID)
    if manifest_input.package_id is not None and manifest_input.package_id != package_id:
        raise ValueError("package_id must align with package identity")

    layout_status = manifest_input.package_layout_metadata.get("layout_status")
    if layout_status != "layout_declared":
        raise ValueError("layout status must be declared")
    if manifest_input.package_layout_metadata.get("layout_version") != (
        package_layout_rules.PACKAGE_LAYOUT_VERSION
    ):
        raise ValueError("layout version is required")
    if not package_layout_rules.package_layout_boundaries_are_separated(
        manifest_input.package_layout_metadata
    ):
        raise ValueError("package layout boundaries must be separated")


def _check_integrity_placeholder(manifest_input: ManifestInput) -> None:
    if manifest_input.integrity_status != integrity.INTEGRITY_STATUS[0]:
        raise ValueError("manifest integrity status must remain not_implemented")
    if manifest_input.hash_algorithm != hashing.HASH_ALGORITHM:
        raise ValueError("manifest hash algorithm metadata is unsupported")
    if manifest_input.hash_version != hashing.HASH_VERSION:
        raise ValueError("manifest hash version metadata is unsupported")


def _validate_source_artifact_references(manifest_input: ManifestInput) -> None:
    if not manifest_input.source_artifact_references:
        raise ValueError("source artifact references are required")
    seen_references: set[str] = set()
    for reference in manifest_input.source_artifact_references:
        if not isinstance(reference, Mapping):
            raise TypeError("source artifact references must be mappings")
        reference_id = reference.get("source_reference")
        provenance = reference.get("provenance")
        redaction_status = reference.get("redaction_status")
        if not isinstance(reference_id, str) or not reference_id:
            raise ValueError("source artifact reference id is required")
        if not isinstance(provenance, str) or not provenance:
            raise ValueError("source artifact provenance is required")
        if not isinstance(redaction_status, str) or not redaction_status:
            raise ValueError("source artifact redaction status is required")
        seen_references.add(reference_id)
    unknown_references = set(manifest_input.section_source_reference.values()) - seen_references
    if unknown_references:
        raise ValueError("section source references must be known")


def _validate_sections(manifest_input: ManifestInput) -> None:
    section_names = set(manifest_input.section_status)
    if not section_names:
        raise ValueError("section status is required")
    if section_names != set(manifest_input.section_provenance):
        raise ValueError("section provenance is required for every section")
    if section_names != set(manifest_input.section_redaction_status):
        raise ValueError("section redaction status is required for every section")
    if section_names != set(manifest_input.section_source_reference):
        raise ValueError("section source reference is required for every section")
    if any(not value for value in manifest_input.section_provenance.values()):
        raise ValueError("missing section provenance")
    if any(not value for value in manifest_input.section_redaction_status.values()):
        raise ValueError("missing section redaction status")


def _validate_run_id_alignment(manifest_input: ManifestInput) -> None:
    for reference in manifest_input.source_artifact_references:
        source_run_id = reference.get("run_id")
        if source_run_id != manifest_input.canonical_run_id:
            raise ValueError("mixed run_id inputs are not manifest eligible")


def _reject_filesystem_dependent_input(manifest_input: ManifestInput) -> None:
    for reference in manifest_input.source_artifact_references:
        for key, value in reference.items():
            if "path" in str(key).lower():
                raise ValueError("filesystem-dependent manifest inputs are not eligible")
            if isinstance(value, str) and (value.startswith("/") or value.startswith("~")):
                raise ValueError("filesystem-dependent manifest inputs are not eligible")
