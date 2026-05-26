# Replayability Foundations

## Purpose

This document reviews the governance foundations required for replay-grade
operational fidelity in OpenClaw. It models what must be captured and governed
before future evaluation infrastructure can safely compare strategies,
parameters, allocation rules, lifecycle behavior, or risk controls.

This document is architecture review only. It does not approve replay
infrastructure, simulation infrastructure, evaluation tooling, promotion
tooling, runtime mutation, execution activation, or production behavior changes.

## Why Replayability Matters

Replayability matters because future improvement must be evidence-based rather
than live self-modifying.

Replay allows OpenClaw to answer:

- What did the approved production runtime decide?
- Which inputs and state produced that decision?
- Would a candidate version have made a different decision?
- Did the difference come from strategy logic, parameters, state, risk controls,
  allocation rules, or timing?
- Would the candidate have preserved deterministic governance boundaries?

Without replayability, evaluation becomes anecdotal. A candidate change may look
better because the environment changed, the state was incomplete, or execution
assumptions were inconsistent.

## Current OpenClaw Observability Maturity

OpenClaw currently has observed-only runtime visibility and deterministic
governance boundaries.

Current maturity includes:

- Deterministic signal generation.
- Deterministic reconciliation and risk gating.
- Deterministic execution gating boundary.
- Hard-cap exposure enforcement.
- Observed-only runtime visibility.
- Separation between strategy approval, reconciliation approval, and execution
  approval.
- No automatic sell or rebalance behavior.
- No live self-modifying strategies.
- No live autonomous parameter mutation.

This is a strong foundation for auditability, but it is not yet replay-grade
operational capture.

## Current Replayability Gaps

Current replayability gaps include:

- No approved replay package format.
- No replay infrastructure.
- No evaluation infrastructure.
- No promotion tooling.
- No versioned replay input bundles.
- No formal portfolio-state snapshot contract.
- No formal lifecycle-state snapshot contract.
- No formal broker-visible state capture contract.
- No timing and sequencing model for replay windows.
- No attribution engine for decision differences.
- No replay integrity validation.
- No simulation boundary.

These gaps do not imply runtime instability. They define the work required
before future evaluation systems can produce promotion-grade evidence.

## Deterministic Replay Requirements

Deterministic replay requires the same replay package and same replay version to
produce the same outputs.

Replay requires:

- Versioned source code.
- Versioned configuration.
- Versioned strategy and parameter definitions.
- Captured market data inputs.
- Captured portfolio state.
- Captured broker-visible state, if used.
- Captured timing assumptions.
- Captured governance rules.
- Captured prior decisions relevant to the replay window.
- Stable data adjustment assumptions.
- Deterministic ordering of events.
- Reproducible reconciliation and risk-gating behavior.

If any required input remains mutable or implicit, replay results cannot be
treated as reliable evidence.

## Required Replay State Concepts

A replay-grade state model should define the state needed to reproduce
decisions.

Required concepts may include:

- Input state: market data, signals, calendars, and reference data.
- Portfolio state: positions, cost basis if used, exposure, cash, and buying
  power.
- Lifecycle state: entry history, hold state, saturation state, aging state,
  and prior lifecycle decisions.
- Broker-visible state: account, position, order, fill, and connection state
  observed from broker interfaces.
- Governance state: caps, risk limits, strategy eligibility, and execution
  boundaries.
- Decision state: prior proposals, approvals, blocks, deferrals, and execution
  gating outcomes.

Each concept needs a stable schema before replay can become operational.

## Portfolio-State Snapshot Concepts

Portfolio-state snapshots represent the portfolio at a point in time.

A future snapshot may include:

- Positions by symbol.
- Quantity and market value.
- Current exposure.
- Projected exposure calculations.
- Cash.
- Buying power.
- Open orders, if relevant.
- Pending fills, if relevant.
- Exposure caps.
- Portfolio-level budgets.
- Sector, strategy, or factor classifications, if used.
- Timestamp and data source.

The snapshot must make clear whether it represents internal state, broker-
visible state, reconciled state, or a composite of multiple sources.

## Lifecycle-State Snapshot Concepts

Lifecycle-state snapshots represent the state of each position within its
governed lifecycle.

Future lifecycle snapshots may include:

- Entry timestamp.
- Entry rationale.
- Last signal timestamp.
- Last review timestamp.
- Hold rationale.
- Saturation state.
- Aging metrics.
- Opportunity-cost state.
- Trim or exit candidacy.
- Rebalance candidacy.
- Prior lifecycle decisions.
- Manual overrides.

OpenClaw does not currently implement lifecycle governance. These concepts are
required only if future phases introduce hold, exit, rebalance, capital
recycling, or portfolio rotation behavior.

## Broker-Visible State Requirements

Broker-visible state is the state observed from broker interfaces, not
necessarily the same as internal portfolio state.

Replay-grade broker-visible state may require:

- Account identifier or account scope.
- Positions.
- Cash and buying power values.
- Open orders.
- Order statuses.
- Fill events.
- Rejections or cancellations.
- Connection state.
- Timestamps from broker observations.
- Source and freshness of each observation.

Broker-visible state must remain observed-only unless execution activation is
approved separately. Capturing broker-visible state for replay does not create
execution authority.

## Timing and Sequencing Requirements

Replay must preserve timing and event ordering.

Timing requirements include:

- Decision timestamp.
- Market data timestamp.
- Portfolio snapshot timestamp.
- Broker observation timestamp.
- Signal generation timestamp.
- Reconciliation timestamp.
- Execution-gating timestamp.
- Order and fill timestamps, if used in future replay.
- Calendar and market-session assumptions.
- Timezone assumptions.

Sequencing requirements include:

- Event order within a replay window.
- Treatment of simultaneous events.
- Staleness rules for data and state.
- Whether decisions use start-of-cycle, end-of-cycle, or latest-observed state.
- How missing or late data is handled.

Without timing fidelity, replay can accidentally evaluate a decision using
information that was not available at the time.

## Evaluation Reproducibility Requirements

Evaluation reproducibility requires more than replaying one scenario.

Evaluation should preserve:

- Candidate version.
- Baseline production version.
- Replay package set.
- Metrics definitions.
- Comparison windows.
- Inclusion and exclusion criteria.
- Transaction-cost assumptions.
- Fill assumptions, if simulated.
- Portfolio and risk metrics.
- Random seeds, if any stochastic process is ever introduced.
- Generated reports and evidence artifacts.

The same evaluation definition should be runnable again and produce equivalent
results unless input versions intentionally change.

## Portfolio/Risk State Contract Planning

The minimum portfolio/risk replay state contract is recorded in
`docs/replay_package_specification.md` under Portfolio/Risk Replay State
Contract Planning.

This contract is the next architecture lane after closure of the 3-close
evidence phase. It defines the required portfolio snapshots, broker-visible
state boundary, position and exposure fields, reconciliation evidence,
risk-governance decisions, exposure saturation evidence, event-order evidence,
and attribution requirements needed before deterministic evaluation can become
implementation-ready.

This planning does not approve replay infrastructure, snapshot capture tooling,
runtime changes, broker/live/API work, VPS validation, strategy behavior
changes, risk behavior changes, execution activation, or production mutation.

## Attribution Requirements

Replay must support attribution of decision differences.

Attribution should distinguish differences caused by:

- Strategy code.
- Strategy parameters.
- Input data.
- Portfolio state.
- Broker-visible state.
- Exposure caps.
- Risk limits.
- Ranking logic.
- Allocation rules.
- Lifecycle rules.
- Timing assumptions.
- Execution assumptions.
- Data quality issues.

Attribution prevents a candidate from being promoted for the wrong reason and
helps identify whether a changed outcome is a desired improvement or a
governance regression.

## Replay Package Concepts

A replay package is a versioned bundle of inputs and metadata sufficient to
reproduce a decision window.

A future replay package may include:

- Package identifier.
- Replay window.
- Source code reference.
- Configuration reference.
- Strategy and parameter references.
- Market data bundle.
- Portfolio-state snapshots.
- Broker-visible state snapshots.
- Lifecycle-state snapshots, if applicable.
- Governance rule references.
- Prior decision logs.
- Timing and calendar metadata.
- Data-quality notes.
- Integrity checks.

Replay packages should be immutable once used for evaluation evidence. If a
package changes, it should receive a new version.

## Replay Package Envelope Schema Planning

The replay package envelope schema planning record is documented in
`docs/replay_package_specification.md`.

The envelope is intended to standardize package identity, schema versioning,
evidence references, integrity markers, section status, immutability markers,
attribution references, and authority boundaries before any implementation
gate. It remains docs-only and not implemented.

This planning does not approve replay writer implementation, runtime capture,
JSONL or observation schema changes, `main.py` changes, broker/live/API work,
IBKR/TWS work, Alpaca calls, VPS validation, strategy behavior changes,
risk/reconciliation behavior changes, execution behavior, sell behavior, trim
behavior, rebalance behavior, resize behavior, promotion behavior, or production
mutation.

## Replay vs Simulation

Replay and simulation are related but distinct.

Replay reproduces decisions from recorded or fixed inputs. It answers what the
system did or would have done under a captured scenario.

Simulation creates hypothetical paths or assumptions that may not have occurred.
It may model fills, costs, slippage, alternate market conditions, or portfolio
trajectories.

Replay is closer to audit reproduction. Simulation is closer to prospective
analysis. Both can be useful, but simulation assumptions must be explicit and
must not be confused with production evidence.

## Replay Integrity Risks

Replay integrity can fail in several ways:

- Missing input data.
- Mutated historical data.
- Unversioned configuration.
- Incomplete portfolio snapshots.
- Incomplete broker-visible state.
- Incorrect event ordering.
- Timezone errors.
- Lookahead bias.
- Survivorship bias.
- Hidden manual interventions.
- Inconsistent data adjustments.
- Non-deterministic code paths.
- Candidate logic reading data unavailable to production.

Replay integrity controls must detect or disclose these risks before replay
outputs are used for governance decisions.

## Replay Remains Non-Authoritative

Replay remains non-authoritative because it is an evaluation and evidence tool,
not a production control plane.

Replay must not:

- Mutate production state.
- Change strategy code.
- Change parameters.
- Approve execution.
- Create broker-facing orders.
- Sell, trim, or rebalance positions.
- Promote candidates automatically.
- Override risk governance.

Replay can inform approval. It cannot grant approval.

## Future Relationship Between Replay, Evaluation, Promotion, and Production

The future controlled evolution flow should remain:

1. Production runtime observes and records decisions.
2. Replay reproduces historical or recorded decision windows.
3. Evaluation compares baseline and candidate behavior.
4. Governance reviews evidence.
5. Promotion moves an approved change into a versioned production path.
6. Production runtime runs only approved promoted versions.

This relationship keeps research and evaluation separate from live production
authority while allowing the system to improve through evidence.

## Deferred Implementation Boundaries

This document does not approve implementation.

Deferred areas include:

- Replay package schema.
- Replay runner.
- Replay data store.
- Snapshot capture tooling.
- Broker-visible state capture beyond current approved visibility.
- Lifecycle-state capture tooling.
- Evaluation engine.
- Attribution engine.
- Simulation engine.
- Promotion tooling.
- Replay integrity validation tooling.
- AI-assisted replay analysis.
- Any production mutation based on replay output.

Future implementation should begin only after a phase explicitly approves
scope, data contracts, authority boundaries, storage requirements, audit
requirements, and operational controls.

Until then, replayability remains a governance foundation to be modeled before
evaluation infrastructure is implemented.
