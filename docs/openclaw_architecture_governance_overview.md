# OpenClaw Architecture Governance Overview

## Purpose

This document consolidates the current and future OpenClaw architecture
governance model. It is an architecture synthesis document only. It does not
approve runtime changes, execution activation, portfolio construction,
allocation arbitration, factor awareness, adaptive sizing, rebalance behavior,
or autonomous optimization.

The goal is to provide one institutional narrative that ties together the
current validated system, the approved governance boundaries, and the future
architecture concepts that remain deferred.

## Current Validated Architecture State

OpenClaw currently has a deterministic runtime architecture with explicitly
bounded responsibilities:

- A deterministic signal engine produces strategy proposals.
- Deterministic reconciliation and risk gating evaluate proposals against
  current known state and configured limits.
- Deterministic execution gating exists as a boundary, but execution activation
  remains detached.
- Hard-cap exposure governance prevents projected exposure from exceeding
  approved limits.
- Runtime visibility is observed-only.
- No automatic sell or rebalance behavior exists.
- No portfolio-construction layer exists.
- No allocation arbitration exists.
- No factor-awareness layer exists.
- No rebalance lifecycle exists.
- No adaptive sizing or autonomous optimization is approved.

The validated architecture is therefore a controlled proposal and governance
system, not an autonomous portfolio optimizer or execution system.

## Post-Replay Roadmap Rebase

The first guarded replay fixture phase is complete and parked.

Completed replay fixture scope:

- One risk-blocked event-stream fixture was approved through a controlled
  artifact-intake gate, copied, source-controlled, inventoried,
  hash/structure guarded, mapper-compatibility guarded, pushed, synced to VPS,
  and settled under the Alpaca timer baseline.
- The fixture remains an `EVENT_STREAM_REPLAY_FIXTURE`: event-only,
  incomplete, evidence-only, non-authoritative, and not a complete replay
  package.
- The current replay mapper remains in-memory only. No file ingestion is
  approved.
- The single approved fixture intake is closed. No further artifact copying is
  approved without a separate explicit gate.

Deferred replay and evaluation gates remain:

- Replay package creation.
- File ingestion.
- Replay writer.
- Runtime capture.
- Storage and immutability.
- Evaluation framework.
- Strategy promotion workflow.
- Additional fixture intake.
- Broker/API/TWS/IBKR work.
- Live trading.

Operational and roadmap ordering after replay park:

- The Alpaca timer baseline remains the current operational baseline.
- IBKR remains parked and broker-sensitive, including the known managed
  non-flat AAPL paper state. IBKR review must remain read-only unless a future
  gate explicitly opens broker work.
- Strategy and risk roadmap work remains governance-only until replay,
  evaluation, attribution, and promotion contracts are explicitly opened.
- Recommended next-lane ordering should stay read-only or docs-only unless a
  new explicit gate opens implementation authority.

## Current Deterministic Operational Model

The current operational model is deterministic across signal production,
reconciliation, and execution gating.

The validated behavior includes repeated BUY proposals for a saturated symbol,
deterministic reconciliation blocks when projected exposure exceeds the hard cap,
and no runtime drift or architecture instability. A blocked proposal does not
become an execution request, sell request, rebalance request, or resized order.

This model intentionally allows strategy demand and portfolio approval to
diverge. The strategy may continue to express conviction while reconciliation
prevents additional exposure.

## Current Approved Governance Boundaries

The current approved boundaries are:

- Signal generation may produce proposals.
- Reconciliation may approve or block proposals based on deterministic state and
  risk controls.
- Hard exposure caps are authoritative.
- Execution approval remains separate from strategy approval and reconciliation
  approval.
- `execution_use_case` remains detached.
- Runtime visibility remains observed-only.
- Presenter and mapper boundaries remain frozen.
- Broker-facing execution behavior is not activated.

These boundaries preserve auditability by keeping each approval concept
separate and reviewable.

## Functional Distinctions

### Signal Generation

Signal generation answers: "What does the strategy want?"

A strategy signal expresses opportunity, direction, conviction, score, or trade
intent from the strategy's perspective. It is not capital allocation, risk
approval, execution permission, or execution.

### Portfolio Construction

Portfolio construction answers: "What should the portfolio own or change given
all signals, constraints, budgets, risks, and objectives?"

No portfolio-construction layer exists today. Current hard-cap enforcement is a
portfolio control, but it is not a complete portfolio-construction system.

### Risk Governance

Risk governance answers: "Is this proposal or portfolio intent allowed under
approved limits?"

Current risk governance is expressed through deterministic reconciliation and
hard-cap exposure checks. Future risk governance may include broader exposure
budgets, factor limits, concentration limits, and regime-specific constraints.

### Execution Permission

Execution permission answers: "Has this action passed all required approvals to
move toward broker-facing activity?"

Execution permission is downstream of signal generation, allocation decisions,
risk governance, and reconciliation. A strategy signal or blocked proposal does
not imply permission to execute.

### Execution

Execution is broker-facing order activity. It must not create portfolio intent,
infer allocation decisions, or convert blocked proposals into action.

In the current state, execution remains detached and non-authoritative for
portfolio construction.

## Current Observed-Only Systems

Runtime visibility is currently observed-only. It may expose runtime state and
broker-visible information for inspection, but it does not authorize mutation,
orders, portfolio changes, or execution activation.

Observed-only systems are useful for verification and operator confidence, but
they must not be treated as control planes unless a later governance decision
explicitly changes their role.

## Detached and Frozen Systems

Several systems are intentionally detached or frozen:

- `execution_use_case` is modeled but detached from live execution authority.
- Broker execution architecture remains separated from signal and
  reconciliation logic.
- Runtime visibility remains read-only.
- Presenter and mapper boundaries remain frozen.
- Reconciliation ownership remains the active approval point for hard-cap
  exposure enforcement.
- Portfolio construction, factor awareness, allocation arbitration, adaptive
  sizing, and rebalance lifecycle remain deferred.

Detached and frozen systems protect the current architecture from accidental
scope expansion.

## Future Conceptual Architecture Layers

Future OpenClaw architecture may introduce additional layers, but each requires
separate policy approval and implementation governance.

Possible future layers include:

- Regime classifier.
- Strategy router.
- Approved strategy library.
- Portfolio-construction layer.
- Capital-allocation layer.
- Exposure-budgeting layer.
- Factor-awareness layer.
- Portfolio allocator.
- Rebalance lifecycle.
- Execution lifecycle orchestration.
- Expanded risk governance.

These layers should be additive only after their responsibilities, inputs,
outputs, authority, and audit requirements are defined.

## Future Regime-Aware Routing Concepts

A future regime-aware architecture could identify market conditions and route
approved strategies accordingly.

A regime classifier might identify trend, volatility, liquidity, correlation,
or risk-on/risk-off conditions. A strategy router might use that classification
to enable, disable, deprioritize, or route approved strategies.

This concept remains deferred. Regime awareness must not become implicit
execution approval, ungoverned strategy creation, or non-deterministic runtime
behavior. Any regime-aware routing model would need deterministic rules,
versioned inputs, and auditable explanations.

## Future Portfolio-Construction Concepts

A future portfolio-construction layer would convert multiple strategy signals
into coherent portfolio intent. It could decide target exposures, add/trim
intent, no-action decisions, allocation priorities, and rebalance candidates.

Such a layer would need to account for:

- Existing positions.
- Available cash and buying power.
- Current and projected exposure.
- Hard caps and broader exposure budgets.
- Strategy conviction and ranking.
- Liquidity and execution feasibility.
- Opportunity cost.
- Portfolio concentration.
- Risk and factor exposure.
- Rebalance and sell policy.

This layer does not currently exist and is not approved for implementation.

## Future Factor-Awareness Concepts

Factor awareness would evaluate shared drivers of return and risk across the
portfolio. It is broader than per-symbol exposure.

Potential factor dimensions include:

- Market beta.
- Sector and industry exposure.
- Momentum exposure.
- Value or growth exposure.
- Size exposure.
- Volatility exposure.
- Interest-rate sensitivity.
- Liquidity exposure.
- Correlation clusters.

Factor awareness could be used for reporting, limits, ranking adjustment,
allocation budgeting, or rebalance decisions. Each use has different governance
consequences and must be approved separately.

## Future Allocation and Arbitration Concepts

Allocation arbitration would resolve competition between signals and limited
capital or risk budgets.

Future arbitration might distinguish:

- Raw signal conviction.
- Capital-adjusted opportunity.
- Risk-adjusted opportunity.
- Execution readiness.
- Rebalance priority.
- Reduction or exit priority.
- Manual review priority.

Any arbitration layer would need deterministic ranking rules, tie-breakers,
stale-signal handling, budget hierarchy, and explicit treatment of saturated
positions.

Until those rules are approved, OpenClaw should not introduce autonomous
allocation arbitration.

## Governance Hierarchy and Authority Flow

The current and future architecture should follow a clear authority flow:

1. Approved data inputs establish the observable state.
2. Strategy generation produces signals.
3. Optional future routing determines which approved strategies are eligible.
4. Optional future portfolio construction converts signals into portfolio
   intent.
5. Risk governance validates intent against approved limits.
6. Reconciliation approves, blocks, resizes, or defers only according to
   approved policy.
7. Execution gating determines whether an approved action may proceed toward
   broker-facing execution.
8. Execution performs only authorized broker-facing activity.
9. Observability records decisions, state, approvals, blocks, and outcomes.

Authority should move downstream. Downstream layers must not invent upstream
intent, and upstream layers must not bypass downstream controls.

## Deterministic Governance Principles

OpenClaw governance should preserve the following principles:

- Same inputs should produce the same decisions.
- Signal approval, allocation approval, risk approval, execution permission, and
  execution must remain distinct.
- Hard caps and approved risk limits must be authoritative.
- Runtime visibility must not mutate state unless explicitly approved.
- Suppressed, blocked, resized, deferred, and approved decisions must be
  auditable.
- Portfolio state snapshots and input versions must be recoverable.
- Optimization must not obscure decision rationale.
- Sell, rebalance, dynamic sizing, and execution behavior require explicit
  policy approval before implementation.

These principles are more important than adding sophistication quickly.

## Implementation Deferral Rationale

Implementation is deferred because the current system is stable and the future
governance model is not yet approved.

The current architecture already provides deterministic signal generation,
reconciliation controls, hard-cap exposure enforcement, execution separation,
and observed-only runtime visibility. Adding portfolio construction,
allocation arbitration, factor awareness, or adaptive optimization before their
policies are settled would blur boundaries and create audit risk.

Deferred implementation protects the system from:

- Strategy logic becoming mixed with allocation logic.
- Risk governance becoming advisory instead of authoritative.
- Execution behavior activating without full approval.
- Rebalance behavior emerging without sell policy.
- Adaptive sizing weakening hard caps.
- Non-deterministic optimization obscuring audit trails.

## Operational Maturity Requirements

Future implementation requires operational maturity before architecture
expansion.

Minimum requirements include:

- Stable and reconciled position state.
- Reliable cash and buying-power state.
- Versioned strategy outputs.
- Approved strategy library metadata.
- Documented exposure definitions.
- Documented cap and budget hierarchy.
- Deterministic replay of decisions.
- Observable blocked, suppressed, resized, deferred, and approved decisions.
- Explicit sell and rebalance policy, if any.
- Factor, sector, liquidity, and regime data-quality checks.
- Execution lifecycle controls for partial fills, rejects, sequencing, and
  broker errors.
- Test coverage for saturation, competing opportunities, budget exhaustion,
  ranking, and gating boundaries.
- Operator review workflows for high-impact allocation or execution changes.

Without these capabilities, future layers would add complexity before the system
can govern them safely.

## Explicit Non-Approved Areas

The following areas are not approved by this overview:

- Live execution activation.
- Automatic sell behavior.
- Automatic rebalance behavior.
- Adaptive sizing.
- Dynamic cap enforcement.
- Exposure-aware strategy suppression.
- Portfolio-construction implementation.
- Allocation arbitration.
- Factor-aware limits or ranking.
- Regime-aware strategy routing.
- Autonomous optimization.
- Runtime mutation through observed-only systems.
- Presenter, mapper, or orchestration boundary changes.

These topics remain conceptual unless a future policy explicitly approves them.

## Long-Term Architectural Vision

The long-term OpenClaw architecture can evolve into an institutional portfolio
governance system with layered responsibility and deterministic authority flow.

In that future model, strategy signals would remain pure expressions of
opportunity. Regime routing would determine eligible strategies. Portfolio
construction would evaluate competing opportunities against current holdings,
capital, risk budgets, and factor exposure. Risk governance would enforce
approved limits. Execution gating would confirm permission. Execution would
perform only authorized broker-facing actions. Observability would make each
decision reproducible and reviewable.

That vision is deliberately staged. The current architecture should remain
stable, deterministic, and conservative until the required governance policies,
operational maturity, and audit controls exist.
