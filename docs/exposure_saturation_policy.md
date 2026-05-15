# Exposure Saturation Policy Definition

## Purpose

This document defines the current exposure saturation policy for the validated
runtime behavior. It is policy documentation only. It does not approve any
runtime, strategy, reconciliation, execution, sell, rebalance, or sizing change.

## Current Deterministic Behavior

The currently validated behavior is deterministic:

- The strategy can repeatedly produce MSFT BUY proposals.
- Reconciliation blocks a proposal when projected exposure would exceed the
  configured `max_position_size`.
- The block is deterministic and repeatable for the same projected exposure
  inputs.
- No runtime drift has been observed.
- No architecture instability has been observed.
- No automatic sell or rebalance behavior occurs.
- `execution_use_case` remains detached.
- Runtime visibility remains observed-only.

This means saturation is currently handled as a reconciliation-time rejection,
not as a strategy-time suppression or execution-time correction.

## Projected Exposure

Projected exposure is the position exposure that would exist if a proposed order
were accepted and applied to the current known position state.

For a BUY proposal, projected exposure is the existing exposure plus the
additional exposure introduced by the proposed order. A proposal is considered
over the cap when that projected exposure is greater than `max_position_size`.

Projected exposure is a pre-execution control value. It is evaluated before an
order is approved for execution and does not require an executed trade to exist.

## Current Hard-Cap Enforcement

The current policy is a hard-cap enforcement model:

- `max_position_size` is treated as a strict upper bound.
- A BUY proposal that would move projected exposure above the cap is blocked.
- The block occurs during reconciliation.
- The system does not resize the proposal to fit the remaining available
  exposure.
- The system does not sell, trim, or rebalance existing exposure to make room.
- The system does not reinterpret the blocked proposal as a partial fill,
  rebalance request, or execution instruction.

This behavior preserves the cap as an invariant. The strategy may continue to
express demand, but reconciliation prevents that demand from becoming an
approved execution candidate when it would exceed the configured limit.

## Approval Boundaries

Exposure saturation requires three approval concepts to remain distinct.

### Strategy Approval

Strategy approval means the strategy has produced a proposal that satisfies its
own signal and selection rules. It does not mean the proposal is portfolio-safe,
reconciliation-approved, or executable.

Under current behavior, repeated MSFT BUY proposals can still be strategy-
approved while the position is saturated.

### Reconciliation Approval

Reconciliation approval means the proposal has passed portfolio and state
controls, including projected exposure validation against `max_position_size`.

Under current behavior, reconciliation blocks proposals whose projected exposure
would exceed the cap. This rejection is the active exposure saturation control.

### Execution Approval

Execution approval would mean an order has passed the required execution
boundary and is allowed to proceed toward brokerage-side action.

Under current behavior, execution approval is not reached for proposals blocked
by reconciliation. `execution_use_case` remains detached, so blocked proposals
must not be interpreted as execution instructions.

## Absence of Automatic Sell or Rebalance Behavior

The current system does not automatically sell, trim, rebalance, or otherwise
reduce an existing position when a new BUY proposal is blocked by exposure
saturation.

This absence is intentional in the current policy state. A blocked BUY proposal
does not imply that the system should create an offsetting SELL proposal, reduce
the current position, rotate capital, or alter the portfolio to satisfy the
strategy signal.

Any sell-capable or rebalance-capable behavior would be a separate policy and
implementation decision.

## Saturation-State Implications

When a symbol is saturated, the system can repeatedly produce strategy-approved
BUY proposals that are deterministically blocked by reconciliation. This is an
allowed state under the current policy.

The implications are:

- Repeated blocked proposals are not runtime drift by themselves.
- Repeated blocked proposals are not evidence of architecture instability.
- Strategy demand and portfolio approval can intentionally diverge.
- The cap remains authoritative even if the strategy continues to signal BUY.
- The runtime remains observed-only unless a separate execution path is approved.
- Saturation can persist indefinitely without automatic correction.

Saturation is therefore a stable policy state, not an error state, as long as the
block remains deterministic and no unintended execution, sell, rebalance, or
state mutation occurs.

## Possible Future Policy Models

The current behavior does not decide the long-term product policy. Several
future models remain possible.

### Permanent Hard Cap

The system could keep the current model permanently. Strategy proposals may
continue to be generated, and reconciliation remains the sole authority that
blocks any projected exposure above `max_position_size`.

This model is simple, conservative, and easy to reason about. Its main drawback
is that saturated symbols can continue producing proposals that are known in
advance to be blocked.

### Exposure-Aware Strategy Suppression

The strategy layer could become exposure-aware and suppress BUY proposals before
they reach reconciliation when a symbol is already saturated or when no available
exposure remains.

This could reduce repeated blocked proposals and improve signal cleanliness, but
it would move portfolio-state awareness into strategy behavior. That would need
careful boundary design so strategy approval does not become confused with
reconciliation approval.

### Rebalance/Sell-Capable Model

The system could introduce explicit rebalance or sell behavior that reduces
existing exposure, rotates capital, or creates room for a new BUY proposal.

This would materially change the policy surface. It would require independent
rules for sell authorization, position trimming, tax and risk considerations,
order sequencing, failure handling, and execution approval. It must not be
treated as a minor extension of the current block behavior.

### Dynamic Sizing Model

The system could resize proposed orders based on remaining available exposure.
Instead of blocking a BUY proposal that exceeds the cap, reconciliation or a
dedicated sizing layer could reduce the order to the largest permitted size.

This would reduce hard rejections, but it would change proposal semantics. A
strategy-approved size would no longer be the size considered for execution.
That requires explicit policy for minimum order size, rounding, partial sizing,
and whether resized orders still represent the strategy's intent.

## Risks of Relaxing Current Enforcement

Relaxing current hard-cap enforcement introduces material risk:

- Overexposure risk if projected exposure checks become advisory rather than
  authoritative.
- Boundary confusion between strategy approval, reconciliation approval, and
  execution approval.
- Accidental execution if blocked proposals are allowed to cross into execution
  paths.
- Hidden rebalance behavior if the system starts correcting saturation without
  explicit sell policy.
- Runtime drift if saturation handling becomes stateful or non-deterministic.
- Audit ambiguity if proposal size, approved size, and executed size diverge
  without clear policy.
- Operational risk if execution-side failures occur after partial resizing,
  sell-before-buy sequencing, or rebalance actions.

These risks are why the current hard cap should remain authoritative unless a
future policy explicitly replaces it.

## No Implementation Change Approved Yet

No implementation change is approved by this document.

The validated system is stable under the current deterministic block behavior.
There is no evidence that repeated saturated BUY proposals require immediate
runtime correction. The current behavior preserves a clear separation between
strategy demand, reconciliation approval, and execution approval.

Because the possible future models carry different architectural and operational
consequences, choosing one requires a separate policy decision. Documentation of
the saturation state is therefore the appropriate current action.

## Reopening Policy Implementation

Policy implementation should be reopened only if future pressure demonstrates
that the current deterministic hard-cap model is insufficient.

Examples of sufficient pressure include:

- Repeated blocked proposals materially reduce operator clarity or alert quality.
- Saturation causes meaningful reporting, ranking, or decision-making noise.
- Product requirements call for exposure-aware proposal suppression.
- Portfolio policy explicitly requires sell, trim, rebalance, or capital
  rotation behavior.
- Execution policy is approved and requires pre-execution resizing semantics.
- `max_position_size` needs to support dynamic sizing instead of strict blocking.
- Audit requirements demand a different representation of saturated strategy
  demand.

Until that pressure exists and a specific policy model is approved, the current
hard-cap reconciliation block remains the correct exposure saturation behavior.
