"""Inert package identity and layout vocabulary for replay prerequisites.

This module defines package identity and layout labels only. It does not create
packages, build directories, read or write files, generate manifests, compute
hashes, validate integrity, store artifacts, capture runtime data, evaluate
strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TypeAlias


PACKAGE_IDENTITY = "package_identity_vocabulary_only"
PACKAGE_LAYOUT = "package_layout_vocabulary_only"
PACKAGE_ID = "package_id"
CANONICAL_RUN_ID = "canonical_run_id"
PACKAGE_LAYOUT_VERSION = "0.1-layout-rules"

PackageIdentityFieldName: TypeAlias = str
PackageLayoutSectionName: TypeAlias = str
PackageLayoutStatusValue: TypeAlias = str
PackageLayoutBoundaryName: TypeAlias = str

PACKAGE_IDENTITY_FIELDS: tuple[str, ...] = (
    CANONICAL_RUN_ID,
    PACKAGE_ID,
)

PACKAGE_LAYOUT_SECTIONS: tuple[str, ...] = (
    "package_identity",
    "manifest",
    "source_artifact_references",
    "integrity",
    "authority_boundary",
)

PACKAGE_LAYOUT_STATUS: tuple[str, ...] = (
    "layout_declared",
    "layout_draft",
    "layout_blocked",
    "absent",
    "not_applicable",
    "missing",
    "malformed",
    "ambiguous",
    "stale",
    "mixed_run",
    "blocked_sensitive",
    "unknown",
)

PACKAGE_LAYOUT_FAIL_CLOSED_STATUS: tuple[str, ...] = (
    "layout_draft",
    "layout_blocked",
    "missing",
    "malformed",
    "ambiguous",
    "stale",
    "mixed_run",
    "blocked_sensitive",
    "unknown",
)

PACKAGE_SECTION_BOUNDARIES: tuple[str, ...] = (
    "artifact_section",
    "manifest_section",
    "provenance_section",
    "redaction_section",
    "immutable_evidence_section",
    "mutable_evaluation_section",
    "authority_boundary",
)

PACKAGE_LAYOUT_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "vocabulary_only",
    "in_memory_only",
    "non_authoritative",
    "no_package_creation",
    "no_filesystem_access",
    "no_manifest_generation",
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
class PackageId:
    """Static package identifier field vocabulary."""

    field_name: str = PACKAGE_ID


@dataclass(frozen=True, slots=True)
class CanonicalRunId:
    """Static canonical run identifier field vocabulary."""

    field_name: str = CANONICAL_RUN_ID


@dataclass(frozen=True, slots=True)
class PackageIdentity:
    """Static package identity vocabulary container."""

    name: str = PACKAGE_IDENTITY
    fields: tuple[str, ...] = PACKAGE_IDENTITY_FIELDS


@dataclass(frozen=True, slots=True)
class PackageLayout:
    """Static package layout vocabulary container."""

    name: str = PACKAGE_LAYOUT
    version: str = PACKAGE_LAYOUT_VERSION
    sections: tuple[str, ...] = PACKAGE_LAYOUT_SECTIONS
    statuses: tuple[str, ...] = PACKAGE_LAYOUT_STATUS
    section_boundaries: tuple[str, ...] = PACKAGE_SECTION_BOUNDARIES
    authority_boundary: tuple[str, ...] = PACKAGE_LAYOUT_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageLayoutVersion:
    """Static package layout rule version vocabulary."""

    value: str = PACKAGE_LAYOUT_VERSION


@dataclass(frozen=True, slots=True)
class PackageLayoutStatus:
    """Static package layout status vocabulary."""

    values: tuple[str, ...] = PACKAGE_LAYOUT_STATUS
    fail_closed_values: tuple[str, ...] = PACKAGE_LAYOUT_FAIL_CLOSED_STATUS


@dataclass(frozen=True, slots=True)
class PackageSectionBoundary:
    """Static conceptual package section-boundary vocabulary entry."""

    name: PackageLayoutBoundaryName
    section: PackageLayoutSectionName


def package_identity_is_complete(identity: Mapping[str, object]) -> bool:
    """Return True only for one complete, unambiguous package identity."""

    canonical_run_id = identity.get(CANONICAL_RUN_ID)
    package_id = identity.get(PACKAGE_ID)
    run_ids = identity.get("run_ids", (canonical_run_id,))

    if not isinstance(canonical_run_id, str) or not canonical_run_id:
        return False
    if not isinstance(package_id, str) or not package_id:
        return False
    if not isinstance(run_ids, tuple) or not run_ids:
        return False
    return all(run_id == canonical_run_id for run_id in run_ids)


def package_layout_boundaries_are_separated(
    boundaries: Mapping[str, object],
) -> bool:
    """Return True only when mutable and immutable boundaries are distinct."""

    immutable_section = boundaries.get("immutable_evidence_section")
    mutable_section = boundaries.get("mutable_evaluation_section")

    if not isinstance(immutable_section, str) or not immutable_section:
        return False
    if not isinstance(mutable_section, str) or not mutable_section:
        return False
    return immutable_section != mutable_section


def layout_status_allows_downstream_authority(status: object) -> bool:
    """Package layout status never grants downstream authority in Unit 4."""

    if not isinstance(status, str):
        return False
    if status not in PACKAGE_LAYOUT_STATUS:
        return False
    return False
