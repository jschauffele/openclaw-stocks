"""Deterministic replay package-execution orchestration layer.

This module chains the governed replay package modules into a single
deterministic, fail-closed orchestration:

1. derive A2 terminal-completion eligibility from already-read JSONL bytes,
2. validate last_run_report.json alignment from already-read report bytes,
3. assemble manifest / hash / integrity / package-creation / storage evidence
   through existing source-controlled modules,
4. write one governed package artifact via package_writer.py (tmp_path only in
   tests),
5. build package persistence metadata,
6. bind the result through complete_package_authority.py.

It is exercised now only with tmp_path synthetic evidence. It contains a
hard-pinned future ``vps`` mode whose roots must equal the source-controlled
governed roots, but that mode is not executed in this gate: it fails closed and
defers to a separate bounded VPS execution gate. This module does not read real
VPS artifacts, write real VPS packages, create repo-root replay_packages,
execute runtime capture, bind order_state.json, self-declare production Gate C
completion, open Gate D, unblock Unit 12, evaluate, promote, or touch
broker/API/trading.

This module performs no direct filesystem access. All real writes are delegated
to package_writer.py / filesystem_writer.py under tmp_path in tests.

Governance basis: Gate C Record C1 (complete replay package authority
contract) and the IMPLEMENT_PACKAGE_EXECUTION_ORCHESTRATOR gate.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import sys
from typing import Any, Mapping, Sequence

import tools.replay.canonical_bytes as canonical_bytes
import tools.replay.canonical_json as canonical_json
import tools.replay.complete_package_authority as complete_package_authority
import tools.replay.filesystem_storage_authority as filesystem_storage_authority
import tools.replay.hash_computation as hash_computation
import tools.replay.hashing as hashing
import tools.replay.integrity_validation as integrity_validation
import tools.replay.manifest_builder as manifest_builder
import tools.replay.package_completeness as package_completeness
import tools.replay.package_creation as package_creation
import tools.replay.package_layout as package_layout
import tools.replay.package_persistence as package_persistence
import tools.replay.package_writer as package_writer
import tools.replay.runtime_artifact_discovery as runtime_artifact_discovery
import tools.replay.runtime_artifacts as runtime_artifacts
import tools.replay.source_artifacts as source_artifacts
import tools.replay.source_path_ingestion as source_path_ingestion
import tools.replay.storage_implementation as storage_implementation
from tools.replay.last_run_report_alignment import (
    LastRunReportAlignmentRequest,
    validate_last_run_report_alignment,
)
from tools.replay.source_paths import KNOWN_SOURCE_PATH_FAMILIES
from tools.replay.terminal_completion_evaluator import (
    TerminalCompletionEvaluationRequest,
    evaluate_terminal_completion_jsonl,
)


PACKAGE_EXECUTION_ORCHESTRATOR_AUTHORITY = "package_execution_orchestrator_authority"
PACKAGE_EXECUTION_ORCHESTRATOR_RESULT = "package_execution_orchestrator_result"
GOVERNED_ARTIFACT_ROOT = "/opt/openclaw-stocks"
GOVERNED_PACKAGE_ROOT = "/opt/openclaw-stocks/replay_packages"
GOVERNED_PACKAGE_ROOT_LABEL = "replay_packages"
PACKAGE_EXECUTION_LOCAL_TEST_ONLY = (
    "tmp_path_synthetic_evidence_validates_mechanics_only"
)
PRODUCTION_GATE_C_COMPLETION_REQUIRES_DOCS_RECORD = (
    "production gate c completion requires a separate docs record and a bounded "
    "vps execution gate"
)
PACKAGE_EXECUTION_VPS_COMMAND_CANDIDATE = (
    "package_execution_orchestrator --run-id <run_id> --execution-mode vps"
)
VPS_EXECUTION_DEFERRED_MESSAGE = (
    "vps execution is not authorized in this lane; it requires a separate bounded "
    "vps execution gate"
)
ORDER_STATE_EXECUTION_BLOCKED_MESSAGE = (
    "order_state.json binding is blocked pending a later explicit binding gate"
)

EXECUTION_MODE_TMP_PATH_TEST = "tmp_path_test"
EXECUTION_MODE_VPS = "vps"
ALLOWED_EXECUTION_MODES: tuple[str, ...] = (
    EXECUTION_MODE_TMP_PATH_TEST,
    EXECUTION_MODE_VPS,
)

_EVENT_JSONL_REF = "event_jsonl"
_DRAFT_PACKAGE_REF = "draft_package"
_GOVERNED_SOURCE_REFERENCES: tuple[str, ...] = (_EVENT_JSONL_REF, _DRAFT_PACKAGE_REF)

PACKAGE_EXECUTION_ORCHESTRATOR_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "orchestrates_governed_artifact_reads_only",
    "terminal_completion_derived_from_jsonl_bytes",
    "last_run_report_alignment_required",
    "package_output_root_hard_pinned",
    "tmp_path_tests_do_not_satisfy_production_gate_c",
    "no_direct_filesystem_access_in_orchestrator",
    "no_real_vps_runtime_artifact_reads",
    "no_real_vps_package_writes",
    "no_runtime_capture_execution",
    "no_order_state_binding",
    "no_gate_d_authority",
    "no_evaluation_or_promotion",
    "no_broker_api_authority",
    "no_strategy_risk_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

PACKAGE_EXECUTION_ORCHESTRATOR_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "unknown_execution_mode",
    "production_gate_c_claimed_from_local_lane",
    "order_state_binding_attempt",
    "vps_execution_not_authorized_in_this_lane",
    "vps_mode_unapproved_artifact_root",
    "vps_mode_unapproved_package_root",
    "tmp_path_mode_governed_vps_root_rejected",
    "tmp_path_mode_non_absolute_root_rejected",
    "terminal_completion_not_eligible",
    "error_terminal_completion_status",
    "stale_last_run_report",
    "report_status_contradiction",
    "malformed_package_evidence",
    "content_hash_mismatch",
    "mixed_run_id",
)


@dataclass(frozen=True, slots=True)
class PackageExecutionRequest:
    """Inputs for a deterministic local package-execution orchestration."""

    canonical_run_id: str
    execution_mode: str
    artifact_root_path: str
    package_root_path: str
    jsonl_filename: str
    jsonl_bytes: bytes
    last_run_report_bytes: bytes
    package_dir_path: str
    approved_artifact_root_paths: tuple[str, ...]
    approved_package_root_paths: tuple[str, ...]
    provenance: str = "recorded"
    redaction_status: str = "not_required"
    sensitive_data_status: str = "clear"
    production_gate_c_claimed: bool = False


@dataclass(frozen=True, slots=True)
class PackageExecutionResult:
    """Deterministic local package-execution orchestration result."""

    canonical_run_id: str
    execution_mode: str
    terminal_completion_status: str
    written_artifact_path: str
    written_artifact_sha256: str
    complete_package_authority_result: Any
    result_type: str = PACKAGE_EXECUTION_ORCHESTRATOR_RESULT
    complete_package_authority: bool = True
    local_mechanics_only: str = PACKAGE_EXECUTION_LOCAL_TEST_ONLY
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
    governed_package_root: str = GOVERNED_PACKAGE_ROOT
    authority_boundary: tuple[str, ...] = (
        PACKAGE_EXECUTION_ORCHESTRATOR_AUTHORITY_BOUNDARY
    )


def execute_package_orchestration(
    request: PackageExecutionRequest,
) -> PackageExecutionResult:
    """Run the deterministic package-execution chain, or fail closed."""

    if not request.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if request.execution_mode not in ALLOWED_EXECUTION_MODES:
        raise ValueError(f"unknown execution_mode: '{request.execution_mode}'")
    if request.production_gate_c_claimed:
        raise ValueError(PRODUCTION_GATE_C_COMPLETION_REQUIRES_DOCS_RECORD)
    _reject_order_state(request)
    _validate_roots_for_mode(request)

    if request.execution_mode == EXECUTION_MODE_VPS:
        # Roots are validated above; real VPS execution is deferred to a separate
        # bounded gate and never performed here.
        raise ValueError(VPS_EXECUTION_DEFERRED_MESSAGE)

    run_id = request.canonical_run_id

    terminal = evaluate_terminal_completion_jsonl(
        TerminalCompletionEvaluationRequest(
            canonical_run_id=run_id,
            jsonl_bytes=request.jsonl_bytes,
            jsonl_filename=request.jsonl_filename,
            expected_filename_stem=run_id,
        )
    )
    validate_last_run_report_alignment(
        LastRunReportAlignmentRequest(
            canonical_run_id=run_id,
            report_bytes=request.last_run_report_bytes,
            terminal_completion_status=terminal.terminal_completion_status,
            terminal_completion_eligible=terminal.terminal_completion_eligible,
        )
    )

    evidence = _assemble_governed_evidence(request, run_id)
    cpa_result = complete_package_authority.build_complete_package_authority_result(
        evidence["cpa_request"]
    )
    writer_result = evidence["writer_result"]
    return PackageExecutionResult(
        canonical_run_id=run_id,
        execution_mode=request.execution_mode,
        terminal_completion_status=terminal.terminal_completion_status,
        written_artifact_path=writer_result["artifact_path"],
        written_artifact_sha256=writer_result["artifact_sha256"],
        complete_package_authority_result=cpa_result,
    )


def _reject_order_state(request: PackageExecutionRequest) -> None:
    for value in (
        request.canonical_run_id,
        request.jsonl_filename,
        request.package_dir_path,
        request.package_root_path,
        request.artifact_root_path,
    ):
        if "order_state" in str(value):
            raise ValueError(ORDER_STATE_EXECUTION_BLOCKED_MESSAGE)


def _validate_roots_for_mode(request: PackageExecutionRequest) -> None:
    if request.execution_mode == EXECUTION_MODE_VPS:
        if request.artifact_root_path != GOVERNED_ARTIFACT_ROOT:
            raise ValueError("vps mode requires the governed artifact root")
        if request.package_root_path != GOVERNED_PACKAGE_ROOT:
            raise ValueError("vps mode requires the governed package root")
        if tuple(request.approved_artifact_root_paths) != (GOVERNED_ARTIFACT_ROOT,):
            raise ValueError("vps mode requires exactly the governed artifact root")
        if tuple(request.approved_package_root_paths) != (GOVERNED_PACKAGE_ROOT,):
            raise ValueError("vps mode requires exactly the governed package root")
        return

    # tmp_path_test mode
    for root in (request.artifact_root_path, request.package_root_path):
        if not root.startswith("/"):
            raise ValueError("tmp_path_test roots must be absolute test paths")
    if request.artifact_root_path == GOVERNED_ARTIFACT_ROOT:
        raise ValueError("tmp_path_test mode must not use the governed VPS artifact root")
    if request.package_root_path == GOVERNED_PACKAGE_ROOT:
        raise ValueError("tmp_path_test mode must not use the governed VPS package root")
    if request.package_root_path not in request.approved_package_root_paths:
        raise ValueError("tmp_path_test package root must be approved")


def _assemble_governed_evidence(
    request: PackageExecutionRequest,
    run_id: str,
) -> dict[str, Any]:
    provenance = request.provenance
    redaction_status = request.redaction_status
    package_id = f"package_{run_id}"

    package_creation_result = package_creation.build_draft_package(
        _draft_package_creation_input(run_id, package_id, provenance, redaction_status)
    )
    package_hash = package_creation_result["hash_records"][0]
    integrity_result = package_creation_result["integrity_validation_result"]

    storage_finalization_result = storage_implementation.build_finalized_storage_record(
        _storage_writer_metadata_input(
            run_id, package_id, package_creation_result, provenance, redaction_status
        )
    )
    storage_impl_result = storage_finalization_result
    fsa_result = storage_impl_result["filesystem_storage_authority_result"]

    completeness_result = package_completeness.validate_package_completeness(
        _package_completeness_evidence(
            run_id, package_id, storage_impl_result, provenance, redaction_status
        )
    )

    artifact_bytes = _package_artifact_bytes(run_id, package_id)
    content_hash = hashlib.sha256(artifact_bytes).hexdigest()

    writer_result = package_writer.write_package_artifact(
        _package_writer_request(
            request,
            run_id,
            fsa_result,
            completeness_result,
            storage_impl_result,
            artifact_bytes,
            provenance,
            redaction_status,
        )
    )
    persistence_result = package_persistence.build_package_persistence_result(
        _package_persistence_request(
            run_id, fsa_result, storage_impl_result, provenance, redaction_status
        )
    )

    written_artifact_evidence = {
        "canonical_run_id": run_id,
        "artifact_relative_path": f"{run_id}/manifest.json",
        "written_bytes": artifact_bytes,
        "content_hash": content_hash,
    }

    cpa_request = complete_package_authority.CompletePackageAuthorityRequest(
        canonical_run_id=run_id,
        terminal_completion_status="blocked",
        terminal_completion_eligible=True,
        runtime_artifact_discovery_result=_discovery_result(run_id, provenance, redaction_status),
        source_artifact_authority_result=_source_artifact_result(run_id, provenance, redaction_status),
        source_path_ingestion_result=_source_path_ingestion_result(run_id, provenance, redaction_status),
        runtime_artifact_metadata=_runtime_artifact_metadata(run_id, provenance, redaction_status),
        approved_file_read_result=_approved_file_read_result(run_id, request.jsonl_bytes, provenance, redaction_status),
        package_layout_result=_package_layout_result(run_id, package_id),
        manifest=package_creation_result["manifest"],
        deterministic_serialization_result=_serialization_result(run_id),
        hash_record=package_hash,
        integrity_validation_result=integrity_result,
        redaction_status=redaction_status,
        provenance=provenance,
        package_writer_result=writer_result,
        package_persistence_result=persistence_result,
        storage_finalization_result=storage_finalization_result,
        written_artifact_evidence=written_artifact_evidence,
        immutability_marker=storage_implementation.IMMUTABILITY_MARKER,
        optional_artifact_declarations={
            "order_state": "absent",
            "observations": "not_applicable",
            "runtime_visibility": "not_applicable",
        },
        sensitive_data_status=request.sensitive_data_status,
        production_gate_c_claimed=False,
    )
    return {"cpa_request": cpa_request, "writer_result": writer_result}


# --- governed input builders (parameterized by run_id and roots) ---


def _hash_metadata(run_id: str, provenance: str, redaction_status: str) -> dict[str, Any]:
    return {
        "hash_algorithm": hashing.HASH_ALGORITHM,
        "hash_version": hashing.HASH_VERSION,
        "canonical_run_id": run_id,
        "run_ids": (run_id,),
        "provenance": provenance,
        "redaction_status": redaction_status,
        "sensitive_data_status": "clear",
        "source_reference": _EVENT_JSONL_REF,
        "known_source_references": (_EVENT_JSONL_REF,),
        "package_scope": "draft_package",
    }


def _draft_manifest_input(
    run_id: str, package_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "created_at": "2026-06-11T00:00:00Z",
        "package_identity": {
            "canonical_run_id": run_id,
            "package_id": package_id,
            "run_ids": (run_id,),
        },
        "package_layout_metadata": {
            "layout_status": "layout_declared",
            "layout_version": package_layout.PACKAGE_LAYOUT_VERSION,
            "immutable_evidence_section": "immutable_evidence",
            "mutable_evaluation_section": "mutable_evaluation",
        },
        "source_artifact_references": (
            {
                "source_reference": _EVENT_JSONL_REF,
                "run_id": run_id,
                "provenance": provenance,
                "redaction_status": redaction_status,
            },
        ),
        "section_status": {"package_identity": "present"},
        "section_provenance": {"package_identity": provenance},
        "section_redaction_status": {"package_identity": redaction_status},
        "section_source_reference": {"package_identity": _EVENT_JSONL_REF},
    }


def _draft_package_creation_input(
    run_id: str, package_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    canonical_payload = canonical_json.canonicalize_json({"section": "package"})
    canonical_input = canonical_bytes.build_canonical_bytes(canonical_payload)
    package_hash = hash_computation.build_package_hash(
        canonical_input, _hash_metadata(run_id, provenance, redaction_status)
    )
    integrity_result = integrity_validation.validate_integrity(package_hash, package_hash)
    return {
        "canonical_run_id": run_id,
        "package_identity": {"canonical_run_id": run_id, "package_id": package_id},
        "manifest": manifest_builder.build_draft_manifest(
            _draft_manifest_input(run_id, package_id, provenance, redaction_status)
        ),
        "canonical_bytes": canonical_input,
        "hash_records": (package_hash,),
        "integrity_validation_result": integrity_result,
        "provenance": provenance,
        "redaction_status": redaction_status,
        "source_references": (_EVENT_JSONL_REF,),
        "known_source_references": (_EVENT_JSONL_REF,),
        "input_run_ids": (run_id,),
    }


def _filesystem_storage_authority_input(
    run_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "storage_root": GOVERNED_PACKAGE_ROOT_LABEL,
        "approved_storage_roots": (GOVERNED_PACKAGE_ROOT_LABEL,),
        "package_path": f"{GOVERNED_PACKAGE_ROOT_LABEL}/{run_id}",
        "approved_package_paths": (f"{GOVERNED_PACKAGE_ROOT_LABEL}/{run_id}",),
        "package_directory": run_id,
        "approved_package_directories": (run_id,),
        "provenance": provenance,
        "redaction_status": redaction_status,
        "source_reference": _DRAFT_PACKAGE_REF,
        "known_source_references": (_DRAFT_PACKAGE_REF,),
        "input_run_ids": (run_id,),
        "read_authority": True,
        "write_authority": True,
        "storage_writer_authority": True,
        "path_resolver_authority": True,
        "package_directory_resolver_authority": True,
    }


def _storage_writer_metadata_input(
    run_id: str,
    package_id: str,
    package_creation_result: Mapping[str, Any],
    provenance: str,
    redaction_status: str,
) -> dict[str, Any]:
    fsa_result = filesystem_storage_authority.validate_filesystem_storage_authority(
        _filesystem_storage_authority_input(run_id, provenance, redaction_status)
    )
    return {
        "canonical_run_id": run_id,
        "package_creation_result": package_creation_result,
        "filesystem_storage_authority_result": fsa_result,
        "package_identity": {"canonical_run_id": run_id, "package_id": package_id},
        "storage_root": GOVERNED_PACKAGE_ROOT_LABEL,
        "package_path": f"{GOVERNED_PACKAGE_ROOT_LABEL}/{run_id}",
        "package_directory": run_id,
        "lifecycle_status": "finalized",
        "provenance": provenance,
        "redaction_status": redaction_status,
        "source_reference": _DRAFT_PACKAGE_REF,
        "known_source_references": (_DRAFT_PACKAGE_REF,),
        "input_run_ids": (run_id,),
        "package_completeness_authority": False,
    }


def _package_completeness_evidence(
    run_id: str,
    package_id: str,
    storage_impl_result: Mapping[str, Any],
    provenance: str,
    redaction_status: str,
) -> dict[str, Any]:
    package_creation_result = storage_impl_result["package_creation_result"]
    return {
        "canonical_run_id": run_id,
        "package_identity": {"canonical_run_id": run_id, "package_id": package_id},
        "package_creation_result": package_creation_result,
        "manifest": package_creation_result["manifest"],
        "canonical_bytes": package_creation_result["canonical_bytes"],
        "hash_records": package_creation_result["hash_records"],
        "integrity_validation_result": package_creation_result[
            "integrity_validation_result"
        ],
        "storage_implementation_result": storage_impl_result,
        "storage_lifecycle_state": "finalized",
        "provenance": provenance,
        "redaction_status": redaction_status,
        "source_references": _GOVERNED_SOURCE_REFERENCES,
        "known_source_references": _GOVERNED_SOURCE_REFERENCES,
        "input_run_ids": (run_id,),
    }


def _package_writer_request(
    request: PackageExecutionRequest,
    run_id: str,
    fsa_result: Mapping[str, Any],
    completeness_result: Mapping[str, Any],
    storage_impl_result: Mapping[str, Any],
    artifact_bytes: bytes,
    provenance: str,
    redaction_status: str,
) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "filesystem_storage_authority_result": fsa_result,
        "package_completeness_result": completeness_result,
        "storage_implementation_result": storage_impl_result,
        "storage_root": GOVERNED_PACKAGE_ROOT_LABEL,
        "approved_storage_roots": (GOVERNED_PACKAGE_ROOT_LABEL,),
        "package_path": f"{GOVERNED_PACKAGE_ROOT_LABEL}/{run_id}",
        "approved_package_paths": (f"{GOVERNED_PACKAGE_ROOT_LABEL}/{run_id}",),
        "package_directory": run_id,
        "approved_package_directories": (run_id,),
        "storage_root_path": request.package_root_path,
        "approved_storage_root_paths": (request.package_root_path,),
        "artifact_relative_path": f"{run_id}/manifest.json",
        "artifact_bytes": artifact_bytes,
        "lifecycle_status": "finalized",
        "provenance": provenance,
        "redaction_status": redaction_status,
        "source_references": _GOVERNED_SOURCE_REFERENCES,
        "known_source_references": _GOVERNED_SOURCE_REFERENCES,
        "input_run_ids": (run_id,),
        "allow_absolute_storage_root": True,
    }


def _package_persistence_request(
    run_id: str,
    fsa_result: Mapping[str, Any],
    storage_impl_result: Mapping[str, Any],
    provenance: str,
    redaction_status: str,
) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "storage_root": GOVERNED_PACKAGE_ROOT_LABEL,
        "package_path": f"{GOVERNED_PACKAGE_ROOT_LABEL}/{run_id}",
        "lifecycle_status": "finalized",
        "filesystem_storage_authority_result": fsa_result,
        "storage_implementation_result": storage_impl_result,
        "provenance": provenance,
        "redaction_status": redaction_status,
    }


def _source_artifact_result(
    run_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    return source_artifacts.validate_source_artifact_authority(
        {
            "canonical_run_id": run_id,
            "source_references": _GOVERNED_SOURCE_REFERENCES,
            "known_source_references": _GOVERNED_SOURCE_REFERENCES,
            "source_artifact_provenance": provenance,
            "source_artifact_redaction_status": redaction_status,
            "source_artifact_eligibility": "eligible",
            "input_run_ids": (run_id,),
            "source_path_identity": "source-metadata:event_jsonl",
        }
    )


def _discovery_result(
    run_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    return runtime_artifact_discovery.validate_runtime_artifact_discovery(
        {
            "canonical_run_id": run_id,
            "source_artifact_authority_result": _source_artifact_result(
                run_id, provenance, redaction_status
            ),
            "source_references": _GOVERNED_SOURCE_REFERENCES,
            "known_source_references": _GOVERNED_SOURCE_REFERENCES,
            "eligible_runtime_artifact_vocabulary": _GOVERNED_SOURCE_REFERENCES,
            "terminal_completion_rule": {
                "required": True,
                "satisfied": True,
                "terminal_event": "run_completed",
            },
            "runtime_artifact_candidates": (
                {
                    "artifact_id": "event_stream",
                    "artifact_type": _EVENT_JSONL_REF,
                    "source_reference": _EVENT_JSONL_REF,
                    "canonical_run_id": run_id,
                    "provenance": provenance,
                    "redaction_status": redaction_status,
                    "eligible": True,
                    "source_path_metadata": "source-metadata:event_jsonl",
                },
            ),
            "runtime_artifact_provenance": provenance,
            "runtime_artifact_redaction_status": redaction_status,
            "input_run_ids": (run_id,),
        }
    )


def _source_path_ingestion_result(
    run_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    ingestion_input = {
        "canonical_run_id": run_id,
        "source_reference": _EVENT_JSONL_REF,
        "path_family": KNOWN_SOURCE_PATH_FAMILIES[0],
        "path_value": f"logs/{run_id}.jsonl",
        "provenance": provenance,
        "redaction_status": redaction_status,
        "approved": True,
    }
    failures = source_path_ingestion.validate_source_path_ingestion(ingestion_input)
    if failures:
        raise ValueError(f"source path ingestion failed: {failures}")
    return {**ingestion_input, "failures": tuple(failures), "governed": True}


def _runtime_artifact_metadata(
    run_id: str, provenance: str, redaction_status: str
) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "artifact_type": runtime_artifacts.JSONL_EVENT_STREAM,
        "status": runtime_artifacts.RUNTIME_ARTIFACT_ELIGIBLE,
        "provenance": provenance,
        "redaction_status": redaction_status,
    }


def _approved_file_read_result(
    run_id: str, jsonl_bytes: bytes, provenance: str, redaction_status: str
) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "read_performed": True,
        "artifact_family": "jsonl_event_stream",
        "file_sha256": hashlib.sha256(jsonl_bytes).hexdigest(),
        "provenance": provenance,
        "redaction_status": redaction_status,
    }


def _package_layout_result(run_id: str, package_id: str) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "package_id": package_id,
        "layout_status": "layout_declared",
        "layout_version": package_layout.PACKAGE_LAYOUT_VERSION,
    }


def _serialization_result(run_id: str) -> dict[str, Any]:
    return {
        "canonical_run_id": run_id,
        "serializer": "canonical_json",
        "deterministic": True,
        "canonical_bytes_present": True,
    }


def _package_artifact_bytes(run_id: str, package_id: str) -> bytes:
    payload = {
        "canonical_run_id": run_id,
        "package_id": package_id,
        "artifact": "manifest",
        "manifest_present": True,
    }
    return canonical_bytes.build_canonical_bytes(canonical_json.canonicalize_json(payload))


def main(argv: Sequence[str] | None = None) -> int:
    """Deterministic, bounded CLI stub.

    This CLI never performs real VPS reads/writes in this gate. ``vps`` mode is
    rejected and deferred to a separate bounded VPS execution gate. ``tmp_path_test``
    mode requires programmatic invocation with already-read bytes (tests),
    because this module performs no direct filesystem reads.
    """

    parser = argparse.ArgumentParser(
        prog="package_execution_orchestrator",
        description="Deterministic replay package execution orchestration (bounded).",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--execution-mode", required=True, choices=list(ALLOWED_EXECUTION_MODES)
    )
    args = parser.parse_args(argv)

    if args.execution_mode == EXECUTION_MODE_VPS:
        print(VPS_EXECUTION_DEFERRED_MESSAGE)
        print(f"candidate: {PACKAGE_EXECUTION_VPS_COMMAND_CANDIDATE}")
        return 2
    print(
        "tmp_path_test orchestration requires programmatic invocation with "
        "already-read bytes; the CLI performs no direct filesystem reads."
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
