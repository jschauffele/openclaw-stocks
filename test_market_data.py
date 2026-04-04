from __future__ import annotations

from alpaca_data_provider import AlpacaMarketDataProvider
from market_data import get_historical_bars


def main() -> None:
    provider = AlpacaMarketDataProvider()

    result = get_historical_bars(
        provider=provider,
        symbol="AAPL",
        timeframe="1Day",
        limit=5,
    )

    print("=== MARKET DATA TEST ===")
    print(f"symbol={result.symbol}")
    print(f"timeframe={result.timeframe}")
    print(f"source={result.source}")
    print(f"adjustment_type={result.adjustment_type}")
    print(f"is_adjusted={result.is_adjusted}")
    print(f"bar_count={len(result.candles)}")

    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    else:
        print("warnings: none")

    print("first_bar:")
    first_bar = result.candles[0]
    print(
        f"  timestamp={first_bar.timestamp.isoformat()} "
        f"open={first_bar.open} high={first_bar.high} "
        f"low={first_bar.low} close={first_bar.close} volume={first_bar.volume}"
    )

    print("last_bar:")
    last_bar = result.candles[-1]
    print(
        f"  timestamp={last_bar.timestamp.isoformat()} "
        f"open={last_bar.open} high={last_bar.high} "
        f"low={last_bar.low} close={last_bar.close} volume={last_bar.volume}"
    )


if __name__ == "__main__":
    main()
