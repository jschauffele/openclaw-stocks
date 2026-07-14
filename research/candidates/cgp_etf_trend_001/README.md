# CGP-ETF-TREND-001 — Diversified ETF Trend/Risk Portfolio

Status: **FROZEN_UNRUN**. This is a candidate, not a claim of success.

## Broker and data boundary

**Execution broker: Interactive Brokers (IBKR), paper account first.**

This candidate has no Alpaca broker dependency. Historical research data and broker execution are separate control planes:

- historical testing must use a certified point-in-time daily total-return dataset from the OpenClaw research data layer;
- paper orders, positions, fills, commissions, rejects, and reconciliation must use the repository's current IBKR adapter/runtime path;
- live raw IBKR prices are used for order sizing and reconciliation;
- adjusted research prices are never submitted as executable prices;
- no candidate code may activate or bypass IBKR safety gates;
- no production or paper integration occurs before the candidate passes all research gates.

The prior README language referring to existing Alpaca infrastructure and an Alpaca research feed was incorrect and has been removed.

## Purpose

Build a practical multi-asset candidate while obeying OpenClaw's no-rescue, point-in-time, effective-breadth, cost, and multiple-testing rules.

## Frozen rule

At the final common trading-day close of each month:

1. Compute total returns over 63, 126, and 252 trading days for each ETF using data available at that close.
2. An ETF is eligible when at least two returns are strictly positive.
3. Set raw risk weight to `(positive_votes / 3) / trailing_63_day_volatility`.
4. Normalize across eligible ETFs.
5. Cap each ETF at 15% and each asset class at 35%; leave residual in cash.
6. Submit target orders through IBKR no earlier than the next common regular trading session.
7. Rebalance monthly. No shorting and no leverage.

Primary research costs are 5 bps one way. Stress tests use 10 and 15 bps plus an additional trading-day execution delay. Paper evaluation uses actual IBKR-reported commissions and fill slippage in addition to the frozen research assumptions.

## Universe

`SPY, QQQ, IWM, EFA, EEM, VNQ, SHY, IEF, TLT, LQD, HYG, GLD, DBC, UUP`

IBKR contract qualification must succeed for every symbol before shadow or paper activation. Any ambiguous, unavailable, or non-primary listing fails closed.

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

## Current implementation

- `model.py` contains the frozen signal and target-weight logic.
- `simulation.py` contains the broker-neutral historical simulator.
- `test_candidate.py` contains deterministic mechanical tests.
- `candidate.json` contains the preregistered specification and kill criteria.
- `ibkr_paper_deployment.md` defines the IBKR-only deployment boundary.

There is currently no `backtest.py` CLI in this candidate directory. The earlier README command naming that nonexistent file was incorrect. A repository-native certified-data runner must be added without changing the frozen signal rules.

## Required evaluation

Do not advance from a backtest alone. Results must pass:

- benchmark-relative and factor-adjusted inference;
- verified global trial count and updated false-strategy noise ceiling;
- Deflated Sharpe Ratio;
- block-bootstrap or appropriate dependent-return inference;
- yearly and return-concentration diagnostics;
- base, doubled-cost, tripled-cost, and delayed-execution stress;
- clean-environment independent reproduction;
- IBKR shadow-order reconciliation;
- IBKR paper trading with actual fills and commissions.

## Non-negotiable decision rule

Any failed predeclared gate kills the candidate. No filter, lookback, universe, weighting, broker-fill interpretation, or execution change may be introduced after viewing results. A modification is a new candidate and a new trial.
