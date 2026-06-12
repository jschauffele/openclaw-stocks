"""Pure deterministic last_run_report.json alignment validator.

This module validates already-read ``last_run_report.json`` bytes against a
selected canonical run_id and a prior JSONL terminal-completion evaluation. It
accepts bytes only; it does not read files, write files, resolve paths,
discover artifacts, capture runtime data, evaluate or promote strategies, call
broker APIs, authorize execution, approve paper trading, or authorize live
trading.

Per Gate A Record A2, ``last_run_report.json`` is a derived operational summary
only: it does not independently establish canonical run_id authority, and a
stale report (run_id mismatch) must fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


LAST_RUN_REPORT_ALIGNMENT_AUTHORITY = "last_run_report_alignment_authority"
LAST_RUN_REPORT_ALIGNMENT_RESULT = "last_run_report_alignment_result"

_REPORT_STATUS_KEYS: tuple[str, ...] = (
    "status",
    "terminal_status",
    "completion_status",
    "final_status",
)
_DIAGNOSTIC_ONLY_STATUSES: tuple[str, ...] = ("error",)

LAST_RUN_REPORT_ALIGNMENT_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "already_read_report_bytes_only",
    "derived_summary_only_not_run_id_authority",
    "last_run_report_run_id_must_match_jsonl_stem",
    "stale_report_fails_closed",
    "no_filesystem_reads",
    "no_filesystem_writes",
    "no_runtime_capture_execution",
    "no_real_vps_runtime_artifact_reads",
    "no_package_writes",
    "no_gate_d_authority",
    "no_evaluation_or_promotion",
    "no_broker_api_authority",
    "no_trading_authority",
)

LAST_RUN_REPORT_ALIGNMENT_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "malformed_utf8_report_bytes",
    "malformed_json_report",
    "non_object_report",
    "missing_report_run_id",
    "stale_or_mismatched_report_run_id",
    "report_status_contradicts_terminal_status",
    "report_error_status_not_packageable",
    "report_status_contradicts_terminal_eligibility",
)


@dataclass(frozen=True, slots=True)
class LastRunReportAlignmentRequest:
    """Already-read report bytes plus the selected run identity and status."""

    canonical_run_id: str
    report_bytes: bytes
    terminal_completion_status: str
    terminal_completion_eligible: bool


@dataclass(frozen=True, slots=True)
class LastRunReportAlignmentResult:
    """Deterministic report alignment result."""

    canonical_run_id: str
    report_run_id: str
    report_status: str | None
    provenance: str
    aligned: bool
    result_type: str = LAST_RUN_REPORT_ALIGNMENT_RESULT
    runtime_capture_execution: bool = False
    real_vps_runtime_artifact_reads: bool = False
    package_writes: bool = False
    gate_d_authority: bool = False
    evaluation_or_promotion: bool = False
    broker_api_authority: bool = False
    trading_authority: bool = False
    authority_boundary: tuple[str, ...] = LAST_RUN_REPORT_ALIGNMENT_AUTHORITY_BOUNDARY


def validate_last_run_report_alignment(
    request: LastRunReportAlignmentRequest,
) -> LastRunReportAlignmentResult:
    """Validate report alignment with the selected run_id, or fail closed."""

    if not request.canonical_run_id:
        raise ValueError("canonical_run_id is required")

    try:
        text = request.report_bytes.decode("utf-8")
    except (UnicodeDecodeError, AttributeError) as exc:
        raise ValueError("malformed utf-8 report bytes") from exc

    try:
        report = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("malformed json report") from exc
    if not isinstance(report, dict):
        raise ValueError("non-object report")

    report_run_id = report.get("run_id", report.get("canonical_run_id"))
    if not report_run_id:
        raise ValueError("report is missing run_id")
    if report_run_id != request.canonical_run_id:
        raise ValueError("stale or mismatched last_run_report run_id")

    report_status = _extract_report_status(report)
    if report_status is not None:
        if report_status in _DIAGNOSTIC_ONLY_STATUSES:
            raise ValueError("report error status is not packageable")
        if report_status != request.terminal_completion_status:
            raise ValueError("report status contradicts terminal completion status")
    if request.terminal_completion_eligible is True and (
        report_status in _DIAGNOSTIC_ONLY_STATUSES
    ):
        raise ValueError("report status contradicts terminal eligibility")

    provenance = report.get("provenance")
    provenance_label = provenance if isinstance(provenance, str) and provenance else (
        "not_present"
    )

    return LastRunReportAlignmentResult(
        canonical_run_id=request.canonical_run_id,
        report_run_id=report_run_id,
        report_status=report_status,
        provenance=provenance_label,
        aligned=True,
    )


def _extract_report_status(report: dict[str, Any]) -> str | None:
    for key in _REPORT_STATUS_KEYS:
        value = report.get(key)
        if isinstance(value, str) and value:
            return value
    return None
