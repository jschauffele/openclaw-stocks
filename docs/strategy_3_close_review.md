# 3-Close Momentum Strategy Review

## Purpose

This document records a docs-only strategy behavior review gate for controlled improvement of the current 3-close momentum strategy.

This is review only. It does not approve code implementation, strategy logic changes, trading behavior changes, live trading, IBKR/runtime work, broker work, JSONL emission, observation emission, risk changes, order behavior, reporting behavior, or configuration behavior.

## Current Baseline

Current strategy behavior remains unchanged.

The current 3-close strategy is the baseline for this review. It must be treated as the existing deterministic behavior until a separate test-first implementation gate approves a specific change.

Any future improvement must be:

- deterministic
- test-first
- isolated from risk, execution, broker, runtime, reporting, JSONL, observation, state, order, and configuration behavior
- attributable to explicit evidence and acceptance criteria
- reviewed separately before implementation

AI may advise during review, but AI must not execute trades, override deterministic rules, bypass policy, or become runtime authority.

## Baseline Strengths To Preserve

The current 3-close momentum rule likely does well when the market shows simple directional continuation.

Strengths to preserve:

- It is simple enough to reason about and test.
- It can be evaluated deterministically from closing prices.
- It avoids hidden discretion and AI-dependent interpretation.
- It is compatible with the current metadata-only strategy architecture.
- It can produce stable fixtures for regression tests.
- It does not require broker, runtime, risk, JSONL, observation, or reporting changes to review.

## Weaknesses To Investigate

The current baseline may be vulnerable where three consecutive closes are not enough evidence of durable momentum.

Potential weaknesses:

- It may react late after much of a short move has already occurred.
- It may overreact to small close-to-close changes that are not meaningful after volatility.
- It may perform poorly in range-bound markets.
- It may treat weak candles and strong candles similarly if only closes are considered.
- It may enter after false breakouts if price quickly returns into a prior range.
- It may ignore volume confirmation when the available data supports it.
- It may use thresholds that are too generic across symbols with different volatility profiles.
- It may mix broad momentum behavior with specialized treasury-proxy or MSTR-style behavior if strategy families are not kept separate.

## Failure Modes To Review

Failure modes to investigate before any future change:

- Whipsaw in sideways or range-bound markets.
- False positives after small close-only moves.
- False breakouts near recent highs or lows.
- Momentum signals during unstable or high-volatility regimes.
- Signals that depend on one unusually large candle.
- Signals that reverse quickly after entry.
- Symbol-specific overfitting from thresholds tuned to one instrument.
- Strategy ID ambiguity if a modified rule is treated as compatible with the existing baseline.

## Evidence Required Before Changing Behavior

No strategy behavior change should proceed without evidence that the current baseline has a specific, repeatable deficiency.

Required evidence before implementation planning:

- Historical examples showing where the current 3-close rule performs poorly.
- Positive examples showing where the baseline should continue to behave the same.
- Edge cases around flat closes, tiny moves, gaps, volatile reversals, and range-bound periods.
- Deterministic input fixtures with expected outcomes.
- Acceptance criteria independent of AI discretion.
- A decision on whether the change modifies the current strategy ID or creates a new strategy ID.
- A boundary statement confirming no signal, action, risk, order, broker, runtime, JSONL, observation, reporting, state, or configuration behavior changes are approved by the review document itself.

Historical examples, paper-trading evidence, or user-provided strategy reference material are needed before any implementation gate. User-provided strategy reference material is required if the desired improvement is based on a specific trading thesis, external playbook, or treasury-proxy/MSTR-style strategy concept.

## Deterministic Acceptance Criteria Required

A future implementation gate would need explicit deterministic acceptance criteria before code changes.

Required acceptance criteria:

- Exact input fields and lookback windows.
- Exact threshold values or threshold derivation rules.
- Exact behavior for insufficient data.
- Exact behavior for flat or equal closes.
- Exact behavior for volatile, sideways, uptrend, downtrend, and unknown regimes if regime gating is used.
- Exact expected output for each fixture.
- Proof that the change does not affect risk sizing, broker behavior, order behavior, runtime sequencing, state writes, JSONL events, observation payloads, or reporting ownership.
- Targeted tests for unchanged baseline-compatible cases and changed cases.
- Test evidence that any new or modified strategy remains deterministic and free of outer-mechanism dependencies.

## Strategy ID Compatibility

The default safe assumption is that a material behavior change should create a new strategy ID rather than silently changing the current baseline.

The current strategy ID may be modified only if a future review gate proves the change is backward-compatible, minor, and does not alter the meaning of historical strategy metadata.

A new strategy ID is likely required if the change introduces:

- additional confirmation rules
- new thresholds
- regime-aware gating
- volume requirements
- range-market avoidance
- symbol-specific behavior
- a materially different thesis or instrument family

Treasury-proxy or MSTR-style behavior must remain a separate strategy family unless a future research gate explicitly proves it is only a documentation label and not a distinct strategy behavior.

## Candidate Improvement Ideas For Review Only

The following ideas are not approved for implementation. They are candidate review topics only.

### Stronger Trend Confirmation

Potential value:

- May reduce weak momentum signals by requiring more evidence than three closes alone.

Evidence needed:

- Historical examples where three closes fire too early.
- Fixtures proving stronger confirmation avoids false positives without suppressing desired continuation cases.

Future gate required:

- Test-first strategy behavior planning with exact confirmation rule and strategy ID decision.

### Volatility Filter

Potential value:

- May avoid signals during unstable moves where close-only direction is less reliable.

Evidence needed:

- Volatility definition, threshold rationale, and examples showing current baseline failure during noisy periods.

Future gate required:

- Strategy behavior planning plus targeted tests proving the filter does not touch risk sizing or runtime behavior.

### Range-Market Avoidance

Potential value:

- May reduce whipsaw where closes move slightly inside a flat range.

Evidence needed:

- Deterministic range definition and fixtures for sideways market behavior.

Future gate required:

- Strategy or regime-classifier planning gate depending on whether the rule belongs inside the strategy or regime layer.

### False Breakout Avoidance

Potential value:

- May avoid entries after weak breaks that quickly revert.

Evidence needed:

- Exact breakout definition, re-entry rules, and examples of failed baseline signals.

Future gate required:

- Test-first strategy behavior planning with explicit lookback and threshold rules.

### Minimum Candle Quality Or Body Confirmation

Potential value:

- May distinguish strong directional candles from close-only drift.

Evidence needed:

- Availability and trust level of open/high/low data in the intended review scope.
- Exact candle body or range calculation.

Future gate required:

- Separate data-input boundary review if the current approved strategy input surface would expand beyond closes.

### Volume Confirmation

Potential value:

- May improve confidence that momentum has participation.

Evidence needed:

- Availability and reliability of volume data.
- Deterministic volume threshold and examples.

Future gate required:

- Separate data-input and strategy behavior gate, because volume expands the strategy evidence surface beyond closes.

### Regime-Aware Gating

Potential value:

- May prevent momentum behavior in regimes where continuation is less reliable.

Evidence needed:

- Exact regime IDs, classifier behavior, and expected routing outcomes.

Future gate required:

- Regime-classifier or strategy-router planning gate before implementation.

### Symbol-Specific Thresholds

Potential value:

- May account for instruments with different volatility and movement profiles.

Evidence needed:

- Symbol list, threshold rationale, overfitting guardrails, and fixtures per symbol class.

Future gate required:

- Strategy behavior gate plus configuration boundary review if thresholds become configurable.

### Treasury-Proxy Strategy Family Kept Separate

Potential value:

- Keeps MSTR-style or treasury-proxy research from being silently folded into the current 3-close baseline.

Evidence needed:

- User-provided reference material defining thesis, instruments, constraints, horizon, and evaluation metrics.

Future gate required:

- Separate research review gate before any strategy candidate can be proposed.

## Next Gate

The next allowed gate is docs-only evidence intake for the current 3-close strategy review.

Implementation remains blocked until a future gate defines exact deterministic rule changes, fixture expectations, strategy ID compatibility, and targeted tests.

VPS validation is not needed for this docs-only review phase.
