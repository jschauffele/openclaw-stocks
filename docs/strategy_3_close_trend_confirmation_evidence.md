# Stronger Trend Confirmation Evidence Intake

## Purpose

This document defines the docs-only evidence intake gate for evaluating stronger trend confirmation as the first possible improvement to the current 3-close momentum strategy.

This is evidence intake only. Stronger trend confirmation is a candidate improvement only. This document does not approve code implementation, strategy logic changes, trading behavior changes, live trading, broker/runtime/IBKR work, signal changes, action changes, risk changes, order behavior changes, JSONL emission, observation emission, reporting behavior changes, state changes, or configuration behavior changes.

## Current Baseline

Current 3-close behavior remains unchanged.

The current 3-close strategy remains the baseline until a separate test-first implementation gate approves a specific deterministic rule change.

Stronger trend confirmation should remain close-only unless a future gate approves a broader input surface. Open, high, low, volume, indicators, symbol-specific configuration, broker state, runtime state, observations, JSONL events, risk data, execution data, and order data are not approved inputs by this evidence gate.

Any future rule must be:

- deterministic
- test-first
- isolated from signal, action, risk, order, broker, runtime, JSONL, observation, reporting, state, execution, and configuration behavior
- attributable to explicit evidence
- reviewed before implementation

AI may assist with review, but expected outcomes must not depend on AI discretion.

## Evidence Required Before Test Planning

Evidence must be concrete enough to support deterministic fixtures and expected outcomes.

Each example must include:

- exact close-price sequence
- current expected 3-close baseline outcome
- proposed stronger-confirmation expected outcome
- reason the expected outcome is deterministic
- whether the example is a positive control, false-positive case, neutral case, or edge case
- whether the percent threshold remains unchanged or is part of the review
- whether the example supports modifying the current strategy ID or creating a new strategy ID

Historical examples, paper-trading examples, or user-provided reference material are needed before this candidate can move to test planning.

## Required Example Classes

### Positive Controls

Positive controls are examples where the current 3-close BUY should remain BUY after stronger trend confirmation.

Required evidence:

- at least 3 exact close-price sequences
- expected outcome remains BUY for each case
- evidence that each sequence shows durable enough trend behavior to preserve the baseline BUY
- explanation of why stronger confirmation should not reject the case

### False-Positive Cases

False-positive cases are examples where the current 3-close BUY appears to fire too early.

Required evidence:

- at least 3 exact close-price sequences
- current baseline outcome is BUY
- proposed stronger-confirmation expected outcome is not BUY
- explanation of why the current BUY is considered early, weak, or unreliable
- follow-through or context evidence if available from historical or paper-trading records

### HOLD Or Neutral Cases

Neutral cases are examples where HOLD should remain HOLD.

Required evidence:

- at least 3 exact close-price sequences
- current baseline outcome is HOLD
- proposed stronger-confirmation expected outcome remains HOLD
- explanation of why stronger confirmation must not introduce a new BUY

## Required Edge Cases

The evidence set should include exact close-price sequences for these edge cases before test planning:

- small incremental closes
- one large final candle after weak prior closes
- choppy alternating closes
- shallow trend versus strong trend
- insufficient close count

Each edge case must include deterministic expected output and must identify whether the current percent threshold remains unchanged or becomes part of the review.

## Threshold Review Question

Before test planning, the review must decide whether the current percent threshold remains unchanged.

Default assumption:

- The percent threshold remains unchanged for the first stronger-confirmation evaluation.

Changing the threshold would expand the candidate beyond confirmation logic and would require explicit review evidence, expected fixtures, and a strategy ID compatibility decision.

## Strategy ID Question

Before test planning, the review must decide whether stronger trend confirmation modifies the existing strategy ID or requires a new strategy ID.

Default assumption:

- Stronger trend confirmation likely requires a new strategy ID if it changes BUY/HOLD behavior in any material way.

The existing strategy ID may be modified only if a future review proves the change is minor, backward-compatible, and does not alter the meaning of historical strategy metadata.

## Acceptance Criteria Before Test Planning

This candidate may move to test planning only after all of the following are true:

- at least 3 positive control examples exist
- at least 3 false-positive examples exist
- at least 3 HOLD or neutral examples exist
- each example has an exact close-price sequence
- each example has deterministic expected output
- no expected output depends on AI discretion
- no new input surface beyond closes is required unless separately approved
- threshold behavior is explicitly decided
- strategy ID compatibility is explicitly decided
- no risk, execution, broker, order, runtime, JSONL, observation, reporting, state, or configuration behavior change is approved

## Blocked Scope

The following remain blocked by this evidence gate:

- implementation
- tests
- signal generation changes
- action proposal changes
- strategy execution
- risk sizing changes
- broker behavior changes
- order behavior changes
- runtime behavior changes
- JSONL event changes
- observation payload changes
- reporting behavior changes
- state behavior changes
- configuration behavior changes
- live trading
- IBKR work
- VPS validation

## Recommended Next Gate

The next gate is docs-only evidence collection for stronger trend confirmation.

Do not proceed to test planning until the required examples, threshold decision, expected outcomes, and strategy ID recommendation are recorded.
