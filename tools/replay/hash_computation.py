"""Pure in-memory hash computation helper for replay prerequisites.

This module computes non-authoritative hash records from already-canonical
bytes only. It does not validate integrity, assert package completeness, create
packages, touch the filesystem, store artifacts, capture runtime data,
evaluate strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from tools.replay.hashing import HASH_ALGORITHM, HASH_VERSION


SECTION_HASH = "section_hash"
MANIFEST_HASH = "manifest_hash"
PACKAGE_HASH = "package_hash"
HASH_COMPUTATION = "sha256_canonical_bytes_hash_computation"
HASH_INPUT_ELIGIBILITY = "canonical_bytes_only"
HASH_SCOPE = "explicit_hash_scope_required"
SECTION_HASH_SCOPE = "section_hash_scope"
MANIFEST_HASH_SCOPE = "manifest_hash_scope"
PACKAGE_HASH_SCOPE = "package_hash_scope"
CANONICAL_HASH_INPUT = "canonical_bytes"

HASH_COMPUTATION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "canonical_bytes_only",
    "evidence_only",
    "non_authoritative",
    "no_integrity_validation",
    "no_package_completeness",
    "no_package_creation",
    "no_filesystem_access",
    "no_storage_finalization",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class CanonicalHashInput:
    """Already-canonical bytes plus governed hash metadata."""

    canonical_bytes: bytes
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class HashInputEligibility:
    """Static hash input eligibility vocabulary."""

    input_model: str = CANONICAL_HASH_INPUT
    algorithm: str = HASH_ALGORITHM
    version: str = HASH_VERSION


@dataclass(frozen=True, slots=True)
class HashScope:
    """Static explicit hash-scope vocabulary."""

    name: str = HASH_SCOPE


@dataclass(frozen=True, slots=True)
class SectionHashScope:
    """Static section hash-scope vocabulary."""

    name: str = SECTION_HASH_SCOPE


@dataclass(frozen=True, slots=True)
class ManifestHashScope:
    """Static manifest hash-scope vocabulary."""

    name: str = MANIFEST_HASH_SCOPE


@dataclass(frozen=True, slots=True)
class PackageHashScope:
    """Static package hash-scope vocabulary."""

    name: str = PACKAGE_HASH_SCOPE


@dataclass(frozen=True, slots=True)
class HashComputation:
    """Static hash computation vocabulary."""

    name: str = HASH_COMPUTATION
    authority_boundary: tuple[str, ...] = HASH_COMPUTATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class SectionHash:
    """Non-authoritative section hash record vocabulary."""

    hash_type: str = SECTION_HASH


@dataclass(frozen=True, slots=True)
class ManifestHash:
    """Non-authoritative manifest hash record vocabulary."""

    hash_type: str = MANIFEST_HASH


@dataclass(frozen=True, slots=True)
class PackageHash:
    """Non-authoritative package hash record vocabulary."""

    hash_type: str = PACKAGE_HASH


def build_section_hash(
    canonical_bytes: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a non-authoritative section hash record."""

    return _build_hash_record(SECTION_HASH, canonical_bytes, metadata)


def build_manifest_hash(
    canonical_bytes: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a non-authoritative manifest hash record."""

    return _build_hash_record(MANIFEST_HASH, canonical_bytes, metadata)


def build_package_hash(
    canonical_bytes: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a non-authoritative package hash record."""

    return _build_hash_record(PACKAGE_HASH, canonical_bytes, metadata)


def _build_hash_record(
    hash_type: str,
    canonical_bytes: bytes,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    _check_hash_input(hash_type, canonical_bytes, metadata)
    return {
        "hash_type": hash_type,
        "hash_algorithm": HASH_ALGORITHM,
        "hash_version": HASH_VERSION,
        "digest": hashlib.sha256(canonical_bytes).hexdigest(),
        "canonical_input": CANONICAL_HASH_INPUT,
        "metadata": dict(metadata),
        "evidence_only": True,
        "non_authoritative": True,
        "authority_boundary": HASH_COMPUTATION_AUTHORITY_BOUNDARY,
    }


def _check_hash_input(
    hash_type: str,
    canonical_bytes: bytes,
    metadata: Mapping[str, Any],
) -> None:
    if hash_type not in {SECTION_HASH, MANIFEST_HASH, PACKAGE_HASH}:
        raise ValueError("unknown hash type")
    if not isinstance(canonical_bytes, bytes):
        raise TypeError("hash input must be canonical bytes")
    if not isinstance(metadata, Mapping):
        raise TypeError("hash metadata must be already-loaded metadata")
    if metadata.get("hash_algorithm") != HASH_ALGORITHM:
        raise ValueError("missing or unsupported hash algorithm metadata")
    if metadata.get("hash_version") != HASH_VERSION:
        raise ValueError("missing or unsupported hash version metadata")
    if not metadata.get("canonical_run_id"):
        raise ValueError("canonical_run_id is required")
    if not metadata.get("provenance"):
        raise ValueError("missing provenance")
    if not metadata.get("redaction_status"):
        raise ValueError("missing redaction status")
    if metadata.get("sensitive_data_status") != "clear":
        raise ValueError("sensitive data ambiguity")
    if hash_type == SECTION_HASH and not metadata.get("section_scope"):
        raise ValueError("undefined section scope")
    if hash_type == MANIFEST_HASH and not metadata.get("manifest_scope"):
        raise ValueError("undefined manifest scope")
    if hash_type == PACKAGE_HASH and not metadata.get("package_scope"):
        raise ValueError("undefined package scope")
    _reject_filesystem_dependent_metadata(metadata)
    _validate_source_reference(metadata)
    _validate_run_id_alignment(metadata)


def _validate_source_reference(metadata: Mapping[str, Any]) -> None:
    known_references = metadata.get("known_source_references")
    source_reference = metadata.get("source_reference")
    if not isinstance(known_references, tuple) or not known_references:
        raise ValueError("unknown source references")
    if source_reference not in known_references:
        raise ValueError("unknown source references")


def _validate_run_id_alignment(metadata: Mapping[str, Any]) -> None:
    canonical_run_id = metadata["canonical_run_id"]
    for run_id in metadata.get("run_ids", (canonical_run_id,)):
        if run_id != canonical_run_id:
            raise ValueError("mixed run_id hash input")


def _reject_filesystem_dependent_metadata(metadata: Mapping[str, Any]) -> None:
    for key, value in metadata.items():
        if "path" in str(key).lower():
            raise ValueError("filesystem-dependent hash inputs are not eligible")
        if isinstance(value, str) and (value.startswith("/") or value.startswith("~")):
            raise ValueError("filesystem-dependent hash inputs are not eligible")
