from __future__ import annotations

from typing import Any, Iterable

from runtime_visibility_preflight import run_runtime_visibility_preflight


def build_runtime_visibility_summary(
    providers: Iterable[object],
) -> dict[str, Any]:
    reports = run_runtime_visibility_preflight(providers)
    blocking_report = next(
        (report for report in reports if bool(report.get("blocking"))),
        None,
    )
    return {
        "runtime_visibility_reports": reports,
        "runtime_visibility_blocking": blocking_report is not None,
        "runtime_visibility_reason": _summary_reason(blocking_report),
    }


def _summary_reason(blocking_report: dict[str, Any] | None) -> str:
    if blocking_report is None:
        return "runtime_visibility_clear"
    provider_name = blocking_report.get("provider_name") or "unknown_provider"
    reason = blocking_report.get("reason") or "unknown_reason"
    return f"{provider_name}:{reason}"
