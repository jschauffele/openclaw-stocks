from __future__ import annotations


ALLOWED_ACTIONS = {"buy", "hold", "sell"}


def build_action_proposal(
    symbol: str,
    qty: int,
    signal_result: dict,
) -> dict:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol must be non-empty")

    if qty <= 0:
        raise ValueError("qty must be greater than 0")

    signal = str(signal_result["signal"]).strip().lower()
    decision = str(signal_result["decision"]).strip().lower()
    reason = str(signal_result["reason"]).strip()

    if decision == "buy":
        action = "buy"
        should_submit = True
    elif decision == "sell":
        action = "sell"
        should_submit = False
    else:
        action = "hold"
        should_submit = False

    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported action: {action}")

    return {
        "action": action,
        "should_submit": should_submit,
        "symbol": normalized_symbol,
        "qty": qty,
        "signal": signal,
        "decision": decision,
        "reason": reason,
        "previous_close": float(signal_result["previous_close"]),
        "latest_close": float(signal_result["latest_close"]),
        "price_delta": float(signal_result["price_delta"]),
        "percent_change": float(signal_result["percent_change"]),
        "three_close_percent_change": float(
            signal_result["three_close_percent_change"]
        ),
    }
