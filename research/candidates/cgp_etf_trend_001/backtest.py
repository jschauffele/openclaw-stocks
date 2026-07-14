from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from model import Bar, UNIVERSE  # noqa: E402
from simulation import run_backtest  # noqa: E402

DEFAULT_DATA_ROOT = Path('/Users/openclawcontrol/openclaw-market-data')


def _latest_parquet(partition: Path) -> Path:
    files = sorted(partition.glob('tiingo-*.parquet'))
    if not files:
        files = sorted(partition.glob('*.parquet'))
    if not files:
        raise FileNotFoundError(f'No parquet files found under {partition}')
    return files[-1]


def load_tiingo_bars(data_root: Path) -> dict[str, list[Bar]]:
    base = data_root.expanduser().resolve() / 'tiingo'
    canonical_root = base / 'canonical'
    derived_root = base / 'derived'
    bars_by_symbol: dict[str, list[Bar]] = {}

    for symbol in UNIVERSE:
        canonical_path = _latest_parquet(canonical_root / f'ticker={symbol}')
        derived_path = _latest_parquet(derived_root / f'ticker={symbol}')

        canonical = pd.read_parquet(canonical_path)
        derived = pd.read_parquet(derived_path)
        canonical['date'] = pd.to_datetime(canonical['date']).dt.normalize()
        derived['date'] = pd.to_datetime(derived['date']).dt.normalize()

        merged = canonical.merge(
            derived[['date', 'ticker', 'computed_adjClose']],
            on=['date', 'ticker'],
            how='inner',
            validate='one_to_one',
        ).sort_values('date')
        if merged.empty:
            raise ValueError(f'{symbol}: canonical/derived merge produced no rows')
        if (merged['close'] <= 0).any() or (merged['computed_adjClose'] <= 0).any():
            raise ValueError(f'{symbol}: non-positive raw or adjusted close')

        factor = merged['computed_adjClose'] / merged['close']
        merged['adj_open'] = merged['open'] * factor
        merged['adj_high'] = merged['high'] * factor
        merged['adj_low'] = merged['low'] * factor
        merged['adj_close'] = merged['computed_adjClose']

        bars_by_symbol[symbol] = [
            Bar(
                trading_date=row.date.date(),
                open=float(row.adj_open),
                high=float(row.adj_high),
                low=float(row.adj_low),
                close=float(row.adj_close),
                volume=float(row.volume),
            )
            for row in merged.itertuples(index=False)
        ]

    return bars_by_symbol


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run CGP-ETF-TREND-001 on certified Tiingo parquet data')
    parser.add_argument('--data-root', default=str(DEFAULT_DATA_ROOT))
    parser.add_argument('--start', default='2010-01-01')
    parser.add_argument('--end', default=None)
    parser.add_argument('--cost-bps', type=float, default=5.0)
    parser.add_argument('--execution-delay-days', type=int, default=1)
    parser.add_argument(
        '--output',
        default=str(HERE / 'artifacts' / 'cgp_etf_trend_001_backtest.json'),
    )
    args = parser.parse_args(argv)

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else None
    bars = load_tiingo_bars(Path(args.data_root))
    result = run_backtest(
        bars,
        start=start,
        end=end,
        cost_bps=args.cost_bps,
        execution_delay_days=args.execution_delay_days,
    )
    output = Path(args.output).expanduser().resolve()
    _write_json(output, result)

    final = result['daily'][-1]
    print(json.dumps({
        'candidate_id': result['candidate_id'],
        'output': str(output),
        'observations': len(result['daily']),
        'rebalances': len(result['rebalances']),
        'final_portfolio_value': final['portfolio_value'],
        'final_date': final['date'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
