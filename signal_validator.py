from __future__ import annotations


ALLOWED_SIGNALS = {"buy", "hold"}
ALLOWED_DECISIONS = {"buy", "hold"}


def validate_signal_result(signal_result: dict) -> dict:
    if not isinstance(signal_result, dict):
        raise ValueError("signal_result must be a dict")

    required_keys = {
        "signal",
        "decision",
        "reason",
        "previous_close",
        "latest_close",
        "price_delta",
        "percent_change",
    }

    missing = required_keys - set(signal_result.keys())
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"signal_result missing required keys: {missing_list}")

    signal = str(signal_result["signal"]).strip().lower()
    decision = str(signal_result["decision"]).strip().lower()
    reason = str(signal_result["reason"]).strip()

    if signal not in ALLOWED_SIGNALS:
        raise ValueError(f"Unsupported signal: {signal}")

    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision: {decision}")

    if not reason:
        raise ValueError("signal_result.reason must be non-empty")

    previous_close = float(signal_result["previous_close"])
    latest_close = float(signal_result["latest_close"])
    price_delta = float(signal_result["price_delta"])
    percent_change = float(signal_result["percent_change"])

    return {
        "signal": signal,
        "decision": decision,
        "reason": reason,
        "previous_close": previous_close,
        "latest_close": latest_close,
        "price_delta": price_delta,
        "percent_change": percent_change,
    }
