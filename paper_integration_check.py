#!/usr/bin/env python3
from __future__ import annotations

import os

from dotenv import load_dotenv

from alpaca_data_provider import AlpacaMarketDataProvider
from decision_engine import build_action_proposal
from market_data import get_historical_bars
from signal_validator import validate_signal_result
from strategy_engine import generate_signal_from_closes


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> int:
    load_dotenv()

    symbol = os.getenv("OPENCLAW_SYMBOL", "AAPL").strip().upper()
    timeframe = os.getenv("OPENCLAW_SIGNAL_TIMEFRAME", "1Day").strip()
    limit = _env_int("OPENCLAW_SIGNAL_LIMIT", 5)
    qty = _env_int("OPENCLAW_QTY", 1)

    print("=== PAPER INTEGRATION CHECK ===")
    print("This check fetches market data, generates a signal, validates it, and prints a decision.")
    print("It does NOT place trades.")
    print()

    provider = AlpacaMarketDataProvider()

    result = get_historical_bars(
        provider=provider,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )

    closes = [candle.close for candle in result.candles]
    raw_signal_result = generate_signal_from_closes(closes)
    signal_result = validate_signal_result(raw_signal_result)
    action_proposal = build_action_proposal(
        symbol=symbol,
        qty=qty,
        signal_result=signal_result,
    )

    print("data_fetch: PASS")
    print(f"symbol={result.symbol}")
    print(f"timeframe={result.timeframe}")
    print(f"source={result.source}")
    print(f"bar_count={len(result.candles)}")

    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    else:
        print("warnings: none")

    print()
    print("signal_generation: PASS")
    print(f"previous_close={signal_result['previous_close']}")
    print(f"latest_close={signal_result['latest_close']}")
    print(f"price_delta={signal_result['price_delta']}")
    print(f"percent_change={signal_result['percent_change']:.4f}")
    print(f"signal={signal_result['signal']}")

    print()
    print("decision_output: PASS")
    print(f"decision={signal_result['decision']}")
    print(f"reason={signal_result['reason']}")

    print()
    print("action_proposal: PASS")
    print(f"action={action_proposal['action']}")
    print(f"should_submit={action_proposal['should_submit']}")
    print(f"symbol={action_proposal['symbol']}")
    print(f"qty={action_proposal['qty']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
