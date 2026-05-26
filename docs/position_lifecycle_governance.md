# Position Lifecycle Governance

## Purpose

This document models future governed position lifecycle behavior for OpenClaw.
It is an architecture review document only. It does not authorize
implementation of SELL behavior, exit logic, rebalance behavior, capital
recycling, portfolio rotation, adaptive exits, allocation arbitration, execution
activation, or runtime changes.

The goal is to define the lifecycle concepts that must be governed before
OpenClaw can safely move beyond entry-focused BUY proposal controls.

## Lifecycle Governance Domains

Position lifecycle governance has four distinct domains.

### Entry Governance

Entry governance determines whether new or additional exposure may be opened.

Current OpenClaw behavior is strongest in this domain. The strategy may produce
BUY proposals, and reconciliation deterministically blocks proposals whose
projected exposure would exceed hard caps.

Entry governance answers:

- Is the strategy signal valid?
- Is the proposed exposure allowed?
- Is the position already saturated?
- Does the proposal pass reconciliation and risk controls?
- Does the proposal have execution permission?

### Hold Governance

Hold governance determines whether an existing position should remain unchanged.

Hold governance is not the same as absence of a BUY proposal or absence of a
SELL proposal. A governed hold decision should be explicit when the system has
enough lifecycle maturity to evaluate existing positions.

Hold governance answers:

- Does the original thesis remain valid?
- Is the position still within risk and exposure limits?
- Has the position aged beyond its intended lifecycle?
- Is the capital still justified relative to alternatives?
- Should the position remain untouched despite new signals?

### Exit Governance

Exit governance determines whether exposure should be reduced or closed.

SELL semantics belong primarily to exit governance. An exit decision may be
driven by risk reduction, thesis invalidation, stop conditions, time-based
review, opportunity cost, portfolio rotation, or manual governance.

Exit governance answers:

- Why should exposure be reduced?
- Is the SELL action risk-driven, signal-driven, lifecycle-driven, or
  allocation-driven?
- Is the exit partial or full?
- Is execution allowed?
- What state remains after the exit?

### Rebalance Governance

Rebalance governance determines whether the portfolio should adjust existing
positions toward target exposures.

Rebalance is broader than exit governance. It may include trimming winners,
adding to underweight names, reducing concentration, restoring factor balance,
or rotating capital across opportunities.

Rebalance governance answers:

- What target state is the portfolio moving toward?
- Which positions are overweight or underweight?
- Which trades are required to reach the target?
- Are sells required before buys?
- How are partial fills, transaction costs, and sequencing handled?

## Current OpenClaw Lifecycle Maturity

OpenClaw is currently entry-governance mature but lifecycle-governance immature.

Current validated maturity includes:

- Deterministic signal generation.
- Deterministic reconciliation and risk gating.
- Deterministic hard-cap exposure enforcement.
- Deterministic execution gating boundary.
- Observed-only runtime visibility.
- Clear separation between strategy approval, reconciliation approval, and
  execution approval.

Current non-maturity includes:

- No sell lifecycle.
- No rebalance lifecycle.
- No hold lifecycle.
- No capital recycling policy.
- No portfolio rotation policy.
- No position-aging policy.
- No adaptive exit policy.
- No autonomous lifecycle optimization.

The current system can block additional exposure. It does not yet govern the
full life of a position after entry.

## Current Lifecycle Gaps

The main lifecycle gaps are:

- No formal definition of when a position should be held.
- No formal definition of when a position should be reduced.
- No approved SELL semantics.
- No approved trim semantics.
- No approved exit ranking.
- No approved rebalance trigger.
- No approved capital recycling model.
- No approved rotation model.
- No approved lifecycle observability model.
- No approved deterministic exit governance.

These gaps are expected in the current governance phase. They are reasons to
defer implementation, not reasons to infer behavior from existing BUY proposal
logic.

## Importance of SELL Semantics

SELL semantics are institutionally important because a sell action can mean many
different things.

A SELL may represent:

- Risk reduction.
- Thesis invalidation.
- Stop-loss behavior.
- Profit taking.
- Time-based exit.
- Rebalance trimming.
- Capital recycling.
- Portfolio rotation.
- Factor or sector exposure reduction.
- Manual liquidation.
- Tax or liquidity management.

These meanings have different governance consequences. A system that emits or
executes SELL actions without explicit semantics can create ambiguity about
intent, authority, risk, and auditability.

Before SELL behavior is implemented, OpenClaw must define why a SELL exists,
which component may propose it, which component may approve it, and which
conditions allow execution.

## Position-Aging Concepts

Position aging measures how long exposure has existed and how its lifecycle
state changes over time.

Future position-aging concepts may include:

- Entry timestamp.
- Signal timestamp.
- Last confirmation timestamp.
- Holding-period target.
- Maximum holding period.
- Minimum holding period.
- Time since last add.
- Time since last review.
- Thesis freshness.
- Staleness threshold.

Position aging could support hold review, exit review, rebalance timing, or
opportunity-cost evaluation. It must not trigger live exits unless a future
policy explicitly approves deterministic exit rules.

## Opportunity-Cost Concepts

Opportunity cost is the cost of keeping capital in an existing position instead
of reallocating it to another opportunity.

Future opportunity-cost governance may evaluate:

- Current position conviction.
- New opportunity conviction.
- Expected improvement from rotation.
- Transaction costs.
- Tax considerations.
- Liquidity constraints.
- Risk budget consumption.
- Factor or sector concentration.
- Capital scarcity.

Opportunity cost can justify future lifecycle review, but it does not currently
authorize automatic sells, trims, or reallocations.

## Saturation-Release Concepts

Saturation release describes how a full position becomes eligible for additional
BUY exposure again.

Potential saturation-release mechanisms include:

- Market value declines below the cap.
- Manual trim.
- Governed SELL action.
- Rebalance reduction.
- Dynamic cap increase.
- Portfolio-level budget expansion.
- Change in position classification.
- Cash or exposure-budget update.

Current OpenClaw does not automatically release saturation through selling or
rebalancing. A saturated position may remain saturated while the strategy
continues to emit BUY proposals that reconciliation blocks.

Any active saturation-release mechanism requires separate policy approval.

## Rebalance Governance Concepts

Rebalance governance defines how the portfolio moves from current exposure to a
target exposure state.

Future rebalance governance should define:

- Rebalance trigger.
- Target exposure model.
- Position-level and portfolio-level constraints.
- Whether rebalancing is periodic, threshold-based, signal-driven, or manually
  approved.
- Whether sells must complete before buys.
- How transaction costs affect the rebalance.
- How partial fills are handled.
- How failed orders affect the target state.
- Whether rebalancing can cross strategy, sector, factor, or regime budgets.

Rebalance must be treated as its own lifecycle system, not as a hidden side
effect of blocked BUY proposals.

## Capital Recycling Concepts

Capital recycling is the process of freeing capital from existing positions and
redeploying it into new or higher-ranked opportunities.

Future capital recycling governance may define:

- Which positions are eligible sources of capital.
- Which opportunities are eligible destinations.
- Whether recycling is risk-driven or return-driven.
- Whether cash is preferred over selling.
- Whether recycling can reduce a profitable position.
- Whether recycling can realize losses.
- How recycling interacts with tax, liquidity, and transaction costs.

Capital recycling requires both sell authority and allocation authority. Neither
exists in the current OpenClaw runtime.

## Portfolio Rotation Concepts

Portfolio rotation is a broader allocation process that changes portfolio
composition over time.

Rotation may occur across:

- Symbols.
- Sectors.
- Strategies.
- Factors.
- Regimes.
- Risk budgets.
- Time horizons.

A governed rotation model should distinguish between reducing exposure because
an existing position is weak and reducing exposure because another opportunity
is stronger. These are different lifecycle rationales and should be auditable.

Current OpenClaw does not rotate the portfolio.

## Lifecycle Observability Requirements

Future lifecycle governance requires observability beyond entry proposals.

Lifecycle observability should capture:

- Entry date and entry rationale.
- Current lifecycle state.
- Hold rationale.
- Exit rationale.
- Rebalance rationale.
- Saturation state.
- Aging metrics.
- Opportunity-cost comparisons.
- Capital recycling candidates.
- Rotation candidates.
- Proposed SELL, trim, or rebalance actions.
- Approval, rejection, or deferral reasons.
- Execution permission status.
- Post-action state.

Without lifecycle observability, exit and rebalance behavior would be difficult
to audit and unsafe to automate.

## Deterministic Exit Governance Principles

Any future exit governance must remain deterministic and auditable.

Principles include:

- Exit signals must have explicit semantics.
- SELL proposals must be distinct from execution permission.
- Exit approval must be separate from strategy signal generation.
- Rebalance trims must be distinguishable from risk exits.
- Position state snapshots must be versioned.
- Exit decisions must be reproducible from recorded inputs.
- Partial exits and full exits must have separate rules.
- Manual overrides must be recorded.
- Execution failure must not silently change lifecycle intent.
- Portfolio construction must not bypass risk governance.

Exit governance should be at least as explicit as entry governance before
production implementation.

## Risks of Premature Adaptive Exits

Premature adaptive exits create material governance risk.

Risks include:

- SELL behavior emerging without approved semantics.
- Strategy logic silently becoming portfolio lifecycle logic.
- Adaptive exits weakening deterministic auditability.
- Capital recycling occurring without allocation governance.
- Rebalance behavior occurring without target-state policy.
- AI or optimization systems changing live exposure without authority.
- Excess turnover from unstable exit triggers.
- Poor attribution between signal failure, allocation change, and risk control.
- Execution-side consequences from ungoverned sell sequencing.

Adaptive exits may be useful in a mature system, but they require policy,
evaluation, replay, approval, and promotion before production use.

## Future Relationship Between Core Governance Layers

A mature OpenClaw lifecycle architecture would require clear relationships
between portfolio construction, allocation governance, and lifecycle governance.

### Portfolio Construction

Portfolio construction would define desired portfolio intent. It may decide that
a position should be added, held, trimmed, exited, or rebalanced based on the
whole portfolio context.

### Allocation Governance

Allocation governance would determine whether capital should remain assigned to
an existing position or move elsewhere. It would govern opportunity cost,
capital recycling, ranking, budget use, and target exposure.

### Lifecycle Governance

Lifecycle governance would define how a position moves through entry, hold,
trim, exit, and rebalance states. It would ensure that position-state changes
have explicit semantics and deterministic approval.

These layers should cooperate, but they must not collapse into one implicit
decision engine. Each layer needs a distinct authority boundary and audit trail.

## Deferred Implementation Boundaries

This document does not approve implementation.

Deferred areas include:

- SELL proposal generation.
- Exit approval logic.
- Trim logic.
- Hold-state evaluation.
- Position-aging triggers.
- Saturation-release automation.
- Rebalance lifecycle.
- Capital recycling.
- Portfolio rotation.
- Lifecycle observability tooling.
- Adaptive exits.
- AI-assisted lifecycle mutation.
- Execution activation for SELL or rebalance actions.

Future implementation should begin only after a phase explicitly approves
semantics, authority, data requirements, evaluation requirements, audit
requirements, and rollback controls.

Until then, OpenClaw remains governed by deterministic entry controls,
hard-cap exposure enforcement, separated execution permission, and no automatic
sell or rebalance behavior.

## Replay-State Dependency For Lifecycle Governance

Lifecycle governance should not move toward implementation until replay packages
can preserve the portfolio/risk state that produced each lifecycle-relevant
decision.

The minimum portfolio/risk replay state contract is recorded in
`docs/replay_package_specification.md`. Future lifecycle evaluation will need
that contract plus separately approved lifecycle-state fields before hold,
trim, exit, rebalance, capital recycling, opportunity-cost, or saturation-
release behavior can be evaluated deterministically.

This dependency does not approve lifecycle-state capture tooling, SELL
semantics, rebalance semantics, broker/live/API work, VPS validation, execution
activation, or strategy behavior changes.
