"""Deterministic file-read helper for replay evidence.

This module reads only explicitly approved replay evidence files. It does not
read runtime logs, discover paths, ingest arbitrary paths, copy artifacts,
capture runtime output, evaluate or promote strategies, call broker APIs,
authorize execution, approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


FILE_READ_AUTHORITY = "file_read_authority"
REPLAY_FILE_READER = "replay_file_reader"
RUNTIME_ARTIFACT_FILE_READER = "runtime_artifact_file_reader"
SOURCE_ARTIFACT_FILE_READER = "source_artifact_file_reader"
APPROVED_FILE_READ_REQUEST = "approved_file_read_request"
APPROVED_FILE_READ_RESULT = "approved_file_read_result"
FILE_READ_PREFLIGHT_RESULT = "file_read_preflight_result"
FILE_READ_PATH_RESOLUTION_RESULT = "file_read_path_resolution_result"
FILE_READ_NO_ACCESS_RESULT = "file_read_no_access_result"
FILE_READ_CHECKSUM_RESULT = "file_read_checksum_result"
FILE_READ_SIZE_LIMIT_RESULT = "file_read_size_limit_result"
FILE_READ_ENCODING_RESULT = "file_read_encoding_result"
FILE_READ_PROVENANCE_RESULT = "file_read_provenance_result"
FILE_READ_REDACTION_RESULT = "file_read_redaction_result"
FILE_READ_RUN_ID_ALIGNMENT_RESULT = "file_read_run_id_alignment_result"
FILE_READ_TERMINAL_COMPLETION_PREREQUISITE = (
    "file_read_terminal_completion_prerequisite"
)
FILE_READ_FAILURE = "file_read_failure"
RUNTIME_LOG_ACCESS_PREREQUISITE = "runtime_log_access_prerequisite"
ARTIFACT_COPYING_PREREQUISITE = "artifact_copying_prerequisite"
RUNTIME_CAPTURE_PREREQUISITE = "runtime_capture_prerequisite"

FILE_READ_RESULT = "file_read_result"
FILE_READ_HASH_ALGORITHM = "sha256"

FILE_READ_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "deterministic_file_read_only",
    "approved_test_controlled_files_only",
    "no_runtime_log_access",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_capture",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

FILE_READ_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "runtime_artifact_discovery_result_present_and_valid",
    "source_artifact_authority_result_present_and_valid",
    "approved_source_reference_present_and_known",
    "approved_file_identity_explicit",
    "approved_storage_root_or_artifact_root_identity_explicit",
    "approved_path_metadata_explicit",
    "terminal_completion_rules_explicit",
    "provenance_present_and_valid",
    "redaction_status_present_and_valid",
    "eligible_runtime_artifact_vocabulary_explicit",
    "no_runtime_log_access",
    "no_file_path_ingestion_behavior",
    "no_source_path_ingestion_behavior",
    "no_artifact_copying",
    "no_runtime_artifact_capture",
    "no_runtime_capture",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
    "no_strategy_risk_execution_inputs",
    "no_paper_live_authority",
)

FILE_READ_FAIL_CLOSED_BOUNDARIES: tuple[str, ...] = (
    "missing_runtime_artifact_discovery_result",
    "failed_runtime_artifact_discovery_result",
    "missing_source_artifact_authority_result",
    "failed_source_artifact_authority_result",
    "missing_source_references",
    "unknown_source_references",
    "ambiguous_source_references",
    "missing_approved_file_identity",
    "unapproved_file_identity",
    "missing_approved_artifact_root",
    "unapproved_artifact_root",
    "missing_approved_path_metadata",
    "malformed_approved_path_metadata",
    "path_traversal",
    "absolute_path_injection",
    "symlink_ambiguity",
    "non_repo_path_ambiguity",
    "missing_terminal_completion_rule",
    "failed_terminal_completion_rule",
    "missing_provenance",
    "malformed_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
    "missing_eligible_runtime_artifact_vocabulary",
    "malformed_eligible_runtime_artifact_vocabulary",
    "sensitive_data_exposure",
    "stale_file_read_metadata",
    "malformed_file_read_metadata",
    "mixed_run_id",
    "runtime_log_dependency",
    "source_path_ingestion_dependency",
    "file_path_ingestion_dependency",
    "artifact_copying_dependency",
    "runtime_artifact_capture_dependency",
    "runtime_capture_dependency",
    "evaluation_dependency",
    "broker_dependency",
    "strategy_risk_execution_dependency",
    "file_read_authority_as_runtime_log_access",
    "file_read_authority_as_artifact_copying",
    "file_read_authority_as_runtime_capture",
    "file_read_authority_as_evaluation_approval",
    "file_read_authority_as_execution_permission",
    "file_read_authority_as_paper_trading_authority",
    "file_read_authority_as_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class FileReadAuthority:
    """Static file-read authority vocabulary."""

    name: str = FILE_READ_AUTHORITY
    authority_boundary: tuple[str, ...] = FILE_READ_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class ReplayFileReader:
    """Static replay file reader vocabulary."""

    name: str = REPLAY_FILE_READER


@dataclass(frozen=True, slots=True)
class RuntimeArtifactFileReader:
    """Static runtime artifact file reader vocabulary."""

    name: str = RUNTIME_ARTIFACT_FILE_READER


@dataclass(frozen=True, slots=True)
class SourceArtifactFileReader:
    """Static source artifact file reader vocabulary."""

    name: str = SOURCE_ARTIFACT_FILE_READER


@dataclass(frozen=True, slots=True)
class ApprovedFileReadRequest:
    """Already-approved file-read request metadata."""

    canonical_run_id: str
    runtime_artifact_discovery_result: Mapping[str, Any]
    source_artifact_authority_result: Mapping[str, Any]
    source_references: tuple[str, ...]
    known_source_references: tuple[str, ...]
    approved_file_identity: str
    approved_file_identities: tuple[str, ...]
    artifact_root: str
    approved_artifact_roots: tuple[str, ...]
    artifact_root_path: str
    approved_artifact_root_paths: tuple[str, ...]
    file_relative_path: str
    approved_path_metadata: Mapping[str, Any]
    terminal_completion_rule: Mapping[str, Any]
    provenance: str
    redaction_status: str
    eligible_runtime_artifact_vocabulary: tuple[str, ...]
    input_run_ids: tuple[str, ...]
    expected_sha256: str | None = None
    max_size_bytes: int | None = None
    expected_encoding: str | None = None
    allow_absolute_artifact_root: bool = False
    symlink_status: str = "not_symlink"
    repo_relative: bool = True
    sensitive_data_status: str = "clear"
    stale_file_read_metadata: bool = False
    malformed_file_read_metadata: bool = False
    ambiguous_source_references: bool = False
    runtime_log_dependent: bool = False
    source_path_ingestion_dependent: bool = False
    file_path_ingestion_dependent: bool = False
    artifact_copying_dependent: bool = False
    runtime_artifact_capture_dependent: bool = False
    runtime_capture_dependent: bool = False
    evaluation_dependent: bool = False
    broker_dependent: bool = False
    strategy_risk_execution_dependent: bool = False
    attempted_runtime_log_access: bool = False
    attempted_artifact_copying: bool = False
    attempted_runtime_capture: bool = False
    attempted_evaluation_approval: bool = False
    attempted_execution_permission: bool = False
    attempted_paper_trading_authority: bool = False
    attempted_live_trading_authority: bool = False
    paper_trading_authority: bool = False
    live_trading_authority: bool = False


@dataclass(frozen=True, slots=True)
class ApprovedFileReadResult:
    """Static approved file-read result vocabulary."""

    result_type: str = APPROVED_FILE_READ_RESULT


@dataclass(frozen=True, slots=True)
class FileReadPreflightResult:
    """Static file-read preflight result vocabulary."""

    result_type: str = FILE_READ_PREFLIGHT_RESULT


@dataclass(frozen=True, slots=True)
class FileReadPathResolutionResult:
    """Static file-read path resolution result vocabulary."""

    result_type: str = FILE_READ_PATH_RESOLUTION_RESULT


@dataclass(frozen=True, slots=True)
class FileReadNoAccessResult:
    """Static no-access result vocabulary."""

    result_type: str = FILE_READ_NO_ACCESS_RESULT
    authority_boundary: tuple[str, ...] = FILE_READ_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class FileReadChecksumResult:
    """Static file-read checksum result vocabulary."""

    result_type: str = FILE_READ_CHECKSUM_RESULT


@dataclass(frozen=True, slots=True)
class FileReadSizeLimitResult:
    """Static file-read size limit result vocabulary."""

    result_type: str = FILE_READ_SIZE_LIMIT_RESULT


@dataclass(frozen=True, slots=True)
class FileReadEncodingResult:
    """Static file-read encoding result vocabulary."""

    result_type: str = FILE_READ_ENCODING_RESULT


@dataclass(frozen=True, slots=True)
class FileReadProvenanceResult:
    """Static file-read provenance result vocabulary."""

    result_type: str = FILE_READ_PROVENANCE_RESULT


@dataclass(frozen=True, slots=True)
class FileReadRedactionResult:
    """Static file-read redaction result vocabulary."""

    result_type: str = FILE_READ_REDACTION_RESULT


@dataclass(frozen=True, slots=True)
class FileReadRunIdAlignmentResult:
    """Static file-read run_id alignment result vocabulary."""

    result_type: str = FILE_READ_RUN_ID_ALIGNMENT_RESULT


@dataclass(frozen=True, slots=True)
class FileReadTerminalCompletionPrerequisite:
    """Static file-read terminal completion prerequisite vocabulary."""

    name: str = FILE_READ_TERMINAL_COMPLETION_PREREQUISITE


@dataclass(frozen=True, slots=True)
class FileReadFailure:
    """Static fail-closed file-read vocabulary."""

    result_type: str = FILE_READ_FAILURE


@dataclass(frozen=True, slots=True)
class RuntimeLogAccessPrerequisite:
    """Static runtime log access prerequisite vocabulary."""

    name: str = RUNTIME_LOG_ACCESS_PREREQUISITE


@dataclass(frozen=True, slots=True)
class ArtifactCopyingPrerequisite:
    """Static artifact copying prerequisite vocabulary."""

    name: str = ARTIFACT_COPYING_PREREQUISITE


@dataclass(frozen=True, slots=True)
class RuntimeCapturePrerequisite:
    """Static runtime capture prerequisite vocabulary."""

    name: str = RUNTIME_CAPTURE_PREREQUISITE


def validate_file_read_authority(
    read_request: ApprovedFileReadRequest | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate approved file-read metadata without reading file bytes."""

    return build_file_read_preflight_result(read_request)


def build_file_read_preflight_result(
    read_request: ApprovedFileReadRequest | Mapping[str, Any],
) -> dict[str, Any]:
    """Build an approved file-read preflight result without reading."""

    normalized = _normalize_read_request(read_request)
    target_path = _validate_read_request(normalized)
    return {
        **_build_result(
            normalized,
            target_path,
            file_bytes=None,
            dry_run=True,
            read_performed=False,
        ),
        "result_type": FILE_READ_PREFLIGHT_RESULT,
    }


def resolve_approved_file_read_path(
    read_request: ApprovedFileReadRequest | Mapping[str, Any],
) -> dict[str, Any]:
    """Resolve the approved file path without reading."""

    normalized = _normalize_read_request(read_request)
    target_path = _validate_read_request(normalized)
    return {
        **_build_result(
            normalized,
            target_path,
            file_bytes=None,
            dry_run=True,
            read_performed=False,
        ),
        "result_type": FILE_READ_PATH_RESOLUTION_RESULT,
    }


def dry_run_file_read(
    read_request: ApprovedFileReadRequest | Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic no-access file-read dry run."""

    normalized = _normalize_read_request(read_request)
    target_path = _validate_read_request(normalized)
    return {
        **_build_result(
            normalized,
            target_path,
            file_bytes=None,
            dry_run=True,
            read_performed=False,
        ),
        "result_type": FILE_READ_NO_ACCESS_RESULT,
    }


def read_approved_replay_file(
    read_request: ApprovedFileReadRequest | Mapping[str, Any],
) -> dict[str, Any]:
    """Read one explicitly approved replay evidence file."""

    normalized = _normalize_read_request(read_request)
    target_path = _validate_read_request(normalized)
    file_bytes = target_path.read_bytes()
    _validate_observed_bytes(normalized, file_bytes)
    return {
        **_build_result(
            normalized,
            target_path,
            file_bytes=file_bytes,
            dry_run=False,
            read_performed=True,
        ),
        "result_type": APPROVED_FILE_READ_RESULT,
        "file_bytes": file_bytes,
    }


def compute_file_read_checksum(payload: bytes) -> str:
    """Compute a deterministic checksum for already-loaded file bytes."""

    if not isinstance(payload, bytes):
        raise TypeError("file read checksum payload must be bytes")
    return _sha256(payload)


def _normalize_read_request(
    read_request: ApprovedFileReadRequest | Mapping[str, Any],
) -> ApprovedFileReadRequest:
    if isinstance(read_request, ApprovedFileReadRequest):
        return read_request
    if not isinstance(read_request, Mapping):
        raise TypeError("file read request must be approved metadata")
    return ApprovedFileReadRequest(**read_request)


def _validate_read_request(read_request: ApprovedFileReadRequest) -> Path:
    _reject_forbidden_dependencies(read_request)
    _validate_authority_results(read_request)
    _validate_file_identity(read_request)
    _validate_metadata(read_request)
    target_path = _resolve_target_path(read_request)
    _validate_target_path(read_request, target_path)
    return target_path


def _reject_forbidden_dependencies(read_request: ApprovedFileReadRequest) -> None:
    if read_request.malformed_file_read_metadata:
        raise ValueError("malformed file-read metadata")
    if read_request.stale_file_read_metadata:
        raise ValueError("stale file-read metadata")
    if read_request.ambiguous_source_references:
        raise ValueError("ambiguous source references")
    if read_request.runtime_log_dependent or read_request.attempted_runtime_log_access:
        raise ValueError("file-read authority is not runtime log access")
    if read_request.source_path_ingestion_dependent:
        raise ValueError("source path ingestion dependency")
    if read_request.file_path_ingestion_dependent:
        raise ValueError("file path ingestion dependency")
    if read_request.artifact_copying_dependent or read_request.attempted_artifact_copying:
        raise ValueError("file-read authority is not artifact copying")
    if read_request.runtime_artifact_capture_dependent:
        raise ValueError("runtime artifact capture dependency")
    if read_request.runtime_capture_dependent or read_request.attempted_runtime_capture:
        raise ValueError("file-read authority is not runtime capture")
    if read_request.evaluation_dependent or read_request.attempted_evaluation_approval:
        raise ValueError("file-read success is not evaluation approval")
    if read_request.broker_dependent:
        raise ValueError("broker dependency")
    if read_request.strategy_risk_execution_dependent:
        raise ValueError("strategy/risk/execution dependency")
    if read_request.attempted_execution_permission:
        raise ValueError("file-read success is not execution permission")
    if read_request.attempted_paper_trading_authority or (
        read_request.paper_trading_authority
    ):
        raise ValueError("file-read success is not paper trading authority")
    if read_request.attempted_live_trading_authority or (
        read_request.live_trading_authority
    ):
        raise ValueError("file-read success is not live trading authority")


def _validate_authority_results(read_request: ApprovedFileReadRequest) -> None:
    discovery_result = read_request.runtime_artifact_discovery_result
    if not isinstance(discovery_result, Mapping) or not discovery_result:
        raise ValueError("runtime artifact discovery result is required")
    if discovery_result.get("runtime_artifact_discovery_authority") is not True:
        raise ValueError("runtime artifact discovery result must be valid")
    if discovery_result.get("metadata_only") is not True:
        raise ValueError("runtime artifact discovery result must be metadata-only")
    if discovery_result.get("file_reads") is not False:
        raise ValueError("runtime artifact discovery must not read files")
    if discovery_result.get("runtime_capture") is not False:
        raise ValueError("runtime artifact discovery must not capture runtime data")
    if discovery_result.get("canonical_run_id") != read_request.canonical_run_id:
        raise ValueError("mixed run_id file-read metadata")
    source_result = read_request.source_artifact_authority_result
    if not isinstance(source_result, Mapping) or not source_result:
        raise ValueError("source artifact authority result is required")
    if source_result.get("source_artifact_authority") is not True:
        raise ValueError("source artifact authority result must be valid")
    if source_result.get("metadata_only") is not True:
        raise ValueError("source artifact authority result must be metadata-only")
    if source_result.get("file_path_ingestion") is not False:
        raise ValueError("source artifact authority must not ingest paths")
    if source_result.get("runtime_capture") is not False:
        raise ValueError("source artifact authority must not capture runtime data")
    if source_result.get("canonical_run_id") != read_request.canonical_run_id:
        raise ValueError("mixed run_id file-read metadata")


def _validate_file_identity(read_request: ApprovedFileReadRequest) -> None:
    if not read_request.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not read_request.approved_file_identity:
        raise ValueError("approved file identity is required")
    if read_request.approved_file_identity not in read_request.approved_file_identities:
        raise ValueError("unapproved file identity")
    if not read_request.artifact_root:
        raise ValueError("approved artifact root is required")
    if read_request.artifact_root not in read_request.approved_artifact_roots:
        raise ValueError("unapproved artifact root")
    for run_id in read_request.input_run_ids:
        if run_id != read_request.canonical_run_id:
            raise ValueError("mixed run_id file-read metadata")


def _validate_metadata(read_request: ApprovedFileReadRequest) -> None:
    if not read_request.source_references:
        raise ValueError("missing source references")
    known_references = set(read_request.known_source_references)
    if not known_references:
        raise ValueError("unknown source references")
    for source_reference in read_request.source_references:
        if source_reference not in known_references:
            raise ValueError("unknown source references")
    if not isinstance(read_request.terminal_completion_rule, Mapping) or not (
        read_request.terminal_completion_rule
    ):
        raise ValueError("missing terminal completion rule")
    if read_request.terminal_completion_rule.get("required") is not True:
        raise ValueError("missing terminal completion rule")
    if read_request.terminal_completion_rule.get("satisfied") is not True:
        raise ValueError("failed terminal completion rule")
    if not isinstance(read_request.provenance, str):
        raise ValueError("malformed provenance")
    if not read_request.provenance:
        raise ValueError("missing provenance")
    if not read_request.redaction_status:
        raise ValueError("missing redaction status")
    if read_request.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if not read_request.eligible_runtime_artifact_vocabulary:
        raise ValueError("missing eligible runtime artifact vocabulary")
    for artifact_type in read_request.eligible_runtime_artifact_vocabulary:
        if not isinstance(artifact_type, str) or not artifact_type:
            raise ValueError("malformed eligible runtime artifact vocabulary")
    if read_request.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")
    if read_request.max_size_bytes is not None and read_request.max_size_bytes < 1:
        raise ValueError("malformed file-read metadata")
    if read_request.expected_encoding is not None and not (
        isinstance(read_request.expected_encoding, str)
        and read_request.expected_encoding
    ):
        raise ValueError("malformed file-read metadata")


def _resolve_target_path(read_request: ApprovedFileReadRequest) -> Path:
    if not isinstance(read_request.approved_path_metadata, Mapping) or not (
        read_request.approved_path_metadata
    ):
        raise ValueError("approved path metadata is required")
    if read_request.approved_path_metadata.get("approved") is not True:
        raise ValueError("malformed approved path metadata")
    if read_request.approved_path_metadata.get("file_identity") != (
        read_request.approved_file_identity
    ):
        raise ValueError("malformed approved path metadata")
    metadata_relative_path = read_request.approved_path_metadata.get("relative_path")
    if metadata_relative_path != read_request.file_relative_path:
        raise ValueError("malformed approved path metadata")
    if _has_path_traversal_shape(read_request.file_relative_path):
        raise ValueError("path traversal")
    if _has_absolute_path_shape(read_request.file_relative_path):
        raise ValueError("absolute path injection")
    artifact_root_path = Path(read_request.artifact_root_path)
    if artifact_root_path.is_absolute() and not (
        read_request.allow_absolute_artifact_root
    ):
        raise ValueError("absolute path injection")
    if str(artifact_root_path) not in read_request.approved_artifact_root_paths:
        raise ValueError("unapproved artifact root")
    return artifact_root_path / read_request.file_relative_path


def _validate_target_path(
    read_request: ApprovedFileReadRequest,
    target_path: Path,
) -> None:
    artifact_root_path = Path(read_request.artifact_root_path)
    if not _is_relative_to(target_path, artifact_root_path):
        raise ValueError("unapproved path")
    if read_request.symlink_status != "not_symlink":
        raise ValueError("symlink ambiguity")
    if target_path.is_symlink() or artifact_root_path.is_symlink():
        raise ValueError("symlink ambiguity")
    if read_request.repo_relative is not True:
        raise ValueError("non-repo path ambiguity")
    if not target_path.exists():
        raise ValueError("unapproved path")
    if not target_path.is_file():
        raise ValueError("unapproved path")


def _validate_observed_bytes(
    read_request: ApprovedFileReadRequest,
    file_bytes: bytes,
) -> None:
    if read_request.max_size_bytes is not None and len(file_bytes) > (
        read_request.max_size_bytes
    ):
        raise ValueError("file read size limit exceeded")
    if read_request.expected_sha256 is not None and _sha256(file_bytes) != (
        read_request.expected_sha256
    ):
        raise ValueError("checksum verification failed")
    if read_request.expected_encoding is not None:
        try:
            file_bytes.decode(read_request.expected_encoding)
        except UnicodeError as exc:
            raise ValueError("file read encoding validation failed") from exc


def _build_result(
    read_request: ApprovedFileReadRequest,
    target_path: Path,
    *,
    file_bytes: bytes | None,
    dry_run: bool,
    read_performed: bool,
) -> dict[str, Any]:
    observed_sha256 = _sha256(file_bytes) if file_bytes is not None else None
    return {
        "result_type": FILE_READ_RESULT,
        "canonical_run_id": read_request.canonical_run_id,
        "approved_file_identity": read_request.approved_file_identity,
        "artifact_root": read_request.artifact_root,
        "file_relative_path": read_request.file_relative_path,
        "file_path": str(target_path),
        "observed_sha256": observed_sha256,
        "expected_sha256": read_request.expected_sha256,
        "hash_algorithm": FILE_READ_HASH_ALGORITHM,
        "max_size_bytes": read_request.max_size_bytes,
        "expected_encoding": read_request.expected_encoding,
        "dry_run": dry_run,
        "read_performed": read_performed,
        "checksum_verified": (
            observed_sha256 == read_request.expected_sha256
            if read_request.expected_sha256 is not None and observed_sha256 is not None
            else False
        ),
        "runtime_log_access": False,
        "source_path_ingestion": False,
        "file_path_ingestion": False,
        "artifact_copying": False,
        "runtime_artifact_capture": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "strategy_risk_execution_behavior": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": FILE_READ_AUTHORITY_BOUNDARY,
        "prerequisites": FILE_READ_PREREQUISITES,
        "fail_closed_boundaries": FILE_READ_FAIL_CLOSED_BOUNDARIES,
    }


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
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
