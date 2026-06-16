"""Pure in-memory approved file-read configuration for governed runtime artifacts.

This module defines approved read configurations and request builders for the
governed runtime artifact path families established in Gate A (A1 + A2). It
does not read files, resolve paths, ingest arbitrary paths, discover artifacts,
copy artifacts, execute runtime capture, write packages, evaluate strategies,
call broker APIs, authorize execution, approve paper trading, or authorize live
trading.

Governance basis: Gate A Record A1 (VPS artifact root, path families) and
Gate A Record A2 (terminal completion rules, run_id binding).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.source_references import (
    SOURCE_REF_EVENT_JSONL,
    SOURCE_REF_LAST_RUN_REPORT,
    SOURCE_REF_ORDER_STATE,
    KNOWN_SOURCE_REFERENCES,
)
from tools.replay.source_paths import (
    SOURCE_PATH_FAMILY_EVENT_JSONL,
    SOURCE_PATH_FAMILY_LAST_RUN_REPORT,
    SOURCE_PATH_FAMILY_PER_RUN_REPORT,
    SOURCE_PATH_FAMILY_ORDER_STATE,
    KNOWN_SOURCE_PATH_FAMILIES,
)


APPROVED_FILE_READS_AUTHORITY = "approved_file_reads_authority_metadata_only"
APPROVED_FILE_READS_RESULT = "approved_file_reads_result"

VPS_ARTIFACT_ROOT_LABEL = "vps_artifact_root"
APPROVED_VPS_ARTIFACT_ROOT_PATH_STRING = "/opt/openclaw-stocks"

JSONL_EVENT_STREAM_READ = "jsonl_event_stream_read"
LAST_RUN_REPORT_READ = "last_run_report_read"
PER_RUN_REPORT_READ = "per_run_report_read"
ORDER_STATE_READ_BLOCKED = "order_state_read_blocked"

APPROVED_RUNTIME_ARTIFACT_READ_FAMILIES: tuple[str, ...] = (
    SOURCE_PATH_FAMILY_EVENT_JSONL,
    SOURCE_PATH_FAMILY_LAST_RUN_REPORT,
    SOURCE_PATH_FAMILY_PER_RUN_REPORT,
)

BLOCKED_RUNTIME_ARTIFACT_READ_FAMILIES: tuple[str, ...] = (
    SOURCE_PATH_FAMILY_ORDER_STATE,
)

APPROVED_FILE_READS_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "approved_governed_paths_only",
    "no_filesystem_reads",
    "no_path_resolution",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_discovery",
    "no_runtime_capture",
    "no_package_writing",
    "no_storage_finalization",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

APPROVED_FILE_READS_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "missing_source_artifact_authority_result",
    "missing_runtime_artifact_discovery_result",
    "missing_terminal_completion_rule",
    "terminal_completion_not_satisfied",
    "missing_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
    "missing_artifact_root_path",
    "unapproved_artifact_root_path",
    "missing_input_run_ids",
    "mixed_run_ids",
    "order_state_read_requires_later_binding_gate",
)


@dataclass(frozen=True, slots=True)
class ApprovedFileReadsAuthority:
    """Static approved file reads authority vocabulary."""

    name: str = APPROVED_FILE_READS_AUTHORITY
    authority_boundary: tuple[str, ...] = APPROVED_FILE_READS_AUTHORITY_BOUNDARY


def build_jsonl_event_stream_read_request(
    canonical_run_id: str,
    artifact_root_path_string: str,
    source_artifact_authority_result: Mapping[str, Any],
    runtime_artifact_discovery_result: Mapping[str, Any],
    *,
    provenance: str = "recorded",
    redaction_status: str = "not_required",
    expected_sha256: str | None = None,
    max_size_bytes: int | None = None,
    expected_encoding: str | None = "utf-8",
) -> dict[str, Any]:
    """Build an approved request to read a governed JSONL event stream artifact.

    Returns a dict suitable for file_reader.read_approved_replay_file().
    No file is read. No path is resolved. No runtime capture is performed.
    """

    if not canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not artifact_root_path_string:
        raise ValueError("artifact_root_path_string is required")

    file_relative_path = SOURCE_PATH_FAMILY_EVENT_JSONL.replace(
        "{run_id}", canonical_run_id
    )
    approved_path_metadata: dict[str, Any] = {
        "approved": True,
        "file_identity": JSONL_EVENT_STREAM_READ,
        "relative_path": file_relative_path,
    }
    terminal_completion_rule: dict[str, Any] = {
        "required": True,
        "satisfied": True,
        "terminal_event": "system_completion",
    }
    request: dict[str, Any] = {
        "canonical_run_id": canonical_run_id,
        "runtime_artifact_discovery_result": runtime_artifact_discovery_result,
        "source_artifact_authority_result": source_artifact_authority_result,
        "source_references": (SOURCE_REF_EVENT_JSONL,),
        "known_source_references": KNOWN_SOURCE_REFERENCES,
        "approved_file_identity": JSONL_EVENT_STREAM_READ,
        "approved_file_identities": (JSONL_EVENT_STREAM_READ,),
        "artifact_root": VPS_ARTIFACT_ROOT_LABEL,
        "approved_artifact_roots": (VPS_ARTIFACT_ROOT_LABEL,),
        "artifact_root_path": artifact_root_path_string,
        "approved_artifact_root_paths": (artifact_root_path_string,),
        "file_relative_path": file_relative_path,
        "approved_path_metadata": approved_path_metadata,
        "terminal_completion_rule": terminal_completion_rule,
        "provenance": provenance,
        "redaction_status": redaction_status,
        "eligible_runtime_artifact_vocabulary": (SOURCE_REF_EVENT_JSONL,),
        "input_run_ids": (canonical_run_id,),
        "allow_absolute_artifact_root": True,
        "repo_relative": False,
        "sensitive_data_status": "clear",
    }
    if expected_sha256 is not None:
        request["expected_sha256"] = expected_sha256
    if max_size_bytes is not None:
        request["max_size_bytes"] = max_size_bytes
    if expected_encoding is not None:
        request["expected_encoding"] = expected_encoding
    return request


def build_last_run_report_read_request(
    canonical_run_id: str,
    artifact_root_path_string: str,
    source_artifact_authority_result: Mapping[str, Any],
    runtime_artifact_discovery_result: Mapping[str, Any],
    *,
    provenance: str = "recorded",
    redaction_status: str = "not_required",
    expected_sha256: str | None = None,
    max_size_bytes: int | None = None,
    expected_encoding: str | None = "utf-8",
) -> dict[str, Any]:
    """Build an approved request to read a governed last_run_report.json artifact.

    Returns a dict suitable for file_reader.read_approved_replay_file().
    No file is read. No path is resolved. No runtime capture is performed.
    last_run_report.json is read as a derived operational summary only;
    it does not independently establish canonical run_id authority.
    """

    if not canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not artifact_root_path_string:
        raise ValueError("artifact_root_path_string is required")

    file_relative_path = SOURCE_PATH_FAMILY_LAST_RUN_REPORT
    approved_path_metadata: dict[str, Any] = {
        "approved": True,
        "file_identity": LAST_RUN_REPORT_READ,
        "relative_path": file_relative_path,
    }
    terminal_completion_rule: dict[str, Any] = {
        "required": True,
        "satisfied": True,
        "terminal_event": "system_completion",
    }
    request: dict[str, Any] = {
        "canonical_run_id": canonical_run_id,
        "runtime_artifact_discovery_result": runtime_artifact_discovery_result,
        "source_artifact_authority_result": source_artifact_authority_result,
        "source_references": (SOURCE_REF_LAST_RUN_REPORT,),
        "known_source_references": KNOWN_SOURCE_REFERENCES,
        "approved_file_identity": LAST_RUN_REPORT_READ,
        "approved_file_identities": (LAST_RUN_REPORT_READ,),
        "artifact_root": VPS_ARTIFACT_ROOT_LABEL,
        "approved_artifact_roots": (VPS_ARTIFACT_ROOT_LABEL,),
        "artifact_root_path": artifact_root_path_string,
        "approved_artifact_root_paths": (artifact_root_path_string,),
        "file_relative_path": file_relative_path,
        "approved_path_metadata": approved_path_metadata,
        "terminal_completion_rule": terminal_completion_rule,
        "provenance": provenance,
        "redaction_status": redaction_status,
        "eligible_runtime_artifact_vocabulary": (SOURCE_REF_LAST_RUN_REPORT,),
        "input_run_ids": (canonical_run_id,),
        "allow_absolute_artifact_root": True,
        "repo_relative": False,
        "sensitive_data_status": "clear",
    }
    if expected_sha256 is not None:
        request["expected_sha256"] = expected_sha256
    if max_size_bytes is not None:
        request["max_size_bytes"] = max_size_bytes
    if expected_encoding is not None:
        request["expected_encoding"] = expected_encoding
    return request


def build_per_run_report_read_request(
    canonical_run_id: str,
    artifact_root_path_string: str,
    source_artifact_authority_result: Mapping[str, Any],
    runtime_artifact_discovery_result: Mapping[str, Any],
    *,
    provenance: str = "recorded",
    redaction_status: str = "not_required",
    expected_sha256: str | None = None,
    max_size_bytes: int | None = None,
    expected_encoding: str | None = "utf-8",
) -> dict[str, Any]:
    """Build an approved request to read a governed per-run report artifact."""

    if not canonical_run_id:
        raise ValueError("canonical_run_id is required")
    if not artifact_root_path_string:
        raise ValueError("artifact_root_path_string is required")

    file_relative_path = SOURCE_PATH_FAMILY_PER_RUN_REPORT.replace(
        "{run_id}", canonical_run_id
    )
    approved_path_metadata: dict[str, Any] = {
        "approved": True,
        "file_identity": PER_RUN_REPORT_READ,
        "relative_path": file_relative_path,
    }
    terminal_completion_rule: dict[str, Any] = {
        "required": True,
        "satisfied": True,
        "terminal_event": "system_completion",
    }
    request: dict[str, Any] = {
        "canonical_run_id": canonical_run_id,
        "runtime_artifact_discovery_result": runtime_artifact_discovery_result,
        "source_artifact_authority_result": source_artifact_authority_result,
        "source_references": (SOURCE_REF_LAST_RUN_REPORT,),
        "known_source_references": KNOWN_SOURCE_REFERENCES,
        "approved_file_identity": PER_RUN_REPORT_READ,
        "approved_file_identities": (PER_RUN_REPORT_READ,),
        "artifact_root": VPS_ARTIFACT_ROOT_LABEL,
        "approved_artifact_roots": (VPS_ARTIFACT_ROOT_LABEL,),
        "artifact_root_path": artifact_root_path_string,
        "approved_artifact_root_paths": (artifact_root_path_string,),
        "file_relative_path": file_relative_path,
        "approved_path_metadata": approved_path_metadata,
        "terminal_completion_rule": terminal_completion_rule,
        "provenance": provenance,
        "redaction_status": redaction_status,
        "eligible_runtime_artifact_vocabulary": (SOURCE_REF_LAST_RUN_REPORT,),
        "input_run_ids": (canonical_run_id,),
        "allow_absolute_artifact_root": True,
        "repo_relative": False,
        "sensitive_data_status": "clear",
    }
    if expected_sha256 is not None:
        request["expected_sha256"] = expected_sha256
    if max_size_bytes is not None:
        request["max_size_bytes"] = max_size_bytes
    if expected_encoding is not None:
        request["expected_encoding"] = expected_encoding
    return request


def build_order_state_read_request(*_args: object, **_kwargs: object) -> None:
    """order_state.json reads require a later explicit binding gate.

    This function always fails closed. order_state.json is recorded as a
    blocked artifact family. It must not be read until a separate
    order_state binding gate is opened and explicitly source-controlled.
    """

    raise ValueError(
        "order_state.json reads require a later explicit binding gate: "
        f"'{ORDER_STATE_READ_BLOCKED}' is not an active read family in this lane"
    )
