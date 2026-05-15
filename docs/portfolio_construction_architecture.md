# Portfolio Construction Architecture

## Purpose

This document models a future portfolio-construction architecture for OpenClaw.
It is architecture documentation only. It does not approve implementation of a
portfolio-construction layer, allocation arbitration, factor awareness,
rebalance lifecycle, adaptive sizing, autonomous optimization, execution
behavior, or runtime changes.

The current validated state remains:

- Deterministic signal engine.
- Deterministic reconciliation and risk gating.
- Deterministic execution gating.
- Hard-cap exposure governance.
- `execution_use_case` detached.
- Runtime visibility observed-only.
- No portfolio-construction layer.
- No allocation arbitration.
- No factor-awareness layer.
- No rebalance lifecycle.
- No adaptive sizing.
- No autonomous optimization.

## Portfolio Construction vs Signal Generation

Signal generation answers the question: "What does the strategy want?"

Portfolio construction answers the question: "Given all signals, positions,
constraints, budgets, risks, and portfolio objectives, what should the portfolio
own or change?"

These are different responsibilities. A strategy signal can identify an
attractive symbol, direction, or trade idea without deciding how much capital the
portfolio should allocate. Portfolio construction evaluates that signal in the
context of competing opportunities, current exposure, portfolio concentration,
risk budgets, liquidity, factor balance, and governance constraints.

Under the current architecture, OpenClaw has deterministic signal generation and
deterministic reconciliation gates, but it does not yet have a dedicated
portfolio-construction layer. Current hard-cap enforcement prevents overexposure
but does not optimize the portfolio.

## Strategy Signal, Allocation Decision, and Execution Permission

The architecture must preserve a clear distinction between three concepts.

### Strategy Signal

A strategy signal is the strategy layer's expression of opportunity or
conviction. It may include symbol, direction, confidence, score, or proposed
action. It is not by itself an allocation decision or execution instruction.

The current system allows strategy demand to remain visible even when a position
is saturated.

### Allocation Decision

An allocation decision determines whether capital should be assigned, withheld,
reduced, resized, rotated, or rebalanced across opportunities. It requires
portfolio context that a pure signal engine should not implicitly own.

OpenClaw does not currently have an allocation-arbitration layer. Current
reconciliation can block proposals that violate exposure caps, but blocking is
not the same as portfolio construction.

### Execution Permission

Execution permission is the authority to send or prepare an order for brokerage
execution after all required approvals have passed.

Execution permission must remain downstream of strategy signals, allocation
decisions, reconciliation, and execution gating. A signal or allocation
preference must not be treated as permission to execute.

## Future Portfolio-Construction Layer

A future portfolio-construction layer would sit between strategy signal
generation and execution approval. Its role would be to convert many possible
signals into a coherent portfolio intent, subject to governance limits.

Possible responsibilities include:

- Evaluating competing strategy signals.
- Ranking opportunities across symbols, strategies, and regimes.
- Allocating scarce capital among approved opportunities.
- Identifying saturated, underweight, overweight, or excluded positions.
- Proposing target exposure changes.
- Distinguishing hold, add, trim, exit, and rebalance intent.
- Producing auditable portfolio intent before reconciliation and execution.

This layer would not replace risk governance or execution approval. It would
produce portfolio intent that still requires deterministic validation.

## Future Capital-Allocation Layer

A capital-allocation layer would decide how much capital each approved
opportunity may receive.

It could consider:

- Available cash.
- Existing position exposure.
- Strategy conviction.
- Opportunity rank.
- Maximum position size.
- Portfolio concentration.
- Liquidity and tradeability.
- Risk budget consumption.
- Existing unrealized gains or losses.
- Rebalance and rotation policy.

Capital allocation should be explicit and auditable. It must not be hidden
inside strategy signal generation or execution routing.

## Future Exposure-Budgeting Layer

An exposure-budgeting layer would define the amount of risk or notional
exposure available across symbols, sectors, strategies, regimes, or other
portfolio dimensions.

Exposure budgeting could include:

- Per-symbol caps.
- Per-sector or industry caps.
- Per-strategy caps.
- Per-regime caps.
- Gross exposure limits.
- Net exposure limits.
- Cash reserve requirements.
- Factor exposure limits.
- Concentration limits.
- Liquidity-adjusted exposure limits.

The current hard-cap model is a narrow form of exposure governance. A future
budgeting layer would broaden that model from per-symbol enforcement to
portfolio-level capacity management.

## Future Component Relationships

A mature portfolio architecture would require clear contracts between the
following components.

### Regime Classifier

A regime classifier would identify market context such as trend, volatility,
risk-on/risk-off behavior, liquidity condition, or correlation regime.

Its output should be advisory until policy approves how regime state changes
strategy eligibility, allocation budgets, or execution constraints.

### Strategy Router

A strategy router would select which strategies are eligible to run under the
current regime and governance state. It should route among approved strategies,
not create new ungoverned strategies.

Routing must remain deterministic and auditable. A router decision should
explain why a strategy was enabled, disabled, deprioritized, or passed through.

### Approved Strategy Library

An approved strategy library would define the strategies that are allowed to
produce signals. Each approved strategy should have documented assumptions,
inputs, outputs, eligibility conditions, and governance limits.

The library is the control surface that prevents experimental logic from
becoming live allocation or execution behavior without approval.

### Portfolio Allocator

The portfolio allocator would arbitrate between approved signals and current
portfolio state. It would decide desired exposure changes before risk and
execution approval.

The allocator should produce explicit outputs such as target weights, target
notional exposure, add/trim intent, or no-action decisions. It should also
record rejected or suppressed opportunities when they matter for audit.

### Risk Governance

Risk governance would validate portfolio intent against approved limits. It
should remain independent from the allocator so optimization preferences cannot
silently override constraints.

Risk governance can reject, cap, resize, defer, or require manual approval only
if those behaviors are explicitly approved by policy.

### Execution

Execution converts approved intent into broker-facing activity. It should not
create portfolio intent, resolve allocation conflicts, or infer sell/rebalance
behavior from blocked buys.

Execution remains downstream. In the current OpenClaw state,
`execution_use_case` is detached and runtime visibility is observed-only.

## Factor-Awareness Concepts

Factor awareness means understanding whether the portfolio is unintentionally
concentrated in shared drivers of return or risk. Factor awareness is broader
than symbol-level exposure.

Potential factor dimensions include:

- Market beta.
- Sector and industry concentration.
- Momentum exposure.
- Value or growth exposure.
- Size exposure.
- Volatility exposure.
- Interest-rate sensitivity.
- Dollar or currency exposure.
- Liquidity exposure.
- Single-name correlation clusters.

Factor awareness can be used for reporting only, governance limits, ranking
adjustment, allocation budgeting, or rebalance decisions. Each use has different
policy consequences.

In the current state, no factor-awareness layer exists. Therefore factor
concepts should remain modeling inputs only until data quality, classification,
governance limits, and audit rules are defined.

## Saturation Beyond Per-Symbol Limits

The existing saturation model focuses on per-symbol exposure. A portfolio can be
saturated in other ways even when no individual symbol is at its cap.

Examples include:

- Sector exposure is full.
- Strategy exposure is full.
- Gross exposure is full.
- Cash reserve is below the required threshold.
- Factor exposure is above budget.
- Correlated positions consume the same risk budget.
- Liquidity budget is exhausted.
- A regime-specific exposure budget is full.

A mature portfolio-construction layer must distinguish symbol saturation from
portfolio saturation. A BUY proposal may be acceptable under a per-symbol cap
but still unacceptable under a sector, factor, strategy, or gross exposure
budget.

## Portfolio-Level Exposure Concepts

Portfolio-level exposure governance may require several exposure definitions:

- Current exposure: exposure represented by existing positions.
- Projected exposure: exposure after a proposed action is applied.
- Gross exposure: total long and short exposure before offsets.
- Net exposure: directional exposure after offsets.
- Concentration exposure: exposure to one symbol, sector, factor, or cluster.
- Liquidity-adjusted exposure: exposure weighted by ability to enter or exit.
- Risk-budget exposure: exposure measured against volatility, drawdown, or loss
  budget.
- Strategy exposure: capital assigned to a specific strategy family.
- Regime exposure: capital allowed under a specific market regime.

These definitions must be explicit before implementation. Otherwise allocation
and risk decisions may use the same word while measuring different things.

## Opportunity-Cost Governance

Opportunity cost is the cost of allocating capital to one opportunity instead of
another. Current hard-cap governance can block overexposure, but it does not
decide whether capital should rotate from a lower-ranked holding to a
higher-ranked signal.

Future opportunity-cost governance would need to answer:

- Whether stronger signals can displace weaker holdings.
- Whether saturated positions can be trimmed for better opportunities.
- Whether cash should be reserved for future signals.
- Whether existing positions receive a hold advantage over new candidates.
- Whether transaction costs, taxes, spreads, and liquidity reduce the benefit of
  rotation.
- Whether opportunity cost is evaluated continuously, periodically, or only at
  manual review points.

Without this policy, repeated blocked BUY proposals should be interpreted as
unallocated demand, not as authorization to rotate the portfolio.

## Ranking and Arbitration Philosophy

Ranking is not a single universal concept. A portfolio architecture may need
separate rankings for:

- Raw strategy conviction.
- Risk-adjusted expected return.
- Capital-adjusted opportunity.
- Rebalance priority.
- Execution readiness.
- Reduction or exit priority.
- Manual review priority.

Arbitration is the process of resolving conflicts between ranked opportunities
and limited capital or risk budgets.

A deterministic arbitration philosophy should define:

- Inputs used for ranking.
- Tie-breakers.
- How stale signals are handled.
- How saturated names remain visible or are suppressed.
- Whether existing holdings have priority over new candidates.
- Whether strategies compete globally or inside separate budgets.
- Whether allocation outputs are target exposures, order deltas, or approval
  decisions.

Until this philosophy is approved, OpenClaw should not introduce autonomous
allocation arbitration.

## Deterministic Governance Requirements

Any future portfolio-construction implementation must preserve deterministic
governance. At minimum, it should provide:

- Versioned inputs.
- Explicit portfolio state snapshots.
- Deterministic ranking rules.
- Deterministic allocation rules.
- Deterministic cap and budget calculations.
- Clear separation between signal, allocation, risk, and execution approvals.
- Audit records for suppressed, rejected, resized, deferred, and approved
  opportunities.
- Reproducible decisions for the same inputs.
- Tests covering boundary conditions and saturation states.
- Human-readable explanations for allocation and rejection decisions.

Optimization should never be allowed to obscure why a decision occurred.

## Dangers of Premature Adaptive Optimization

Adaptive optimization can be useful, but introducing it before the governance
model is mature creates material risk.

Risks include:

- Strategy signals becoming entangled with allocation decisions.
- Dynamic sizing silently weakening hard exposure caps.
- Optimization outputs being mistaken for execution approval.
- Rebalance behavior emerging without sell policy.
- Non-deterministic decisions caused by unstable inputs or changing objectives.
- Overfitting to recent performance or market regime.
- Poor auditability when allocation changes cannot be reproduced.
- Hidden concentration in factors or correlated names.
- Increased operational complexity before observability is ready.

Premature optimization would also make it harder to validate whether runtime
changes are caused by signal behavior, allocation logic, risk governance, or
execution behavior.

## Why Implementation Is Deferred

Implementation is deferred because the current system has not approved the
policy primitives required for portfolio construction.

OpenClaw currently has stable deterministic signal, reconciliation, and
execution-gating boundaries. The current hard-cap model handles exposure
saturation by blocking over-cap proposals. That is not a complete portfolio
construction system, but it is a clear and auditable governance model.

Before implementation, OpenClaw would need approved answers for:

- Which allocation objective the portfolio is optimizing.
- Whether strategy signals should remain pure or become exposure-aware.
- Whether sells and rebalances are allowed.
- Whether adaptive sizing is allowed.
- Which exposure budgets exist beyond per-symbol caps.
- Which factor classifications are trusted.
- Which ranking and arbitration rules are authoritative.
- Which decisions remain manual.
- Which runtime paths are allowed to execute.

Until those decisions exist, implementation would create architecture ambiguity
and governance risk.

## Required Operational Maturity Before Implementation

Operational maturity should precede any portfolio-construction implementation.
Minimum requirements include:

- Stable and reconciled position state.
- Reliable cash and buying-power state.
- Versioned strategy outputs.
- Approved strategy library metadata.
- Documented exposure definitions.
- Documented risk budgets and cap hierarchy.
- Observable rejected, suppressed, resized, and approved decisions.
- Deterministic replay of allocation decisions.
- Explicit sell and rebalance policy, if any.
- Execution lifecycle controls for partial fills, rejects, and sequencing.
- Data-quality checks for factor, sector, liquidity, and regime inputs.
- Test coverage for saturation, competing opportunities, and budget exhaustion.
- Operator review workflows for high-impact allocation changes.

Only after those capabilities are in place should OpenClaw consider implementing
a portfolio-construction layer, capital allocator, exposure-budgeting engine,
factor-aware model, rebalance lifecycle, or adaptive sizing system.
