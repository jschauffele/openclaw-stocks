from __future__ import annotations

import json
from pathlib import Path

import config
from utils import utc_now_iso


OBSERVATION_LOG_FILE = (
    Path(config.BASE_DIR) / "observations" / "observation_log.jsonl"
)


def build_observation_row(
    *,
    run_id: str,
    action_proposal: dict,
    result=None,
    signal_timeframe: str | None = None,
    signal_limit: int | None = None,
    latest_candle_timestamp: str | None = None,
    timestamp_utc: str | None = None,
) -> dict:
    return {
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


def append_observation(
    *,
    run_id: str,
    action_proposal: dict,
    result=None,
    signal_timeframe: str | None = None,
    signal_limit: int | None = None,
    latest_candle_timestamp: str | None = None,
    log_file: str | Path = OBSERVATION_LOG_FILE,
) -> None:
    row = build_observation_row(
        run_id=run_id,
        action_proposal=action_proposal,
        result=result,
        signal_timeframe=signal_timeframe,
        signal_limit=signal_limit,
        latest_candle_timestamp=latest_candle_timestamp,
    )
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":"), sort_keys=False))
        f.write("\n")
