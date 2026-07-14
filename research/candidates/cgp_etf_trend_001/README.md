# CGP-ETF-TREND-001 — Diversified ETF Trend/Risk Portfolio

Status: **FROZEN_UNRUN**. This is a candidate, not a claim of success.

## Purpose

Build the highest-probability practical candidate that can be researched and paper traded with retail-accessible data and the existing Alpaca infrastructure, while obeying OpenClaw's no-rescue, multi-asset, point-in-time, and multiple-testing rules.

## Rule

At the final common trading-day close of each month:

1. Compute adjusted total returns over 63, 126, and 252 trading days for each ETF.
2. An ETF is eligible when at least two returns are positive.
3. Set raw risk weight to `(positive_votes / 3) / trailing_63_day_volatility`.
4. Normalize across eligible ETFs.
5. Cap each ETF at 15% and each asset class at 35%; leave residual in cash.
6. Execute at the next common trading-day adjusted open.
7. Rebalance monthly. No shorting and no leverage.

The primary test assumes 5 bps one-way costs. Stress tests use 10 and 15 bps and an additional execution-day delay.

## Why this candidate

It deliberately avoids:

- single-security inference;
- inaccessible alternative data;
- fragile event timestamps;
- high turnover;
- optimized portfolio weights;
- leverage and borrow assumptions;
- machine-learning degrees of freedom.

It is not novel. That is intentional: the first goal is a credible paper-tradable survivor, not an impressive narrative.

## Data requirement

The script requests Alpaca daily bars with `adjustment="all"`. It fails closed when any ETF lacks sufficient pre-start history or common dates. The research feed defaults to `iex`; use `OPENCLAW_RESEARCH_FEED=sip` only when the account is entitled to it.

Historical adjusted data are appropriate for research return construction, but the strategy must use live raw prices for orders. Production integration is a separate gate.

## Run

From the repository root after activating the environment:

```bash
python research/candidates/cgp_etf_trend_001/backtest.py \
  --start 2010-01-01 \
  --end 2026-07-13 \
  --cost-bps 5 \
  --execution-delay-days 1
```

Run tests:

```bash
python -m pytest research/candidates/cgp_etf_trend_001/test_backtest.py -q
```

If `pytest` is unavailable:

```bash
python -m pip install pytest
```

## Required evaluation after execution

Do not advance from the backtest alone. The output must be passed through the tournament validator for:

- benchmark-relative and factor-adjusted inference;
- verified global trial count and updated false-strategy noise ceiling;
- Deflated Sharpe Ratio;
- block-bootstrap/HAC inference;
- yearly and trade-concentration diagnostics;
- cost and delayed-execution stress;
- clean-environment reproduction;
- forward shadow and paper trading.

## Non-negotiable decision rule

Any failed predeclared gate kills the candidate. No filter, lookback, universe, weighting, or execution change may be introduced after viewing results. A modification is a new candidate and a new trial.
