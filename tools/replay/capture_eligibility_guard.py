"""Pure deterministic market-session package-capture eligibility guard (Gate D D13).

This guard converts the Gate D Record D12 market-session sufficiency rule into a
deterministic, fail-closed, capture-time check. It inspects already-read JSONL
bytes and already-read last_run_report bytes for the terminal-completion
market/session reason and decides whether a run is capture-eligible. It reads no
files, writes no files, writes no packages, executes no runtime capture,
evaluates nothing, scores nothing, and carries no promotion, broker,
strategy/risk/execution, paper-trading, or live-trading authority.

Eligibility rules:
- A market/session-ineligible reason (market_holiday_or_closed_day,
  before_regular_session_open, after_regular_session_close, market_closed /
  market-closed, or any market/session reason token) on the terminal event
  (``payload.reason`` or top-level ``reason``) or on the last_run_report reason
  fails closed.
- A ``blocked`` terminal status with a missing reason fails closed.
- A ``blocked`` terminal status with an ambiguous / unknown reason (not on the
  explicit non-market eligible allowlist) fails closed.
- A ``blocked`` terminal status with an explicit non-market eligible reason is
  eligible.
- A non-``blocked`` (e.g. ``ok``) terminal status is eligible (market/session
  guards only ever block; an ``ok`` run is a decision/submission/dry-run).

This guard does not replace the terminal-completion status / run_id-alignment /
report-alignment / order_state / no-overwrite / explicit-authorization
protections; it is an additional capture-time guard layered before package
writing.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


CAPTURE_ELIGIBILITY_GUARD = "capture_market_session_eligibility_guard_in_memory_only"
CAPTURE_ELIGIBILITY_GUARD_RESULT = "capture_eligibility_guard_result"

TERMINAL_BLOCKED_STATUS = "blocked"

MARKET_SESSION_INELIGIBLE_REASONS: tuple[str, ...] = (
    "market_holiday_or_closed_day",
    "before_regular_session_open",
    "after_regular_session_close",
    "market_closed",
)

# Normalized substring tokens that mark a reason as market/session ineligible,
# catching variants beyond the exact set above.
_MARKET_SESSION_TOKENS: tuple[str, ...] = (
    "market_holiday",
    "market_closed",
    "closed_day",
    "before_regular_session",
    "after_regular_session",
    "regular_session",
    "session_closed",
    "market_session",
)

# Explicit non-market production block reasons that remain capture-eligible.
# Conservative allowlist: any blocked reason not listed here fails closed, so a
# later lane may extend it; an incomplete allowlist over-rejects (safe), never
# over-accepts.
ELIGIBLE_NON_MARKET_BLOCK_REASONS: tuple[str, ...] = (
    "killswitch_disabled",
    "duplicate",
    "duplicate_recent_order",
    "duplicate_cooldown_active",
    "projected_exposure_exceeds_max_position_size",
    "risk_blocked",
    "manual_review_required",
    "reconciliation_ambiguous",
    "reconciliation_manual_review_required",
    "strategy_hold",
    "no_signal",
)

_ELIGIBLE_NON_MARKET_NORMALIZED: frozenset[str] = frozenset(
    reason.lower().replace("-", "_") for reason in ELIGIBLE_NON_MARKET_BLOCK_REASONS
)

CAPTURE_ELIGIBILITY_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "market_holiday_or_closed_day_reason",
    "before_regular_session_open_reason",
    "after_regular_session_close_reason",
    "market_closed_reason",
    "market_session_reason_token",
    "missing_blocked_reason",
    "ambiguous_unknown_blocked_reason",
    "malformed_jsonl_bytes",
    "malformed_report_bytes",
    "terminal_completion_event_not_isolated",
    "missing_canonical_run_id",
)

CAPTURE_ELIGIBILITY_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "market_session_capture_eligibility_only",
    "evidence_only",
    "non_authoritative",
    "fail_closed_on_market_session_or_unknown_blocked_reason",
    "no_package_writes",
    "no_filesystem_reads",
    "no_runtime_capture_execution",
    "no_evaluation_or_scoring",
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class CaptureEligibilityGuard:
    """Static governed capture-eligibility guard vocabulary."""

    name: str = CAPTURE_ELIGIBILITY_GUARD
    market_ineligible_reasons: tuple[str, ...] = MARKET_SESSION_INELIGIBLE_REASONS
    eligible_non_market_block_reasons: tuple[str, ...] = (
        ELIGIBLE_NON_MARKET_BLOCK_REASONS
    )
    authority_boundary: tuple[str, ...] = CAPTURE_ELIGIBILITY_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class CaptureEligibilityGuardFailClosedConditions:
    """Static fail-closed condition vocabulary for the capture eligibility guard."""

    conditions: tuple[str, ...] = CAPTURE_ELIGIBILITY_FAIL_CLOSED_CONDITIONS


def _normalize_reason(reason: object) -> str:
    if not isinstance(reason, str):
        return ""
    return reason.strip().lower().replace("-", "_")


def is_market_session_reason(reason: object) -> bool:
    """Return True for any market/session-ineligible reason (exact or token)."""

    normalized = _normalize_reason(reason)
    if not normalized:
        return False
    if normalized in MARKET_SESSION_INELIGIBLE_REASONS:
        return True
    return any(token in normalized for token in _MARKET_SESSION_TOKENS)


def _terminal_reason_from_jsonl(jsonl_bytes: bytes) -> str | None:
    try:
        text = jsonl_bytes.decode("utf-8")
    except (UnicodeDecodeError, AttributeError) as exc:
        raise ValueError("malformed jsonl bytes for eligibility guard") from exc
    completion_events: list[dict[str, Any]] = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError("malformed jsonl bytes for eligibility guard") from exc
        if not isinstance(record, dict):
            raise ValueError("malformed jsonl bytes for eligibility guard")
        if record.get("event_type") == "system" and record.get("stage") == "completion":
            completion_events.append(record)
    if len(completion_events) != 1:
        raise ValueError("terminal completion event is not isolated")
    event = completion_events[0]
    payload = event.get("payload")
    if isinstance(payload, dict) and payload.get("reason"):
        return payload.get("reason")
    return event.get("reason")


def _report_reason(report_bytes: bytes | None) -> str | None:
    if report_bytes is None or report_bytes == b"":
        return None
    try:
        text = report_bytes.decode("utf-8")
    except (UnicodeDecodeError, AttributeError) as exc:
        raise ValueError("malformed report bytes for eligibility guard") from exc
    try:
        report = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("malformed report bytes for eligibility guard") from exc
    if not isinstance(report, dict):
        raise ValueError("malformed report bytes for eligibility guard")
    if report.get("reason"):
        return report.get("reason")
    payload = report.get("payload")
    if isinstance(payload, dict) and payload.get("reason"):
        return payload.get("reason")
    return None


def evaluate_capture_market_eligibility(
    *,
    canonical_run_id: str,
    terminal_completion_status: str,
    jsonl_bytes: bytes,
    last_run_report_bytes: bytes | None,
) -> dict[str, Any]:
    """Decide market-session capture eligibility, or fail closed.

    Returns governed non-authoritative metadata on eligibility; raises
    ValueError for any market/session-ineligible, missing, ambiguous, or
    malformed evidence.
    """

    if not canonical_run_id:
        raise ValueError("canonical_run_id is required")

    terminal_reason = _terminal_reason_from_jsonl(jsonl_bytes)
    report_reason = _report_reason(last_run_report_bytes)

    # Block if either source carries a market/session-ineligible reason.
    if is_market_session_reason(terminal_reason) or is_market_session_reason(
        report_reason
    ):
        raise ValueError(
            "market/session-ineligible run is not capture-eligible"
        )

    if terminal_completion_status != TERMINAL_BLOCKED_STATUS:
        # ok (or other eligible non-blocked) terminal status: a decision,
        # submission, or dry run; market/session guards only ever block.
        return _result(
            canonical_run_id=canonical_run_id,
            terminal_completion_status=terminal_completion_status,
            eligibility_basis="non_blocked_eligible",
            terminal_reason=terminal_reason,
            report_reason=report_reason,
        )

    # Blocked terminal status: require an explicit non-market eligible reason.
    effective_reason = _normalize_reason(terminal_reason) or _normalize_reason(
        report_reason
    )
    if not effective_reason:
        raise ValueError(
            "blocked run is missing a reason and is not capture-eligible"
        )
    if effective_reason not in _ELIGIBLE_NON_MARKET_NORMALIZED:
        raise ValueError(
            "blocked run has an ambiguous or unknown reason and is not "
            "capture-eligible"
        )
    return _result(
        canonical_run_id=canonical_run_id,
        terminal_completion_status=terminal_completion_status,
        eligibility_basis="explicit_non_market_block_eligible",
        terminal_reason=terminal_reason,
        report_reason=report_reason,
    )


def _result(
    *,
    canonical_run_id: str,
    terminal_completion_status: str,
    eligibility_basis: str,
    terminal_reason: str | None,
    report_reason: str | None,
) -> dict[str, Any]:
    return {
        "result_type": CAPTURE_ELIGIBILITY_GUARD_RESULT,
        "canonical_run_id": canonical_run_id,
        "terminal_completion_status": terminal_completion_status,
        "capture_market_eligible": True,
        "eligibility_basis": eligibility_basis,
        "terminal_reason": terminal_reason,
        "report_reason": report_reason,
        "evidence_only": True,
        "non_authoritative": True,
        "package_writes": False,
        "filesystem_reads": False,
        "runtime_capture_execution": False,
        "evaluation_or_scoring": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": CAPTURE_ELIGIBILITY_AUTHORITY_BOUNDARY,
    }
