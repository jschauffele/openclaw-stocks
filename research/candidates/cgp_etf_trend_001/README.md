# CGP-ETF-TREND-001 — Diversified ETF Trend/Risk Portfolio

Status: **FROZEN_UNRUN**. This is a candidate, not a claim of success.

## Broker and data boundary

**Execution broker: Interactive Brokers (IBKR), paper account first.**

This candidate has no Alpaca broker dependency. Historical research data and broker execution are separate control planes:

- historical testing uses the certified Tiingo daily data layout under the OpenClaw research data root;
- paper orders, positions, fills, commissions, rejects, and reconciliation use the repository's IBKR adapter/runtime path;
- live raw IBKR prices are used for order sizing and reconciliation;
- adjusted research prices are never submitted as executable prices;
- candidate code may not activate or bypass IBKR safety gates;
- no paper integration occurs before all research gates pass.

## Frozen rule

At the final common trading-day close of each month:

1. Compute total returns over 63, 126, and 252 trading days for each ETF.
2. An ETF is eligible when at least two returns are strictly positive.
3. Set raw risk weight to `(positive_votes / 3) / trailing_63_day_volatility`.
4. Normalize across eligible ETFs.
5. Cap each ETF at 15% and each asset class at 35%; leave residual in cash.
6. Execute no earlier than the next common regular trading session.
7. Rebalance monthly. No shorting and no leverage.

Primary research costs are 5 bps one way. Stress tests use 10 and 15 bps plus an additional trading-day execution delay. Paper evaluation uses actual IBKR commissions and fill slippage.

## Universe

`SPY, QQQ, IWM, EFA, EEM, VNQ, SHY, IEF, TLT, LQD, HYG, GLD, DBC, UUP`

## Exact local run sequence

From the repository root:

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks
git fetch origin
git switch research/cgp-etf-trend-001
git pull --ff-only origin research/cgp-etf-trend-001
```

Activate the project environment:

```bash
source .venv-312/bin/activate
```

Install research dependencies only when missing:

```bash
python -m pip install pandas pyarrow pytest
```

### 1. Ingest the complete ETF universe

The ingestion command requires `TIINGO_API_TOKEN` in the environment and writes outside the repository to `/Users/openclawcontrol/openclaw-market-data` by default.

```bash
python -m data_layer.ingest \
  --symbols SPY QQQ IWM EFA EEM VNQ SHY IEF TLT LQD HYG GLD DBC UUP
```

The command must end with:

```text
PHASE_1_INGESTION_IMPLEMENTATION_OBSERVED
```

If it reports `BLOCKED`, do not run the candidate until the stated data problem is resolved.

### 2. Run mechanical tests

```bash
python -m pytest research/candidates/cgp_etf_trend_001/test_candidate.py -q
```

### 3. Run the frozen primary backtest once

```bash
python research/candidates/cgp_etf_trend_001/backtest.py \
  --data-root /Users/openclawcontrol/openclaw-market-data \
  --start 2010-01-01 \
  --cost-bps 5 \
  --execution-delay-days 1 \
  --output research/candidates/cgp_etf_trend_001/artifacts/primary.json
```

The command prints the output path, observation count, rebalance count, final date, and final portfolio value. The full daily and rebalance records are written to `artifacts/primary.json`.

### 4. Run only the preregistered stress cases

```bash
python research/candidates/cgp_etf_trend_001/backtest.py \
  --data-root /Users/openclawcontrol/openclaw-market-data \
  --start 2010-01-01 --cost-bps 10 --execution-delay-days 1 \
  --output research/candidates/cgp_etf_trend_001/artifacts/cost_10bps.json

python research/candidates/cgp_etf_trend_001/backtest.py \
  --data-root /Users/openclawcontrol/openclaw-market-data \
  --start 2010-01-01 --cost-bps 15 --execution-delay-days 1 \
  --output research/candidates/cgp_etf_trend_001/artifacts/cost_15bps.json

python research/candidates/cgp_etf_trend_001/backtest.py \
  --data-root /Users/openclawcontrol/openclaw-market-data \
  --start 2010-01-01 --cost-bps 5 --execution-delay-days 2 \
  --output research/candidates/cgp_etf_trend_001/artifacts/delay_2days.json
```

Do not change lookbacks, the ETF universe, caps, signal threshold, volatility window, or execution timing after seeing these results.

## IBKR paper phase

There is intentionally no one-command IBKR strategy submission yet. The candidate must first clear the historical validation, noise-ceiling, DSR, cost, delay, concentration, and independent-reproduction gates. After that, a separate shadow adapter must translate frozen target weights into IBKR-qualified contracts and proposed orders, with no submission authority. Only after shadow reconciliation passes can the existing paper-only IBKR execution gates be used.

## Required evaluation

A backtest does not advance the candidate by itself. Results must pass:

- benchmark-relative and factor-adjusted inference;
- verified global trial count and updated noise ceiling;
- Deflated Sharpe Ratio;
- dependent-return inference;
- yearly and return-concentration diagnostics;
- all preregistered cost and delay stresses;
- clean-environment independent reproduction;
- IBKR shadow reconciliation;
- IBKR paper trading with actual fills and commissions.

## Non-negotiable decision rule

Any failed predeclared gate kills the candidate. No rescue modification is permitted.
