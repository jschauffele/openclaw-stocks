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
- Expected stronger-confirmation behavior: N/A, rejected as fixture for current review set
- Review status: rejected as fixture for current review set
- Decision: `REJECT_AS_FIXTURE_FOR_CURRENT_REVIEW_SET`
- Decision rationale: one large final close after two weak prior upward closes is too ambiguous for the current stronger-confirmation review set.
- Decision rationale: weak prior closes show insufficient sustained buyer control.
- Decision rationale: the large final close could represent breakout, exhaustion, stop-hunt behavior, news/liquidity effects, short-covering, or other non-repeatable movement.
- Decision rationale: the current review set should focus on cleaner patterns where momentum builds consistently across the full close sequence.
- Governance note: this fixture is rejected for this review set, not converted into BUY or HOLD.
- Governance note: the rejected fixture remains documented for governance history and possible future empirical review.

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
- `REJECTED_FOR_CURRENT_REVIEW_SET`

### Fixture Classification Table

| Example | Fixture review classification | Rationale |
| --- | --- | --- |
| Positive Control 1 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Clear close-only upward continuation is suitable as a review fixture, but it is not a test and still needs user review before test planning. |
| Positive Control 2 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Clear close-only accelerating continuation is suitable as a review fixture, but it is not a test and still needs user review before test planning. |
| Positive Control 3 | `NEEDS_HISTORICAL_CONFIRMATION` | Steady continuation is plausible, but the document already marks it as needing historical confirmation before it can support test planning. |
| False-Positive Review 1 | `NEEDS_HISTORICAL_CONFIRMATION` | Small incremental closes are a useful concern, but historical or paper evidence is needed to show this pattern is actually weak. |
| False-Positive Review 2 | `REJECTED_FOR_CURRENT_REVIEW_SET` | User decision rejects this fixture for the current stronger-confirmation review set because one large final close after weak prior upward closes is too ambiguous. The rejected fixture remains documented for governance history and possible future empirical review. |
| False-Positive Review 3 | `NEEDS_HISTORICAL_CONFIRMATION` | Choppy movement followed by a short upward run is plausible as a false positive, but follow-through evidence is needed. |
| Neutral Example 1 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Flat closes are a clean close-only neutral review fixture, but not an approved test. |
| Neutral Example 2 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Choppy alternating closes are a useful close-only neutral review fixture, but not an approved test. |
| Neutral Example 3 | `ACCEPTED_FOR_REVIEW_FIXTURE` | Downward continuation is a clean close-only HOLD review fixture, but not an approved test. |
| Insufficient Close Count Edge Case | `ACCEPTED_FOR_REVIEW_FIXTURE` | Insufficient data is a required deterministic edge-case review fixture, but not an approved test. |

### Review Boundary

The fixture classifications do not approve tests, implementation, strategy behavior changes, trading behavior changes, threshold changes, final strategy ID decisions, or expanded input data.

The next required gate remains user/Codex fixture acceptance review before any separate test-planning gate.

## Threshold And Strategy ID Resolution Review

Fixture evidence is sufficient for threshold decision review.

Test planning remains blocked. Implementation remains blocked. Accepted fixtures remain candidates only, not tests.

Historical or paper confirmation is still required for:

- Positive Control 3
- False-Positive Review 1
- False-Positive Review 3

This resolution review records provisional review recommendations only. It does not approve tests, implementation, strategy behavior changes, trading behavior changes, final threshold changes, final strategy ID decisions, or expanded input data.

### 1. Percent Threshold

Resolution surface:

- Current threshold remains unchanged unless later evidence justifies change.
- This gate does not change the threshold.

Recorded status:

- `PROVISIONAL_RECOMMENDATION_KEEP_THRESHOLD_UNCHANGED`

Evidence that could justify changing the threshold later remains limited to user-accepted examples, historical or paper-trading confirmation, deterministic fixtures, and explicit strategy ID compatibility analysis.

### 2. Stronger Confirmation Rule

Resolution surface:

- Candidate rule must remain close-only.
- Candidate rule should distinguish strong multi-close continuation from weak, choppy, or late-spike sequences.
- Exact rule is not finalized in this gate.

Recorded status:

- `CANDIDATE_RULE_REQUIRES_USER_APPROVAL`

Future rule review must identify exact close sequence requirements, lookback handling, insufficient-data behavior, and expected outputs before any separate test-planning gate.

### 3. Strategy ID

Resolution surface:

- Default recommendation is a new strategy ID for material behavior change.
- Existing strategy ID may remain only if future review proves the change is backward-compatible and does not alter historical metadata meaning.

Recorded status:

- `PROVISIONAL_RECOMMENDATION_NEW_STRATEGY_ID_IF_IMPLEMENTED`

This is not a final strategy ID decision.

### 4. Fixture Decisions

Resolution surface:

- User must accept, revise, or reject each provisional example before test planning.
- Examples needing historical or paper confirmation remain blocked until confirmation exists.

Current fixture decision status:

- accepted review fixtures remain candidates only
- historical-confirmation examples remain blocked for test planning
- rejected examples remain outside the current review set
- no fixture is promoted to a test in this gate

### 5. Next Gate

The next required gate is user/Codex explicit fixture decision review.

Only after that review can a separate test-planning gate be considered.

## Explicit Fixture Decision Review

This review records explicit fixture decision status for stronger trend confirmation examples.

This review does not approve tests. This review does not approve implementation. This review does not approve strategy behavior changes, trading behavior changes, threshold changes, final strategy ID decisions, or expanded input data. Accepted items remain candidates only, not tests.

Threshold remains provisional and unchanged. Strategy ID recommendation remains provisional. Final candidate rule remains unapproved. Test planning remains blocked until enough fixtures are explicitly accepted and required confirmations are satisfied.

Allowed decision statuses:

- `ACCEPT_FOR_TEST_PLANNING_CANDIDATE`
- `REVISE_BEFORE_TEST_PLANNING`
- `REJECT`
- `BLOCKED_PENDING_HISTORICAL_CONFIRMATION`
- `BLOCKED_PENDING_USER_REVIEW`

### Explicit Fixture Decision Table

| Example | Decision status | Reason |
| --- | --- | --- |
| Positive Control 1 | `ACCEPT_FOR_TEST_PLANNING_CANDIDATE` | Clear close-only upward continuation is suitable as a future test-planning candidate, but it is not a test. |
| Positive Control 2 | `ACCEPT_FOR_TEST_PLANNING_CANDIDATE` | Clear close-only accelerating continuation is suitable as a future test-planning candidate, but it is not a test. |
| Positive Control 3 | `BLOCKED_PENDING_HISTORICAL_CONFIRMATION` | Historical or paper confirmation remains required before this steady-continuation example can support test planning. |
| False-Positive Review 1 | `BLOCKED_PENDING_HISTORICAL_CONFIRMATION` | Historical or paper evidence remains required before small incremental closes can be treated as a confirmed weak-trend example. |
| False-Positive Review 2 | `REJECT` | User decision rejects this fixture for the current stronger-confirmation review set. It is not converted into BUY or HOLD and remains documented for governance history and possible future empirical review. |
| False-Positive Review 3 | `BLOCKED_PENDING_HISTORICAL_CONFIRMATION` | Historical or paper confirmation remains required before the choppy-then-upward-run example can support test planning. |
| Neutral Example 1 | `ACCEPT_FOR_TEST_PLANNING_CANDIDATE` | Flat closes are suitable as a future neutral candidate, but this does not approve a test. |
| Neutral Example 2 | `ACCEPT_FOR_TEST_PLANNING_CANDIDATE` | Choppy alternating closes are suitable as a future neutral candidate, but this does not approve a test. |
| Neutral Example 3 | `ACCEPT_FOR_TEST_PLANNING_CANDIDATE` | Downward continuation is suitable as a future HOLD candidate, but this does not approve a test. |
| Insufficient Close Count Edge Case | `ACCEPT_FOR_TEST_PLANNING_CANDIDATE` | Insufficient close count is suitable as a future edge-case candidate, but this does not approve a test. |

### Historical And Paper Confirmation Requirements

Historical or paper confirmation remains required for:

- Positive Control 3
- False-Positive Review 1
- False-Positive Review 3

### Remaining Blocks

Before any separate test-planning gate can be considered:

- blocked fixtures must receive historical or paper confirmation
- threshold recommendation must remain explicit and provisional or be resolved in a later gate
- strategy ID recommendation must remain explicit and provisional or be resolved in a later gate
- final close-only candidate rule must be approved for test planning in a separate gate
- accepted fixture candidates must still be translated into tests only by a future test-planning gate

## Historical And Paper Confirmation Planning

This section plans confirmation requirements for blocked stronger trend confirmation fixtures.

This is docs-only planning. It does not approve test planning, implementation, strategy behavior changes, threshold changes, final strategy ID decisions, final confirmation-rule decisions, or expanded input data. VPS validation is not needed.

### Accepted Fixture Candidates Already Identified

The following 6 fixtures are accepted only as future test-planning candidates, not tests:

- Positive Control 1
- Positive Control 2
- Neutral Example 1
- Neutral Example 2
- Neutral Example 3
- Insufficient Close Count Edge Case

### Blocked Fixtures

The following fixtures remain blocked:

- Positive Control 3
- False-Positive Review 1
- False-Positive Review 3

The following fixture is rejected for the current review set:

- False-Positive Review 2

### Positive Control 3 Confirmation Requirement

Fixture:

- Close sequence: `200.00, 203.00, 206.00, 209.00`
- Provisional stronger-confirmation behavior: BUY

Historical or paper evidence required:

- example records where a steady multi-close continuation remained constructive after the signal
- evidence that stronger confirmation should preserve this pattern as a positive control
- confirmation that the move is not just an overfit synthetic sequence
- close-only data is sufficient unless a future gate separately approves broader inputs

Planning status:

- blocked pending historical or paper confirmation

### False-Positive Review 1 Confirmation Requirement

Fixture:

- Close sequence: `100.00, 100.05, 100.10, 100.15`
- Provisional stronger-confirmation behavior: HOLD

Historical or paper evidence required:

- examples where very small incremental upward closes produced weak or unreliable follow-through
- evidence that the current 3-close BUY can fire on close-only movement that is too shallow to treat as durable momentum
- comparison against positive controls showing the difference between shallow and stronger continuation
- confirmation that no threshold change is required to evaluate this concern unless a later gate explicitly approves threshold review

Planning status:

- blocked pending historical or paper confirmation

### False-Positive Review 3 Confirmation Requirement

Fixture:

- Close sequence: `100.00, 99.80, 100.05, 100.20, 100.35`
- Provisional stronger-confirmation behavior: HOLD

Historical or paper evidence required:

- examples where choppy movement followed by a short upward run produced unreliable follow-through
- evidence that stronger confirmation should distinguish choppy recovery from durable continuation
- confirmation that close-only review is sufficient for this fixture
- comparison against accepted neutral choppy fixture and positive-control continuation fixtures

Planning status:

- blocked pending historical or paper confirmation

### False-Positive Review 2 Rejection Decision

Fixture:

- Close sequence: `100.00, 100.05, 100.10, 103.00`
- Prior provisional stronger-confirmation behavior: HOLD

Decision:

- `REJECT_AS_FIXTURE_FOR_CURRENT_REVIEW_SET`

Rationale:

- one large final close after two weak prior upward closes is too ambiguous for the current stronger-confirmation review set
- weak prior closes show insufficient sustained buyer control
- the large final close could represent breakout, exhaustion, stop-hunt behavior, news/liquidity effects, short-covering, or other non-repeatable movement
- the current review set should focus on cleaner patterns where momentum builds consistently across the full close sequence

Planning status:

- rejected for this review set
- not converted into BUY or HOLD
- remains documented for governance history and possible future empirical review

### Planning Boundary

Threshold remains provisional and unchanged. Strategy ID recommendation remains provisional. Final stronger confirmation rule remains unapproved. Test planning remains blocked. Implementation remains blocked. VPS validation is not needed.

Recommended next gate:

- historical/paper evidence collection for Positive Control 3, False-Positive Review 1, and False-Positive Review 3

## Historical And Paper Evidence Collection Plan

This section defines the docs-only evidence collection plan for remaining unresolved stronger trend confirmation fixtures.

This plan does not approve test planning, implementation, strategy behavior changes, threshold changes, final strategy ID decisions, final stronger confirmation rule decisions, or expanded input data.

False-Positive Review 2 remains rejected for the current review set. Threshold remains provisional and unchanged. Strategy ID recommendation remains provisional. Final stronger confirmation rule remains unapproved. Test planning remains blocked. Implementation remains blocked. VPS validation is not needed.

### Positive Control 3 Evidence Collection Plan

Exact close pattern being evaluated:

- `200.00, 203.00, 206.00, 209.00`
- steady multi-close continuation
- current 3-close expected behavior: BUY
- provisional stronger-confirmation behavior: BUY

Historical or paper evidence that would support the fixture:

- comparable close-only sequences where each close advances meaningfully from the prior close
- evidence that follow-through remained constructive after the signal window
- examples showing that stronger confirmation should preserve steady continuation as a positive control
- records showing the pattern is not merely a synthetic or overfit sequence

Evidence that would reject or weaken the fixture:

- repeated examples where similar steady continuation quickly failed after the signal
- evidence that this pattern commonly appears at exhaustion points rather than durable continuation
- evidence that the sequence requires unavailable context beyond closes to interpret reliably
- inability to find any comparable historical or paper examples

Evidence out of scope:

- broker fills, order outcomes, risk sizing, execution quality, position state, JSONL events, observations, report formatting, or VPS logs
- volume, open/high/low, candle-body, news, liquidity, options, or intraday context unless a future gate approves broader inputs
- changing the threshold or strategy ID based on this fixture alone

Close-only evidence sufficiency:

- Close-only evidence is sufficient for this gate if comparable close sequences and follow-through records can be reviewed without adding new input fields.

Why this fixture remains blocked:

- It remains blocked until historical or paper evidence confirms that this steady continuation pattern is a valid positive-control candidate for future test planning.

### False-Positive Review 1 Evidence Collection Plan

Exact close pattern being evaluated:

- `100.00, 100.05, 100.10, 100.15`
- very small incremental upward closes
- current 3-close expected behavior: BUY
- provisional stronger-confirmation behavior: HOLD

Historical or paper evidence that would support the fixture:

- comparable close-only sequences where tiny incremental upward closes produced weak or unreliable follow-through
- examples showing the baseline can classify shallow close drift as BUY even when trend quality is poor
- evidence that shallow progression differs materially from accepted positive-control continuation patterns
- records showing that the concern can be evaluated without changing the percent threshold in this gate

Evidence that would reject or weaken the fixture:

- repeated examples where similar shallow incremental closes produced reliable continuation
- evidence that the current threshold already filters out this pattern in actual strategy evaluation
- evidence that the fixture is unrealistic for the instrument universe being reviewed
- inability to separate this concern from a threshold-change question

Evidence out of scope:

- threshold changes, symbol-specific tuning, risk sizing, broker behavior, execution results, state, JSONL, observations, reporting, VPS logs, or order outcomes
- volume, open/high/low, candle body, spread, liquidity, or news context unless a future gate approves broader inputs
- treating this fixture as proof of a behavior change without accepted historical or paper evidence

Close-only evidence sufficiency:

- Close-only evidence is sufficient for this gate if historical or paper records can show shallow close-only progression and its follow-through without additional input data.

Why this fixture remains blocked:

- It remains blocked until historical or paper evidence confirms that tiny incremental upward closes are a valid weak-trend false-positive candidate.

### False-Positive Review 3 Evidence Collection Plan

Exact close pattern being evaluated:

- `100.00, 99.80, 100.05, 100.20, 100.35`
- choppy movement followed by a short upward run
- current 3-close expected behavior: BUY
- provisional stronger-confirmation behavior: HOLD

Historical or paper evidence that would support the fixture:

- comparable close-only sequences where a choppy recovery followed by a short upward run produced unreliable follow-through
- examples showing that stronger confirmation should distinguish choppy recovery from durable continuation
- comparison records against accepted neutral choppy examples and positive-control continuation examples
- evidence that the pattern can be evaluated using closes only

Evidence that would reject or weaken the fixture:

- repeated examples where similar choppy recovery sequences produced reliable continuation
- evidence that the earlier choppy movement is irrelevant to the current 3-close baseline behavior
- evidence that interpreting the pattern requires regime, volume, candle, liquidity, or news context outside this gate
- inability to find comparable historical or paper examples

Evidence out of scope:

- regime changes, volume confirmation, candle-quality rules, symbol-specific thresholds, risk sizing, execution, broker behavior, JSONL, observations, reporting, state, order outcomes, or VPS validation
- changing the stronger confirmation rule before a separate test-planning gate
- converting this fixture into a test without accepted evidence

Close-only evidence sufficiency:

- Close-only evidence is sufficient for this gate if comparable close sequences can show whether choppy recovery differs from durable continuation using closes alone.

Why this fixture remains blocked:

- It remains blocked until historical or paper evidence confirms that choppy movement followed by a short upward run is a valid false-positive candidate.

### Evidence Collection Plan Boundary

The collection plan is docs-only and evidence-only. It does not approve tests, implementation, threshold changes, strategy ID finalization, stronger confirmation rule finalization, runtime validation, broker work, risk changes, execution changes, JSONL changes, observation changes, reporting changes, state changes, order behavior changes, or VPS use.

Recommended next gate:

- collect or provide historical/paper evidence for Positive Control 3, False-Positive Review 1, and False-Positive Review 3, then run a read-only evidence sufficiency checkpoint

## Read-Only Evidence Source Inventory Result

Read-only local evidence source inventory found no existing local historical or paper close-sequence evidence artifacts for:

- Positive Control 3
- False-Positive Review 1
- False-Positive Review 3

Local artifact directory status:

- `logs/` was not present locally.
- `reports/` was not present locally.
- `saved_run_artifacts/` was not present locally.

Existing relevant docs are planning and governance only, not empirical evidence.

`docs/ibkr_read_only_runtime_visibility_smoke_evidence.md` exists but is IBKR visibility evidence, not close-sequence strategy evidence.

Evidence is not sufficient for a future evidence sufficiency checkpoint.

Missing evidence remains:

- comparable close-only historical or paper sequences
- follow-through evidence after signal window
- positive-control evidence for steady continuation
- false-positive evidence for weak shallow upward drift
- false-positive evidence for choppy recovery followed by short upward run

False-Positive Review 2 remains rejected for the current review set. Threshold remains provisional and unchanged. Strategy ID recommendation remains provisional. Final stronger confirmation rule remains unapproved. Test planning remains blocked. Implementation remains blocked. VPS validation is not needed.

Recommended next gate:

- provide or locate historical/paper close-sequence evidence for Positive Control 3, False-Positive Review 1, and False-Positive Review 3, then run a read-only evidence sufficiency checkpoint

## Evidence Intake Template

This section provides a docs-only template for future user-provided or externally located evidence. It does not accept evidence, approve tests, approve implementation, approve strategy behavior changes, finalize threshold behavior, finalize strategy ID, or finalize the stronger confirmation rule.

No evidence has been accepted yet for Positive Control 3, False-Positive Review 1, or False-Positive Review 3.

False-Positive Review 2 remains rejected for the current review set. Threshold remains provisional and unchanged. Strategy ID recommendation remains provisional. Final stronger confirmation rule remains unapproved. Test planning remains blocked. Implementation remains blocked. VPS validation is not needed.

Evidence entries must remain close-only for this gate. If source material contains non-close data, that data must be identified as present but out of scope unless a later governance gate approves a broader input surface.

### Positive Control 3 Evidence Entry Template

- Fixture name: Positive Control 3
- Symbol: TBD
- Date/time range: TBD
- Timeframe: TBD
- Close sequence: TBD
- Signal-window closes: TBD
- Follow-through closes after signal window: TBD
- Source of evidence: TBD
- Evidence type: TBD historical or paper
- Fixture effect: TBD supports, weakens, or rejects the fixture
- Notes on ambiguity: TBD
- Uses close-only data: TBD
- Non-close data present but out of scope: TBD
- Reviewer decision: TBD
- Review status: pending evidence intake

### False-Positive Review 1 Evidence Entry Template

- Fixture name: False-Positive Review 1
- Symbol: TBD
- Date/time range: TBD
- Timeframe: TBD
- Close sequence: TBD
- Signal-window closes: TBD
- Follow-through closes after signal window: TBD
- Source of evidence: TBD
- Evidence type: TBD historical or paper
- Fixture effect: TBD supports, weakens, or rejects the fixture
- Notes on ambiguity: TBD
- Uses close-only data: TBD
- Non-close data present but out of scope: TBD
- Reviewer decision: TBD
- Review status: pending evidence intake

### False-Positive Review 3 Evidence Entry Template

- Fixture name: False-Positive Review 3
- Symbol: TBD
- Date/time range: TBD
- Timeframe: TBD
- Close sequence: TBD
- Signal-window closes: TBD
- Follow-through closes after signal window: TBD
- Source of evidence: TBD
- Evidence type: TBD historical or paper
- Fixture effect: TBD supports, weakens, or rejects the fixture
- Notes on ambiguity: TBD
- Uses close-only data: TBD
- Non-close data present but out of scope: TBD
- Reviewer decision: TBD
- Review status: pending evidence intake

### Evidence Intake Boundary

This template does not collect or create new market data. It only defines required fields for future evidence supplied by the user or located externally under a separate allowed evidence-review gate.

Future evidence must be reviewed before it can support an evidence sufficiency checkpoint. Accepted fixture candidates remain candidates only, not tests.

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
