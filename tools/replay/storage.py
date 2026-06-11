"""Pure in-memory storage lifecycle vocabulary for replay prerequisites.

This module defines storage root/path/lifecycle/finalization/immutability
identity vocabulary only. It does not touch the filesystem, create
directories, perform reads or writes, finalize storage, enforce immutability,
assert package completeness, capture runtime data, evaluate strategies, or
authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass


STORAGE_ROOT = "storage_root"
STORAGE_PATH = "storage_path"
PACKAGE_DIRECTORY = "package_directory"
PACKAGE_PATH = "package_path"
PACKAGE_LIFECYCLE_STATE = "package_lifecycle_state"
FINALIZATION_STATE = "finalization_state"
FINALIZED_PACKAGE = "finalized_package"
INVALIDATED_PACKAGE = "invalidated_package"
SUPERSEDED_PACKAGE = "superseded_package"
IMMUTABILITY_MARKER = "immutability_marker"
LINEAGE_REFERENCE = "lineage_reference"
CORRECTION_REFERENCE = "correction_reference"
INVALIDATION_REFERENCE = "invalidation_reference"
SUPERSESSION_REFERENCE = "supersession_reference"

PACKAGE_LIFECYCLE_STATES: tuple[str, ...] = (
    "draft",
    "finalized",
    "invalidated",
    "superseded",
)

STORAGE_LIFECYCLE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "evidence_only",
    "non_authoritative",
    "no_actual_filesystem_reads",
    "no_actual_filesystem_writes",
    "no_package_directory_creation",
    "no_finalized_storage",
    "no_immutability_enforcement",
    "no_package_completeness",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class StorageRoot:
    """Storage root identity vocabulary."""

    name: str = STORAGE_ROOT


@dataclass(frozen=True, slots=True)
class StoragePath:
    """Storage path identity vocabulary."""

    name: str = STORAGE_PATH


@dataclass(frozen=True, slots=True)
class PackageDirectory:
    """Package directory identity vocabulary."""

    name: str = PACKAGE_DIRECTORY


@dataclass(frozen=True, slots=True)
class PackagePath:
    """Package path identity vocabulary."""

    name: str = PACKAGE_PATH


@dataclass(frozen=True, slots=True)
class PackageLifecycleState:
    """Package lifecycle state vocabulary."""

    name: str = PACKAGE_LIFECYCLE_STATE
    states: tuple[str, ...] = PACKAGE_LIFECYCLE_STATES


@dataclass(frozen=True, slots=True)
class FinalizationState:
    """Finalization state vocabulary (metadata only)."""

    name: str = FINALIZATION_STATE


@dataclass(frozen=True, slots=True)
class FinalizedPackage:
    """Finalized package identity vocabulary (metadata only)."""

    name: str = FINALIZED_PACKAGE


@dataclass(frozen=True, slots=True)
class InvalidatedPackage:
    """Invalidated package identity vocabulary (metadata only)."""

    name: str = INVALIDATED_PACKAGE


@dataclass(frozen=True, slots=True)
class SupersededPackage:
    """Superseded package identity vocabulary (metadata only)."""

    name: str = SUPERSEDED_PACKAGE


@dataclass(frozen=True, slots=True)
class ImmutabilityMarker:
    """Immutability marker vocabulary (metadata only)."""

    name: str = IMMUTABILITY_MARKER


@dataclass(frozen=True, slots=True)
class LineageReference:
    """Lineage reference vocabulary."""

    name: str = LINEAGE_REFERENCE


@dataclass(frozen=True, slots=True)
class CorrectionReference:
    """Correction reference vocabulary."""

    name: str = CORRECTION_REFERENCE


@dataclass(frozen=True, slots=True)
class InvalidationReference:
    """Invalidation reference vocabulary."""

    name: str = INVALIDATION_REFERENCE


@dataclass(frozen=True, slots=True)
class SupersessionReference:
    """Supersession reference vocabulary."""

    name: str = SUPERSESSION_REFERENCE
