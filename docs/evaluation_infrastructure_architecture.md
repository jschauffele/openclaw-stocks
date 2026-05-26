# Evaluation Infrastructure Architecture

## Purpose

This document models a future governance-level evaluation infrastructure for
OpenClaw. It defines how the system may safely evolve through replay,
evaluation, evidence, approval, and controlled promotion without introducing
uncontrolled runtime mutation.

This document is architecture modeling only. It does not approve implementation
of replay infrastructure, experiment tracking, promotion tooling, paper trading,
shadow evaluation, AI-controlled evaluation, runtime mutation, execution
activation, or autonomous optimization.

## System Distinctions

Evaluation governance requires four systems to remain distinct.

### Production Runtime

The production runtime is the approved deterministic system that produces live
signals, reconciliation decisions, risk-gating decisions, and execution-gating
decisions from versioned code, versioned configuration, and recorded state.

Production runtime must remain deterministic, versioned, reproducible, and
non-self-modifying.

### Replay Systems

Replay systems reproduce historical or recorded scenarios under controlled
conditions. Their purpose is to answer: "What would this approved or candidate
version have decided under the same inputs and state?"

Replay systems do not have production authority. They must not mutate live
state, approve execution, change production parameters, or change production
strategy logic.

### Evaluation Systems

Evaluation systems compare replay outputs, candidate strategies, parameter
sets, allocation rules, risk controls, and portfolio outcomes. Their purpose is
to generate evidence.

Evaluation systems may produce reports, metrics, comparisons, and
recommendations. They do not promote changes by themselves.

### Promotion Systems

Promotion systems move an approved candidate from research or evaluation into a
versioned production path.

Promotion must be governed, reviewable, and reversible where possible. Promotion
is the point where evidence and approval become production behavior.

## Replay Philosophy

Replay exists to make change evaluation disciplined.

The core replay question is not whether a candidate appears attractive in
isolation. The core question is whether the candidate behaves better than the
current approved production version under comparable inputs, constraints, and
governance rules.

Replay should support:

- Reproducing production decisions.
- Explaining historical behavior.
- Comparing candidate strategies or parameters.
- Testing risk and exposure boundary behavior.
- Evaluating saturation states.
- Identifying operational side effects before promotion.

Replay must remain separate from live execution and production mutation.

## Deterministic Replay Requirements

Deterministic replay requires stable inputs and versioned decision logic.

At minimum, replay should preserve or reference:

- Source code version.
- Configuration version.
- Strategy version.
- Parameter version.
- Market data inputs.
- Portfolio state snapshot.
- Cash and buying-power state, if used.
- Broker-visible state, if used.
- Existing positions.
- Prior decisions relevant to the replay window.
- Time and calendar assumptions.
- Corporate action and data-adjustment assumptions.
- Reconciliation and risk-gating rules.

The same replay version, given the same replay package, should produce the same
results. If replay depends on external mutable data, that dependency must be
captured or versioned.

## Evidence Collection Requirements

Evaluation infrastructure should collect evidence that is sufficient to support
governed decisions.

Evidence may include:

- Decision logs.
- Signal outputs.
- Reconciliation outcomes.
- Risk-gating outcomes.
- Blocked, suppressed, resized, deferred, and approved proposals.
- Position and exposure changes.
- Portfolio-level metrics.
- Drawdown and volatility measures.
- Turnover and transaction-cost estimates.
- Saturation events.
- Missed-opportunity analysis.
- Execution feasibility assumptions.
- Differences from the current approved production version.

Evidence must be tied to the exact candidate being evaluated. A conclusion
without reproducible evidence is not a promotion basis.

## Attribution Requirements

Evaluation must be able to explain why results changed.

Attribution should distinguish effects caused by:

- Strategy logic changes.
- Parameter changes.
- Market data changes.
- Portfolio state changes.
- Allocation rule changes.
- Risk-governance changes.
- Exposure cap changes.
- Ranking or arbitration changes.
- Sizing changes.
- Sell or rebalance assumptions.
- Execution assumptions.

Without attribution, a positive result may hide a governance regression, and a
negative result may wrongly discredit a useful change.

## Experiment Isolation Requirements

Experiments must be isolated from production.

Isolation requirements include:

- Separate experiment configuration from production configuration.
- Separate candidate strategy versions from approved strategy versions.
- No writes to production runtime state.
- No writes to broker-facing systems.
- No live execution permission.
- No automatic promotion from experiment output.
- Clear experiment identifiers.
- Reproducible input packages.
- Explicit start and end scope for each experiment.

Experiment isolation prevents research from becoming accidental production
behavior.

## Strategy-Version Governance

Strategies should be treated as versioned governed assets.

A future strategy-version model should capture:

- Strategy identifier.
- Strategy version.
- Source code revision.
- Input contract.
- Output contract.
- Approved use case.
- Eligibility constraints.
- Known assumptions.
- Evaluation evidence.
- Approval status.
- Promotion date, if promoted.
- Deprecation or rollback status, if applicable.

A candidate strategy version may be evaluated offline without becoming approved
for production. Production should run only approved versions.

## Parameter-Version Governance

Parameters should also be treated as versioned governed assets.

A future parameter-version model should capture:

- Parameter set identifier.
- Parameter version.
- Associated strategy or portfolio component.
- Current production value.
- Candidate value.
- Rationale for change.
- Replay evidence.
- Sensitivity analysis, when appropriate.
- Risk and exposure impact.
- Approval status.
- Promotion date, if promoted.
- Rollback target.

Parameter changes can materially change behavior and should not be treated as
minor operational tweaks.

## Portfolio-Evaluation Concepts

Portfolio evaluation should compare candidate behavior at the portfolio level,
not only at the individual signal level.

Future portfolio evaluation may consider:

- Total return and risk-adjusted return.
- Drawdown.
- Volatility.
- Turnover.
- Concentration.
- Cash usage.
- Exposure cap utilization.
- Saturation frequency.
- Sector, factor, and strategy exposure.
- Opportunity cost.
- Rebalance assumptions.
- Sell assumptions.
- Transaction-cost estimates.
- Liquidity feasibility.

Portfolio evaluation must distinguish signal quality from allocation policy,
risk governance, and execution assumptions.

## Promotion Workflow Concepts

Promotion is the governed movement of an evaluated candidate into production.

A future promotion workflow should include:

1. Candidate definition.
2. Replay package selection.
3. Evaluation run.
4. Evidence review.
5. Risk and governance review.
6. Approval or rejection.
7. Versioned promotion artifact.
8. Production deployment plan.
9. Monitoring plan.
10. Rollback plan.

Promotion should be explicit. No experiment, AI recommendation, or favorable
metric should automatically change production behavior.

## Shadow Evaluation Concepts

Shadow evaluation means running a candidate in parallel with production for
observation only.

Shadow evaluation may compare what a candidate would have signaled, blocked,
approved, sized, ranked, or allocated while production continues to operate
under the approved version.

Shadow outputs must remain non-authoritative. They may inform future evidence,
but they must not mutate production state, approve execution, or override
production decisions.

## Paper Validation Concepts

Paper validation means testing behavior in a simulated or non-broker-authority
environment before production promotion.

Paper validation can help evaluate:

- Order sequencing assumptions.
- Fill assumptions.
- Execution feasibility.
- Rebalance lifecycle behavior.
- Allocation and sizing behavior.
- Operational observability.
- Failure and rollback handling.

Paper validation is not proof of production readiness by itself. It is one
evidence source within the broader governance process.

## Rollback Governance

Rollback governance defines how an approved production change can be reversed,
disabled, or replaced.

Future rollback governance should define:

- The prior approved version.
- Conditions that trigger rollback review.
- Who or what may initiate rollback.
- Whether rollback is automatic, manual, or approval-gated.
- State implications of rollback.
- Treatment of open positions.
- Treatment of pending or partially executed activity.
- Audit records for rollback decisions.

Rollback planning is required because strategy, parameter, allocation, and
execution changes can have persistent portfolio consequences.

## Live Self-Modification Remains Prohibited

Live self-modification remains prohibited because it weakens deterministic
governance.

The production runtime must not:

- Rewrite strategy logic while live.
- Mutate parameters autonomously.
- Promote candidates based on live results.
- Allow AI to change production behavior.
- Convert evaluation findings into execution authority.
- Change allocation or risk rules without approval.

Live self-modification would make it difficult to reproduce decisions, attribute
outcomes, audit authority, and separate research from production.

## Future AI Advisory and Evaluation Role

AI may support evaluation as an advisory system.

Future AI-assisted evaluation may:

- Summarize replay outputs.
- Compare candidate and production behavior.
- Identify anomalies.
- Draft experiment hypotheses.
- Highlight risk or governance concerns.
- Recommend additional evaluation cases.
- Produce human-review reports.

AI must not:

- Mutate production runtime.
- Promote strategy or parameter changes.
- Approve execution.
- Override risk governance.
- Create live broker-facing actions.
- Rebalance the portfolio.

AI can help evaluate evidence. It cannot become production authority without a
separate explicit governance decision.

## Deferred Implementation Boundaries

This document does not open implementation.

Deferred areas include:

- Replay infrastructure.
- Replay package format.
- Experiment registry.
- Metrics engine.
- Attribution engine.
- Strategy-version registry.
- Parameter-version registry.
- Portfolio-evaluation engine.
- Promotion tooling.
- Shadow evaluation runtime.
- Paper validation runtime.
- Rollback automation.
- AI advisory tooling.

Future implementation should begin only after a phase explicitly approves scope,
authority, data contracts, audit requirements, and operational controls.

Until then, OpenClaw may continue to improve through documented governance
modeling while production runtime remains deterministic, versioned,
reproducible, and non-self-modifying.

## Portfolio/Risk Replay State Contract Prerequisite

Evaluation infrastructure depends on replay-grade portfolio/risk state before
it can produce governance-grade attribution.

The minimum contract is recorded in `docs/replay_package_specification.md`.
Future evaluation must be able to compare baseline and candidate behavior while
preserving portfolio snapshots, broker-visible state boundaries,
position/exposure fields, reconciliation evidence, risk-governance decisions,
exposure saturation evidence, event ordering, and attribution to the exact
cause of any decision difference.

Until that contract is implemented through separate gates, evaluation remains
architecture modeling only. This note does not approve replay infrastructure,
evaluation tooling, broker/live/API work, VPS validation, strategy behavior
changes, risk behavior changes, portfolio mutation, execution activation, or
promotion.

## Replay Package Envelope Schema Prerequisite

Evaluation infrastructure also depends on a stable replay package envelope
schema before evaluation outputs can be compared across packages.

The envelope schema planning record is documented in
`docs/replay_package_specification.md`. It standardizes package identity,
schema versioning, evidence references, section status, integrity,
immutability, attribution references, and authority boundaries.

Until the envelope schema is implemented through separate gates, evaluation
remains architecture modeling only. This note does not approve replay writer
implementation, runtime capture, JSONL or observation schema changes, `main.py`
changes, broker/live/API work, IBKR/TWS work, Alpaca calls, VPS validation,
strategy behavior changes, risk/reconciliation behavior changes, execution
behavior, sell behavior, trim behavior, rebalance behavior, resize behavior,
promotion behavior, or production mutation.
