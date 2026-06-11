"""Thin governed writer wrapper for approved replay package artifact writes.

This module writes governed replay package artifacts using the filesystem_writer.py
infrastructure with inputs validated by package_completeness.py and
storage_implementation.py. It does not perform independent path resolution,
bypass filesystem_writer.py validation, write real VPS packages in tests,
copy artifacts, execute runtime capture, parse artifact content beyond
returning write results, evaluate strategies, call broker APIs, authorize
execution, approve paper trading, or authorize live trading.

Governance basis: Gate B Record B1 (filesystem write authority) and the
IMPLEMENT_PACKAGE_WRITER_PERSISTENCE gate.
Tests use tmp_path synthetic fixtures only. Real VPS package writes require
a separate VPS execution gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import tools.replay.filesystem_writer as filesystem_writer


PACKAGE_WRITER_AUTHORITY = "package_writer_authority"
PACKAGE_WRITER_RESULT = "package_writer_result"
GOVERNED_PACKAGE_ROOT_LABEL = "replay_packages"
GOVERNED_PACKAGE_RELATIVE_PATH_FAMILY = "replay_packages/{run_id}"
APPROVED_VPS_PACKAGE_ROOT_PATH = "/opt/openclaw-stocks/replay_packages"
ORDER_STATE_PACKAGE_WRITE_BLOCKED_MESSAGE = (
    "order_state.json package writes require a later explicit binding gate"
)

PACKAGE_WRITER_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "approved_governed_paths_only",
    "no_vps_package_writes_from_local_dev_gate",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_runtime_artifact_reads",
    "no_artifact_copying",
    "no_runtime_capture_execution",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

PACKAGE_WRITER_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "unapproved_storage_root",
    "unapproved_package_path",
    "unapproved_package_directory",
    "unapproved_storage_root_path",
    "missing_package_completeness_result",
    "package_completeness_not_satisfied",
    "missing_storage_implementation_result",
    "missing_filesystem_storage_authority_result",
    "missing_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
    "missing_artifact_bytes",
    "order_state_write_requires_later_binding_gate",
    "path_traversal",
    "absolute_path_injection",
    "symlink_ambiguity",
    "attempted_overwrite",
    "non_repo_path_ambiguity",
    "unapproved_package_directory_not_exists",
    "mixed_run_id",
    "sensitive_data_exposure",
    "stale_writer_input",
    "malformed_writer_input",
    "runtime_dependent_writer_input",
    "evaluation_dependent_writer_input",
    "broker_dependent_writer_input",
)

PACKAGE_WRITER_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_present",
    "package_completeness_authority_valid",
    "storage_implementation_valid",
    "filesystem_storage_authority_valid",
    "provenance_present",
    "redaction_status_valid",
    "artifact_bytes_present",
    "storage_root_approved",
    "package_path_approved",
    "package_directory_approved",
    "storage_root_path_approved",
    "no_path_traversal",
    "no_absolute_path_injection",
    "no_symlink_ambiguity",
    "no_overwrite",
    "repo_relative_flag",
    "package_directory_exists",
    "no_mixed_run_id",
    "no_sensitive_data",
    "no_runtime_dependent_inputs",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
)


@dataclass(frozen=True, slots=True)
class PackageWriterAuthority:
    """Static package writer authority vocabulary."""

    name: str = PACKAGE_WRITER_AUTHORITY
    authority_boundary: tuple[str, ...] = PACKAGE_WRITER_AUTHORITY_BOUNDARY


def write_package_artifact(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Write a governed replay package artifact.

    Delegates entirely to filesystem_writer.write_replay_package_artifact().
    No independent path resolution. No runtime capture. No VPS access in tests.
    """

    result = filesystem_writer.write_replay_package_artifact(request)
    result["result_type"] = PACKAGE_WRITER_RESULT
    result["governed_package_root_label"] = GOVERNED_PACKAGE_ROOT_LABEL
    return result


def write_order_state_artifact(*_args: object, **_kwargs: object) -> None:
    """order_state.json package writes are blocked pending a later explicit binding gate.

    This function always raises. order_state.json must not be written until a
    separate order_state binding gate is opened and source-controlled.
    """

    raise ValueError(ORDER_STATE_PACKAGE_WRITE_BLOCKED_MESSAGE)
