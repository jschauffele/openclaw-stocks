"""Pure in-memory filesystem/storage authority metadata helper.

This module validates already-loaded storage root and package path authority
metadata only. It does not touch paths, create directories, perform filesystem
reads or writes, finalize storage, enforce immutability, assert package
completeness, capture runtime data, evaluate strategies, or authorize
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


STORAGE_ROOT = "storage_root_authority"
PACKAGE_PATH = "package_path_authority"
PACKAGE_DIRECTORY = "package_directory_authority"
FILESYSTEM_READ_AUTHORITY = "filesystem_read_authority_metadata_only"
FILESYSTEM_WRITE_AUTHORITY = "filesystem_write_authority_metadata_only"
STORAGE_WRITER_AUTHORITY = "storage_writer_authority_metadata_only"
PATH_RESOLVER_AUTHORITY = "path_resolver_authority_metadata_only"
PACKAGE_DIRECTORY_RESOLVER_AUTHORITY = (
    "package_directory_resolver_authority_metadata_only"
)
FILESYSTEM_STORAGE_AUTHORITY = "filesystem_storage_authority_metadata_only"
FILESYSTEM_STORAGE_AUTHORITY_RESULT = "filesystem_storage_authority_result"

FILESYSTEM_STORAGE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
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
    """Approved storage root identity vocabulary."""

    name: str = STORAGE_ROOT


@dataclass(frozen=True, slots=True)
class PackagePath:
    """Approved package path identity vocabulary."""

    name: str = PACKAGE_PATH


@dataclass(frozen=True, slots=True)
class PackageDirectory:
    """Approved package directory identity vocabulary."""

    name: str = PACKAGE_DIRECTORY


@dataclass(frozen=True, slots=True)
class FilesystemReadAuthority:
    """Read authority flag vocabulary, not executable capability."""

    name: str = FILESYSTEM_READ_AUTHORITY


@dataclass(frozen=True, slots=True)
class FilesystemWriteAuthority:
    """Write authority flag vocabulary, not executable capability."""

    name: str = FILESYSTEM_WRITE_AUTHORITY


@dataclass(frozen=True, slots=True)
class StorageWriterAuthority:
    """Storage writer authority flag vocabulary, not a writer."""

    name: str = STORAGE_WRITER_AUTHORITY


@dataclass(frozen=True, slots=True)
class PathResolverAuthority:
    """Path resolver authority flag vocabulary, not a resolver."""

    name: str = PATH_RESOLVER_AUTHORITY


@dataclass(frozen=True, slots=True)
class PackageDirectoryResolverAuthority:
    """Directory resolver authority flag vocabulary, not a resolver."""

    name: str = PACKAGE_DIRECTORY_RESOLVER_AUTHORITY


@dataclass(frozen=True, slots=True)
class FilesystemStorageAuthority:
    """Static filesystem/storage authority metadata vocabulary."""

    name: str = FILESYSTEM_STORAGE_AUTHORITY
    authority_boundary: tuple[str, ...] = FILESYSTEM_STORAGE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class FilesystemStorageAuthorityInput:
    """Already-loaded storage/path authority metadata."""

    canonical_run_id: str
    storage_root: str
    approved_storage_roots: tuple[str, ...]
    package_path: str
    approved_package_paths: tuple[str, ...]
    package_directory: str
    approved_package_directories: tuple[str, ...]
    provenance: str
    redaction_status: str
    source_reference: str
    known_source_references: tuple[str, ...]
    input_run_ids: tuple[str, ...]
    read_authority: bool = False
    write_authority: bool = False
    storage_writer_authority: bool = False
    path_resolver_authority: bool = False
    package_directory_resolver_authority: bool = False
    overwrite_attempt: bool = False
    symlink_status: str = "not_symlink"
    repo_relative: bool = True
    sensitive_data_status: str = "clear"
    runtime_dependent: bool = False
    evaluation_dependent: bool = False
    broker_dependent: bool = False


@dataclass(frozen=True, slots=True)
class FilesystemStorageAuthorityResult:
    """Filesystem/storage authority result vocabulary."""

    result_type: str = FILESYSTEM_STORAGE_AUTHORITY_RESULT
    authority_boundary: tuple[str, ...] = FILESYSTEM_STORAGE_AUTHORITY_BOUNDARY


def validate_filesystem_storage_authority(
    authority_input: FilesystemStorageAuthorityInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Return non-authoritative metadata for approved storage/path authority."""

    normalized = _normalize_authority_input(authority_input)
    _validate_authority_input(normalized)
    return {
        "result_type": FILESYSTEM_STORAGE_AUTHORITY_RESULT,
        "canonical_run_id": normalized.canonical_run_id,
        "storage_root": normalized.storage_root,
        "package_path": normalized.package_path,
        "package_directory": normalized.package_directory,
        "filesystem_read_authority": normalized.read_authority,
        "filesystem_write_authority": normalized.write_authority,
        "storage_writer_authority": normalized.storage_writer_authority,
        "path_resolver_authority": normalized.path_resolver_authority,
        "package_directory_resolver_authority": (
            normalized.package_directory_resolver_authority
        ),
        "provenance": normalized.provenance,
        "redaction_status": normalized.redaction_status,
        "source_reference": normalized.source_reference,
        "evidence_only": True,
        "non_authoritative": True,
        "actual_filesystem_reads": False,
        "actual_filesystem_writes": False,
        "package_directory_creation": False,
        "finalized_storage": False,
        "immutability_enforcement": False,
        "package_completeness": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "live_trading_authority": False,
        "authority_boundary": FILESYSTEM_STORAGE_AUTHORITY_BOUNDARY,
    }


def resolve_package_path_authority(
    authority_input: FilesystemStorageAuthorityInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for validating package path authority metadata."""

    return validate_filesystem_storage_authority(authority_input)


def resolve_package_directory_authority(
    authority_input: FilesystemStorageAuthorityInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for validating package directory authority metadata."""

    return validate_filesystem_storage_authority(authority_input)


def _normalize_authority_input(
    authority_input: FilesystemStorageAuthorityInput | Mapping[str, Any],
) -> FilesystemStorageAuthorityInput:
    if isinstance(authority_input, FilesystemStorageAuthorityInput):
        return authority_input
    if not isinstance(authority_input, Mapping):
        raise TypeError("filesystem/storage authority input must be metadata")
    return FilesystemStorageAuthorityInput(**authority_input)


def _validate_authority_input(authority_input: FilesystemStorageAuthorityInput) -> None:
    _validate_run_identity(authority_input)
    _validate_storage_identity(authority_input)
    _validate_path_identity(authority_input)
    _validate_metadata(authority_input)
    _reject_downstream_dependencies(authority_input)


def _validate_run_identity(authority_input: FilesystemStorageAuthorityInput) -> None:
    if not authority_input.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    for run_id in authority_input.input_run_ids:
        if run_id != authority_input.canonical_run_id:
            raise ValueError("mixed run_id storage authority input")


def _validate_storage_identity(
    authority_input: FilesystemStorageAuthorityInput,
) -> None:
    if not authority_input.storage_root:
        raise ValueError("unknown storage root")
    if authority_input.storage_root not in authority_input.approved_storage_roots:
        raise ValueError("unapproved storage root")
    if not authority_input.package_path:
        raise ValueError("unknown package path")
    if authority_input.package_path not in authority_input.approved_package_paths:
        raise ValueError("unapproved package path")
    if not authority_input.package_directory:
        raise ValueError("unknown package directory")
    if authority_input.package_directory not in (
        authority_input.approved_package_directories
    ):
        raise ValueError("unapproved package directory")


def _validate_path_identity(authority_input: FilesystemStorageAuthorityInput) -> None:
    for value in (
        authority_input.storage_root,
        authority_input.package_path,
        authority_input.package_directory,
    ):
        if _has_absolute_path_shape(value):
            raise ValueError("absolute path injection")
        if _has_path_traversal_shape(value):
            raise ValueError("path traversal")
    if authority_input.symlink_status != "not_symlink":
        raise ValueError("symlink ambiguity")
    if authority_input.repo_relative is not True:
        raise ValueError("non-repo path ambiguity")
    if authority_input.overwrite_attempt:
        raise ValueError("attempted overwrite")


def _validate_metadata(authority_input: FilesystemStorageAuthorityInput) -> None:
    if not isinstance(authority_input.provenance, str):
        raise ValueError("malformed provenance")
    if not authority_input.provenance:
        raise ValueError("missing provenance")
    if not authority_input.redaction_status:
        raise ValueError("missing redaction status")
    if authority_input.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if authority_input.source_reference not in authority_input.known_source_references:
        raise ValueError("unknown source references")
    if authority_input.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")


def _reject_downstream_dependencies(
    authority_input: FilesystemStorageAuthorityInput,
) -> None:
    if authority_input.runtime_dependent:
        raise ValueError("runtime-dependent storage authority input")
    if authority_input.evaluation_dependent:
        raise ValueError("evaluation-dependent storage authority input")
    if authority_input.broker_dependent:
        raise ValueError("broker-dependent storage authority input")


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
