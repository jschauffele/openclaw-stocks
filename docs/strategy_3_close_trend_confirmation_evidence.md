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

## Threshold And Strategy ID Decision Gate

The drafted example set is sufficient to move to threshold-decision planning.

Test planning remains blocked. Implementation remains blocked. Threshold decision remains unresolved. Strategy ID decision remains unresolved. User review remains required.

This gate records decision items only. It does not approve tests, implementation, strategy behavior changes, trading behavior changes, or expanded input data.

### 1. Percent Threshold

Decision item:

- Decide whether the current percent threshold remains unchanged.

Current gate decision:

- No threshold change is approved in this gate.
- The current percent threshold remains unresolved for future review.

Evidence that could justify changing the threshold later:

- user-accepted examples showing the baseline threshold admits weak BUY cases
- historical or paper-trading examples showing repeated false positives at the current threshold
- positive-control examples proving a revised threshold would not reject desired BUY cases
- deterministic fixtures showing the threshold effect without AI discretion
- explicit strategy ID compatibility analysis for any threshold change

### 2. Stronger Trend Confirmation Rule

Decision item:

- Decide what close-only confirmation rule is being considered.

Current gate decision:

- Stronger trend confirmation remains candidate-only.
- No confirmation rule is approved for implementation.
- Any future rule must remain close-only unless a separate gate approves broader inputs.

Possible future rule descriptions must identify exact close sequence requirements, lookback handling, insufficient-data behavior, and expected outputs before test planning.

### 3. Strategy Identity

Decision item:

- Decide whether stronger trend confirmation modifies the existing strategy ID or requires a new strategy ID.

Default recommendation:

- Create a new strategy ID for any material behavior change.

Existing strategy ID may remain only if future review proves the change is minor, backward-compatible, and does not alter historical metadata meaning.

Current gate decision:

- No final strategy ID decision is made in this gate.

### 4. Fixture Acceptance

Decision item:

- User must accept, revise, or reject each provisional example before test planning.

Current gate decision:

- No example is accepted as a test fixture in this gate.
- Historical or paper confirmation remains required for examples marked as needing confirmation.
- Provisional expected outcomes may still be revised before tests are written.

### 5. Next Required Gate

The next required gate is user/Codex fixture acceptance review.

If the fixture acceptance review accepts enough examples and resolves threshold and strategy ID decisions, a separate test-planning gate may follow.

## Fixture Acceptance Review

This section classifies the drafted examples for review-readiness only.

Accepted examples are still not tests. Accepted examples are only candidates for a future separate test-planning gate. Historical or paper confirmation remains required where marked. User review remains required before test planning. Threshold decision remains unresolved. Strategy ID decision remains unresolved. Test planning remains blocked. Implementation remains blocked.

Allowed fixture review classifications:

- `ACCEPTED_FOR_REVIEW_FIXTURE`
- `NEEDS_HISTORICAL_CONFIRMATION`
- `NEEDS_USER_REVIEW`
- `REJECTED_OR_REVISE`

### Fixture Classification Table

| Example | Fixture review classification | Rationale |
| --- | --- | --- |
| Positive Control 1 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Clear close-only upward continuation is suitable as a review fixture, but it is not a test and still needs user review before test planning. |
| Positive Control 2 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Clear close-only accelerating continuation is suitable as a review fixture, but it is not a test and still needs user review before test planning. |
| Positive Control 3 | `NEEDS_HISTORICAL_CONFIRMATION` | Steady continuation is plausible, but the document already marks it as needing historical confirmation before it can support test planning. |
| False-Positive Review 1 | `NEEDS_HISTORICAL_CONFIRMATION` | Small incremental closes are a useful concern, but historical or paper evidence is needed to show this pattern is actually weak. |
| False-Positive Review 2 | `NEEDS_USER_REVIEW` | One large final candle after weak prior closes is a useful review concern, but the provisional HOLD expectation needs user acceptance or revision. |
| False-Positive Review 3 | `NEEDS_HISTORICAL_CONFIRMATION` | Choppy movement followed by a short upward run is plausible as a false positive, but follow-through evidence is needed. |
| Neutral Example 1 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Flat closes are a clean close-only neutral review fixture, but not an approved test. |
| Neutral Example 2 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Choppy alternating closes are a useful close-only neutral review fixture, but not an approved test. |
| Neutral Example 3 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Downward continuation is a clean close-only HOLD review fixture, but not an approved test. |
| Insufficient Close Count Edge Case | `ACCEPTED_FOR_REVIEW_FIXTURE` | Insufficient data is a required deterministic edge-case review fixture, but not an approved test. |

### Review Boundary

The fixture classifications do not approve tests, implementation, strategy behavior changes, trading behavior changes, threshold changes, final strategy ID decisions, or expanded input data.

The next required gate remains user/Codex fixture acceptance review before any separate test-planning gate.

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
