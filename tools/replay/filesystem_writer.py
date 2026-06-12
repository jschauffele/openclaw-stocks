"""Deterministic filesystem writer helper for replay package evidence.

This module writes caller-supplied replay package artifact bytes only to
explicitly approved local paths. It does not discover or capture runtime
artifacts, read runtime logs, evaluate or promote strategies, call broker APIs,
authorize execution, approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS
from tools.replay.storage_implementation import STORAGE_LIFECYCLE_STATES


FILESYSTEM_WRITER_AUTHORITY = "filesystem_writer_authority"
REPLAY_PACKAGE_WRITER = "replay_package_writer"
PACKAGE_PERSISTENCE_WRITER = "package_persistence_writer"
PACKAGE_DIRECTORY_WRITER = "package_directory_writer"
PACKAGE_FILE_WRITER = "package_file_writer"
PACKAGE_ARTIFACT_WRITER = "package_artifact_writer"
WRITER_PREFLIGHT_RESULT = "writer_preflight_result"
WRITER_FINALIZATION_RESULT = "writer_finalization_result"
WRITER_NO_OVERWRITE_RESULT = "writer_no_overwrite_result"
WRITER_PATH_RESOLUTION_RESULT = "writer_path_resolution_result"
WRITER_ATOMIC_WRITE_VOCABULARY = "writer_atomic_write_vocabulary"
WRITER_FSYNC_VOCABULARY = "writer_fsync_vocabulary"
WRITER_CHECKSUM_VERIFICATION = "writer_checksum_verification"
WRITER_ROLLBACK_MARKER = "writer_rollback_marker"
WRITER_DRY_RUN_RESULT = "writer_dry_run_result"

WRITER_RESULT = "filesystem_writer_result"
WRITER_HASH_ALGORITHM = "sha256"
ACCEPTABLE_WRITER_LIFECYCLE_STATES: tuple[str, ...] = ("finalized",)

# Writer authority modes. The default keeps the historical tmp_path-only
# mechanics (the package directory must already exist and the governed VPS root
# is never writable). The vps mode is the narrow extension that authorizes a
# write under exactly /opt/openclaw-stocks/replay_packages/{run_id}.
WRITER_AUTHORITY_MODE_TMP_PATH_TEST = "tmp_path_test"
WRITER_AUTHORITY_MODE_VPS = "vps"
ACCEPTABLE_WRITER_AUTHORITY_MODES: tuple[str, ...] = (
    WRITER_AUTHORITY_MODE_TMP_PATH_TEST,
    WRITER_AUTHORITY_MODE_VPS,
)
GOVERNED_VPS_ARTIFACT_ROOT_PATH = "/opt/openclaw-stocks"
GOVERNED_VPS_PACKAGE_ROOT_PATH = "/opt/openclaw-stocks/replay_packages"

FILESYSTEM_WRITER_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "deterministic_filesystem_writer_only",
    "approved_local_paths_only",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class FilesystemWriterAuthority:
    """Static filesystem writer authority vocabulary."""

    name: str = FILESYSTEM_WRITER_AUTHORITY
    authority_boundary: tuple[str, ...] = FILESYSTEM_WRITER_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class ReplayPackageWriter:
    """Static replay package writer vocabulary."""

    name: str = REPLAY_PACKAGE_WRITER


@dataclass(frozen=True, slots=True)
class PackagePersistenceWriter:
    """Static package persistence writer vocabulary."""

    name: str = PACKAGE_PERSISTENCE_WRITER


@dataclass(frozen=True, slots=True)
class PackageDirectoryWriter:
    """Static package directory writer vocabulary."""

    name: str = PACKAGE_DIRECTORY_WRITER


@dataclass(frozen=True, slots=True)
class PackageFileWriter:
    """Static package file writer vocabulary."""

    name: str = PACKAGE_FILE_WRITER


@dataclass(frozen=True, slots=True)
class PackageArtifactWriter:
    """Static package artifact writer vocabulary."""

    name: str = PACKAGE_ARTIFACT_WRITER


@dataclass(frozen=True, slots=True)
class WriterPreflightResult:
    """Static writer preflight result vocabulary."""

    result_type: str = WRITER_PREFLIGHT_RESULT


@dataclass(frozen=True, slots=True)
class WriterFinalizationResult:
    """Static writer finalization result vocabulary."""

    result_type: str = WRITER_FINALIZATION_RESULT


@dataclass(frozen=True, slots=True)
class WriterNoOverwriteResult:
    """Static no-overwrite result vocabulary."""

    result_type: str = WRITER_NO_OVERWRITE_RESULT


@dataclass(frozen=True, slots=True)
class WriterPathResolutionResult:
    """Static path resolution result vocabulary."""

    result_type: str = WRITER_PATH_RESOLUTION_RESULT


@dataclass(frozen=True, slots=True)
class WriterAtomicWriteVocabulary:
    """Static atomic write vocabulary."""

    name: str = WRITER_ATOMIC_WRITE_VOCABULARY


@dataclass(frozen=True, slots=True)
class WriterFsyncVocabulary:
    """Static fsync vocabulary."""

    name: str = WRITER_FSYNC_VOCABULARY


@dataclass(frozen=True, slots=True)
class WriterChecksumVerification:
    """Static checksum verification vocabulary."""

    name: str = WRITER_CHECKSUM_VERIFICATION


@dataclass(frozen=True, slots=True)
class WriterRollbackMarker:
    """Static rollback marker vocabulary."""

    name: str = WRITER_ROLLBACK_MARKER


@dataclass(frozen=True, slots=True)
class WriterDryRunResult:
    """Static dry-run result vocabulary."""

    result_type: str = WRITER_DRY_RUN_RESULT


@dataclass(frozen=True, slots=True)
class FilesystemWriterInput:
    """Already-loaded package artifact evidence eligible for approved writes."""

    canonical_run_id: str
    filesystem_storage_authority_result: Mapping[str, Any]
    package_completeness_result: Mapping[str, Any]
    storage_implementation_result: Mapping[str, Any]
    storage_root: str
    approved_storage_roots: tuple[str, ...]
    package_path: str
    approved_package_paths: tuple[str, ...]
    package_directory: str
    approved_package_directories: tuple[str, ...]
    storage_root_path: str
    approved_storage_root_paths: tuple[str, ...]
    artifact_relative_path: str
    artifact_bytes: bytes
    lifecycle_status: str
    provenance: str
    redaction_status: str
    source_references: tuple[str, ...]
    known_source_references: tuple[str, ...]
    input_run_ids: tuple[str, ...]
    allow_absolute_storage_root: bool = False
    overwrite_existing: bool = False
    rollback_marker: str = "rollback_marker_recorded"
    symlink_status: str = "not_symlink"
    repo_relative: bool = True
    writer_authority_mode: str = WRITER_AUTHORITY_MODE_TMP_PATH_TEST
    sensitive_data_status: str = "clear"
    stale_input: bool = False
    malformed_input: bool = False
    runtime_dependent: bool = False
    evaluation_dependent: bool = False
    broker_dependent: bool = False
    attempted_runtime_capture: bool = False
    attempted_evaluation_approval: bool = False
    attempted_execution_permission: bool = False
    attempted_live_trading_authority: bool = False


def validate_filesystem_writer_authority(
    writer_input: FilesystemWriterInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate approved writer evidence without writing."""

    normalized = _normalize_writer_input(writer_input)
    target_path = _validate_writer_input(normalized)
    return _build_result(normalized, target_path, dry_run=True, write_performed=False)


def resolve_writer_path(
    writer_input: FilesystemWriterInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Resolve the approved artifact path without writing."""

    normalized = _normalize_writer_input(writer_input)
    target_path = _validate_writer_input(normalized)
    return {
        **_build_result(normalized, target_path, dry_run=True, write_performed=False),
        "result_type": WRITER_PATH_RESOLUTION_RESULT,
    }


def build_writer_preflight_result(
    writer_input: FilesystemWriterInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build an approved writer preflight result without writing."""

    return validate_filesystem_writer_authority(writer_input)


def dry_run_replay_package_write(
    writer_input: FilesystemWriterInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic dry-run result for an approved artifact write."""

    normalized = _normalize_writer_input(writer_input)
    target_path = _validate_writer_input(normalized)
    return {
        **_build_result(normalized, target_path, dry_run=True, write_performed=False),
        "result_type": WRITER_DRY_RUN_RESULT,
    }


def write_replay_package_artifact(
    writer_input: FilesystemWriterInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically write one approved replay package artifact."""

    normalized = _normalize_writer_input(writer_input)
    target_path = _validate_writer_input(normalized)
    if normalized.writer_authority_mode == WRITER_AUTHORITY_MODE_VPS:
        # Validation already pinned the governed root and confirmed the package
        # directory is absent; create the bounded {run_id} package directory.
        package_dir_path = (
            Path(normalized.storage_root_path) / normalized.package_directory
        )
        package_dir_path.mkdir(parents=True, exist_ok=False)
    temporary_path = _temporary_path_for(target_path)
    if temporary_path.exists():
        raise ValueError("non-atomic write path")
    try:
        temporary_path.write_bytes(normalized.artifact_bytes)
        os.replace(temporary_path, target_path)
        observed_digest = _sha256(target_path.read_bytes())
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise
    expected_digest = _sha256(normalized.artifact_bytes)
    if observed_digest != expected_digest:
        raise ValueError("checksum verification failed")
    return {
        **_build_result(normalized, target_path, dry_run=False, write_performed=True),
        "result_type": WRITER_FINALIZATION_RESULT,
        "checksum_verified": True,
        "observed_sha256": observed_digest,
    }


def _normalize_writer_input(
    writer_input: FilesystemWriterInput | Mapping[str, Any],
) -> FilesystemWriterInput:
    if isinstance(writer_input, FilesystemWriterInput):
        return writer_input
    if not isinstance(writer_input, Mapping):
        raise TypeError("filesystem writer input must be already-loaded metadata")
    return FilesystemWriterInput(**writer_input)


def _validate_writer_input(writer_input: FilesystemWriterInput) -> Path:
    _reject_forbidden_dependencies(writer_input)
    _validate_authority_results(writer_input)
    _validate_storage_identity(writer_input)
    _validate_metadata(writer_input)
    target_path = _resolve_target_path(writer_input)
    _validate_target_path(writer_input, target_path)
    return target_path


def _reject_forbidden_dependencies(writer_input: FilesystemWriterInput) -> None:
    if writer_input.malformed_input:
        raise ValueError("malformed package evidence")
    if writer_input.stale_input:
        raise ValueError("stale writer input")
    if writer_input.runtime_dependent or writer_input.attempted_runtime_capture:
        raise ValueError("runtime-dependent writer input")
    if writer_input.evaluation_dependent or writer_input.attempted_evaluation_approval:
        raise ValueError("writer success is not evaluation approval")
    if writer_input.broker_dependent:
        raise ValueError("broker-dependent writer input")
    if writer_input.attempted_execution_permission:
        raise ValueError("writer success is not execution permission")
    if writer_input.attempted_live_trading_authority:
        raise ValueError("writer success is not live trading authority")


def _validate_authority_results(writer_input: FilesystemWriterInput) -> None:
    authority_result = writer_input.filesystem_storage_authority_result
    if not isinstance(authority_result, Mapping) or not authority_result:
        raise ValueError("filesystem/storage authority result is required")
    if authority_result.get("evidence_only") is not True:
        raise ValueError("filesystem/storage authority result must be valid")
    if authority_result.get("actual_filesystem_writes") is not False:
        raise ValueError("filesystem/storage authority result must be metadata-only")
    completeness_result = writer_input.package_completeness_result
    if not isinstance(completeness_result, Mapping) or not completeness_result:
        raise ValueError("package completeness result is required")
    if completeness_result.get("package_completeness") is not True:
        raise ValueError("package completeness result must be valid")
    if completeness_result.get("complete_replay_package_authority") is not True:
        raise ValueError("complete replay package authority is required")
    storage_result = writer_input.storage_implementation_result
    if not isinstance(storage_result, Mapping) or not storage_result:
        raise ValueError("storage implementation result is required")
    if storage_result.get("evidence_only") is not True:
        raise ValueError("storage implementation result must be valid")
    if storage_result.get("actual_filesystem_writes") is not False:
        raise ValueError("storage implementation result must be metadata-only")
    if storage_result.get("canonical_run_id") != writer_input.canonical_run_id:
        raise ValueError("mixed run_id writer input")


def _validate_storage_identity(writer_input: FilesystemWriterInput) -> None:
    if not writer_input.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    authority_result = writer_input.filesystem_storage_authority_result
    identity_checks = (
        ("storage root", writer_input.storage_root, writer_input.approved_storage_roots),
        ("package path", writer_input.package_path, writer_input.approved_package_paths),
        (
            "package directory",
            writer_input.package_directory,
            writer_input.approved_package_directories,
        ),
    )
    for label, value, approved_values in identity_checks:
        if not value:
            raise ValueError(f"{label} is required")
        if value not in approved_values:
            raise ValueError(f"unapproved {label}")
    if writer_input.storage_root != authority_result.get("storage_root"):
        raise ValueError("unapproved storage root")
    if writer_input.package_path != authority_result.get("package_path"):
        raise ValueError("unapproved package path")
    if writer_input.package_directory != authority_result.get("package_directory"):
        raise ValueError("unapproved package directory")
    if writer_input.lifecycle_status not in STORAGE_LIFECYCLE_STATES:
        raise ValueError("unknown lifecycle status")
    if writer_input.lifecycle_status not in ACCEPTABLE_WRITER_LIFECYCLE_STATES:
        raise ValueError("lifecycle metadata is not acceptable for writer")
    for run_id in writer_input.input_run_ids:
        if run_id != writer_input.canonical_run_id:
            raise ValueError("mixed run_id writer input")


def _validate_metadata(writer_input: FilesystemWriterInput) -> None:
    if not isinstance(writer_input.provenance, str):
        raise ValueError("malformed provenance")
    if not writer_input.provenance:
        raise ValueError("missing provenance")
    if not writer_input.redaction_status:
        raise ValueError("missing redaction status")
    if writer_input.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if not writer_input.source_references:
        raise ValueError("unknown source references")
    known_references = set(writer_input.known_source_references)
    if not known_references:
        raise ValueError("unknown source references")
    for source_reference in writer_input.source_references:
        if source_reference not in known_references:
            raise ValueError("unknown source references")
    if writer_input.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")
    if not isinstance(writer_input.artifact_bytes, bytes) or not (
        writer_input.artifact_bytes
    ):
        raise ValueError("artifact bytes are required")
    if not writer_input.rollback_marker:
        raise ValueError("missing rollback marker")


def _resolve_target_path(writer_input: FilesystemWriterInput) -> Path:
    if _has_path_traversal_shape(writer_input.artifact_relative_path):
        raise ValueError("path traversal")
    if _has_absolute_path_shape(writer_input.artifact_relative_path):
        raise ValueError("absolute path injection")
    storage_root_path = Path(writer_input.storage_root_path)
    if storage_root_path.is_absolute() and not writer_input.allow_absolute_storage_root:
        raise ValueError("absolute path injection")
    if str(storage_root_path) not in writer_input.approved_storage_root_paths:
        raise ValueError("unapproved storage root")
    return storage_root_path / writer_input.artifact_relative_path


def _validate_target_path(
    writer_input: FilesystemWriterInput,
    target_path: Path,
) -> None:
    if writer_input.writer_authority_mode not in ACCEPTABLE_WRITER_AUTHORITY_MODES:
        raise ValueError("unknown writer authority mode")
    storage_root_path = Path(writer_input.storage_root_path)
    package_dir_path = storage_root_path / writer_input.package_directory
    if not _is_relative_to(target_path, package_dir_path):
        raise ValueError("unapproved package path")
    if writer_input.symlink_status != "not_symlink":
        raise ValueError("symlink ambiguity")
    if target_path.is_symlink() or package_dir_path.is_symlink():
        raise ValueError("symlink ambiguity")
    if writer_input.repo_relative is not True:
        raise ValueError("non-repo path ambiguity")

    if writer_input.writer_authority_mode == WRITER_AUTHORITY_MODE_VPS:
        _validate_vps_writer_authority(writer_input)
        # Bounded VPS execution creates a fresh package directory. A pre-existing
        # governed package directory for the run fails closed (no-overwrite-safe).
        if package_dir_path.exists():
            raise ValueError("pre-existing vps package directory")
        return

    # tmp_path_test (default): the governed VPS root is never writable here, and
    # the package directory must already exist (created by the test harness).
    if str(storage_root_path) == GOVERNED_VPS_PACKAGE_ROOT_PATH:
        raise ValueError("tmp_path_test writer must not target the governed VPS root")
    if target_path.exists() and not writer_input.overwrite_existing:
        raise ValueError("attempted overwrite")
    if target_path.exists() and writer_input.lifecycle_status == "finalized":
        raise ValueError("no-overwrite violation")
    if not package_dir_path.exists():
        raise ValueError("unapproved package directory")


def _validate_vps_writer_authority(writer_input: FilesystemWriterInput) -> None:
    """Pure (no-filesystem) authority check for a bounded VPS package write.

    Approves a write only when the target is exactly
    /opt/openclaw-stocks/replay_packages/{canonical_run_id}/<artifact>. Every
    other root, run_id, or path shape fails closed.
    """

    run_id = writer_input.canonical_run_id
    if not run_id:
        raise ValueError("canonical_run_id is required")
    if "/" in run_id or ".." in run_id or "order_state" in run_id:
        raise ValueError("unapproved vps run_id")
    if str(Path(writer_input.storage_root_path)) != GOVERNED_VPS_PACKAGE_ROOT_PATH:
        raise ValueError("vps writer requires the governed package root")
    if tuple(writer_input.approved_storage_root_paths) != (
        GOVERNED_VPS_PACKAGE_ROOT_PATH,
    ):
        raise ValueError("vps writer requires exactly the governed package root")
    if writer_input.package_directory != run_id:
        raise ValueError("vps package directory must equal canonical_run_id")
    if not writer_input.allow_absolute_storage_root:
        raise ValueError("vps writer requires absolute governed root authority")
    expected_prefix = f"{run_id}/"
    if not writer_input.artifact_relative_path.startswith(expected_prefix):
        raise ValueError("vps artifact must be under the run package directory")
    if "order_state" in writer_input.artifact_relative_path:
        raise ValueError("order_state.json vps write is blocked")
    governed_package_dir = Path(GOVERNED_VPS_PACKAGE_ROOT_PATH) / run_id
    target_path = (
        Path(writer_input.storage_root_path) / writer_input.artifact_relative_path
    )
    if not _is_relative_to_pure(target_path, governed_package_dir):
        raise ValueError("vps target escapes the governed package directory")


def _build_result(
    writer_input: FilesystemWriterInput,
    target_path: Path,
    *,
    dry_run: bool,
    write_performed: bool,
) -> dict[str, Any]:
    expected_digest = _sha256(writer_input.artifact_bytes)
    return {
        "result_type": WRITER_RESULT,
        "canonical_run_id": writer_input.canonical_run_id,
        "storage_root": writer_input.storage_root,
        "package_path": writer_input.package_path,
        "package_directory": writer_input.package_directory,
        "artifact_relative_path": writer_input.artifact_relative_path,
        "artifact_path": str(target_path),
        "artifact_sha256": expected_digest,
        "hash_algorithm": WRITER_HASH_ALGORITHM,
        "lifecycle_status": writer_input.lifecycle_status,
        "dry_run": dry_run,
        "write_performed": write_performed,
        "atomic_write": True,
        "fsync_vocabulary": WRITER_FSYNC_VOCABULARY,
        "checksum_verification": WRITER_CHECKSUM_VERIFICATION,
        "rollback_marker": writer_input.rollback_marker,
        "no_overwrite": True,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "strategy_risk_execution_behavior": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": FILESYSTEM_WRITER_AUTHORITY_BOUNDARY,
    }


def _temporary_path_for(target_path: Path) -> Path:
    return target_path.with_name(f".{target_path.name}.tmp")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_relative_to_pure(candidate: Path, root: Path) -> bool:
    """Pure path-containment check that does not touch the filesystem."""
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


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
