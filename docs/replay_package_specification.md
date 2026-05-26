# Replay Package Specification

## Purpose

This document specifies the minimum immutable operational evidence package
required for deterministic replay-grade reconstruction in OpenClaw.

A replay package is a versioned bundle of facts that allows a future replay
system to reconstruct what production knew, evaluated, decided, blocked, or
completed during a bounded decision window.

This document is implementation planning only. It does not approve replay
infrastructure, evaluation infrastructure, promotion tooling, runtime mutation,
execution activation, broker writes, or production behavior changes.

## Immutable Evidence Philosophy

Replay packages should be immutable evidence artifacts.

The package should record facts as they were available to the production runtime
at decision time. It should not be edited later to make the run look cleaner,
fill in missing facts, or reinterpret a decision. Corrections, annotations, or
derived views should be appended as separate evidence, not by rewriting the
original package.

The package exists to support reconstruction, comparison, and governance review.
It is not a control plane and does not authorize future behavior.

## Required Package Identity Metadata

Each replay package requires identity metadata that makes it uniquely
referenceable.

Minimum identity metadata:

- Package identifier.
- Package schema version.
- Package creation timestamp.
- Run identifier.
- Replay window start and end.
- Production environment name or classification.
- Trigger source.
- Package producer name or component.
- Package status, such as complete, incomplete, corrected, or invalidated.
- Parent or related package references, if any.

The package identifier should remain stable after creation. If package contents
change, the changed artifact should receive a new package version or identifier.

## Required Code and Version Metadata

Replay-grade reconstruction requires knowing which code and governed assets were
active.

Minimum code and version metadata:

- Source control commit SHA.
- Branch or release label, if available.
- Dirty-worktree indicator, if available.
- Runtime entrypoint.
- Strategy identifier.
- Strategy version.
- Parameter set identifier.
- Parameter set version.
- Risk-governance version.
- Reconciliation-policy version.
- Execution-gating version.
- Runtime visibility-policy version, if used.
- Dependency lock or environment reference, if available.

Without version metadata, replay may reproduce behavior under the wrong code or
configuration and produce misleading evidence.

## Required Configuration Metadata

The replay package should capture the configuration values that shaped the
decision path.

Minimum configuration metadata:

- `OPENCLAW_ENABLED`.
- `OPENCLAW_DRY_RUN`.
- `OPENCLAW_SYMBOL`.
- `OPENCLAW_QTY`.
- `OPENCLAW_MAX_POSITION_SIZE`.
- `OPENCLAW_DUPLICATE_COOLDOWN_SECONDS`.
- `OPENCLAW_BROKER`.
- Allowed symbols.
- Signal timeframe.
- Signal limit.
- Trigger source.
- Broker endpoint classification, without secret values.
- Runtime visibility enablement and provider configuration, if used.
- Any feature flags that affect control flow.

Secrets must not be stored in replay packages. Secret presence or credential
scope may be represented with safe metadata, but raw credentials must remain
excluded.

## Required Market-Input Capture

Market-input capture must preserve the data used by strategy evaluation.

Minimum market-input evidence:

- Market data provider identifier.
- Symbol.
- Timeframe.
- Requested limit or window.
- Query timestamp.
- Returned candle count.
- Full candle set used by the strategy, including timestamp, open, high, low,
  close, and volume when available.
- Data warnings or fallback behavior.
- Latest candle timestamp.
- Calendar and market-session state used by the run.
- Data adjustment assumptions, if any.

Derived values such as latest close, percent change, and three-close percent
change are useful, but they are not a substitute for the input candles.

## Required Strategy-Input Capture

Strategy-input capture records the facts passed into strategy logic and the
strategy output before later gates modify the run outcome.

Minimum strategy evidence:

- Strategy identifier and version.
- Input close sequence or full strategy input payload.
- Strategy thresholds and parameters.
- Signal result.
- Decision result.
- Action proposal.
- Quantity requested.
- Strategy reason.
- Derived metrics used by the strategy.
- Validation result from signal validation.
- Timestamp of strategy evaluation.

This preserves the distinction between strategy signal and later portfolio,
risk, reconciliation, or execution decisions.

## Required Portfolio-State Capture

Portfolio-state capture records the portfolio facts that affected eligibility,
risk, and exposure calculations.

Minimum portfolio-state evidence:

- Portfolio snapshot timestamp.
- Symbol-level existing position quantity.
- Position side, if applicable.
- Buying power.
- Cash or cash-equivalent value, if used.
- Estimated order cost.
- Requested quantity.
- Existing exposure.
- Open buy order quantity.
- Projected exposure.
- Maximum position size.
- Allowed-symbol scope.
- Duplicate-guard state used by the run.
- Prior matching order state, if duplicate logic uses it.

The package should identify whether each portfolio fact came from internal
state, broker-visible state, or a reconciled composite.

## Required Broker-Visible-State Capture

Broker-visible state is the state observed from broker interfaces. It may differ
from internal state and must be captured separately when it influences a
decision.

Minimum broker-visible evidence:

- Broker name.
- Account or account-scope identifier, when safe to store.
- Broker observation timestamp.
- Account buying power result.
- Position lookup result.
- Open-order lookup result.
- Open buy order quantity and count.
- Order identifiers, if any.
- Order status values, if any.
- Fill or execution snapshot, if used.
- Broker errors, timeouts, or partial responses.
- Connection or diagnostics state, if runtime visibility is enabled.
- Source freshness or timeout settings.

Capturing broker-visible state remains observed-only. It does not create
execution authority.

## Required Reconciliation-State Capture

Reconciliation-state capture records the facts and decision that determined
whether a proposal could proceed.

Minimum reconciliation evidence:

- Reconciliation timestamp.
- Requested symbol, side, and quantity.
- Existing position quantity.
- Open buy order quantity.
- Projected position quantity.
- Maximum position size.
- Reconciliation pass or block result.
- Reconciliation reason.
- Reconciliation message.
- Submit reconciliation status, if applicable.
- Manual review flag, if applicable.
- Ambiguity flag, if applicable.
- Filled quantity and working quantity, if applicable.
- Matched execution identifiers, if applicable.
- Raw or structured reconciliation evidence references.

The package should preserve both the normalized decision and the underlying
evidence that produced it.

## Portfolio/Risk Replay State Contract Planning

This planning record defines the minimum replay-grade portfolio and risk state
contract needed for future deterministic evaluation and attribution. It is
docs-only. It does not approve implementation, replay package writing, runtime
changes, strategy behavior changes, broker/live/API work, VPS validation,
execution activation, or portfolio mutation.

Required portfolio-state snapshot fields:

- Snapshot identifier.
- Snapshot schema version.
- Snapshot timestamp and timezone.
- Source classification: internal state, broker-visible state, reconciled
  composite, or operator-supplied review input.
- Run identifier or replay package identifier.
- Symbol universe in scope.
- Per-symbol position records.
- Cash and buying-power facts if they influence eligibility, risk, or exposure.
- Open-order facts if they influence projected exposure or duplicate checks.
- Governance configuration references used by the decision window.
- Data freshness and completeness status.

Required position and exposure fields:

- Symbol.
- Position quantity.
- Position side.
- Position market value or notional exposure when available.
- Average cost or cost basis only if used by the future decision being replayed.
- Existing exposure.
- Requested order side and quantity.
- Estimated order cost or exposure delta.
- Open buy order quantity and count.
- Projected exposure.
- Maximum position size or applicable cap.
- Remaining capacity under the cap.
- Saturation state: unsaturated, saturated, over-cap, unknown, or not
  applicable.
- Exposure source and calculation timestamp.
- Any ambiguity or missing-data reason.

Broker-visible state boundary:

- Broker-visible state is observed evidence, not authority.
- Broker-visible state capture must remain separate from order submission,
  cancellation, flattening, remediation, retry, resubmit, reconciliation
  mutation, and runtime control behavior.
- Broker-visible state may include account scope, positions, open orders,
  order statuses, fills, buying power, connection state, provider name,
  provider status, observation timestamp, freshness, and errors or timeouts.
- Secrets, raw credentials, credential-derived values, and live account
  identifiers that are not safe for persisted evidence must not be stored.
- Capturing broker-visible state does not approve IBKR execution, Alpaca
  trading, broker API calls, live routing, or VPS validation.

Required reconciliation evidence fields:

- Reconciliation timestamp.
- Requested symbol, side, quantity, and estimated exposure impact.
- Existing position quantity and exposure.
- Open buy order quantity and count.
- Projected exposure.
- Applicable cap or limit.
- Pass, block, defer, resize, or manual-review result if those result types are
  approved in the future.
- Reconciliation reason and human-readable message.
- Evidence source references used by reconciliation.
- Ambiguity flag and ambiguity reason.
- Manual review flag if applicable.
- Submit reconciliation status only when a separately approved submit workflow
  is in scope.

Required risk-governance decision fields:

- Risk-governance policy identifier and version.
- Risk decision timestamp.
- Decision result: pass, block, defer, resize, manual review, or not applicable.
- Decision reason.
- Limits evaluated.
- Input values used for each limit.
- Current and projected exposure values.
- Limit utilization before and after the proposal.
- Blocking limit identifier when blocked.
- Whether the result is authoritative or advisory.
- Whether the decision depends on broker-visible state, internal state, or a
  reconciled composite.

Required exposure saturation fields:

- Saturation policy identifier and version.
- Saturation evaluation timestamp.
- Saturation state before the proposal.
- Existing exposure.
- Proposed exposure delta.
- Projected exposure.
- Maximum allowed exposure.
- Remaining capacity.
- Whether the proposal is blocked by hard-cap enforcement.
- Whether any resize, suppress, sell, trim, rebalance, or capital recycling
  behavior is applicable. In the current OpenClaw state this must be recorded
  as not applicable because those behaviors are not approved.
- Explanation preserving the distinction between strategy demand,
  reconciliation approval, risk approval, and execution permission.

Required event-order evidence:

- Ordered event stream identifier.
- Stable event identifiers.
- Event timestamps with timezone.
- Runtime stage names.
- Stage start and completion status.
- Decision-relevant payload references.
- Snapshot references used by each decision.
- Reconciliation and risk decision ordering.
- Early-stop or terminal outcome.
- Final completion event.
- Missing, late, duplicate, corrected, or out-of-order event markers.

Attribution requirements:

- Replay packages must support attribution of differences to strategy logic,
  parameters, market inputs, portfolio state, broker-visible state,
  reconciliation policy, risk policy, exposure caps, event ordering, lifecycle
  assumptions, allocation assumptions, or execution assumptions.
- Attribution must distinguish current approved behavior from candidate
  behavior.
- Attribution must identify whether a changed outcome is caused by a desired
  candidate rule, missing evidence, stale state, data-quality issue, or
  governance regression.
- Attribution must not depend on AI discretion for expected outcomes.

Out of scope for this contract:

- Replay package writer implementation.
- Runtime snapshot capture implementation.
- Broker API calls.
- Alpaca trading or market-data API calls.
- IBKR execution or TWS/IB Gateway work.
- VPS validation.
- Strategy behavior changes.
- Risk, reconciliation, sizing, sell, trim, rebalance, or execution behavior
  changes.
- Production JSONL or observation schema changes.
- Evidence/research collection under the closed 3-close hypothesis.

Future implementation gates required:

- Replay package schema implementation gate.
- Snapshot capture implementation gate.
- Replay package storage and immutability gate.
- Replay integrity validation gate.
- Attribution engine planning and implementation gate.
- Broker-visible state capture gate if broker observations are needed beyond
  currently approved read-only visibility.
- Portfolio/risk evaluation engine gate before any candidate comparison can
  influence governance decisions.
- Promotion workflow gate before any evaluated candidate can affect production.

## Required Lifecycle-State Capture

Lifecycle-state capture is required only when lifecycle governance is introduced
or when lifecycle facts influence decisions.

Minimum future lifecycle evidence may include:

- Entry timestamp.
- Entry rationale.
- Last signal timestamp.
- Last lifecycle review timestamp.
- Hold rationale.
- Saturation state.
- Position age.
- Opportunity-cost state.
- Exit candidacy.
- Trim candidacy.
- Rebalance candidacy.
- Prior lifecycle decisions.
- Manual overrides.

Current OpenClaw does not implement lifecycle governance. Until it does, the
package should explicitly record lifecycle state as not applicable rather than
implying hidden lifecycle behavior.

## Required Sequencing and Event Capture

Replay packages must preserve event order.

Minimum sequencing evidence:

- Ordered event stream.
- Stable event identifiers.
- Event timestamps.
- Stage names.
- Stage statuses.
- Decision-relevant payloads.
- Final completion event.
- Whether the run stopped early.
- Whether the package is complete through terminal outcome.
- Timing assumptions and timezone.
- Staleness rules for data and state, if defined.

The ordered event stream should remain the primary reconstruction surface. Run
reports and observation rows should be treated as derived summaries.

## Replay Package Integrity Concepts

Replay package integrity protects evidence from silent corruption or accidental
reinterpretation.

Future integrity concepts may include:

- Package manifest.
- Content hashes.
- Schema validation.
- Completeness checks.
- Terminal-event checks.
- Required-field checks.
- Source-reference checks.
- Package immutability marker.
- Invalidated-package marker.
- Correction or annotation references.

Integrity checks should make it clear whether a package is replay-grade,
partial, invalid, or suitable only for manual review.

## Append-Only Evidence Concepts

Replay evidence should be append-only.

Append-only evidence means:

- Original package facts are not rewritten.
- Corrections are added as new records.
- Derived metrics are added as derived records.
- Review annotations are added separately.
- Promotion decisions reference package identifiers.
- Evaluation results reference the exact package versions used.

This preserves the evidentiary chain from production observation to replay,
evaluation, approval, and promotion.

## Replay Package Storage Concepts

Storage design remains deferred, but replay package storage should preserve
immutability, discoverability, and durability.

Future storage concepts may include:

- One package directory per run.
- Manifest file plus evidence files.
- JSONL event stream.
- Structured JSON snapshots.
- Raw evidence references.
- Content-addressed artifacts.
- Read-only finalized packages.
- Retention policy.
- Package index for discovery.
- Separation between production evidence and experimental outputs.

Storage should avoid mixing mutable evaluation artifacts into immutable
production evidence packages.

## Replay vs Simulation

Replay reconstructs decisions from captured production evidence.

Simulation explores hypothetical behavior under assumptions that may not have
occurred in production.

Replay should answer:

- What happened?
- What did production know?
- What would another version have decided under the same captured facts?

Simulation may answer:

- What might happen under alternate fills, costs, prices, or market paths?
- What could happen under hypothetical portfolio states?
- How sensitive is a candidate to assumptions?

Simulation can support evaluation, but simulation assumptions must be explicit
and must not be confused with replay evidence.

## Replay Package Authority Limitations

A replay package is evidence, not authority.

A replay package must not:

- Mutate production state.
- Change strategy code.
- Change parameters.
- Approve execution.
- Create broker-facing orders.
- Sell, trim, or rebalance positions.
- Promote candidates automatically.
- Override risk governance.
- Replace human or governed approval.

Replay packages inform evaluation. They do not authorize production behavior.

## Relationship Between Replay, Evaluation, Promotion, and Production

The future relationship should remain:

1. Production runtime generates deterministic decisions and records replay
   packages.
2. Replay systems reconstruct historical or recorded decision windows from
   packages.
3. Evaluation systems compare current production behavior with candidate
   behavior across package sets.
4. Governance reviews evidence and decides whether to approve a change.
5. Promotion moves an approved version into production through a controlled
   path.
6. Production runtime runs only approved promoted versions.

This chain keeps production deterministic while allowing the system to improve
through evidence.

## Deferred Implementation Boundaries

This document does not approve implementation.

Deferred areas include:

- Replay package schema implementation.
- Replay package writer.
- Replay package storage.
- Replay runner.
- Snapshot capture tooling.
- Broker-visible state capture beyond currently approved visibility.
- Lifecycle-state capture tooling.
- Package integrity validation.
- Evaluation engine.
- Simulation engine.
- Promotion tooling.
- AI-assisted replay analysis.
- Any production mutation based on replay output.

Future implementation should begin only after a phase explicitly approves
scope, data contracts, authority boundaries, storage requirements, audit
requirements, and operational controls.

Until then, this specification defines the minimum evidence model that future
replay and evaluation infrastructure should satisfy before it can support
deterministic replay-grade reconstruction.
