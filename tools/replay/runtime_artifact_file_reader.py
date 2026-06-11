"""Thin governed reader wrapper for approved runtime artifact file reads.

This module reads governed runtime artifact files using the file_reader.py
infrastructure with requests built by approved_file_reads.py. It does not
perform independent path resolution, bypass file_reader.py validation, read
real VPS artifacts in tests, copy artifacts, execute runtime capture, parse
artifact content beyond returning bytes, evaluate strategies, call broker APIs,
authorize execution, approve paper trading, or authorize live trading.

Governance basis: Gate A (A1 + A2) approved path families and binding rules.
Tests use tmp_path synthetic fixtures only. Real VPS artifact reads require
a separate VPS execution gate.
"""

from __future__ import annotations

from typing import Any, Mapping

import tools.replay.approved_file_reads as approved_file_reads
import tools.replay.file_reader as file_reader


RUNTIME_ARTIFACT_FILE_READER_AUTHORITY = (
    "runtime_artifact_file_reader_authority"
)
RUNTIME_ARTIFACT_FILE_READER_RESULT = "runtime_artifact_file_reader_result"

RUNTIME_ARTIFACT_FILE_READER_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "approved_governed_paths_only",
    "no_runtime_log_access_beyond_approved_families",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_capture_execution",
    "no_package_writing",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

ORDER_STATE_BLOCKED_MESSAGE = (
    "order_state.json reads require a later explicit binding gate"
)


def read_jsonl_event_stream(
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
    """Read a governed JSONL event stream artifact.

    Builds an approved request via approved_file_reads.py and delegates
    entirely to file_reader.read_approved_replay_file(). No independent path
    resolution. No runtime capture. No VPS access in tests.
    """

    request = approved_file_reads.build_jsonl_event_stream_read_request(
        canonical_run_id=canonical_run_id,
        artifact_root_path_string=artifact_root_path_string,
        source_artifact_authority_result=source_artifact_authority_result,
        runtime_artifact_discovery_result=runtime_artifact_discovery_result,
        provenance=provenance,
        redaction_status=redaction_status,
        expected_sha256=expected_sha256,
        max_size_bytes=max_size_bytes,
        expected_encoding=expected_encoding,
    )
    result = file_reader.read_approved_replay_file(request)
    result["result_type"] = RUNTIME_ARTIFACT_FILE_READER_RESULT
    result["artifact_family"] = approved_file_reads.JSONL_EVENT_STREAM_READ
    return result


def read_last_run_report(
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
    """Read a governed last_run_report.json artifact.

    Builds an approved request via approved_file_reads.py and delegates
    entirely to file_reader.read_approved_replay_file(). last_run_report.json
    is read as a derived operational summary only; it does not independently
    establish canonical run_id authority.
    """

    request = approved_file_reads.build_last_run_report_read_request(
        canonical_run_id=canonical_run_id,
        artifact_root_path_string=artifact_root_path_string,
        source_artifact_authority_result=source_artifact_authority_result,
        runtime_artifact_discovery_result=runtime_artifact_discovery_result,
        provenance=provenance,
        redaction_status=redaction_status,
        expected_sha256=expected_sha256,
        max_size_bytes=max_size_bytes,
        expected_encoding=expected_encoding,
    )
    result = file_reader.read_approved_replay_file(request)
    result["result_type"] = RUNTIME_ARTIFACT_FILE_READER_RESULT
    result["artifact_family"] = approved_file_reads.LAST_RUN_REPORT_READ
    return result


def read_order_state(*_args: object, **_kwargs: object) -> None:
    """order_state.json reads are blocked pending a later explicit binding gate.

    This function always raises. order_state.json must not be read until a
    separate order_state binding gate is opened and source-controlled.
    """

    raise ValueError(ORDER_STATE_BLOCKED_MESSAGE)
