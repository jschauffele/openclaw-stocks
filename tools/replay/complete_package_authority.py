"""Local complete replay package authority binder for Gate C mechanics.

This module validates complete replay package evidence from already-governed
inputs and tmp_path-only synthetic test packages. It binds package writer and
package persistence results, manifest/hash/integrity records, written-byte
evidence, finalized lifecycle, provenance, redaction status, and immutability
marker checks in memory only. It does not read files, write files, inspect
filesystem paths, execute runtime capture, discover artifacts against the
filesystem, ingest real source paths, read real VPS runtime artifacts, write
real VPS packages, evaluate or promote strategies, call broker APIs, authorize
execution, approve paper trading, or authorize live trading.

Local results validate mechanics only. Production Gate C completion requires
actual governed on-disk replay packages and a separate explicit VPS execution
gate (see Gate C Record C1). This module can never mark production Gate C
complete, open Gate D, or unblock Unit 12.

Governance basis: Gate C Record C1 (complete replay package authority
contract) and the IMPLEMENT_COMPLETE_PACKAGE_AUTHORITY gate.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


COMPLETE_PACKAGE_AUTHORITY = "complete_package_authority_local_mechanics_only"
COMPLETE_PACKAGE_AUTHORITY_RESULT = "complete_package_authority_result"
GOVERNED_PACKAGE_ROOT_LABEL = "replay_packages"
APPROVED_VPS_PACKAGE_ROOT_PATH = "/opt/openclaw-stocks/replay_packages"
COMPLETE_PACKAGE_AUTHORITY_LOCAL_TEST_ONLY = (
    "tmp_path_synthetic_evidence_validates_mechanics_only"
)
PRODUCTION_GATE_C_COMPLETION_REQUIRES_VPS_EXECUTION_GATE = (
    "production gate c completion requires a separate explicit vps execution gate"
)
ORDER_STATE_COMPLETE_PACKAGE_BINDING_BLOCKED = (
    "order_state.json complete package binding requires a later explicit binding gate"
)

ELIGIBLE_TERMINAL_COMPLETION_STATUSES: tuple[str, ...] = ("ok", "blocked")

COMPLETE_PACKAGE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "local_complete_package_authority_mechanics_only",
    "tmp_path_tests_do_not_satisfy_production_gate_c",
    "no_real_vps_package_writes",
    "no_real_vps_runtime_artifact_reads",
    "no_runtime_capture_execution",
    "no_order_state_binding",
    "no_gate_d_authority",
    "no_evaluation_or_promotion",
    "no_broker_api_authority",
    "no_strategy_risk_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

COMPLETE_PACKAGE_AUTHORITY_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_present",
    "terminal_completion_eligible_under_a2",
    "runtime_artifact_discovery_result_present",
    "source_artifact_authority_result_present",
    "source_path_ingestion_result_present",
    "runtime_artifact_metadata_present",
    "approved_file_read_result_present",
    "package_layout_result_present",
    "manifest_present",
    "deterministic_serialization_result_present",
    "hash_record_present",
    "integrity_validation_result_valid",
    "redaction_status_valid",
    "provenance_present",
    "package_writer_result_write_performed",
    "package_persistence_result_metadata_only",
    "storage_finalization_status_finalized",
    "known_written_bytes_evidence",
    "content_hash_verified_against_written_bytes",
    "section_hashes_verified_if_section_evidence_present",
    "no_overwrite_finalization_enforced",
    "immutability_marker_present",
    "absent_or_not_applicable_declarations_for_optional_artifacts",
    "fail_closed_on_stale_malformed_mixed_run_ambiguous_sensitive_or_missing_evidence",
)

COMPLETE_PACKAGE_AUTHORITY_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "mixed_run_id",
    "terminal_completion_not_eligible",
    "error_terminal_completion_status",
    "unknown_terminal_completion_status",
    "missing_runtime_artifact_discovery_result",
    "missing_source_artifact_authority_result",
    "missing_source_path_ingestion_result",
    "missing_runtime_artifact_metadata",
    "missing_approved_file_read_result",
    "missing_package_layout_result",
    "missing_manifest",
    "missing_deterministic_serialization_result",
    "missing_hash_record",
    "missing_integrity_validation_result",
    "failed_integrity_validation_result",
    "missing_redaction_status",
    "invalid_redaction_status",
    "missing_provenance",
    "sensitive_data_exposure",
    "missing_package_writer_result",
    "package_writer_write_not_performed",
    "package_writer_downstream_authority_claimed",
    "missing_package_persistence_result",
    "package_persistence_not_metadata_only",
    "package_persistence_downstream_authority_claimed",
    "missing_storage_finalization_result",
    "lifecycle_status_not_finalized",
    "missing_immutability_marker",
    "missing_no_overwrite_evidence",
    "missing_written_bytes_evidence",
    "content_hash_mismatch",
    "section_hash_mismatch",
    "stale_package_evidence",
    "malformed_package_evidence",
    "ambiguous_package_evidence",
    "invalid_optional_artifact_declaration",
    "order_state_binding_attempt",
    "production_gate_c_claimed_from_local_lane",
)

_REQUIRED_MAPPING_FIELDS: tuple[tuple[str, str], ...] = (
    ("runtime_artifact_discovery_result", "runtime artifact discovery result"),
    ("source_artifact_authority_result", "source artifact authority result"),
    ("source_path_ingestion_result", "source path ingestion result"),
    ("runtime_artifact_metadata", "runtime artifact metadata"),
    ("approved_file_read_result", "approved file-read result"),
    ("package_layout_result", "package layout result"),
    ("manifest", "manifest"),
    ("deterministic_serialization_result", "deterministic serialization result"),
    ("hash_record", "hash record"),
    ("integrity_validation_result", "integrity validation result"),
    ("package_writer_result", "package writer result"),
    ("package_persistence_result", "package persistence result"),
    ("storage_finalization_result", "storage finalization result"),
    ("written_artifact_evidence", "written artifact evidence"),
)

_DOWNSTREAM_AUTHORITY_KEYS: tuple[str, ...] = (
    "runtime_capture",
    "evaluation_or_promotion",
    "broker_api_authority",
    "live_trading_authority",
)

_ALLOWED_OPTIONAL_DECLARATIONS: tuple[str, ...] = ("absent", "not_applicable")


@dataclass(frozen=True, slots=True)
class CompletePackageAuthority:
    """Static complete package authority vocabulary."""

    name: str = COMPLETE_PACKAGE_AUTHORITY
    authority_boundary: tuple[str, ...] = COMPLETE_PACKAGE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class CompletePackageWrittenArtifactEvidence:
    """Already-loaded written-byte evidence for one governed package artifact."""

    canonical_run_id: str
    artifact_relative_path: str
    written_bytes: bytes
    content_hash: str


@dataclass(frozen=True, slots=True)
class CompletePackageAuthorityRequest:
    """Already-governed inputs for local complete package authority binding."""

    canonical_run_id: str
    terminal_completion_status: str
    terminal_completion_eligible: bool
    runtime_artifact_discovery_result: Mapping[str, Any]
    source_artifact_authority_result: Mapping[str, Any]
    source_path_ingestion_result: Mapping[str, Any]
    runtime_artifact_metadata: Mapping[str, Any]
    approved_file_read_result: Mapping[str, Any]
    package_layout_result: Mapping[str, Any]
    manifest: Mapping[str, Any]
    deterministic_serialization_result: Mapping[str, Any]
    hash_record: Mapping[str, Any]
    integrity_validation_result: Mapping[str, Any]
    redaction_status: str
    provenance: str
    package_writer_result: Mapping[str, Any]
    package_persistence_result: Mapping[str, Any]
    storage_finalization_result: Mapping[str, Any]
    written_artifact_evidence: Mapping[str, Any]
    immutability_marker: str
    optional_artifact_declarations: Mapping[str, Any] | None = None
    sensitive_data_status: str = "clear"
    production_gate_c_claimed: bool = False


@dataclass(frozen=True, slots=True)
class CompletePackageAuthorityResult:
    """Local complete package authority mechanics result.

    complete_package_authority is True only for locally valid mechanics over
    tmp_path/governed synthetic evidence. production_gate_c_complete is
    always False in this local implementation lane.
    """

    canonical_run_id: str
    content_hash: str
    storage_lifecycle_status: str
    immutability_marker: str
    result_type: str = COMPLETE_PACKAGE_AUTHORITY_RESULT
    complete_package_authority: bool = True
    local_mechanics_only: str = COMPLETE_PACKAGE_AUTHORITY_LOCAL_TEST_ONLY
    production_gate_c_complete: bool = False
    vps_execution_gate_required: bool = True
    real_vps_package_writes: bool = False
    real_vps_runtime_artifact_reads: bool = False
    runtime_capture_execution: bool = False
    order_state_binding: bool = False
    gate_d_authority: bool = False
    evaluation_or_promotion: bool = False
    broker_api_authority: bool = False
    strategy_risk_execution_authority: bool = False
    paper_trading_authority: bool = False
    live_trading_authority: bool = False
    governed_package_root_label: str = GOVERNED_PACKAGE_ROOT_LABEL
    approved_vps_package_root_path: str = APPROVED_VPS_PACKAGE_ROOT_PATH
    authority_boundary: tuple[str, ...] = COMPLETE_PACKAGE_AUTHORITY_BOUNDARY


def build_complete_package_authority_result(
    request: CompletePackageAuthorityRequest,
) -> CompletePackageAuthorityResult:
    """Bind and validate complete package evidence, or fail closed."""

    if request.production_gate_c_claimed:
        raise ValueError(PRODUCTION_GATE_C_COMPLETION_REQUIRES_VPS_EXECUTION_GATE)
    _validate_run_identity(request)
    _validate_terminal_completion(request)
    _validate_required_mappings(request)
    _validate_metadata(request)
    _validate_hash_and_integrity(request)
    _validate_package_writer_result(request)
    _validate_package_persistence_result(request)
    _validate_storage_finalization(request)
    content_hash = _validate_written_artifact_evidence(request)
    _validate_optional_artifact_declarations(request)
    _reject_order_state_binding(request)
    return CompletePackageAuthorityResult(
        canonical_run_id=request.canonical_run_id,
        content_hash=content_hash,
        storage_lifecycle_status="finalized",
        immutability_marker=request.immutability_marker,
    )


def _validate_run_identity(request: CompletePackageAuthorityRequest) -> None:
    if not request.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    for field_name, label in _REQUIRED_MAPPING_FIELDS:
        candidate = getattr(request, field_name)
        if isinstance(candidate, Mapping):
            _require_run_alignment(candidate, label, request.canonical_run_id)


def _require_run_alignment(
    candidate: Mapping[str, Any],
    label: str,
    canonical_run_id: str,
) -> None:
    for key in ("canonical_run_id", "run_id"):
        value = candidate.get(key)
        if value and value != canonical_run_id:
            raise ValueError(f"mixed run_id package evidence: {label}")
    for key in ("input_run_ids", "run_ids"):
        run_ids = candidate.get(key)
        if isinstance(run_ids, (tuple, list)):
            for run_id in run_ids:
                if run_id != canonical_run_id:
                    raise ValueError(f"mixed run_id package evidence: {label}")


def _validate_terminal_completion(request: CompletePackageAuthorityRequest) -> None:
    if request.terminal_completion_status == "error":
        raise ValueError(
            "error terminal completions are diagnostic only and not eligible"
        )
    if request.terminal_completion_status not in ELIGIBLE_TERMINAL_COMPLETION_STATUSES:
        raise ValueError("unknown terminal completion status")
    if request.terminal_completion_eligible is not True:
        raise ValueError("terminal completion is not eligible")


def _validate_required_mappings(request: CompletePackageAuthorityRequest) -> None:
    for field_name, label in _REQUIRED_MAPPING_FIELDS:
        candidate = getattr(request, field_name)
        if not isinstance(candidate, Mapping) or not candidate:
            raise ValueError(f"{label} is required")


def _validate_metadata(request: CompletePackageAuthorityRequest) -> None:
    if not isinstance(request.provenance, str) or not request.provenance:
        raise ValueError("missing provenance")
    if not request.redaction_status:
        raise ValueError("missing redaction status")
    if request.redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")
    if request.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")


def _validate_hash_and_integrity(request: CompletePackageAuthorityRequest) -> None:
    if not request.hash_record.get("digest"):
        raise ValueError("hash record is required")
    integrity_result = request.integrity_validation_result
    if integrity_result.get("integrity_status") != "valid":
        raise ValueError("integrity validation result must be valid")
    if integrity_result.get("hash_match") is not True:
        raise ValueError("integrity validation result must be valid")


def _validate_package_writer_result(request: CompletePackageAuthorityRequest) -> None:
    writer_result = request.package_writer_result
    if writer_result.get("write_performed") is not True:
        raise ValueError("package writer result must record a performed write")
    _reject_downstream_authority(writer_result, "package writer result")


def _validate_package_persistence_result(
    request: CompletePackageAuthorityRequest,
) -> None:
    persistence_result = request.package_persistence_result
    if persistence_result.get("actual_filesystem_writes") is not False:
        raise ValueError("package persistence result must be metadata-only")
    _reject_downstream_authority(persistence_result, "package persistence result")


def _reject_downstream_authority(
    candidate: Mapping[str, Any],
    label: str,
) -> None:
    for key in _DOWNSTREAM_AUTHORITY_KEYS:
        if candidate.get(key) is True:
            raise ValueError(f"{label} claims forbidden downstream authority: {key}")


def _validate_storage_finalization(request: CompletePackageAuthorityRequest) -> None:
    finalization_result = request.storage_finalization_result
    if finalization_result.get("lifecycle_status") != "finalized":
        raise ValueError("finalized lifecycle status is required")
    if not request.immutability_marker:
        raise ValueError("immutability marker is required")
    if not finalization_result.get("immutability_marker"):
        raise ValueError("immutability marker is required")
    if not finalization_result.get("no_overwrite_rule"):
        raise ValueError("no-overwrite finalization evidence is required")
    if request.package_writer_result.get("no_overwrite") is not True:
        raise ValueError("no-overwrite finalization evidence is required")


def _validate_written_artifact_evidence(
    request: CompletePackageAuthorityRequest,
) -> str:
    evidence = request.written_artifact_evidence
    for flag, message in (
        ("stale", "stale package evidence"),
        ("malformed", "malformed package evidence"),
        ("ambiguous", "ambiguous package evidence"),
    ):
        if evidence.get(flag):
            raise ValueError(message)
    written_bytes = evidence.get("written_bytes")
    if not isinstance(written_bytes, bytes) or not written_bytes:
        raise ValueError("known written bytes evidence is required")
    content_hash = evidence.get("content_hash")
    if not isinstance(content_hash, str) or not content_hash:
        raise ValueError("content hash is required")
    if hashlib.sha256(written_bytes).hexdigest() != content_hash:
        raise ValueError("content hash mismatch against written bytes")
    section_byte_evidence = evidence.get("section_byte_evidence")
    if section_byte_evidence is not None:
        if not isinstance(section_byte_evidence, Mapping):
            raise ValueError("malformed package evidence")
        for section_name, section_record in section_byte_evidence.items():
            if not isinstance(section_record, Mapping):
                raise ValueError("malformed package evidence")
            section_bytes = section_record.get("section_bytes")
            section_digest = section_record.get("digest")
            if not isinstance(section_bytes, bytes) or not section_bytes:
                raise ValueError(f"missing section bytes: {section_name}")
            if hashlib.sha256(section_bytes).hexdigest() != section_digest:
                raise ValueError(f"section hash mismatch: {section_name}")
    return content_hash


def _validate_optional_artifact_declarations(
    request: CompletePackageAuthorityRequest,
) -> None:
    declarations = request.optional_artifact_declarations
    if declarations is None:
        return
    if not isinstance(declarations, Mapping):
        raise ValueError("invalid optional artifact declaration")
    for artifact_name, declaration in declarations.items():
        if "order_state" in str(artifact_name) and declaration not in (
            _ALLOWED_OPTIONAL_DECLARATIONS
        ):
            raise ValueError(ORDER_STATE_COMPLETE_PACKAGE_BINDING_BLOCKED)
        if declaration not in _ALLOWED_OPTIONAL_DECLARATIONS:
            raise ValueError(f"invalid optional artifact declaration: {artifact_name}")


def _reject_order_state_binding(request: CompletePackageAuthorityRequest) -> None:
    evidence = request.written_artifact_evidence
    for key, value in evidence.items():
        if "order_state" in str(key):
            raise ValueError(ORDER_STATE_COMPLETE_PACKAGE_BINDING_BLOCKED)
        if isinstance(value, str) and "order_state" in value:
            raise ValueError(ORDER_STATE_COMPLETE_PACKAGE_BINDING_BLOCKED)
    artifact_family = request.approved_file_read_result.get("artifact_family")
    if isinstance(artifact_family, str) and "order_state" in artifact_family:
        raise ValueError(ORDER_STATE_COMPLETE_PACKAGE_BINDING_BLOCKED)
