"""Inert package identity and layout vocabulary for replay prerequisites.

This module defines package identity and layout labels only. It does not create
packages, build directories, read or write files, generate manifests, compute
hashes, validate integrity, store artifacts, capture runtime data, evaluate
strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass


PACKAGE_IDENTITY = "package_identity_vocabulary_only"
PACKAGE_LAYOUT = "package_layout_vocabulary_only"
PACKAGE_ID = "package_id"
CANONICAL_RUN_ID = "canonical_run_id"

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
    sections: tuple[str, ...] = PACKAGE_LAYOUT_SECTIONS
    authority_boundary: tuple[str, ...] = PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
