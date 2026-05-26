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

## Initial Example Fixture Intake

The examples below are proposed review fixtures only. They are not accepted tests, approved thresholds, approved behavior changes, or implementation requirements.

User review is required before any example can move to test planning. Historical confirmation or paper-trading evidence is required where the review concern depends on actual follow-through after the close sequence.

### Positive Control Examples

These examples are intended to preserve clear baseline BUY behavior if stronger trend confirmation is later considered.

#### Positive Control 1

- Close sequence: `100.00, 101.00, 102.20, 103.50`
- Current 3-close expected behavior: BUY
- Proposed review concern: clear consecutive upward closes should not be rejected by stronger confirmation without evidence that the move is weak.
- Expected stronger-confirmation behavior: provisional BUY
- Review status: needs user review

#### Positive Control 2

- Close sequence: `50.00, 51.20, 52.60, 54.10`
- Current 3-close expected behavior: BUY
- Proposed review concern: stronger confirmation should preserve visibly accelerating close-only momentum when no broader input surface is approved.
- Expected stronger-confirmation behavior: provisional BUY
- Review status: needs user review

#### Positive Control 3

- Close sequence: `200.00, 203.00, 206.00, 209.00`
- Current 3-close expected behavior: BUY
- Proposed review concern: steady multi-close continuation should remain a candidate BUY unless historical evidence shows the baseline is unreliable in this pattern.
- Expected stronger-confirmation behavior: provisional BUY
- Review status: needs historical confirmation

### False-Positive Review Examples

These examples are intended to review cases where the current 3-close BUY may fire too early. They are not proof that the current behavior is wrong.

#### False-Positive Review 1

- Close sequence: `100.00, 100.05, 100.10, 100.15`
- Current 3-close expected behavior: BUY
- Proposed review concern: small incremental closes may satisfy direction while showing weak trend quality.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs historical confirmation

#### False-Positive Review 2

- Close sequence: `100.00, 100.05, 100.10, 103.00`
- Current 3-close expected behavior: BUY
- Proposed review concern: one large final candle after weak prior closes may represent late or unstable confirmation rather than durable trend.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs user review

#### False-Positive Review 3

- Close sequence: `100.00, 99.80, 100.05, 100.20, 100.35`
- Current 3-close expected behavior: BUY
- Proposed review concern: a short upward run after choppy movement may be too weak to treat as confirmed momentum.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs historical confirmation

### Neutral Or HOLD Examples

These examples are intended to confirm stronger trend review does not introduce new BUY behavior where the baseline remains HOLD.

#### Neutral Example 1

- Close sequence: `100.00, 100.00, 100.00, 100.00`
- Current 3-close expected behavior: HOLD
- Proposed review concern: flat closes should remain neutral.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs user review

#### Neutral Example 2

- Close sequence: `100.00, 101.00, 100.50, 101.20`
- Current 3-close expected behavior: HOLD
- Proposed review concern: choppy alternating closes should not become BUY only because the final close is higher.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs user review

#### Neutral Example 3

- Close sequence: `100.00, 99.50, 99.00, 98.70`
- Current 3-close expected behavior: HOLD
- Proposed review concern: downward continuation should remain outside BUY behavior.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs user review

### Edge Case Coverage

The proposed examples above cover the required edge-case categories as planning fixtures:

- Small incremental closes: False-Positive Review 1
- One large final candle after weak prior closes: False-Positive Review 2
- Choppy alternating closes: Neutral Example 2 and False-Positive Review 3
- Shallow trend versus strong trend: False-Positive Review 1 compared with Positive Control 1, Positive Control 2, and Positive Control 3
- Insufficient close count: still needed before test planning

#### Insufficient Close Count Edge Case

- Close sequence: `100.00, 101.00`
- Current 3-close expected behavior: HOLD
- Proposed review concern: insufficient close count must remain deterministic and must not produce BUY under stronger confirmation.
- Expected stronger-confirmation behavior: provisional HOLD
- Review status: needs user review

### Intake Decisions Still Required

Before test planning, the following decisions remain unresolved:

- Whether the current percent threshold remains unchanged or becomes part of review.
- Whether stronger trend confirmation modifies the current strategy ID or requires a new strategy ID.
- Which examples are accepted after user review.
- Which examples require historical or paper-trading confirmation.
- Whether any proposed provisional outcome should be changed before tests are written.

No example in this section approves implementation, tests, strategy behavior changes, trading behavior changes, or expanded input data.

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
