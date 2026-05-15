# Full Position Governance Models

## Purpose

This document explores portfolio-governance interpretations of a "full
position" under the current validated hard-cap exposure model. It is a modeling
document only. It does not approve changes to strategy behavior,
reconciliation, execution, sizing, selling, rebalancing, or runtime visibility.

## Current Meaning of a Full Position

Under the current hard-cap model, a full position means the current or projected
position exposure has reached the configured maximum allowed exposure for that
symbol or allocation unit.

The current system treats the configured cap as an authoritative portfolio
constraint. A strategy can still express BUY demand after the position is full,
but reconciliation blocks any proposal whose projected exposure would exceed the
cap.

In this model, "full" does not mean:

- The strategy has lost conviction.
- The position should be sold or trimmed.
- The system should rebalance automatically.
- The execution layer has permission to resize or route an order.
- The symbol is removed from future consideration.

It means the portfolio is already at the allowed exposure limit for additional
BUY activity under the current policy.

## Signal Conviction, Capital Allocation, and Execution Permission

A full position requires three concepts to remain separate.

### Signal Conviction

Signal conviction is the strategy's assessment that a symbol remains desirable.
It may continue even when the position is full. A repeated BUY proposal can
therefore represent continued conviction, not necessarily a defect.

### Capital Allocation

Capital allocation is the portfolio-level decision about how much exposure may
be assigned to a symbol. The cap governs allocation even when strategy conviction
is high.

Under the current model, allocation authority belongs to reconciliation and
portfolio controls, not to the strategy signal alone.

### Execution Permission

Execution permission is the authority to convert an approved order candidate
into brokerage-side action. It is downstream of strategy approval and
reconciliation approval.

Under current behavior, a proposal blocked by reconciliation because the
position is full has no execution permission. It must not be interpreted as an
order, resize instruction, sell instruction, or rebalance instruction.

## Should Saturated Positions Continue Emitting BUY Proposals?

There are two defensible governance interpretations.

One interpretation is that saturated positions should continue emitting BUY
proposals when the strategy signal remains valid. This preserves signal purity:
the strategy reports what it wants, and reconciliation records why the portfolio
will not act on it.

Another interpretation is that saturated positions should suppress BUY proposals
before reconciliation. This reduces operational noise and can make proposal
streams cleaner, but it also means strategy output is now conditioned by
portfolio state.

The current validated behavior follows the first interpretation. Strategy demand
can remain visible even when capital allocation blocks further exposure.

## Exposure-Aware Suppression vs Reconciliation-Time Blocking

### Exposure-Aware Suppression

Exposure-aware suppression prevents or reduces BUY proposals before they reach
reconciliation when the position is already full.

Potential benefits:

- Fewer repeated blocked proposals.
- Cleaner operator-facing proposal streams.
- Less downstream reconciliation traffic.
- Better alignment between emitted proposals and actionable capacity.

Potential costs:

- Strategy behavior becomes coupled to portfolio state.
- Suppressed conviction may become less observable.
- Strategy approval can become harder to distinguish from allocation approval.
- Auditing may need to explain why a valid signal produced no proposal.

### Reconciliation-Time Blocking

Reconciliation-time blocking allows the strategy to emit proposals and relies on
portfolio controls to block proposals that exceed the cap.

Potential benefits:

- Clear separation between signal generation and portfolio approval.
- Deterministic audit trail for every blocked proposal.
- Strategy conviction remains visible even when the portfolio is saturated.
- The cap remains the explicit enforcement point.

Potential costs:

- Repeated blocked proposals can create noise.
- Operator-facing output may include non-actionable recommendations.
- Ranking and reporting layers may need to distinguish conviction from
  capacity.
- Capital efficiency questions are not resolved by the block itself.

## Governance Implications

### Observability

Reconciliation-time blocking improves observability into continuing signal
demand. Operators can see that a symbol remains attractive but is blocked by
allocation limits.

Exposure-aware suppression reduces visible noise but can hide suppressed demand
unless the system adds explicit observability for suppressed signals.

### Ranking

Ranking can mean different things depending on the policy:

- Highest signal conviction.
- Highest actionable proposal.
- Highest capital-adjusted opportunity.
- Highest rebalance candidate.

Under the current model, ranking should not assume that a top BUY proposal is
actionable when the position is already full. A future ranking policy may need
separate fields for signal rank, allocation capacity, and execution eligibility.

### Portfolio Rotation

A full position does not currently trigger rotation. The system does not sell an
existing position to fund another opportunity, and it does not trim a saturated
symbol to make room for a new order.

If portfolio rotation becomes a goal, it should be modeled as a separate
governance function with explicit sell authority, ranking rules, tax/risk
considerations, and execution sequencing.

### Capital Efficiency

Static blocking protects exposure limits but may leave strategy conviction
unacted upon when capital is fully allocated. This can be acceptable for a
conservative governance model, but it may be inefficient if the portfolio should
actively rotate toward stronger signals.

Capital efficiency pressure is therefore a reason to consider future sizing,
rotation, or rebalance policy, not a reason to weaken the current cap without a
replacement model.

### Deterministic Auditing

The current model is strong for deterministic auditing. A proposal, projected
exposure value, configured cap, and reconciliation decision can be reviewed as a
clear sequence.

More adaptive models can remain auditable, but they require additional records:
suppression reasons, resized quantities, dynamic cap inputs, sell decisions,
rebalance rankings, and execution sequencing.

## Future Sell/Rebalance Philosophy Considerations

Any sell-capable or rebalance-capable model requires an explicit philosophy
beyond BUY saturation handling.

Open considerations include:

- Whether selling is allowed only for risk reduction or also for opportunity
  rotation.
- Whether a full position can be trimmed to fund a higher-ranked opportunity.
- Whether rebalancing is periodic, threshold-based, signal-driven, or manually
  approved.
- Whether taxes, holding periods, transaction costs, and liquidity constraints
  affect sell authorization.
- Whether sells must complete before new buys are approved.
- How failed or partial sell execution affects downstream buy eligibility.
- Whether the same strategy that proposes buys can also propose sells.

Without these decisions, a blocked BUY proposal should not imply any automatic
sell or rebalance action.

## Risks of Exposure-Aware Strategy Coupling

Making strategy behavior exposure-aware can create governance and architecture
risks:

- Strategy output may stop representing pure signal conviction.
- Portfolio state may leak into ranking logic in unclear ways.
- A suppressed proposal may be harder to audit than a blocked proposal.
- Strategy approval and reconciliation approval may become indistinguishable.
- Bugs in exposure state can silence valid signals before controls review them.
- Testing must cover both signal correctness and allocation-state interaction.

These risks do not make exposure-aware suppression invalid. They mean it should
be adopted only with explicit policy, observability, and test coverage.

## Risks of Repeated Blocked Proposal Noise

Repeated blocked proposals also carry risks:

- Operators may learn to ignore repeated saturation blocks.
- Alerts or reports may overstate actionable opportunity.
- Ranking views may be cluttered by names that cannot receive more capital.
- Important new candidates may be harder to distinguish from saturated names.
- Proposal counts may look like system churn even when behavior is stable.
- Downstream consumers may misread blocked proposals as failed execution.

These risks may justify future suppression, ranking, or reporting changes, but
they do not by themselves authorize execution, sell, rebalance, or cap-relaxing
behavior.

## Institutional Cap Models

### Static Caps

Static caps assign a fixed maximum exposure per symbol or allocation unit.

Pros:

- Simple to understand and audit.
- Deterministic enforcement.
- Strong protection against concentration drift.
- Clear separation between conviction and allocation.

Cons:

- May underuse strong signals after a position is full.
- Can create repeated non-actionable proposals.
- Does not adapt to volatility, liquidity, confidence, or portfolio context.
- Requires separate policy for rotation and capital efficiency.

### Dynamic Caps

Dynamic caps adjust maximum exposure based on changing inputs such as volatility,
liquidity, risk budget, market regime, or portfolio concentration.

Pros:

- More responsive to current risk conditions.
- Can reduce exposure when risk rises.
- Can allocate more capacity to stronger or lower-risk opportunities.
- Supports more sophisticated institutional portfolio construction.

Cons:

- More complex to audit and test.
- Cap changes can create implicit buy or sell pressure.
- Requires clear governance over cap inputs and update timing.
- May reduce determinism if inputs are unstable or poorly versioned.

### Adaptive Sizing

Adaptive sizing modifies the order size based on available exposure, confidence,
risk, liquidity, or other constraints.

Pros:

- Converts some blocked proposals into smaller actionable proposals.
- Can improve capital deployment.
- Better aligns order size with portfolio capacity.
- Can support minimum/maximum sizing rules.

Cons:

- Strategy-proposed size and approved size may diverge.
- Requires policy for minimum order size, rounding, and partial intent.
- Can obscure whether the strategy or portfolio layer owns sizing.
- Needs explicit audit records for the sizing transformation.

## No Implementation Decision Approved Yet

No implementation decision is approved by this document.

The current hard-cap behavior is validated, deterministic, and stable. It keeps
signal conviction, capital allocation, and execution permission separate. The
governance freeze remains active, and no runtime pressure has been approved that
requires changing strategy suppression, reconciliation behavior, execution
approval, selling, rebalancing, or dynamic sizing.

Future implementation should be considered only after a specific institutional
model is selected and its consequences are accepted. Until then, a full position
continues to mean that BUY demand may exist, but additional exposure is blocked
by reconciliation when projected exposure would exceed the configured cap.
