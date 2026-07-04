from __future__ import annotations

import json
from pathlib import Path

import config
from utils import utc_now_iso


OBSERVATION_LOG_FILE = (
    Path(config.BASE_DIR) / "observations" / "observation_log.jsonl"
)
_UNSET = object()


def build_observation_row(
    *,
    run_id: str,
    action_proposal: dict,
    result=None,
    signal_timeframe: str | None = None,
    signal_limit: int | None = None,
    latest_candle_timestamp: str | None = None,
    submit_state: str | None = None,
    reconciliation_status: str | None = None,
    manual_review_required: bool | None = None,
    terminal_for_run: bool | None = None,
    filled_qty: float | None = None,
    working_qty: float | None = None,
    regime_id: str | None | object = _UNSET,
    selected_strategy_id: str | None | object = _UNSET,
    routing_reason: str | None | object = _UNSET,
    eligible_strategy_ids: tuple[str, ...] | object = _UNSET,
    rejected_strategy_ids: tuple[str, ...] | object = _UNSET,
    timestamp_utc: str | None = None,
) -> dict:
    row = {
        "timestamp_utc": timestamp_utc or utc_now_iso(),
        "run_id": run_id,
        "symbol": action_proposal["symbol"],
        "signal": action_proposal["signal"],
        "action": action_proposal["action"],
        "result": result,
        "reason": action_proposal["reason"],
        "previous_close": action_proposal["previous_close"],
        "latest_close": action_proposal["latest_close"],
        "price_delta": action_proposal["price_delta"],
        "percent_change": action_proposal["percent_change"],
        "three_close_percent_change": action_proposal[
            "three_close_percent_change"
        ],
        "signal_timeframe": signal_timeframe,
        "signal_limit": signal_limit,
        "latest_candle_timestamp": latest_candle_timestamp,
    }
    optional_fields = {
        "submit_state": submit_state,
        "reconciliation_status": reconciliation_status,
        "manual_review_required": manual_review_required,
        "terminal_for_run": terminal_for_run,
        "filled_qty": filled_qty,
        "working_qty": working_qty,
    }
    row.update(
        {
            field: value
            for field, value in optional_fields.items()
            if value is not None
        }
    )
    routing_fields = {
        "regime_id": regime_id,
        "selected_strategy_id": selected_strategy_id,
        "routing_reason": routing_reason,
        "eligible_strategy_ids": eligible_strategy_ids,
        "rejected_strategy_ids": rejected_strategy_ids,
    }
    row.update(
        {
            field: value
            for field, value in routing_fields.items()
            if value is not _UNSET
        }
    )
    return row


def append_observation(
    *,
    run_id: str,
    action_proposal: dict,
    result=None,
    signal_timeframe: str | None = None,
    signal_limit: int | None = None,
    latest_candle_timestamp: str | None = None,
    submit_state: str | None = None,
    reconciliation_status: str | None = None,
    manual_review_required: bool | None = None,
    terminal_for_run: bool | None = None,
    filled_qty: float | None = None,
    working_qty: float | None = None,
    regime_id: str | None | object = _UNSET,
    selected_strategy_id: str | None | object = _UNSET,
    routing_reason: str | None | object = _UNSET,
    eligible_strategy_ids: tuple[str, ...] | object = _UNSET,
    rejected_strategy_ids: tuple[str, ...] | object = _UNSET,
    log_file: str | Path = OBSERVATION_LOG_FILE,
) -> None:
    row = build_observation_row(
        run_id=run_id,
        action_proposal=action_proposal,
        result=result,
        signal_timeframe=signal_timeframe,
        signal_limit=signal_limit,
        latest_candle_timestamp=latest_candle_timestamp,
        submit_state=submit_state,
        reconciliation_status=reconciliation_status,
        manual_review_required=manual_review_required,
        terminal_for_run=terminal_for_run,
        filled_qty=filled_qty,
        working_qty=working_qty,
        regime_id=regime_id,
        selected_strategy_id=selected_strategy_id,
        routing_reason=routing_reason,
        eligible_strategy_ids=eligible_strategy_ids,
        rejected_strategy_ids=rejected_strategy_ids,
    )
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":"), sort_keys=False))
        f.write("\n")
