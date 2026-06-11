"""Pure in-memory package persistence lifecycle coordinator for replay.

This module builds and validates package persistence lifecycle metadata
using storage_implementation.py. It does not directly perform filesystem
writes, read files, ingest paths, discover artifacts, copy artifacts,
execute runtime capture, write packages independently, evaluate strategies,
call broker APIs, authorize execution, approve paper trading, or authorize
live trading.

Actual writes, when approved, must go through package_writer.py and
filesystem_writer.py.

Governance basis: Gate B Record B1 (filesystem write authority) and the
IMPLEMENT_PACKAGE_WRITER_PERSISTENCE gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import tools.replay.storage_implementation as storage_implementation


PACKAGE_PERSISTENCE_AUTHORITY = "package_persistence_authority"
PACKAGE_PERSISTENCE_RESULT = "package_persistence_result"
GOVERNED_STORAGE_LIFECYCLE_ONLY = "governed_storage_lifecycle_only"

PACKAGE_PERSISTENCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "no_actual_filesystem_writes",
    "no_filesystem_reads",
    "no_runtime_artifact_reads",
    "no_file_path_ingestion",
    "no_source_path_ingestion",
    "no_artifact_copying",
    "no_runtime_capture_execution",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

PACKAGE_PERSISTENCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "missing_storage_root",
    "missing_package_path",
    "missing_lifecycle_status",
    "unknown_lifecycle_status",
    "missing_filesystem_storage_authority_result",
    "filesystem_storage_authority_not_evidence_only",
    "missing_storage_implementation_result",
    "storage_implementation_not_evidence_only",
    "mixed_run_id",
    "missing_provenance",
    "missing_redaction_status",
    "invalid_redaction_status",
    "sensitive_data_exposure",
)

PACKAGE_PERSISTENCE_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_present",
    "storage_root_present",
    "package_path_present",
    "lifecycle_status_known",
    "filesystem_storage_authority_evidence_only",
    "storage_implementation_evidence_only",
    "run_id_aligned",
    "provenance_present",
    "redaction_status_valid",
    "no_sensitive_data",
)


@dataclass(frozen=True, slots=True)
class PackagePersistenceAuthority:
    """Static package persistence authority vocabulary."""

    name: str = PACKAGE_PERSISTENCE_AUTHORITY
    authority_boundary: tuple[str, ...] = PACKAGE_PERSISTENCE_AUTHORITY_BOUNDARY


def build_package_persistence_result(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a governed package persistence lifecycle metadata result.

    Returns metadata only. actual_filesystem_writes is always False.
    Delegates lifecycle state access to storage_implementation.py.
    No filesystem access is performed. No runtime capture.
    """

    canonical_run_id = request.get("canonical_run_id", "")
    if not canonical_run_id:
        raise ValueError("canonical_run_id is required")

    storage_root = request.get("storage_root", "")
    if not storage_root:
        raise ValueError("storage_root is required")

    package_path = request.get("package_path", "")
    if not package_path:
        raise ValueError("package_path is required")

    lifecycle_status = request.get("lifecycle_status", "")
    if not lifecycle_status:
        raise ValueError("lifecycle_status is required")
    if lifecycle_status not in storage_implementation.STORAGE_LIFECYCLE_STATES:
        raise ValueError(f"unknown lifecycle_status: '{lifecycle_status}'")

    filesystem_storage_authority_result = request.get(
        "filesystem_storage_authority_result", {}
    )
    if not isinstance(filesystem_storage_authority_result, Mapping):
        raise ValueError("filesystem_storage_authority_result is required")
    if filesystem_storage_authority_result.get("evidence_only") is not True:
        raise ValueError("filesystem_storage_authority_result must be evidence_only")
    if filesystem_storage_authority_result.get("actual_filesystem_writes") is not False:
        raise ValueError("filesystem_storage_authority_result must be metadata-only")

    storage_implementation_result = request.get("storage_implementation_result", {})
    if not isinstance(storage_implementation_result, Mapping):
        raise ValueError("storage_implementation_result is required")
    if storage_implementation_result.get("evidence_only") is not True:
        raise ValueError("storage_implementation_result must be evidence_only")
    if storage_implementation_result.get("actual_filesystem_writes") is not False:
        raise ValueError("storage_implementation_result must be metadata-only")
    if storage_implementation_result.get("canonical_run_id") != canonical_run_id:
        raise ValueError("mixed run_id in persistence request")

    provenance = request.get("provenance", "")
    if not provenance:
        raise ValueError("provenance is required")

    redaction_status = request.get("redaction_status", "")
    if not redaction_status:
        raise ValueError("redaction_status is required")

    sensitive_data_status = request.get("sensitive_data_status", "clear")
    if sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")

    return {
        "result_type": PACKAGE_PERSISTENCE_RESULT,
        "canonical_run_id": canonical_run_id,
        "storage_root": storage_root,
        "package_path": package_path,
        "lifecycle_status": lifecycle_status,
        "governed_storage_lifecycle_only": GOVERNED_STORAGE_LIFECYCLE_ONLY,
        "provenance": provenance,
        "redaction_status": redaction_status,
        "sensitive_data_status": sensitive_data_status,
        "evidence_only": True,
        "actual_filesystem_writes": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "live_trading_authority": False,
        "authority_boundary": PACKAGE_PERSISTENCE_AUTHORITY_BOUNDARY,
    }
