"""Pure deterministic JSONL terminal-completion eligibility evaluator.

This module evaluates the Gate A Record A2 terminal-completion rule over
already-read JSONL bytes. It accepts bytes only; it does not read files, write
files, resolve paths, discover artifacts, capture runtime data, evaluate or
promote strategies, call broker APIs, authorize execution, approve paper
trading, or authorize live trading.

A2 terminal-completion rule (source-controlled):
- A terminal runtime event is exactly one JSONL event where
  ``event_type == "system"`` and ``stage == "completion"``.
- The run_id on every line must match the canonical_run_id, which must equal
  the JSONL filename stem.
- Completion status ``ok`` and ``blocked`` are capture-eligible; ``error`` is
  diagnostic only and not eligible.
- Zero or duplicate terminal events fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


TERMINAL_COMPLETION_EVALUATOR_AUTHORITY = "terminal_completion_evaluator_authority"
TERMINAL_COMPLETION_EVALUATOR_RESULT = "terminal_completion_evaluator_result"
TERMINAL_COMPLETION_ELIGIBLE_STATUSES: tuple[str, ...] = ("ok", "blocked")
TERMINAL_COMPLETION_DIAGNOSTIC_ONLY_STATUSES: tuple[str, ...] = ("error",)

_JSONL_SUFFIX = ".jsonl"

TERMINAL_COMPLETION_EVALUATOR_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "already_read_jsonl_bytes_only",
    "exactly_one_system_completion_event",
    "run_id_must_match_filename_stem",
    "ok_or_blocked_capture_eligible",
    "error_status_diagnostic_only",
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

TERMINAL_COMPLETION_EVALUATOR_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_canonical_run_id",
    "malformed_utf8_jsonl_bytes",
    "empty_jsonl",
    "malformed_json_line",
    "non_object_jsonl_record",
    "jsonl_line_missing_run_id",
    "mixed_run_id",
    "filename_not_jsonl_shape",
    "filename_stem_mismatch",
    "zero_terminal_completion_events",
    "duplicate_terminal_completion_events",
    "missing_terminal_completion_status",
    "error_terminal_completion_status",
    "unknown_terminal_completion_status",
)


@dataclass(frozen=True, slots=True)
class TerminalCompletionEvaluationRequest:
    """Already-read JSONL bytes plus identity metadata for evaluation."""

    canonical_run_id: str
    jsonl_bytes: bytes
    jsonl_filename: str
    expected_filename_stem: str | None = None


@dataclass(frozen=True, slots=True)
class TerminalCompletionEvaluationResult:
    """Deterministic terminal-completion eligibility result."""

    canonical_run_id: str
    filename_stem: str
    line_count: int
    terminal_event_count: int
    terminal_completion_status: str
    terminal_completion_eligible: bool
    result_type: str = TERMINAL_COMPLETION_EVALUATOR_RESULT
    runtime_capture_execution: bool = False
    real_vps_runtime_artifact_reads: bool = False
    package_writes: bool = False
    gate_d_authority: bool = False
    evaluation_or_promotion: bool = False
    broker_api_authority: bool = False
    trading_authority: bool = False
    authority_boundary: tuple[str, ...] = TERMINAL_COMPLETION_EVALUATOR_AUTHORITY_BOUNDARY


def evaluate_terminal_completion_jsonl(
    request: TerminalCompletionEvaluationRequest,
) -> TerminalCompletionEvaluationResult:
    """Evaluate A2 terminal-completion eligibility, or fail closed."""

    if not request.canonical_run_id:
        raise ValueError("canonical_run_id is required")

    filename_stem = _filename_stem(request.jsonl_filename)
    if filename_stem != request.canonical_run_id:
        raise ValueError("filename stem does not match canonical_run_id")
    if (
        request.expected_filename_stem is not None
        and filename_stem != request.expected_filename_stem
    ):
        raise ValueError("filename stem does not match expected stem")

    try:
        text = request.jsonl_bytes.decode("utf-8")
    except (UnicodeDecodeError, AttributeError) as exc:
        raise ValueError("malformed utf-8 jsonl bytes") from exc

    lines = [line for line in text.split("\n") if line.strip()]
    if not lines:
        raise ValueError("empty jsonl")

    terminal_events: list[dict[str, Any]] = []
    for line in lines:
        record = _parse_object_line(line)
        line_run_id = record.get("run_id", record.get("canonical_run_id"))
        if not line_run_id:
            raise ValueError("jsonl line missing run_id")
        if line_run_id != request.canonical_run_id:
            raise ValueError("mixed run_id jsonl")
        if record.get("event_type") == "system" and record.get("stage") == "completion":
            terminal_events.append(record)

    if not terminal_events:
        raise ValueError("zero terminal completion events")
    if len(terminal_events) > 1:
        raise ValueError("duplicate terminal completion events")

    status = terminal_events[0].get("status")
    if not status:
        raise ValueError("missing terminal completion status")
    if status in TERMINAL_COMPLETION_DIAGNOSTIC_ONLY_STATUSES:
        raise ValueError(
            "error terminal completions are diagnostic only and not eligible"
        )
    if status not in TERMINAL_COMPLETION_ELIGIBLE_STATUSES:
        raise ValueError("unknown terminal completion status")

    return TerminalCompletionEvaluationResult(
        canonical_run_id=request.canonical_run_id,
        filename_stem=filename_stem,
        line_count=len(lines),
        terminal_event_count=len(terminal_events),
        terminal_completion_status=status,
        terminal_completion_eligible=True,
    )


def _filename_stem(jsonl_filename: str) -> str:
    if not isinstance(jsonl_filename, str) or not jsonl_filename:
        raise ValueError("jsonl filename is required")
    base = jsonl_filename.rsplit("/", 1)[-1]
    if not base.endswith(_JSONL_SUFFIX) or base == _JSONL_SUFFIX:
        raise ValueError("filename does not match logs/{run_id}.jsonl shape")
    return base[: -len(_JSONL_SUFFIX)]


def _parse_object_line(line: str) -> dict[str, Any]:
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("malformed json line") from exc
    if not isinstance(record, dict):
        raise ValueError("non-object jsonl record")
    return record
