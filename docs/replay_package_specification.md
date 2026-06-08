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

## Replay Package Prerequisite Rebase

The current replay package state is parked and non-authoritative.

Current state:

- The source-controlled replay fixture remains an `EVENT_STREAM_REPLAY_FIXTURE`:
  event-only, incomplete, evidence-only, non-authoritative, and not a complete
  replay package.
- The current mapper is an in-memory scaffold only and accepts already-loaded
  dictionaries only.
- The event stream `run_id` is canonical only inside current in-memory mapper
  behavior. That mapper behavior is not a source-controlled immutable replay
  package.
- Mapper completeness is not equivalent to a complete replay package.

Existing replay package contracts already cover:

- Package identity.
- Code and version metadata.
- Configuration metadata.
- Market input.
- Strategy input.
- Portfolio state.
- Broker-visible state.
- Reconciliation and risk evidence.
- Event ordering.
- Terminal completion requirements.
- Strict `run_id` alignment.
- JSONL as the source of truth.
- Reports and state files as derived summaries.
- As-of feature availability as a prerequisite.
- Replay, evaluation, and promotion authority boundaries.

Missing prerequisites before complete replay packages:

- Replay package schema implementation gate.
- Package writer and exact package layout.
- File ingestion rules, if any.
- Runtime capture or snapshot capture gate.
- Storage and immutability governance.
- Hashing, manifest, integrity validation, and correction or annotation rules.
- Absent or not-applicable completeness semantics.
- Provenance rules for every package section.
- Redaction and sanitization rules for broker or account-sensitive facts.
- Portfolio/risk state contract implementation.
- Broker-visible state capture contract if broker observations are used.
- As-of eligibility checks for market data and derived features.
- Attribution framework and metric definitions.
- Evaluation tooling gate.
- Promotion workflow gate.

Current replay package outputs cannot authorize strategy evaluation, strategy
promotion, runtime capture, artifact writer implementation, storage, broker/API
work, live trading, production behavior changes, execution permission, broker
authority, or strategy/risk behavior changes.

## Runtime Capture Prerequisite Contract

Runtime capture planning remains governance-only. This contract does not approve
runtime capture implementation, replay package creation, artifact copying, file
ingestion, writer behavior, storage implementation, hashing or manifest
implementation, evaluation, attribution, promotion, broker work, or live
trading.

Current runtime artifacts are operational outputs only:

- JSONL event stream.
- `last_run_report.json`.
- `order_state.json`.
- Observations.
- Runtime visibility metadata, when present.

The JSONL event stream remains the canonical source of truth for event
chronology and `run_id` alignment. `last_run_report.json`, `order_state.json`,
observations, and runtime visibility metadata remain derived summaries or
separate evidence.

Runtime capture must not:

- Mutate runtime state.
- Call `main.py`.
- Call broker/API/TWS/Alpaca/IBKR.
- Create execution permission.
- Promote strategies.
- Authorize live trading.

Required future capture scope:

- Exact artifact list.
- Exact source paths or source references.
- Target package layout.
- Allowed source classifications.
- Required absent or not-applicable declarations.
- `run_id` alignment rules.
- Terminal completion requirement.
- Report, state, observation, and runtime visibility alignment rules.
- Source commit and runtime version capture.
- Capture timestamp.
- Decision timestamp where decision-relevant.
- As-of eligibility where feature or input data is used.
- Provenance per section.
- Redaction and sanitization status per section.
- Manifest, hash, and integrity prerequisites.
- Storage and immutability prerequisites.
- Operator evidence requirements.

Required future complete package artifact set:

- Aligned JSONL events.
- Terminal completion event.
- Aligned `last_run_report.json`.
- Aligned or explicitly absent `order_state.json`.
- Run-filtered observations, if present.
- Runtime visibility evidence, if enabled, or explicit absent or not-applicable
  status.
- Configuration and code metadata.
- Market input evidence.
- Strategy input and output evidence.
- Portfolio and risk state evidence.
- Broker-visible state evidence, if used.
- Reconciliation and risk evidence.
- Manifest and integrity evidence once implemented.
- Redaction and provenance evidence once implemented.

Future runtime capture stop conditions:

- Mixed `run_id`.
- Missing terminal completion.
- Stale or post-decision decision-relevant state.
- Missing provenance.
- Missing source path or source reference.
- Missing redaction status.
- Sensitive data exposure.
- Unknown package authority.
- Implied evaluation or promotion authority.
- Missing as-of eligibility for decision-relevant inputs.
- Ambiguous runtime visibility state.
- Broker-visible state mistaken for broker authority.
- Missing absent or not-applicable declaration.
- Hash or manifest mismatch once hashing exists.

Current outputs cannot authorize replay package completeness, evaluation,
attribution, promotion, runtime capture implementation, writer behavior,
storage, broker/API/TWS/IBKR/Alpaca work, execution permission, strategy or
risk behavior changes, or live trading.

## Observability and Reporting Alignment Rebase

Current observability and reporting artifacts remain operational evidence, not
replay package authority.

Source-of-truth boundary:

- JSONL event streams are canonical for event chronology and `run_id`
  alignment.
- `last_run_report.json` is a derived operational summary and cannot be used
  alone as source-of-truth evidence.
- `order_state.json` is separate operational state evidence and cannot be used
  alone as source-of-truth evidence.
- Observations are separate append-only evidence and require `run_id` filtering
  before replay package use.
- Runtime visibility metadata is observed-only readiness evidence. It does not
  create execution permission, submit readiness, cleanup authority, broker
  routing authority, or live trading authority.

Settle-capture evidence for operational classification must include:

- Expected `HEAD`.
- Clean worktree.
- Root filesystem read-write status.
- Timer active after restore.
- Service inactive after settle.
- Latest JSONL identified.
- Latest JSONL terminal event inspected.
- `last_run_report.json` `run_id` matched to latest JSONL `run_id`.
- Terminal `stage`, `status`, and `reason` inspected.

`last_run_report.json` cannot classify a run without matching the latest JSONL
`run_id`. Stale report or stale JSONL evidence must be explicitly classified
and cannot close a deploy gate.

Expected safe terminal reasons depend on market-session state and may include:

- `market_holiday_or_closed_day`.
- `before_regular_session_open`.
- `after_regular_session_close`.
- Other explicitly approved market-session guard reasons.

Closed-day block and pre-market block are both expected safe blocked
classifications when they are consistent with market-session context.

Current report, state, observation, and runtime visibility outputs cannot
authorize replay package completeness, evaluation, attribution, promotion,
runtime capture implementation, writer behavior, storage,
broker/API/TWS/IBKR/Alpaca work, execution permission, strategy or risk
behavior changes, cleanup, flatten, sell, cancel, remediation, or live trading.

Future complete replay packages still require implemented section schemas for
report, state, observation, and runtime visibility evidence; absent and
not-applicable semantics; provenance; redaction; hashing, manifest, and
integrity; storage and immutability; as-of eligibility; and package layout.

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

Portfolio/risk state planning remains governance-only. Current production risk
behavior remains hard-cap enforcement through reconciliation and risk checks.
Broker-visible state is evidence only and does not create execution permission.

State classifications must remain distinct:

- Internal intended state: OpenClaw's local or proposed portfolio facts before
  broker reconciliation.
- Broker-observed state: observed broker facts such as positions, open orders,
  buying power, fills, errors, and freshness.
- Reconciled composite state: the explicit result of reconciling internal and
  broker-observed evidence under approved rules.
- Risk state: configured limits, evaluated values, risk decisions, and reasons.
- Execution permission: downstream approval to proceed toward broker-facing
  activity after all required gates pass.
- Broker execution: actual broker-facing order activity.

Required future state fields include:

- Schema version.
- Source classification.
- Symbol universe.
- Portfolio snapshot timestamp.
- Decision timestamp.
- As-of eligibility timestamp.
- Position quantity.
- Position side.
- Market value or exposure value when available.
- Existing position quantity.
- Open order quantity.
- Projected position quantity.
- Maximum position size.
- Remaining capacity.
- Saturation state.
- Cash or buying power when decision-relevant.
- Broker observation timestamp.
- Broker observation freshness.
- Reconciliation status.
- Ambiguity and manual-review flags.
- Terminal risk decision.

Required exposure definitions:

- Symbol exposure.
- Projected exposure.
- Portfolio exposure.
- Strategy exposure.
- Regime exposure.
- Sector or factor exposure, if later introduced.
- Gross and net exposure, if later introduced.
- Liquidity-adjusted exposure, if later introduced.
- Risk-budget usage, if later introduced.

Timestamp and as-of rules:

- Portfolio state must be proven pre-decision before use.
- Broker-visible state must include observation timestamp and freshness.
- Stale, unknown, ambiguous, or post-decision state must fail closed.
- Mixed-timestamp state must be explicitly classified and cannot silently become
  authoritative.

Provenance rules:

- Every portfolio/risk field needs source identity.
- Every broker-visible field needs broker or source observation metadata.
- Every derived field needs transformation and version metadata.
- Every decision-relevant field needs as-of eligibility evidence.

Absent and not-applicable semantics:

- Missing state must be explicit.
- Not-applicable state must be explicit.
- Absent sections cannot be treated as zero unless a future rule explicitly
  allows it.

Authority boundaries:

- Signal demand is not allocation approval.
- Allocation intent is not risk approval.
- Risk approval is not broker execution.
- Reconciliation evidence is not execution permission.
- Broker-visible observation is not cleanup, flatten, sell, or remediation
  authority.
- Evaluation evidence is not strategy promotion.

Future portfolio construction, allocation arbitration, dynamic sizing, trim,
exit, rebalance, hedge, short, and adaptive optimization require separate
gates. This contract does not approve replay package creation, runtime capture,
portfolio state capture implementation, allocation logic, risk behavior
changes, execution behavior changes, broker work, or live trading.

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

## Storage/Immutability Governance Contract

Storage and immutability planning remains governance-only. This contract does
not approve package creation, artifact copying, file ingestion, writer
behavior, runtime capture, storage implementation, hashing implementation,
manifest implementation, evaluation, promotion, broker work, or live trading.

Replay packages must eventually be immutable evidence artifacts, not mutable
evaluation outputs. Immutable production evidence must be separated from
mutable evaluation outputs, reports, comparisons, and recommendations. Original
facts must not be rewritten. Corrections, annotations, invalidations, and
reviewer notes must be appended as separate records.

Required future package identity and path convention:

- One package directory per canonical `run_id` or explicitly governed
  `package_id`.
- Deterministic package layout.
- Explicit package status such as `draft`, `finalized`, `invalidated`, or
  `superseded`.

Required future manifest fields:

- `package_id`.
- Canonical `run_id`.
- Schema version.
- `created_at` timestamp.
- Source commit.
- Source artifact references.
- Section list.
- Section status.
- Section hashes.
- Completeness status.
- Authority boundary.
- Redaction status.
- Correction and annotation references.

Required hashing and integrity rules:

- Content hash algorithm must be specified before implementation.
- Section-level hashes are required.
- Manifest hash is required.
- Hash mismatch must fail closed.
- Mixed `run_id` evidence must fail closed.
- Missing provenance must fail closed.
- Unclear source path must fail closed.

Required provenance rules:

- Every package section needs source artifact identity.
- Every package section needs a source path or source reference.
- Captured sections need a capture timestamp.
- Decision-relevant sections need a decision timestamp.
- Feature or input data needs as-of eligibility evidence.
- Source commit or runtime version is required where applicable.

Required redaction and sanitization rules:

- Raw credentials and secrets must never be stored.
- Broker/account-sensitive identifiers require explicit safe handling.
- Account identifiers may be stored only if governance marks them safe or
  redacted.
- Redaction must preserve audit usefulness without leaking secrets.

Required retention, discovery, and index policy:

- Finalized package retention rule.
- Invalidated package retention rule.
- Package discovery or index rule.
- Distinction between retained evidence and disposable evaluation artifacts.

Writer authority boundary:

- A future writer may write only approved package artifacts under an explicit
  gate.
- A writer cannot call broker/API/TWS/Alpaca/IBKR.
- A writer cannot call `main.py`.
- A writer cannot mutate runtime state.
- A writer cannot promote strategies or create execution permission.

## Replay Writer Authority Contract

Replay writer planning remains governance-only. This contract does not approve
replay writer implementation, replay package creation, file ingestion, runtime
capture, storage implementation, hashing or manifest implementation,
evaluation, attribution, promotion, broker work, or live trading.

A future writer may write only explicitly approved replay package artifacts
under a separate implementation gate. It may write only to approved package
output paths defined by a future package layout contract.

A future writer must not:

- Overwrite finalized package evidence.
- Mutate runtime state.
- Call `main.py`.
- Call broker/API/TWS/Alpaca/IBKR.
- Submit, cancel, flatten, sell, clean up, retry, remediate, or otherwise
  affect broker state.
- Create execution permission.
- Promote strategies.
- Create live trading authority.
- Treat derived reports, observations, runtime visibility, or broker-visible
  state as source-of-truth without explicit provenance and alignment rules.

Allowed future source inputs, subject to later gates:

- JSONL event streams.
- `last_run_report.json`, only as derived evidence matched to JSONL `run_id`.
- `order_state.json`, only as separate operational state evidence.
- Observations, only when run-filtered and provenance-tagged.
- Runtime visibility metadata, only as observed-only readiness evidence.
- Configuration and code metadata.
- Market input evidence.
- Strategy input and output evidence.
- Portfolio and risk state evidence.
- Broker-visible state evidence, if used, only as observed evidence and not
  broker authority.
- Reconciliation and risk evidence.

Required prerequisites before writer implementation:

- Exact package layout.
- Exact allowed output paths.
- Exact source artifact rules.
- Source path or source reference rules.
- File ingestion rules, if any.
- Package status lifecycle: `draft`, `finalized`, `invalidated`, and
  `superseded`.
- No-overwrite and finalization rules.
- Manifest shape and required fields.
- Section hash requirements.
- Package hash requirements.
- Provenance requirements.
- Redaction and sanitization requirements.
- Absent, not-applicable, disabled, unavailable, stale, redacted, untrusted,
  and unknown semantics.
- Correction and annotation rules.
- Retention and discovery or index policy.
- Storage and immutability gate.
- Runtime capture gate, if runtime artifacts are used.
- Evaluation and promotion gates, if output will later be evaluated.

Writer stop conditions:

- Unknown source path.
- Missing source reference.
- Missing provenance.
- Missing redaction status.
- Mixed `run_id`.
- Missing terminal completion.
- Stale report or stale JSONL.
- Runtime visibility ambiguity.
- Broker-visible state mistaken for broker authority.
- Sensitive data exposure.
- Attempted overwrite of finalized evidence.
- Unknown package authority.
- Implied evaluation authority.
- Implied promotion authority.
- Implied execution permission.
- Implied live trading authority.
- Hash or manifest mismatch once hashing exists.

Writer output remains evidence only. It cannot authorize complete replay
package status unless future schema, storage, and integrity gates define and
validate that status. It cannot authorize evaluation, attribution, promotion,
broker/API/TWS/IBKR/Alpaca work, execution permission, strategy or risk
behavior changes, cleanup, flatten, sell, cancel, remediation, or live trading.
Writer output cannot become runtime truth and cannot replace JSONL as canonical
event chronology.

## Replay Writer Implementation Scope Contract

Replay writer implementation scoping remains governance-only. This contract
does not approve implementation.

The first future implementation, if later approved, must be test-only or pure
in-memory only. It must not:

- Write to the filesystem.
- Create package directories.
- Create manifest files.
- Compute or enforce hashes.
- Implement storage, finalization, immutability, retention, or discovery.
- Read from runtime artifact paths directly.
- Implement file path ingestion.
- Call `main.py`.
- Call broker/API/TWS/Alpaca/IBKR.
- Mutate runtime state.
- Use `.env`.
- Create execution permission.
- Evaluate, attribute, promote, or approve strategies.
- Authorize live trading.

Smallest safe future implementation shape:

- Pure function only.
- Accepts already-loaded dictionaries or an existing `ReplayInputBundle` only.
- Returns a draft package dictionary or envelope only.
- Reuses existing schema constants and current `build_replay_package(...)`
  semantics where possible.
- Preserves event JSONL as canonical `run_id` chronology.
- Preserves evidence-only and non-authoritative flags.
- Preserves event-only fixture incompleteness.
- Preserves mapper scaffold completeness distinction from complete replay
  package authority.
- Does not alter existing mapper behavior unless a separate implementation gate
  explicitly approves it.

Future implementation test requirements:

- Prove no filesystem writes.
- Prove no package directories are created.
- Prove no file path ingestion.
- Prove no runtime capture.
- Prove input objects are not mutated.
- Prove output is draft, evidence-only, and non-authoritative.
- Prove writer, storage, runtime, hash, evaluation, and promotion remain out of
  scope.
- Prove event JSONL remains canonical for `run_id`.
- Prove event-only fixture remains incomplete.
- Prove no complete package status is inferred from mapper scaffold
  completeness.

Naming constraints:

- Avoid names that imply filesystem writer authority unless the module or test
  names explicitly include draft, scaffold, in-memory, or test-only semantics.
- Avoid names that imply package finalization, manifest generation, hashing,
  storage, capture, or evaluation.

Any future implementation gate must cite:

- Replay writer authority contract.
- Replay package layout, manifest, hash, and lifecycle contract.
- Runtime capture prerequisite contract.
- Mapper/schema governance rebase.
- Observability/reporting evidence alignment.
- Storage/immutability governance.
- Replay package authority limitations.

Implementation scope stop conditions:

- Need to write files.
- Need to read runtime paths.
- Need to create package directories.
- Need to create manifest files.
- Need to compute hashes.
- Need to inspect or mutate `.env`.
- Need to call `main.py`.
- Need to call broker/API/TWS/Alpaca/IBKR.
- Need to mutate runtime state.
- Need to change strategy, risk, or execution behavior.
- Need to classify output as a complete replay package.
- Need to evaluate, attribute, promote, or approve strategies.
- Need to imply execution permission or live trading authority.

Future in-memory draft output remains scaffold evidence only. It cannot
authorize replay package completeness, runtime capture, writer behavior,
storage, evaluation, attribution, promotion, broker work, execution permission,
strategy or risk changes, cleanup, flatten, sell, cancel, remediation, or live
trading. It cannot replace JSONL as canonical event chronology.

### Draft Envelope Source Module Closeout

The first draft envelope source-module phase is complete. The module
`tools/replay/draft_envelope.py` exists as a pure in-memory source module.
`build_draft_replay_envelope(...)` accepts only `ReplayInputBundle` or
already-loaded dictionaries, rejects path, string, and arbitrary object inputs,
calls the existing `build_replay_package(...)`, and returns draft envelope
evidence only.

The draft envelope module remains non-authoritative. It does not:

- Create replay packages.
- Write files.
- Create package directories.
- Ingest file paths.
- Generate manifests.
- Compute or enforce hashes.
- Capture runtime artifacts.
- Implement storage, finalization, immutability, retention, or discovery.
- Evaluate, attribute, promote, or approve strategies.
- Call broker/API/TWS/Alpaca/IBKR.
- Call `main.py`.
- Create execution permission.
- Authorize live trading.

Event JSONL remains canonical event chronology. Mapper scaffold `complete`
status remains distinct from complete replay package authority. Event-only
fixtures remain incomplete.

Remaining prerequisites before real replay package creation:

- Package layout implementation.
- Manifest schema and deterministic serialization.
- Section and package hashing.
- Integrity validation.
- Storage, finalization, and immutability.
- Retention, discovery, and indexing.
- Runtime capture gate.
- File ingestion rules, if any.
- Provenance and redaction enforcement.
- Absent and not-applicable semantics.
- Evaluation, attribution, and promotion gates.

Draft envelope output remains scaffold evidence only. It cannot authorize replay
package completeness, runtime capture, storage, evaluation, attribution,
promotion, broker work, execution permission, strategy or risk behavior changes,
cleanup, flatten, sell, cancel, remediation, or live trading.

## Replay Package Creation Authority Contract

Replay package creation authority remains governance-only and is not
implemented yet. This contract does not approve tests, code, package creation
constants, package builder types, package creation modules, package layout
constants, manifest generation, canonical byte generation, hash computation,
integrity validation, storage, finalization, runtime capture, evaluation,
broker work, execution permission, or live trading.

Replay package creation rules must be source-controlled before
implementation. No package builder, package constants, package types, package
creation module, package layout constant, package directory, package file,
manifest output, canonical byte output, hash output, integrity output, storage
output, runtime capture output, evaluation output, or promotion output is
authoritative until a separate implementation gate explicitly approves it.

Authority states remain distinct:

- Draft envelope.
- Mapper scaffold.
- Replay package.
- Complete replay package.
- Finalized immutable replay package.

Required future package layout and identity authority:

- Package layout authority must be explicitly governed before implementation.
- Package identity authority must be explicitly governed before
  implementation.
- `canonical_run_id` and governed `package_id` rules must remain distinct.
- A governed `package_id` must define whether it is derived from
  `canonical_run_id`, assigned independently, or created by another
  source-controlled rule.
- Package layout constants cannot be introduced before layout authority exists.
- Package directories and package paths cannot be introduced before package
  layout and storage path authority exist.
- Ambiguous package identity must fail closed.

Current `build_draft_replay_envelope(...)` output remains draft scaffold
evidence only. Current `build_replay_package(...)` mapper scaffold output may
indicate tracked in-memory bucket completeness, but it cannot create complete
replay package authority. Event JSONL remains canonical event chronology.
`last_run_report.json` remains a derived operational summary and cannot alone
create package authority. `order_state.json`, observations, and runtime
visibility remain separate evidence with provenance requirements.

Required future input authority:

- Already-loaded envelope dictionaries may remain draft-only evidence inputs,
  but they do not create package authority.
- Future manifest inputs require manifest generation authority before package
  creation can consume them as package-shaped output.
- Future source references require source-reference authority before package
  creation can consume them.
- Future approved source paths require source path authority before package
  creation can consume them.
- Future copied artifacts require artifact copying authority before package
  creation can consume them.
- Future runtime-captured artifacts require runtime capture authority before
  package creation can consume them.
- Path-like inputs, unreferenced files, unknown source paths, copied artifacts,
  and runtime-captured artifacts remain forbidden until separate gates approve
  those input models.

Required future lifecycle and completeness rules:

- The first future package-creation lifecycle state, if later approved, must be
  `draft` only.
- Draft-only package assembly, if later approved, must remain non-finalized and
  non-authoritative.
- Draft package creation must not imply finalized package authority.
- Draft package creation must not overwrite existing evidence.
- Current `build_replay_package(...)` `package_status == "complete"` remains
  mapper bucket completeness only and cannot create complete replay package
  authority.
- Complete replay package authority must require explicit package creation,
  manifest, serialization, integrity, and storage/finalization gates.

Required prerequisites before any package creation implementation:

- Source-controlled package creation rules.
- Exact package layout authority.
- Exact package identity authority.
- Exact approved output root and package path authority.
- Exact source artifact authority.
- Exact source reference authority.
- File path ingestion authority, if any.
- Manifest schema authority.
- Manifest generation authority before package creation can produce
  manifest-shaped package output.
- Deterministic serialization authority before package creation can rely on
  canonical bytes.
- Canonical byte authority before package creation can rely on canonical byte
  output.
- Hashing and integrity validation before package creation can claim
  integrity.
- Storage and finalization authority before package creation can persist
  finalized packages.
- Runtime capture authority before package creation can use live runtime
  artifacts.
- Section status semantics.
- Section hash rules.
- Package or manifest hash rules.
- Integrity validation rules.
- Provenance requirements.
- Redaction and sanitization requirements.
- Absent, not-applicable, disabled, unavailable, stale, redacted, untrusted,
  and unknown semantics.
- Correction, annotation, invalidation, and supersession rules.
- No-overwrite and finalization rules.
- Retention, discovery, and index policy.
- Evaluation, attribution, and promotion gates if output will later be
  evaluated.

Allowed future source inputs, subject to later gates:

- JSONL event stream references.
- Already-loaded event dictionaries.
- `last_run_report.json`, only as derived evidence matched to JSONL `run_id`.
- `order_state.json`, only as separate operational state evidence with
  provenance.
- Observations, only when run-filtered and provenance-tagged.
- Runtime visibility metadata, only as observed-only readiness evidence.
- Configuration and code metadata.
- Market input evidence.
- Strategy input and output evidence.
- Portfolio and risk state evidence.
- Broker-visible state evidence, only as observed evidence and not broker
  authority.
- Reconciliation and risk evidence.

Required future evidence and fail-closed rules:

- Provenance must be explicit before package creation.
- Redaction status must be explicit before package creation.
- Source-reference authority must be explicit before package creation.
- Runtime terminal completion requirements must be explicit before
  runtime-derived package inputs are accepted.
- Missing `run_id` must fail closed.
- Mixed `run_id` must fail closed.
- Stale artifacts must fail closed.
- Malformed artifacts must fail closed.
- Missing terminal completion must fail closed for runtime-derived package
  inputs.
- Missing provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Unknown source references must fail closed.
- Sensitive data exposure must stop package creation, manifest generation,
  hashing, integrity validation, storage, indexing, runtime capture,
  evaluation, and finalization.
- Ambiguous package identity must fail closed.

Forbidden or untrusted without later gates:

- Unreferenced files.
- Unknown source paths.
- Mixed `run_id` sources.
- Stale reports.
- Stale JSONL.
- Missing terminal completion.
- Missing provenance.
- Missing redaction status.
- Runtime visibility ambiguity.
- Broker-visible state treated as broker authority.
- Any source implying execution permission.
- Any source implying live trading authority.

Package creation execution boundaries:

- Package creation must remain separate from runtime capture.
- Package creation must remain separate from storage and finalization.
- Package creation must remain separate from evaluation and promotion.
- Package creation must not mutate runtime state.
- Package creation must not call `main.py`.
- Package creation must not stop or start timers.
- Package creation must not call broker/API/TWS/Alpaca/IBKR.
- Package creation must not respond to or remediate blocked buy/sell signals.
- Package creation must not submit, cancel, flatten, sell, cleanup, retry,
  remediate, or otherwise affect broker state.
- Package creation must not approve live trading.

Package creation stop conditions:

- Need package creation constants.
- Need package builder types.
- Need package creation modules.
- Need package layout constants.
- Need to write package files before output-path authority exists.
- Need to create package directories before layout authority exists.
- Need to ingest file paths before file-ingestion rules exist.
- Need to generate manifests before manifest schema exists.
- Need canonical byte generation.
- Need to compute hashes before hash and integrity rules exist.
- Need integrity validation.
- Need to finalize packages before storage and finalization rules exist.
- Need to capture runtime artifacts before a runtime capture gate exists.
- Need to evaluate, attribute, or promote strategies before evaluation and
  promotion gates exist.
- Missing source-controlled package creation rules.
- Missing package layout authority.
- Missing package identity authority.
- Missing canonical `run_id`.
- Missing `run_id`.
- Missing governed `package_id` when package identity requires one.
- Mixed `run_id`.
- Missing terminal completion.
- Stale artifact.
- Malformed artifact.
- Missing source reference authority.
- Unknown source reference.
- Missing provenance.
- Missing redaction status.
- Invalid redaction status.
- Ambiguous package identity.
- Sensitive data exposure.
- Implied manifest authority.
- Implied package completeness.
- Implied hash or integrity authority.
- Implied storage or finalization authority.
- Implied runtime capture authority.
- Implied evaluation or promotion authority.
- Implied broker authority.
- Implied execution permission.
- Implied live trading authority.

Replay package creation cannot authorize manifest authority, manifest
generation, canonical byte generation, hash computation, integrity validation,
package completeness, complete replay package status, finalized immutable
replay package status, storage, finalization, runtime capture, evaluation,
attribution, promotion, broker work, execution permission, strategy or risk
behavior changes, cleanup, flatten, sell, cancel, remediation, or live trading.
`build_draft_replay_envelope(...)` remains draft scaffold evidence only.
`build_replay_package(...)` mapper scaffold completeness remains distinct from
complete replay package authority. Package creation output cannot become
manifest truth, package completeness truth, hash truth, storage truth,
finalization truth, runtime capture truth, evaluation truth, promotion truth,
broker truth, execution permission, or live trading authority.

## Replay Package Layout, Manifest, Hash, and Lifecycle Contract

Package layout, manifest, hash, integrity, finalization, and lifecycle planning
remains governance-only. This contract does not approve package layout
implementation, manifest implementation, hashing implementation, integrity
validation implementation, writer behavior, package creation, file ingestion,
runtime capture, storage implementation, evaluation, attribution, promotion,
broker work, or live trading. Complete replay package authority requires future
implementation gates and validation.

Package identity and layout governance:

- Future packages require either a canonical `run_id` or an explicitly governed
  `package_id`.
- One package directory is required per canonical `run_id` or governed
  `package_id`.
- Deterministic package layout is required before implementation.
- Exact future output root and approved package paths must be defined before
  implementation.
- Exact file names and section layout must be defined before implementation.
- Package layout must separate immutable evidence artifacts from mutable
  evaluation outputs.

Required future package lifecycle states:

- `draft`.
- `finalized`.
- `invalidated`.
- `superseded`.

Lifecycle rules:

- Draft packages may be incomplete and non-authoritative.
- Finalized packages must be immutable evidence artifacts.
- Finalized packages must not be overwritten.
- Invalidated packages must remain retained with invalidation metadata.
- Superseded packages must remain retained with supersession references.
- Corrections, annotations, invalidations, and reviewer notes must be
  append-only records.
- Original facts must not be rewritten.

Manifest governance:

- Future manifest schema must be defined before implementation.
- Future manifest must include `package_id`, canonical `run_id`, package schema
  version, package lifecycle status, `created_at` timestamp, source commit,
  source runtime version when available, source artifact references, section
  list, section status, section hashes, package or manifest hash, completeness
  status, authority boundary, redaction status, provenance summary, and
  correction, annotation, invalidation, or supersession references.
- Manifest serialization must be deterministic before hash enforcement.
- Manifest cannot be used as authority until manifest schema, hash rules, and
  validation rules are implemented.

Hash and integrity governance:

- Content hash algorithm must be explicitly chosen before implementation.
- Canonical serialization rules must be defined before hash enforcement.
- Section-level hashes are required before package completeness can be
  authoritative.
- Manifest or package-level hash relationship must be defined before
  implementation.
- Hash mismatch must fail closed once hashing exists.
- Missing section hash must fail closed once hashing exists.
- Mixed `run_id` must fail closed.
- Missing provenance must fail closed.
- Unknown source path or source reference must fail closed.
- Unclear redaction status must fail closed.

Section completeness governance:

- Future complete package section requirements must be explicit.
- Absent, not-applicable, disabled, unavailable, stale, redacted, untrusted, and
  unknown states must be governed before package authority.
- Current event-only fixture and mapper scaffold completeness remain
  insufficient for complete replay package authority.
- Complete package status cannot be inferred from presence of files alone.
- Complete package status cannot be inferred from `last_run_report.json` alone.
- Complete package status cannot be inferred from mapper scaffold complete
  status alone.

Retention, discovery, and index governance:

- Finalized packages require retention rules before implementation.
- Invalidated and superseded packages require retention rules before
  implementation.
- Discovery or index format must be defined before implementation.
- Retained immutable evidence must be separated from disposable evaluation
  artifacts.

Layout, manifest, hash, and lifecycle stop conditions:

- Missing canonical `run_id` or `package_id`.
- Mixed `run_id`.
- Missing terminal completion.
- Missing source artifact reference.
- Unknown source path.
- Missing provenance.
- Missing redaction status.
- Sensitive data exposure.
- Attempted overwrite of finalized evidence.
- Missing lifecycle status.
- Unknown package authority.
- Missing manifest field once manifest exists.
- Missing section hash once hashing exists.
- Hash or manifest mismatch once hashing exists.
- Non-deterministic serialization discovered.
- Implied evaluation authority.
- Implied promotion authority.
- Implied execution permission.
- Implied broker authority.
- Implied live trading authority.

This contract cannot authorize replay package creation, writer implementation,
file ingestion, runtime capture, storage implementation, evaluation,
attribution, promotion, broker work, execution permission, strategy or risk
behavior changes, cleanup, flatten, sell, cancel, remediation, or live trading.
JSONL remains canonical event chronology until a future governed package can
reference it as immutable evidence. Package artifacts cannot replace JSONL as
canonical event chronology unless explicitly approved by future governance.

Runtime capture prerequisites:

- Storage and immutability contract.
- Manifest and hash contract.
- Provenance and redaction contract.
- Package layout contract.
- Stop conditions.
- Evidence classification rules.

Stop conditions:

- Sensitive data exposure.
- Missing provenance.
- Hash mismatch.
- Mixed `run_id`.
- Unclear source path.
- Unknown package authority.
- Implied evaluation or promotion authority.
- Missing redaction status.
- Missing as-of eligibility for decision-relevant features.

## Manifest Schema Authority Contract

Manifest schema authority remains governance-only and is not implemented yet.
This contract does not approve tests, code, manifest constants, manifest schema
types, manifest builder code, manifest generation, package creation,
deterministic serialization, hashing, storage, runtime capture, evaluation,
broker work, execution permission, or live trading.

Manifest schema vocabulary must be source-controlled before use. Required,
optional, placeholder, and future-only fields must be explicitly separated
before implementation. A manifest schema may define vocabulary and field
requirements only; it must remain separate from manifest generation, package
creation, deterministic serialization, hashing/integrity enforcement, storage,
runtime capture, evaluation, and broker authority. Manifest schema must also
remain separate from mapper completeness: current `build_replay_package(...)`
`package_status == "complete"` is only in-memory bucket completeness and cannot
be treated as complete replay package authority.

Required future field-group authority:

- Identity fields must include `canonical_run_id`, `package_id`,
  `package_schema_version`, and `manifest_schema_version`.
- `canonical_run_id` is required before any manifest can claim run alignment.
- `package_id` may remain a governed placeholder for draft manifests until
  future package identity rules define whether it is derived from
  `canonical_run_id` or assigned separately.
- Schema version fields must be stable, explicit, and source-controlled before
  use.
- Lifecycle fields must include `lifecycle_status`, `lifecycle_reason`, and
  `created_at`.
- `finalized_at`, `invalidated_at`, `superseded_by`, and supersession or
  invalidation status fields remain future-only until storage/finalization and
  immutability gates approve those lifecycle states.
- Source control and generator provenance fields must include `source_commit`,
  `source_branch` when known, `source_runtime_version` when available,
  `generator_name`, `generator_version`, and
  `generator_authority_boundary`.
- Source artifact fields must include `source_artifact_references`,
  `source_artifact_type`, `source_artifact_path_or_reference`,
  `source_artifact_run_id`, `source_artifact_timestamp`,
  `source_artifact_provenance`, and `source_artifact_redaction_status`.
- Source artifact path or reference fields require explicit source reference
  authority and cannot approve file path ingestion by themselves.
- Section fields must include deterministic `section_id`, `section_type`,
  `section_status`, `section_authority`, `section_source_reference`,
  `section_run_id`, `section_provenance`, `section_redaction_status`, and
  `section_hash` as a placeholder only until hashing is approved.
- Completeness fields must include `completeness_status`,
  `completeness_reason`, `missing_sections`, `not_applicable_sections`,
  `unavailable_sections`, `stale_sections`, and `untrusted_sections`.
- Integrity fields such as `hash_algorithm`, `section_hashes`,
  `manifest_hash`, `package_hash`, and `integrity_status` remain placeholders
  until hashing/integrity implementation is separately approved.
- Authority-boundary fields must include `evidence_only`,
  `non_authoritative`, `complete_replay_package_authority`,
  `finalized_immutable_replay_package_authority`,
  `replay_based_evaluation_authority`,
  `replay_based_promotion_authority`, `broker_api_authority`,
  `execution_permission`, and `live_trading_authority`.
- Correction and lineage fields must include `annotations`, `corrections`,
  `invalidation_references`, `supersession_references`, and `reviewer_notes`.

Draft-only lifecycle behavior:

- The first allowed future lifecycle status must be `draft` only.
- Draft schema fields must not imply finalized package authority.
- Draft manifests are non-authoritative.
- Draft manifests cannot imply complete replay package authority.
- Draft manifests cannot imply finalized immutable replay package authority.
- `finalized`, `invalidated`, and `superseded` remain future-only lifecycle
  states until storage/finalization and immutability gates are approved.
- Corrections, annotations, invalidations, and supersessions must preserve
  original facts and must not silently mutate finalized evidence.

Future section status vocabulary must distinguish:

- `present`.
- `absent`.
- `not_applicable`.
- `disabled`.
- `unavailable`.
- `stale`.
- `redacted`.
- `untrusted`.
- `malformed`.
- `invalidated`.
- `unknown`.
- Any future or placeholder state explicitly approved by a later governance
  gate.

Section status rules:

- `absent` and `not_applicable` must remain distinct.
- `redacted` must preserve explicit redaction status without leaking sensitive
  content.
- `present` cannot imply authority unless provenance, redaction status,
  source reference authority, and `run_id` alignment are valid.
- `stale`, `untrusted`, `malformed`, mixed-`run_id`, missing provenance,
  missing redaction status, unknown source references, and `unknown` section
  status must fail closed.
- Invalidated section or package state must preserve lineage and cannot erase
  or rewrite original facts.

Provenance and redaction requirements:

- Provenance fields are required for every source artifact and every section
  before authoritative package use.
- Redaction status is required for every source artifact and every section
  before capture, storage, indexing, package creation, or authoritative use.
- Missing provenance must fail closed.
- Missing redaction status must fail closed.
- Sensitive data exposure must stop manifest generation, package creation,
  storage, indexing, runtime capture, evaluation, and finalization.

Deterministic serialization is required before manifest hashing or manifest
authority. Future serialization rules must define canonical key ordering,
timestamp format, null versus absent semantics, numeric precision, string
encoding, list ordering, nested object ordering, whitespace policy, stable
schema versioning, and deterministic treatment of unavailable,
not-applicable, redacted, unknown, malformed, stale, and untrusted fields.

Manifest schema cannot authorize replay package creation, complete replay
package status, finalized immutable replay package status, runtime capture,
storage, finalization, hashing or integrity enforcement, evaluation,
attribution, promotion, broker work, execution permission, strategy or risk
behavior changes, cleanup, flatten, sell, cancel, remediation, or live trading.
Event JSONL remains canonical chronology. `last_run_report.json` remains a
derived operational summary and cannot alone create package or manifest
authority. `build_draft_replay_envelope(...)` remains draft scaffold evidence
only. `build_replay_package(...)` mapper scaffold completeness remains distinct
from complete replay package authority.

Manifest schema stop conditions:

- Need to implement manifest constants.
- Need to implement manifest schema types.
- Need to implement a manifest object builder.
- Need to generate manifests.
- Need deterministic serialization implementation.
- Need hashing or integrity validation.
- Need package creation.
- Need filesystem reads or writes.
- Need file path ingestion.
- Need package directories.
- Need runtime capture.
- Need storage, finalization, or immutability.
- Need retention, discovery, or index behavior.
- Need evaluation, attribution, experiment registry, or promotion.
- Need broker/API/TWS/Alpaca/IBKR.
- Need `main.py`.
- Missing source-controlled schema vocabulary.
- Missing required versus optional or future-only field separation.
- Missing canonical `run_id`.
- Mixed `run_id`.
- Missing terminal completion.
- Missing source reference authority.
- Missing provenance.
- Missing redaction status.
- Unknown source reference.
- Unknown section status.
- Stale, untrusted, malformed, or invalidated evidence without governed
  lineage handling.
- Sensitive data exposure.
- Implied package creation authority.
- Implied manifest generation authority.
- Implied complete replay package authority.
- Implied broker authority.
- Implied execution permission.
- Implied live trading authority.

## Deterministic Serialization Authority Contract

Deterministic serialization authority remains governance-only and is not
implemented yet. This contract does not approve tests, code, serializer
constants, serialization types, canonical serializer code, canonical byte
generation, manifest serialization, package serialization, hashing or integrity
enforcement, storage, finalization, runtime capture, package creation,
evaluation, broker work, execution permission, or live trading.

Serialization rules must be source-controlled before implementation. Serializer
input eligibility must be explicitly governed before implementation.
Serialization input must not imply manifest generation, package creation,
hashing, storage, runtime capture, evaluation, broker authority, execution
permission, or live trading. Serialization output remains non-authoritative
until manifest schema, hashing/integrity, storage, and finalization gates are
separately approved and validated.

Canonical JSON scope:

- The future canonical format must be JSON unless a later governance gate
  explicitly approves another canonical format.
- The canonical JSON scope must define whether the input is a manifest-shaped
  dictionary, a package-shaped dictionary, a section dictionary, metadata only,
  or another explicitly governed object.
- Manifest schema vocabulary must exist before any serializer can claim
  manifest serialization semantics.
- Serialization cannot generate a manifest, create a package, compute a hash,
  validate integrity, write storage, capture runtime artifacts, evaluate
  strategy output, or create broker/execution/live-trading authority.

Required future ordering rules:

- Object keys must use deterministic canonical ordering.
- Recursive object ordering must apply the same deterministic ordering to
  nested dictionaries.
- Field ordering must be governed by the canonical object-key rule or by an
  explicitly source-controlled schema order before implementation.
- List ordering rules must distinguish chronology-preserving lists from
  lexicographically sortable metadata lists.
- Event JSONL chronology and other evidence-order-preserving lists must not be
  accidentally sorted.
- Metadata lists may be sorted only when their sorting keys and tie-breakers are
  source-controlled.
- Non-deterministic ordering must fail closed.

Required future byte and text rules:

- Serialization must produce stable bytes from semantically identical inputs.
- String encoding must be UTF-8.
- Whitespace policy must be minimal and deterministic.
- Newline policy must be explicit and stable.
- String escaping policy must be deterministic.
- Unsupported string encodings must fail closed.
- Sensitive or redacted fields must not leak original sensitive content through
  escaped strings, metadata, placeholders, or error messages.

Required future primitive value rules:

- Number handling must be explicit.
- Decimal handling must be explicit.
- Ambiguous floats must fail closed unless separately governed.
- Boolean handling must be deterministic.
- `null`, absent fields, and `not_applicable` must remain distinct.
- Absent-field handling must be explicit.
- `not_applicable` handling must be explicit.
- Redacted-field handling must preserve redaction status without leaking
  original sensitive content.
- Unsupported value types must fail closed.
- Non-deterministic objects must fail closed.

Required future status and section serialization rules:

- `present` must require provenance, redaction status, source reference
  authority, and `run_id` alignment before authoritative use.
- `absent` and `not_applicable` must remain distinguishable.
- `disabled` must remain distinguishable from `absent`.
- `unavailable` must remain distinguishable from `unknown`.
- `redacted` must serialize only redaction-safe content and explicit redaction
  status.
- `stale`, `malformed`, `untrusted`, and `invalidated` sections may serialize
  only under governed status semantics and must fail closed for authoritative
  use.
- `unknown` section status must fail closed.
- Missing provenance must fail closed.
- Missing redaction status must fail closed.

Required future timestamp rules:

- Timestamps must be normalized to UTC.
- Timestamp format must be ISO-8601/RFC3339-compatible.
- Timestamp precision must be explicit and fixed before implementation.
- Timezone offsets must be normalized.
- `timestamp_utc` remains canonical for event chronology when available.
- Ambiguous, missing, non-UTC, or unsupported timestamp formats must fail
  closed when timestamp authority is required.

Hashing boundary:

- Serialization may be a prerequisite for hashing, but this contract does not
  approve hashing.
- Future hashing may use only canonical serialized bytes approved by a later
  implementation gate.
- Hash algorithm selection remains a later authority gate.
- Section hash rules remain future-only.
- Manifest hash rules remain future-only.
- Package hash rules remain future-only.
- Integrity validation remains future-only.

Deterministic serialization cannot authorize manifest authority, manifest
generation, replay package creation, complete replay package status, finalized
immutable replay package status, hashing or integrity enforcement, storage,
finalization, runtime capture, evaluation, attribution, promotion, broker work,
execution permission, strategy or risk behavior changes, cleanup, flatten,
sell, cancel, remediation, or live trading. Event JSONL remains canonical
chronology. `last_run_report.json` remains a derived operational summary and
cannot alone create serialization, manifest, package, or hash authority.
`build_draft_replay_envelope(...)` remains draft scaffold evidence only.
`build_replay_package(...)` mapper scaffold completeness remains distinct from
complete replay package authority.

Deterministic serialization stop conditions:

- Need to implement serialization constants.
- Need to implement serialization types.
- Need to implement canonical serializer code.
- Need canonical byte generation.
- Need manifest serialization.
- Need package serialization.
- Need manifest generation.
- Need to compute hashes.
- Need integrity validation.
- Need package creation.
- Need filesystem reads or writes.
- Need file path ingestion.
- Need package directories.
- Need runtime capture.
- Need storage, finalization, or immutability.
- Need retention, discovery, or index behavior.
- Need evaluation, attribution, experiment registry, or promotion.
- Need broker/API/TWS/Alpaca/IBKR.
- Need `main.py`.
- Missing manifest schema authority.
- Missing governed serializer input eligibility.
- Missing canonical JSON scope.
- Missing canonical ordering rules.
- Missing list ordering category.
- Missing timestamp format or precision.
- Missing number or decimal handling.
- Missing `null`, absent, or `not_applicable` semantics.
- Missing redaction-safe serialization rules.
- Missing canonical `run_id`.
- Mixed `run_id`.
- Missing terminal completion.
- Missing provenance.
- Missing redaction status.
- Unknown section status.
- Stale, malformed, untrusted, or invalidated evidence without governed status
  semantics.
- Ambiguous timestamp.
- Unsupported value type.
- Non-deterministic ordering.
- Sensitive data exposure.
- Implied manifest authority.
- Implied manifest generation authority.
- Implied package creation authority.
- Implied hash or integrity authority.
- Implied storage or finalization authority.
- Implied runtime capture authority.
- Implied evaluation or promotion authority.
- Implied broker authority.
- Implied execution permission.
- Implied live trading authority.

## Hashing and Integrity Authority Contract

Hashing and integrity authority remains governance-only and is not implemented
yet. This contract does not approve tests, code, hash constants, hash
algorithm constants, hash helper functions, hash computation, canonical byte
generation, manifest serialization, package serialization, integrity
validation, storage, finalization, runtime capture, package creation,
evaluation, broker work, execution permission, or live trading.

Hashing rules must be source-controlled before implementation. Hash algorithm
and hash version authority must be explicitly governed before implementation.
Hashing depends on approved canonical byte input. Canonical byte input depends
on deterministic serialization authority. Manifest hash scope depends on
manifest schema authority. No hash value is authoritative until manifest schema,
deterministic serialization, hashing/integrity, storage, and finalization
authorities are separately approved and validated.

Hash authority boundaries:

- Placeholder hash fields must not imply computed hash authority.
- Hash output must not create manifest authority.
- Hash output must not create package authority.
- Hash output must not create package completeness.
- Hash output must not create storage authority.
- Hash output must not create finalization authority.
- Hash output must not create runtime capture authority.
- Hash output must not create evaluation or promotion authority.
- Hash output must not create broker authority, execution permission, or live
  trading authority.

Required future hash algorithm and version rules:

- Hash algorithm selection must be source-controlled before use.
- Hash version naming must be source-controlled before use.
- Algorithm migrations must preserve lineage and must not silently reinterpret
  older hashes.
- Unknown, missing, deprecated, or ambiguous hash algorithm/version values must
  fail closed for authoritative use.

Required future section hash rules:

- Section hashes require explicit inclusion and exclusion rules before
  implementation.
- Section hash inputs must be approved canonical serialized bytes only.
- Section hash scope must define whether it covers section identity, section
  type, section status, section authority, source reference, `section_run_id`,
  provenance, redaction status, section payload, and section lineage fields.
- `present`, `absent`, `not_applicable`, `redacted`, `stale`, `malformed`,
  `untrusted`, and `invalidated` sections require governed hash/integrity
  semantics before implementation.
- Missing required section hash must fail closed once hashing exists.
- Section hash presence cannot imply section authority unless provenance,
  redaction status, source reference authority, `run_id` alignment,
  serialization rules, and completeness rules are independently satisfied.

Required future manifest hash rules:

- Manifest hash authority is separate from section hash authority.
- Manifest hash inputs must be approved canonical serialized manifest bytes
  only.
- Manifest hash scope must define whether it covers identity fields, lifecycle
  fields, source artifact references, section metadata, section hashes,
  completeness fields, authority-boundary fields, provenance summaries,
  redaction status, correction references, invalidation references, and
  supersession references.
- Manifest hash presence cannot imply manifest generation authority.
- Manifest hash presence cannot imply package completeness unless package
  completeness rules are independently satisfied.

Required future package hash rules:

- Package hash authority is separate from section hash authority and manifest
  hash authority.
- Package hash inputs must be approved canonical serialized bytes only.
- Package hash scope must define whether it covers only the manifest, all
  section hashes, source artifact references, package layout metadata, package
  lifecycle metadata, or another explicitly governed combination.
- Package hash must not imply package creation.
- Package hash must not imply package completeness unless package completeness
  rules are independently satisfied.
- Package hash must not imply finalization unless storage and finalization
  gates are separately approved.

Required future integrity status vocabulary must be explicitly governed before
implementation and must distinguish at minimum:

- `not_implemented`.
- `not_applicable`.
- `pending`.
- `valid`.
- `invalid`.
- `missing_hash`.
- `mismatch`.
- `unknown`.

Required future integrity validation rules:

- Hash mismatch must fail closed.
- Missing required hash must fail closed for authoritative use.
- Mixed-`run_id` hash inputs must fail closed.
- Malformed provenance must fail closed.
- Missing provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction state must fail closed.
- Unknown source references must fail closed.
- Stale, malformed, untrusted, redacted, not-applicable, absent, and
  invalidated sections must have governed hash/integrity semantics before
  implementation.
- Sensitive data exposure must stop hashing, integrity validation, storage,
  indexing, package creation, runtime capture, evaluation, and finalization.
- Integrity validation output remains non-authoritative until hashing,
  manifest schema, serialization, storage, and finalization gates define and
  validate authority.

Correction, invalidation, and supersession lineage behavior:

- Corrections must preserve original facts and must not silently mutate
  finalized evidence.
- Original facts must not be rewritten.
- Corrections, annotations, invalidations, supersessions, and reviewer notes
  must be append-only records when later approved.
- Corrected or invalidated evidence must reference the affected package,
  manifest, section, source reference, hash algorithm/version, and hash lineage
  when hashing exists.

Hashing and integrity cannot authorize replay package creation, complete replay
package status, finalized immutable replay package status, manifest generation,
manifest authority, deterministic serialization, canonical byte generation,
storage, finalization, runtime capture, evaluation, attribution, promotion,
broker work, execution permission, strategy or risk behavior changes, cleanup,
flatten, sell, cancel, remediation, or live trading. Event JSONL remains
canonical chronology. `last_run_report.json` remains a derived operational
summary and cannot alone create hash, integrity, manifest, package, or storage
authority. `build_draft_replay_envelope(...)` remains draft scaffold evidence
only. `build_replay_package(...)` mapper scaffold completeness remains distinct
from complete replay package authority.

Hashing and integrity stop conditions:

- Need to implement hash constants.
- Need to implement hash algorithm constants.
- Need to implement hash helper functions.
- Need hash computation.
- Need canonical byte generation.
- Need manifest serialization.
- Need package serialization.
- Need integrity validation.
- Need storage, finalization, or immutability.
- Need runtime capture.
- Need package creation.
- Need filesystem reads or writes.
- Need file path ingestion.
- Need package directories.
- Need retention, discovery, or index behavior.
- Need evaluation, attribution, experiment registry, or promotion.
- Need broker/API/TWS/Alpaca/IBKR.
- Need `main.py`.
- Missing source-controlled hashing rules.
- Missing governed hash algorithm or version authority.
- Missing approved canonical byte input.
- Missing deterministic serialization authority.
- Missing manifest schema authority.
- Missing section hash scope.
- Missing manifest hash scope.
- Missing package hash scope.
- Missing hash inclusion or exclusion rules.
- Missing integrity status vocabulary.
- Missing canonical `run_id`.
- Mixed `run_id`.
- Missing terminal completion.
- Missing required hash once hashing exists.
- Hash mismatch once hashing exists.
- Malformed provenance.
- Missing provenance.
- Missing redaction status.
- Invalid redaction state.
- Unknown source reference.
- Stale, malformed, untrusted, redacted, not-applicable, absent, or
  invalidated section without governed hash/integrity semantics.
- Sensitive data exposure.
- Implied manifest authority.
- Implied package authority.
- Implied package completeness.
- Implied storage or finalization authority.
- Implied runtime capture authority.
- Implied evaluation or promotion authority.
- Implied broker authority.
- Implied execution permission.
- Implied live trading authority.

## Storage, Finalization, and Immutability Authority Contract

Storage, finalization, and immutability authority remains governance-only and
is not implemented yet. This contract does not approve tests, code, storage
constants, storage paths, package directories, filesystem reads, filesystem
writes, retention, discovery, index behavior, finalization state,
immutability enforcement, runtime capture, package creation, evaluation,
broker work, execution permission, or live trading.

Storage rules must be source-controlled before implementation. No filesystem
path, package directory, package file, storage root, index, finalized package
state, or immutable package marker is authoritative until a separate
implementation gate explicitly approves it. Storage output remains
non-authoritative until package layout, package creation, manifest schema,
deterministic serialization, hashing/integrity validation, storage, and
finalization gates are separately approved and validated.

Required future storage root, path, and package directory authority:

- Storage root authority must be explicitly governed before implementation.
- Package path authority must be explicitly governed before implementation.
- Package directory naming authority must be explicitly governed before
  implementation.
- Approved storage roots, package paths, and package directory naming rules
  must be source-controlled before use.
- Package layout authority must exist before storage paths or package
  directories can be implemented.
- Package creation authority must exist before finalized package storage can
  be implemented.
- `canonical_run_id` and `package_id` naming rules must be explicitly
  separated.
- Package directory naming must use `canonical_run_id`, a governed
  `package_id`, or another source-controlled rule approved by a later gate.
- Package paths must separate immutable evidence packages from mutable
  evaluation outputs.
- Missing paths, unknown storage roots, unclear package paths, ambiguous
  package identity, and unknown source references must fail closed.

Required future dependency rules:

- Manifest schema authority must exist before finalized package metadata can
  be implemented.
- Deterministic serialization authority must exist before storage can rely on
  canonical bytes.
- Hashing and integrity validation must exist before finalization.
- Finalization preconditions must be explicit before any finalized lifecycle
  state can be implemented.
- Runtime capture remains blocked until package layout, package creation,
  manifest schema, deterministic serialization, hashing/integrity, redaction,
  provenance, storage, and finalization authority are separately promoted.

Required future package lifecycle rules:

- Package lifecycle states must be explicitly governed before implementation.
- Minimum future lifecycle states are `draft`, `finalized`, `invalidated`, and
  `superseded`.
- Draft evidence may be incomplete and non-authoritative.
- Draft evidence must not imply finalization authority.
- Finalized evidence must be immutable and no-overwrite.
- Finalized evidence must not be silently mutated.
- Invalidated and superseded packages must remain discoverable without
  becoming mutable.
- Invalidated and superseded evidence must remain retained with lineage
  references when later approved.
- Missing, unknown, or malformed lifecycle status must fail closed.

Required future immutability and lineage semantics:

- Immutable evidence packages must preserve original facts.
- Original facts must not be rewritten.
- Corrections, annotations, invalidations, supersessions, and reviewer notes
  must be append-only and lineage-preserving.
- Corrections, invalidations, and supersessions must identify the affected
  package, manifest, section, source reference, and hash lineage once hashing
  exists.
- Attempted overwrite of finalized evidence must fail closed.
- Immutable evidence must remain distinct from derived reports, comparisons,
  recommendations, experiments, and other mutable evaluation artifacts.

Required future retention, discovery, and index rules:

- Retention authority remains future-only until separately approved.
- Discovery authority remains future-only until separately approved.
- Index authority remains future-only until separately approved.
- Retention rules for finalized packages must be approved before
  implementation.
- Retention rules for invalidated and superseded packages must be approved
  before implementation.
- Discovery or index behavior is non-authoritative until separately approved.
- Index or discovery entries must not imply completeness, package authority,
  finalization, evaluation authority, promotion, broker authority, execution
  permission, or live trading authority.
- Disposable evaluation artifacts must not be mixed with retained immutable
  evidence.

Required future provenance, source-reference, and redaction rules:

- Provenance must be explicit before storage, finalization, indexing, or
  runtime capture.
- Source-reference authority must be explicit before storage, finalization,
  indexing, or runtime capture.
- `run_id` alignment must be explicit before storage or finalization.
- Mixed-`run_id` storage inputs must fail closed.
- Missing provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Raw credentials and secrets must never be stored.
- Broker/account-sensitive identifiers require explicit safe handling.
- Sensitive data exposure must stop storage, indexing, package creation,
  runtime capture, evaluation, and finalization.

Filesystem writer authority boundaries:

- This contract does not approve filesystem reads or filesystem writes.
- A future writer may write only approved package artifacts under an explicit
  implementation gate.
- A future writer may write only to approved storage roots and package paths.
- A future writer must not create package authority or package completeness.
- A future writer must not overwrite finalized evidence.
- A future writer must not mutate runtime state.
- A future writer must not call `main.py`.
- A future writer must not call broker/API/TWS/Alpaca/IBKR.
- A future writer must not create evaluation authority, broker authority,
  execution permission, strategy promotion, or live trading authority.

Storage, finalization, and immutability cannot authorize manifest authority,
manifest generation, replay package creation, package authority, package
completeness, complete replay package status, finalized immutable replay
package status, deterministic serialization, canonical byte generation,
hashing or integrity enforcement, runtime capture, evaluation, attribution,
promotion, broker work, execution permission, strategy or risk behavior
changes, cleanup, flatten, sell, cancel, remediation, or live trading. Event
JSONL remains canonical chronology. `last_run_report.json` remains a derived
operational summary and cannot alone create storage, finalization,
immutability, package, index, or runtime capture authority.
`build_draft_replay_envelope(...)` remains draft scaffold evidence only.
`build_replay_package(...)` mapper scaffold completeness remains distinct from
complete replay package authority.

Storage, finalization, and immutability stop conditions:

- Need to implement storage constants.
- Need to implement storage path constants.
- Need to implement package directory constants.
- Need storage paths.
- Need package directories.
- Need filesystem reads or writes.
- Need filesystem writer implementation.
- Need finalization state implementation.
- Need immutability enforcement.
- Need retention, discovery, or index behavior.
- Need runtime capture.
- Need manifest schema implementation.
- Need deterministic serialization implementation.
- Need hashing or integrity implementation.
- Need package creation.
- Need file ingestion.
- Need replay package files.
- Need evaluation, attribution, or promotion.
- Need broker/API/TWS/Alpaca/IBKR.
- Need `main.py`.
- Missing source-controlled storage rules.
- Missing approved storage root.
- Missing approved package path.
- Missing package directory naming authority.
- Missing package layout authority.
- Missing package creation authority.
- Missing canonical `run_id`.
- Missing governed `package_id` when package identity requires one.
- Mixed `run_id`.
- Missing manifest schema authority.
- Missing deterministic serialization authority.
- Missing hashing or integrity authority.
- Missing hash or integrity validation before finalization.
- Missing finalization preconditions.
- Missing lifecycle status.
- Missing source reference authority.
- Unknown source reference.
- Attempted overwrite of finalized evidence.
- Unknown package authority.
- Missing provenance.
- Missing redaction status.
- Invalid redaction state.
- Sensitive data exposure.
- Implied manifest authority.
- Implied package creation authority.
- Implied package completeness.
- Implied hash or integrity authority.
- Implied runtime capture authority.
- Implied evaluation or promotion authority.
- Implied broker authority.
- Implied execution permission.
- Implied live trading authority.

## Source Reference And Source Artifact Authority Contract

Source reference and source artifact authority remains governance-only and is
not implemented yet. This contract defines the first upstream prerequisite for
future runtime artifact discovery, source path authority, file path ingestion,
artifact copying, package creation, immutable package evidence, runtime
capture, and evaluation work.

This contract does not approve tests, code, source reference modules, source
artifact modules, runtime artifact discovery, source path ingestion, file path
ingestion, file reads, artifact copying, runtime capture, replay package
creation, manifest generation, hashing or integrity validation, storage,
finalization, immutability, evaluation, promotion, broker work, paper trading,
or live trading.

Source reference scope:

- A source reference is a source-controlled identifier or declaration that
  names the class and ownership of future evidence without resolving a path or
  reading bytes.
- A source artifact class is a governed category of future evidence, such as
  canonical event chronology, derived operational summary evidence, observed
  runtime visibility evidence, configuration metadata, market input evidence,
  strategy decision evidence, portfolio/risk evidence, broker-visible observed
  evidence, or reconciliation/risk evidence.
- Future replay and capture planning may use source references only when the
  reference is known, unambiguous, aligned to the canonical run identity, and
  paired with explicit provenance and redaction status.
- Source references may identify which replay package section could later
  receive evidence, but they cannot populate that section, create package
  completeness, create immutable evidence, approve runtime capture, or approve
  evaluation.
- Source references must preserve the distinction between present, absent, and
  not-applicable declarations when later gates define those states.

Source reference dependencies:

- Provenance and redaction authority must be defined before any source
  reference can be used as trusted evidence metadata.
- Runtime artifact discovery authority must be defined before source
  references can be matched to discovered runtime artifacts.
- Terminal completion and run eligibility authority must be defined before a
  source reference can support capture eligibility.
- Package layout authority must be defined before a source reference can target
  a replay package section.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Source path ingestion.
- File path ingestion.
- File reads.
- Artifact copying.
- Runtime artifact discovery.
- Runtime capture.
- Replay package creation.
- Manifest generation.
- Hashing or integrity validation.
- Storage, finalization, or immutability.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual source reference vocabulary:

- Canonical event chronology reference.
- Derived operational summary reference.
- Operational state evidence reference.
- Append-only observation evidence reference.
- Runtime visibility evidence reference.
- Configuration or code metadata reference.
- Market input evidence reference.
- Strategy input/output evidence reference.
- Portfolio/risk state evidence reference.
- Broker-visible observed evidence reference.
- Reconciliation/risk evidence reference.
- Explicit absence declaration.
- Explicit not-applicable declaration.

This vocabulary is conceptual only. It does not create constants, types,
modules, source paths, file paths, artifact reads, artifact copies, runtime
capture, package sections, immutable evidence, evaluation inputs, broker
authority, or trading authority.

Unknown and ambiguous source reference handling:

- Unknown source references must fail closed.
- Ambiguous source references must fail closed.
- Mixed-run source references must fail closed.
- Source references with missing provenance must fail closed.
- Source references with missing redaction status must fail closed.
- Source references with invalid redaction status must fail closed.
- Source references that imply path resolution, file reads, artifact copying,
  runtime capture, package creation, evaluation, broker/API work, paper
  trading, or live trading must fail closed.

Provenance and redaction attachment:

- Every future source reference must carry explicit provenance.
- Every future source reference must carry explicit redaction status.
- Provenance must identify the source environment, source artifact class,
  run identity relationship, and whether the reference is present, absent, or
  not applicable when those states are later governed.
- Redaction status must identify whether the referenced future evidence is
  clear, redacted, sanitized, absent, not applicable, or blocked by sensitive
  data exposure when those states are later governed.
- Provenance and redaction presence does not imply artifact eligibility,
  runtime artifact discovery, path authority, file-read authority, artifact
  copying, runtime capture, package completeness, immutable evidence,
  evaluation, promotion, broker authority, paper trading, or live trading.

Required future test-only guards:

- Unknown source references fail closed.
- Ambiguous source references fail closed.
- Mixed-run source references fail closed.
- Missing provenance fails closed.
- Missing or invalid redaction status fails closed.
- Source references cannot imply source path authority.
- Source references cannot imply file path ingestion.
- Source references cannot imply file-read authority.
- Source references cannot imply artifact copying.
- Source references cannot imply runtime artifact discovery.
- Source references cannot imply runtime capture.
- Source references cannot imply package creation.
- Source references cannot imply immutable package evidence.
- Source references cannot imply evaluation, scoring, reporting, or promotion.
- Source references cannot imply broker/API, execution, paper trading, or live
  trading authority.

Future implementation stop conditions:

- Need real runtime logs.
- Need real runtime artifacts.
- Need filesystem reads.
- Need filesystem writes.
- Need source path resolution.
- Need file path ingestion.
- Need artifact copying.
- Need runtime artifact discovery.
- Need runtime capture.
- Need package creation.
- Need manifest generation.
- Need hashing or integrity validation.
- Need storage, finalization, or immutability.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need `.env` access.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Source reference and source artifact authority is not runtime artifact
discovery, source path authority, file path ingestion, file-read authority,
artifact copying, runtime capture, package creation, manifest authority,
hashing or integrity authority, storage/finalization/immutability authority,
immutable package evidence, evaluation, promotion, broker authority, execution
permission, paper trading approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_SOURCE_REFERENCE_ARTIFACT_AUTHORITY_GUARD`. That future gate must be
test-only and must not inspect runtime logs, inspect runtime artifacts, edit
production code, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## Provenance And Redaction Authority Contract

Provenance and redaction authority remains governance-only and is not
implemented yet. This contract defines the next upstream prerequisite after
source reference and source artifact authority, before runtime artifact
discovery, source path authority, file path ingestion, artifact copying,
package creation, immutable package evidence, runtime capture, or evaluation
implementation can be considered.

This contract does not approve tests, code, provenance modules, redaction
modules, runtime artifact discovery, source path ingestion, file path
ingestion, file reads, artifact copying, runtime capture, replay package
creation, manifest generation, hashing or integrity validation, storage,
finalization, immutability, immutable package evidence, evaluation, promotion,
broker work, paper trading, or live trading.

Provenance and redaction scope:

- Provenance for replay evidence is governed metadata that identifies where
  future evidence came from, which run identity it belongs to, which source
  reference and artifact class it claims, who or what produced it, and whether
  that origin is known, complete, and unambiguous.
- Redaction status for replay evidence is governed metadata that identifies
  whether future evidence is safe to reference, has been redacted, is verified
  clean, is not applicable, is unknown, or is blocked by sensitive data
  exposure.
- Required future provenance fields are conceptual only and include
  `source_reference_id`, `run_id`, `artifact_class`, `producer`,
  `generated_at` or `observed_at`, and `provenance_status`.
- Required future redaction fields are conceptual only and include
  `redaction_status`, `redaction_reason`, and `sensitive_fields_policy`.
- Provenance and redaction metadata must attach to every future source
  reference and every future runtime artifact before any downstream gate may
  treat that reference or artifact as eligible evidence.
- Provenance and redaction metadata may describe a future evidence claim, but
  cannot read the evidence, resolve paths, copy artifacts, create packages,
  finalize immutable evidence, evaluate results, promote strategies, access a
  broker/API, or approve trading.

Provenance and redaction dependencies:

- Source Reference and Source Artifact Authority must be defined before
  provenance or redaction metadata can attach to a governed source reference.
- Runtime Artifact Discovery Authority must be defined before provenance or
  redaction metadata can attach to discovered runtime artifacts.
- Terminal completion and run eligibility authority must be defined before
  provenance or redaction metadata can support capture eligibility.
- Package layout authority must be defined before provenance or redaction
  metadata can target package sections.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Source path ingestion.
- File path ingestion.
- File reads.
- Artifact copying.
- Runtime artifact discovery.
- Runtime capture.
- Replay package creation.
- Manifest generation.
- Hashing or integrity validation.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual provenance and redaction vocabulary:

- `source_reference_id`.
- `run_id`.
- `artifact_class`.
- `producer`.
- `generated_at`.
- `observed_at`.
- `redaction_status`.
- `redaction_reason`.
- `sensitive_fields_policy`.
- `provenance_status`.
- Source-controlled source reference provenance.
- Runtime artifact provenance.
- Section-level provenance.
- Redaction-safe declaration.
- Sensitive-data-blocked declaration.

This vocabulary is conceptual only. It does not create constants, types,
modules, path authority, file-read authority, artifact-copying authority,
runtime capture authority, package sections, manifests, hashes, storage,
immutable evidence, evaluation inputs, broker authority, or trading authority.

Required future redaction states:

- `not_applicable` means redaction is not relevant to the source reference or
  artifact class and must be explicitly justified.
- `redacted` means sensitive fields have been removed or replaced according to
  a future governed redaction policy.
- `verified_clean` means the future evidence was reviewed under a governed
  sensitive-fields policy and contains no sensitive fields requiring
  redaction.
- `blocked_sensitive` means the evidence must not proceed because sensitive
  data exposure is known or suspected.
- `unknown` means the redaction state is unresolved and is not acceptable for
  downstream authority.

Unknown, missing, malformed, or invalid redaction status must fail closed.

Fail-closed handling:

- Missing provenance must fail closed.
- Malformed provenance must fail closed.
- Ambiguous provenance must fail closed.
- Mixed-run provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive data exposure must fail closed.
- Unknown source references with provenance-looking metadata still fail
  closed.
- Provenance or redaction metadata that implies path resolution, file reads,
  artifact copying, runtime capture, package creation, immutable evidence,
  evaluation, broker/API work, paper trading, or live trading must fail closed.

Required future test-only guards:

- Missing provenance fails closed.
- Malformed provenance fails closed.
- Ambiguous provenance fails closed.
- Mixed-run provenance fails closed.
- Missing redaction status fails closed.
- Invalid redaction status fails closed.
- Sensitive-data markers block downstream authority.
- Unknown source references with provenance-looking metadata fail closed.
- Provenance cannot imply source path authority.
- Provenance cannot imply file path ingestion.
- Provenance cannot imply file-read authority.
- Provenance cannot imply artifact copying.
- Provenance cannot imply runtime artifact discovery.
- Provenance cannot imply runtime capture.
- Provenance cannot imply package creation.
- Provenance cannot imply immutable package evidence.
- Provenance cannot imply evaluation, scoring, reporting, or promotion.
- Provenance cannot imply broker/API, execution, paper trading, or live
  trading authority.
- Redaction status cannot imply artifact eligibility, package completeness,
  immutable evidence, evaluation, promotion, broker authority, paper trading,
  or live trading.

Future implementation stop conditions:

- Need real runtime logs.
- Need real runtime artifacts.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need filesystem reads.
- Need filesystem writes.
- Need source path resolution.
- Need file path ingestion.
- Need artifact copying.
- Need runtime artifact discovery.
- Need runtime capture.
- Need package creation.
- Need manifest generation.
- Need hashing or integrity validation.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Provenance and redaction authority is not runtime artifact discovery, source
path authority, file path ingestion, file-read authority, artifact copying,
runtime capture, package creation, manifest authority, hashing or integrity
authority, storage/finalization/immutability authority, immutable package
evidence, evaluation, promotion, broker authority, execution permission, paper
trading approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_PROVENANCE_REDACTION_AUTHORITY_GUARD`. That future gate must be
test-only and must not inspect runtime logs, inspect runtime artifacts, edit
production code, edit docs, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## Runtime Artifact Discovery Authority Contract

Runtime artifact discovery authority remains governance-only and is not
implemented yet. This contract defines metadata-only discovery authority after
source reference and source artifact authority and provenance/redaction
authority, before source path authority, file path ingestion, artifact
copying, package creation, immutable package evidence, runtime capture, or
evaluation implementation can be considered.

This contract does not approve tests, code, runtime artifact discovery
modules, runtime log inspection, runtime artifact content inspection, source
path authority, file path ingestion, file reads, artifact copying, runtime
capture, replay package creation, manifest generation, hashing or integrity
validation, storage, finalization, immutability, immutable package evidence,
evaluation, promotion, broker work, paper trading, or live trading.

Runtime artifact discovery scope:

- Runtime artifact discovery means metadata-only identification of future
  runtime evidence candidates that may be relevant to a replay package.
- Discovery may identify candidate artifact classes, candidate artifact
  reference identifiers, declared absence, not-applicable states, discovery
  status, provenance status, redaction status, and eligibility metadata
  conceptually.
- Discovery does not read artifact content.
- Discovery does not inspect runtime logs.
- Discovery does not copy artifacts.
- Discovery does not create packages.
- Discovery does not approve runtime capture.
- Discovery metadata may describe that a candidate is present, absent, not
  applicable, stale, malformed, mixed-run, blocked by sensitive data, or
  unknown, but those states do not grant downstream authority.

Runtime artifact discovery dependencies:

- Source Reference and Source Artifact Authority must be defined before runtime
  artifact discovery can bind candidate metadata to governed source
  references.
- Provenance and Redaction Authority must be defined before runtime artifact
  discovery can treat candidate metadata as eligible for downstream planning.
- Terminal completion and run eligibility authority must be defined before
  runtime artifact discovery can support capture eligibility.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact content inspection.
- Source path authority.
- File path ingestion.
- File reads.
- Artifact copying.
- Runtime capture.
- Replay package creation.
- Manifest generation.
- Hashing or integrity validation.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual runtime artifact discovery vocabulary:

- `artifact_class`.
- `artifact_reference_id`.
- `run_id`.
- `discovery_status`.
- `absent`.
- `not_applicable`.
- `discovered`.
- `stale`.
- `malformed`.
- `mixed_run`.
- `provenance_status`.
- `redaction_status`.
- `eligibility_status`.
- Candidate artifact metadata.
- Explicit absence declaration.
- Explicit not-applicable declaration.
- Metadata-only discovery result.

This vocabulary is conceptual only. It does not create constants, types,
modules, runtime log access, runtime artifact content access, source paths,
file paths, artifact reads, artifact copies, runtime capture, package
sections, manifests, hashes, storage, immutable evidence, evaluation inputs,
broker authority, or trading authority.

Required future discovery statuses:

- `discovered` means candidate metadata exists for a governed artifact class,
  but content access and capture remain unauthorized.
- `absent` means the artifact class was explicitly declared absent under later
  governed terminal completion and run eligibility rules.
- `not_applicable` means the artifact class is explicitly not applicable to
  the run or package section under later governed rules.
- `stale` means candidate metadata is not current enough for downstream use.
- `malformed` means candidate metadata is structurally invalid.
- `mixed_run` means candidate metadata spans or conflicts with more than one
  run identity.
- `blocked_sensitive` means candidate metadata or associated evidence is
  blocked by sensitive data exposure.
- `unknown` means discovery status is unresolved and is not acceptable for
  downstream authority.

Unknown, missing, malformed, stale, mixed-run, or sensitive discovery status
must fail closed for downstream authority.

Fail-closed handling:

- Missing discovery result must fail closed.
- Unknown artifact class must fail closed.
- Unknown discovery status must fail closed.
- Stale artifact metadata must fail closed.
- Malformed artifact metadata must fail closed.
- Mixed-run artifact metadata must fail closed.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absence declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- Discovery metadata that implies runtime log inspection, runtime artifact
  content inspection, path resolution, file reads, artifact copying, runtime
  capture, package creation, immutable evidence, evaluation, broker/API work,
  paper trading, or live trading must fail closed.

Required future test-only guards:

- Discovery vocabulary remains metadata-only.
- Discovery cannot inspect runtime logs.
- Discovery cannot inspect runtime artifact content.
- Discovery cannot imply source path authority.
- Discovery cannot imply file path ingestion.
- Discovery cannot imply approved file reads.
- Discovery cannot imply artifact copying.
- Discovery cannot imply runtime capture.
- Discovery cannot imply package creation.
- Discovery cannot imply immutable package evidence.
- Discovery cannot imply evaluation, scoring, reporting, or promotion.
- Discovery cannot imply broker/API, execution, paper trading, or live trading
  authority.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.
- Stale metadata fails closed.
- Malformed metadata fails closed.
- Mixed-run metadata fails closed.
- Missing or invalid provenance fails closed.
- Missing or invalid redaction status fails closed.
- Sensitive-data markers block downstream authority.

Future implementation stop conditions:

- Need real runtime logs.
- Need real runtime artifact content.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need uncontrolled filesystem reads.
- Need filesystem writes.
- Need source path resolution.
- Need file path ingestion.
- Need file reads.
- Need artifact copying.
- Need runtime capture.
- Need package creation.
- Need manifest generation.
- Need hashing or integrity validation.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Runtime artifact discovery authority is not runtime log access authority,
runtime artifact content access, source path authority, file path ingestion,
file-read authority, artifact copying, runtime capture, package creation,
manifest authority, hashing or integrity authority,
storage/finalization/immutability authority, immutable package evidence,
evaluation, promotion, broker authority, execution permission, paper trading
approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY_GUARD`. That future gate must
be test-only and must not inspect runtime logs, inspect runtime artifacts,
edit production code, edit docs, touch VPS, call broker APIs, inspect `.env`,
change scheduler/systemd, approve paper trading, or approve live trading.

## Source Path Authority Contract

Source path authority remains governance-only and is not implemented yet. This
contract defines a conceptual authority boundary after source reference and
source artifact authority, provenance/redaction authority, and runtime
artifact discovery authority, before file path ingestion, artifact copying,
package creation, immutable package evidence, runtime capture, or evaluation
implementation can be considered.

This contract does not approve tests, code, source path modules, path
resolution, runtime log inspection, runtime artifact content inspection, file
path ingestion, file reads, artifact copying, runtime capture, replay package
creation, manifest generation, hashing or integrity validation, storage,
finalization, immutability, immutable package evidence, evaluation, promotion,
broker work, paper trading, or live trading.

Source path scope:

- A source path is a governed path-like metadata declaration that may name
  where a future source artifact could be found, without resolving,
  traversing, opening, reading, copying, or validating the filesystem target.
- A source reference identifies a governed evidence class or ownership
  declaration. A source artifact class categorizes the future evidence. A
  source path names a conceptual path-like reference for that class. File path
  ingestion is a separate downstream authority that may later decide whether
  actual path resolution or file access is permitted.
- Source path authority may only define whether a path-like reference can be
  named conceptually.
- Source path authority does not resolve paths.
- Source path authority does not read files.
- Source path authority does not copy artifacts.
- Source path authority does not inspect runtime artifacts.
- Source path authority does not inspect runtime logs.
- Source path authority does not approve runtime capture.
- Source path metadata may describe a declaration as present, absent, not
  applicable, malformed, ambiguous, stale, mixed-run, blocked by sensitive
  data, or unknown, but those states do not grant downstream authority.

Source path dependencies:

- Source Reference and Source Artifact Authority must be defined before source
  path metadata can bind to a governed source reference or artifact class.
- Provenance and Redaction Authority must be defined before source path
  metadata can be considered eligible for downstream planning.
- Runtime Artifact Discovery Authority must be defined before source path
  metadata can attach to discovered runtime artifact candidates.
- Terminal completion and run eligibility authority must be defined before
  source path metadata can support capture eligibility.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact content inspection.
- File path ingestion.
- File reads.
- Path traversal.
- Symlink traversal.
- Artifact copying.
- Runtime capture.
- Replay package creation.
- Manifest generation.
- Hashing or integrity validation.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual source path vocabulary:

- `source_path_reference`.
- `repo_relative_source_path`.
- `runtime_relative_source_path`.
- `artifact_declared_source_path`.
- `path_authority_status`.
- `path_scope`.
- `path_provenance_status`.
- `path_redaction_status`.
- `path_eligibility_status`.
- Explicit absence declaration.
- Explicit not-applicable declaration.
- Metadata-only source path result.

This vocabulary is conceptual only. It does not create constants, types,
modules, path resolution, filesystem traversal, symlink handling, file path
ingestion, file reads, artifact copies, runtime capture, package sections,
manifests, hashes, storage, immutable evidence, evaluation inputs, broker
authority, or trading authority.

Required future source path statuses:

- `declared` means a governed source path reference has been named
  conceptually, but path resolution and file access remain unauthorized.
- `absent` means the source path was explicitly declared absent under later
  governed terminal completion and run eligibility rules.
- `not_applicable` means the source path is explicitly not applicable to the
  source reference, artifact class, run, or package section under later
  governed rules.
- `malformed` means the source path metadata is structurally invalid.
- `ambiguous` means the source path metadata cannot identify exactly one
  governed conceptual path reference.
- `stale` means the source path metadata is not current enough for downstream
  use.
- `mixed_run` means the source path metadata spans or conflicts with more than
  one run identity.
- `blocked_sensitive` means the source path metadata or associated evidence is
  blocked by sensitive data exposure.
- `unknown` means source path status is unresolved and is not acceptable for
  downstream authority.

Unknown, missing, malformed, ambiguous, stale, mixed-run, or sensitive path
status must fail closed for downstream authority.

Fail-closed handling:

- Missing source path status must fail closed.
- Unknown source path status must fail closed.
- Malformed source path metadata must fail closed.
- Ambiguous source path metadata must fail closed.
- Mixed-run source path metadata must fail closed.
- Stale source path metadata must fail closed.
- Absolute path smuggling must fail closed.
- Parent traversal must fail closed.
- Symlink or link-like path claims must fail closed until separately
  authorized.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absent declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- Source path metadata that implies runtime log inspection, runtime artifact
  content inspection, path resolution, file path ingestion, file reads,
  artifact copying, runtime capture, package creation, immutable evidence,
  evaluation, broker/API work, paper trading, or live trading must fail
  closed.

Required future test-only guards:

- Source path vocabulary remains non-resolving and metadata-only.
- Source path authority cannot inspect runtime logs.
- Source path authority cannot inspect runtime artifact content.
- Source path authority cannot imply file path ingestion.
- Source path authority cannot imply approved file reads.
- Source path authority cannot imply artifact copying.
- Source path authority cannot imply runtime capture.
- Source path authority cannot imply package creation.
- Source path authority cannot imply immutable package evidence.
- Source path authority cannot imply evaluation, scoring, reporting, or
  promotion.
- Source path authority cannot imply broker/API, execution, paper trading, or
  live trading authority.
- Absolute path smuggling fails closed.
- Parent traversal fails closed.
- Ambiguous source path metadata fails closed.
- Malformed source path metadata fails closed.
- Stale source path metadata fails closed.
- Mixed-run source path metadata fails closed.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.

Future implementation stop conditions:

- Need real runtime logs.
- Need real runtime artifact content.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need uncontrolled filesystem reads.
- Need filesystem writes.
- Need actual path resolution.
- Need symlink resolution.
- Need file path ingestion.
- Need file reads.
- Need artifact copying.
- Need runtime capture.
- Need package creation.
- Need manifest generation.
- Need hashing or integrity validation.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Source path authority is not runtime log access authority, runtime artifact
content access, path resolution, file path ingestion, file-read authority,
artifact copying, runtime capture, package creation, manifest authority,
hashing or integrity authority, storage/finalization/immutability authority,
immutable package evidence, evaluation, promotion, broker authority, execution
permission, paper trading approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_SOURCE_PATH_AUTHORITY_GUARD`. That future gate must be test-only
and must not inspect runtime logs, inspect runtime artifacts, edit production
code, edit docs, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## File Path Ingestion Authority Contract

File path ingestion authority remains governance-only and is not implemented
yet. This contract defines a conceptual authority boundary after source path
authority, before artifact copying, package creation, immutable package
evidence, runtime capture, or evaluation implementation can be considered.

This contract does not approve tests, code, file path ingestion modules, real
path resolution, directory traversal, symlink traversal, runtime log
inspection, runtime artifact content inspection, file reads, artifact copying,
runtime capture, replay package creation, manifest generation, hashing or
integrity validation, storage, finalization, immutability, immutable package
evidence, evaluation, promotion, broker work, paper trading, or live trading.

File path ingestion scope:

- File path ingestion means governed metadata acceptance for path-like values
  as future ingestion candidates, without resolving, traversing, opening,
  reading, copying, or validating any filesystem target.
- A source reference identifies a governed evidence class or ownership
  declaration. A source artifact class categorizes the future evidence. Source
  path authority governs whether a path-like reference may be named
  conceptually. File path ingestion authority may only define when path-like
  metadata can be accepted as an ingestion candidate.
- File path ingestion authority does not read files.
- File path ingestion authority does not resolve real filesystem paths.
- File path ingestion authority does not traverse directories.
- File path ingestion authority does not follow symlinks.
- File path ingestion authority does not copy artifacts.
- File path ingestion authority does not inspect runtime artifacts.
- File path ingestion authority does not inspect runtime logs.
- File path ingestion authority does not approve runtime capture.
- File path ingestion metadata may describe a candidate as declared, absent,
  not applicable, malformed, ambiguous, stale, mixed-run, blocked by sensitive
  data, or unknown, but those states do not grant downstream authority.

File path ingestion dependencies:

- Source Reference and Source Artifact Authority must be defined before file
  path ingestion metadata can bind to a governed source reference or artifact
  class.
- Provenance and Redaction Authority must be defined before file path
  ingestion metadata can be considered eligible for downstream planning.
- Runtime Artifact Discovery Authority must be defined before file path
  ingestion metadata can attach to discovered runtime artifact candidates.
- Source Path Authority must be defined before file path ingestion metadata
  can be considered as a downstream candidate.
- Terminal completion and run eligibility authority must be defined before
  file path ingestion metadata can support capture eligibility.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact content inspection.
- File reads.
- Directory traversal.
- Path resolution.
- Symlink traversal.
- Artifact copying.
- Runtime capture.
- Replay package creation.
- Manifest generation.
- Hashing or integrity validation.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual file path ingestion vocabulary:

- `file_path_reference`.
- `ingestion_candidate_path`.
- `repo_relative_ingestion_path`.
- `runtime_relative_ingestion_path`.
- `ingestion_path_scope`.
- `ingestion_path_status`.
- `ingestion_path_provenance_status`.
- `ingestion_path_redaction_status`.
- `ingestion_path_eligibility_status`.
- Explicit absence declaration.
- Explicit not-applicable declaration.
- Metadata-only file path ingestion result.

This vocabulary is conceptual only. It does not create constants, types,
modules, path resolution, filesystem traversal, symlink handling, file reads,
artifact copies, runtime capture, package sections, manifests, hashes,
storage, immutable evidence, evaluation inputs, broker authority, or trading
authority.

Required future file path ingestion statuses:

- `candidate_declared` means an ingestion candidate path has been named
  conceptually, but path resolution and file access remain unauthorized.
- `absent` means the ingestion candidate path was explicitly declared absent
  under later governed terminal completion and run eligibility rules.
- `not_applicable` means the ingestion candidate path is explicitly not
  applicable to the source reference, artifact class, run, or package section
  under later governed rules.
- `malformed` means the ingestion path metadata is structurally invalid.
- `ambiguous` means the ingestion path metadata cannot identify exactly one
  governed conceptual ingestion candidate.
- `stale` means the ingestion path metadata is not current enough for
  downstream use.
- `mixed_run` means the ingestion path metadata spans or conflicts with more
  than one run identity.
- `blocked_sensitive` means the ingestion path metadata or associated evidence
  is blocked by sensitive data exposure.
- `unknown` means ingestion path status is unresolved and is not acceptable for
  downstream authority.

Unknown, missing, malformed, ambiguous, stale, mixed-run, or sensitive
ingestion-path status must fail closed for downstream authority.

Fail-closed handling:

- Missing ingestion path status must fail closed.
- Unknown ingestion path status must fail closed.
- Malformed ingestion path metadata must fail closed.
- Ambiguous ingestion path metadata must fail closed.
- Mixed-run ingestion path metadata must fail closed.
- Stale ingestion path metadata must fail closed.
- Absolute path smuggling must fail closed.
- Parent traversal must fail closed.
- Symlink or link-like path claims must fail closed until separately
  authorized.
- Directory traversal claims must fail closed.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absent declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- File path ingestion metadata that implies runtime log inspection, runtime
  artifact content inspection, path resolution, directory traversal, symlink
  traversal, file reads, artifact copying, runtime capture, package creation,
  immutable evidence, evaluation, broker/API work, paper trading, or live
  trading must fail closed.

Required future test-only guards:

- File path ingestion vocabulary remains metadata-only.
- File path ingestion cannot inspect runtime logs.
- File path ingestion cannot inspect runtime artifact content.
- File path ingestion cannot imply approved file reads.
- File path ingestion cannot imply path resolution.
- File path ingestion cannot imply symlink traversal.
- File path ingestion cannot imply directory traversal.
- File path ingestion cannot imply artifact copying.
- File path ingestion cannot imply runtime capture.
- File path ingestion cannot imply package creation.
- File path ingestion cannot imply immutable package evidence.
- File path ingestion cannot imply evaluation, scoring, reporting, or
  promotion.
- File path ingestion cannot imply broker/API, execution, paper trading, or
  live trading authority.
- Absolute path smuggling fails closed.
- Parent traversal fails closed.
- Ambiguous ingestion path metadata fails closed.
- Malformed ingestion path metadata fails closed.
- Stale ingestion path metadata fails closed.
- Mixed-run ingestion path metadata fails closed.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.

Future implementation stop conditions:

- Need real runtime logs.
- Need real runtime artifact content.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need uncontrolled filesystem reads.
- Need filesystem writes.
- Need actual path resolution.
- Need symlink resolution.
- Need directory traversal.
- Need file reads.
- Need artifact copying.
- Need runtime capture.
- Need package creation.
- Need manifest generation.
- Need hashing or integrity validation.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

File path ingestion authority is not runtime log access authority, runtime
artifact content access, path resolution, directory traversal, symlink
traversal, file-read authority, artifact copying, runtime capture, package
creation, manifest authority, hashing or integrity authority,
storage/finalization/immutability authority, immutable package evidence,
evaluation, promotion, broker authority, execution permission, paper trading
approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_FILE_PATH_INGESTION_AUTHORITY_GUARD`. That future gate must be
test-only and must not inspect runtime logs, inspect runtime artifacts, edit
production code, edit docs, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## Artifact Copying Authority Contract

Artifact copying authority remains governance-only and is not implemented yet.
This contract defines a conceptual authority boundary after file path ingestion
authority, before package creation, immutable package evidence, runtime
capture, or evaluation implementation can be considered.

This contract does not approve tests, code, artifact copying modules, real path
resolution, directory traversal, symlink traversal, runtime log inspection,
runtime artifact semantic inspection, uncontrolled file reads, uncontrolled
file writes, replay package creation, manifest generation, hashing or integrity
proof, storage, finalization, immutability, immutable package evidence, runtime
capture, evaluation, promotion, broker work, paper trading, or live trading.

Artifact copying scope:

- Artifact copying means a governed future operation that may copy an
  already-approved ingestion candidate into a controlled future package or
  staging context.
- A source reference identifies a governed evidence class or ownership
  declaration. Runtime artifact discovery identifies metadata-only candidate
  artifact classes and states. Source path authority governs whether path-like
  references may be named conceptually. File path ingestion authority governs
  when path-like metadata may be accepted as an ingestion candidate. Artifact
  copying authority may only define when an already-approved ingestion
  candidate may be copied into a controlled future package or staging context.
- Artifact copying authority does not inspect artifact content semantically.
- Artifact copying authority does not approve uncontrolled file reads.
- Artifact copying authority does not approve directory traversal.
- Artifact copying authority does not approve symlink traversal.
- Artifact copying authority does not create complete replay packages.
- Artifact copying authority does not create immutable evidence.
- Artifact copying authority does not approve runtime capture.
- Artifact copying authority does not approve evaluation or promotion.
- Copy metadata may describe a candidate as declared, approved, blocked,
  absent, not applicable, malformed, ambiguous, stale, mixed-run, blocked by
  sensitive data, or unknown, but those states do not grant downstream
  authority.

Artifact copying dependencies:

- Source Reference and Source Artifact Authority must be defined before copy
  metadata can bind to a governed source reference or artifact class.
- Provenance and Redaction Authority must be defined before copy metadata can
  be considered eligible for downstream planning.
- Runtime Artifact Discovery Authority must be defined before copy metadata can
  attach to discovered runtime artifact candidates.
- Source Path Authority must be defined before copy metadata can refer to
  governed source path metadata.
- File Path Ingestion Authority must be defined before copy metadata can refer
  to an ingestion candidate.
- Terminal completion and run eligibility authority must be defined before
  artifact copying metadata can support capture eligibility.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact semantic inspection.
- Uncontrolled file reads.
- Directory traversal.
- Path resolution outside approved boundaries.
- Symlink traversal.
- Replay package creation.
- Manifest generation.
- Hashing or integrity proof.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Runtime capture.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual artifact copying vocabulary:

- `copy_candidate_reference`.
- `approved_copy_source`.
- `controlled_copy_target`.
- `copy_scope`.
- `copy_status`.
- `copy_provenance_status`.
- `copy_redaction_status`.
- `copy_integrity_status`.
- `copy_eligibility_status`.
- Explicit absence declaration.
- Explicit not-applicable declaration.
- Metadata-only artifact copying result.

This vocabulary is conceptual only. It does not create constants, types,
modules, filesystem reads, filesystem writes, path resolution, directory
traversal, symlink handling, artifact copies, package directories, complete
replay packages, manifests, hashes, storage, immutable evidence, runtime
capture, evaluation inputs, broker authority, or trading authority.

Required future artifact copying statuses:

- `copy_candidate_declared` means a copy candidate has been named
  conceptually, but copying remains unauthorized until a later implementation
  gate explicitly approves it.
- `copy_approved` means a future governed copy candidate has passed all
  conceptual preconditions for copying, but this status alone still does not
  grant package creation, immutable evidence, runtime capture, evaluation, or
  trading authority.
- `copy_blocked` means copy metadata or policy blocks copying and must fail
  closed for downstream authority.
- `absent` means the copy candidate was explicitly declared absent under later
  governed terminal completion and run eligibility rules.
- `not_applicable` means the copy candidate is explicitly not applicable to
  the source reference, artifact class, run, or package section under later
  governed rules.
- `malformed` means copy metadata is structurally invalid.
- `ambiguous` means copy metadata cannot identify exactly one governed copy
  candidate, source, and controlled target.
- `stale` means copy metadata is not current enough for downstream use.
- `mixed_run` means copy metadata spans or conflicts with more than one run
  identity.
- `blocked_sensitive` means copy metadata or associated evidence is blocked by
  sensitive data exposure.
- `unknown` means copy status is unresolved and is not acceptable for
  downstream authority.

Unknown, missing, malformed, ambiguous, stale, mixed-run, sensitive, or blocked
copy status must fail closed for downstream authority.

Fail-closed handling:

- Missing copy status must fail closed.
- Unknown copy status must fail closed.
- Malformed copy metadata must fail closed.
- Ambiguous copy metadata must fail closed.
- Mixed-run copy metadata must fail closed.
- Stale copy metadata must fail closed.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absolute path smuggling must fail closed.
- Parent traversal must fail closed.
- Symlink or link-like path claims must fail closed until separately
  authorized.
- Directory traversal claims must fail closed.
- Absent declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- Copy success must not imply package completeness, immutable evidence,
  runtime capture, evaluation, promotion, broker/API authority, paper trading,
  or live trading.
- Artifact copying metadata that implies runtime log inspection, runtime
  artifact semantic inspection, uncontrolled file reads, path resolution
  outside approved boundaries, directory traversal, symlink traversal, package
  creation, manifest generation, hashing or integrity proof, storage,
  finalization, immutability, immutable evidence, runtime capture, evaluation,
  broker/API work, paper trading, or live trading must fail closed.

Required future test-only guards:

- Artifact copying vocabulary remains metadata-only unless separately
  authorized.
- Artifact copying cannot inspect runtime logs.
- Artifact copying cannot inspect runtime artifact content semantically.
- Artifact copying cannot imply uncontrolled file reads.
- Artifact copying cannot imply path resolution outside approved boundaries.
- Artifact copying cannot imply symlink traversal.
- Artifact copying cannot imply directory traversal.
- Artifact copying cannot imply package creation.
- Artifact copying cannot imply manifest generation.
- Artifact copying cannot imply hashing or integrity authority.
- Artifact copying cannot imply storage, finalization, or immutability.
- Artifact copying cannot imply immutable package evidence.
- Artifact copying cannot imply runtime capture.
- Artifact copying cannot imply evaluation, scoring, reporting, or promotion.
- Artifact copying cannot imply broker/API, execution, paper trading, or live
  trading authority.
- Absolute path smuggling fails closed.
- Parent traversal fails closed.
- Ambiguous copy metadata fails closed.
- Malformed copy metadata fails closed.
- Stale copy metadata fails closed.
- Mixed-run copy metadata fails closed.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.

Future implementation stop conditions:

- Need real runtime logs.
- Need semantic runtime artifact inspection.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need uncontrolled filesystem reads.
- Need uncontrolled filesystem writes.
- Need actual path resolution outside approved boundaries.
- Need symlink traversal.
- Need directory traversal.
- Need package creation.
- Need manifest generation.
- Need hashing or integrity proof.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need runtime capture.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Artifact copying authority is not runtime log access authority, runtime
artifact semantic inspection, uncontrolled file-read authority, package
creation, manifest generation, hashing or integrity proof,
storage/finalization/immutability authority, immutable package evidence,
runtime capture, evaluation, promotion, broker authority, execution
permission, paper trading approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_ARTIFACT_COPYING_AUTHORITY_GUARD`. That future gate must be
test-only and must not inspect runtime logs, inspect runtime artifacts, edit
production code, edit docs, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## Terminal Completion And Run Eligibility Authority Contract

Terminal completion and run eligibility authority remains governance-only and
is not implemented yet. This contract defines a conceptual authority boundary
after artifact copying authority, before package layout, package creation,
manifest generation, deterministic serialization, hashing, storage,
finalization, immutable package evidence, runtime capture, or evaluation
implementation can be considered.

This contract does not approve tests, code, terminal completion modules, run
eligibility modules, runtime log inspection, runtime artifact semantic
inspection, uncontrolled file reads, artifact copying, package layout
implementation, replay package creation, manifest generation, deterministic
serialization, hashing or integrity proof, storage, finalization,
immutability, immutable package evidence, runtime capture, evaluation,
promotion, broker work, paper trading, or live trading.

Terminal completion and run eligibility scope:

- Terminal completion means governed metadata that may later establish whether
  a run has exactly one acceptable terminal state for future capture
  consideration.
- Run eligibility means governed metadata conditions that may later establish
  whether a completed run can be considered for future capture planning.
- Runtime artifact discovery identifies metadata-only candidate artifact
  classes and states. Artifact copying governs future copy eligibility for
  already-approved ingestion candidates. Terminal completion and run
  eligibility governs whether a run is complete enough for future capture
  consideration. Package creation produces package output only under a later
  implementation gate. Runtime capture records approved runtime evidence only
  under a later implementation gate. Evaluation compares evidence only under a
  later evaluation gate.
- Terminal completion authority may only define whether a run can be
  considered complete enough for future capture consideration.
- Run eligibility authority may only define metadata conditions for future
  capture consideration.
- Terminal completion and run eligibility authority does not inspect runtime
  logs.
- Terminal completion and run eligibility authority does not inspect runtime
  artifact content.
- Terminal completion and run eligibility authority does not create packages.
- Terminal completion and run eligibility authority does not create immutable
  evidence.
- Terminal completion and run eligibility authority does not approve runtime
  capture.
- Terminal completion and run eligibility authority does not approve evaluation
  or promotion.
- Terminal and eligibility metadata may describe a run as complete, failed,
  cancelled, absent, not applicable, missing, duplicate, malformed, ambiguous,
  stale, mixed-run, blocked by sensitive data, or unknown, but those states do
  not grant downstream authority.

Terminal completion and run eligibility dependencies:

- Source Reference and Source Artifact Authority must be defined before
  terminal or eligibility metadata can bind to a governed source reference or
  artifact class.
- Provenance and Redaction Authority must be defined before terminal or
  eligibility metadata can be considered eligible for downstream planning.
- Runtime Artifact Discovery Authority must be defined before terminal or
  eligibility metadata can attach to discovered runtime artifact candidates.
- Source Path Authority must be defined before terminal or eligibility metadata
  can refer to governed source path metadata.
- File Path Ingestion Authority must be defined before terminal or eligibility
  metadata can refer to an ingestion candidate.
- Artifact Copying Authority must be defined before terminal or eligibility
  metadata can refer to copy candidate status.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact semantic inspection.
- Uncontrolled file reads.
- Artifact copying.
- Package layout authority.
- Replay package creation.
- Manifest generation.
- Deterministic serialization.
- Hashing or integrity proof.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Runtime capture.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual terminal completion and run eligibility vocabulary:

- `terminal_event`.
- `completion_event`.
- `completion_status`.
- `run_id`.
- `run_identity`.
- `run_eligibility_status`.
- `terminal_timestamp`.
- `terminal_timestamp_utc`.
- `run_started`.
- `run_completed`.
- `run_failed`.
- `run_cancelled`.
- `run_unknown`.
- `single_completion_event`.
- `duplicate_completion_event`.
- `missing_completion_event`.
- `mixed_run`.
- `stale_run`.
- `malformed_run_metadata`.
- Explicit absence declaration.
- Explicit not-applicable declaration.
- Metadata-only terminal completion result.
- Metadata-only run eligibility result.

This vocabulary is conceptual only. It does not create constants, types,
modules, runtime log reads, runtime artifact inspection, filesystem reads,
filesystem writes, artifact copies, package layout, package directories,
complete replay packages, manifests, canonical bytes, hashes, storage,
immutable evidence, runtime capture, evaluation inputs, broker authority, or
trading authority.

Required future terminal completion and run eligibility statuses:

- `complete` means a run has a governed future terminal-completion state, but
  this status alone does not grant runtime capture, package creation,
  immutable evidence, evaluation, or trading authority.
- `failed` means a run ended in a failed state and must fail closed for capture
  eligibility unless separately authorized.
- `cancelled` means a run ended in a cancelled state and must fail closed for
  capture eligibility unless separately authorized.
- `absent` means the terminal or eligibility evidence was explicitly declared
  absent under later governed rules.
- `not_applicable` means terminal or eligibility evidence is explicitly not
  applicable to the source reference, artifact class, run, or package section
  under later governed rules.
- `missing` means required terminal or eligibility evidence is missing.
- `duplicate` means more than one terminal event or completion state is present
  for the same governed run.
- `malformed` means terminal or eligibility metadata is structurally invalid.
- `ambiguous` means terminal or eligibility metadata cannot identify exactly
  one governed run completion state.
- `stale` means terminal or eligibility metadata is not current enough for
  downstream use.
- `mixed_run` means terminal or eligibility metadata spans or conflicts with
  more than one run identity.
- `blocked_sensitive` means terminal or eligibility metadata or associated
  evidence is blocked by sensitive data exposure.
- `unknown` means terminal or eligibility status is unresolved and is not
  acceptable for downstream authority.

Unknown, missing, duplicate, malformed, ambiguous, stale, mixed-run,
sensitive, failed, cancelled, or blocked status must fail closed for downstream
capture authority unless separately authorized.

Fail-closed handling:

- Missing run_id must fail closed.
- Missing terminal event must fail closed.
- Duplicate terminal events must fail closed.
- Ambiguous terminal event must fail closed.
- Malformed terminal event must fail closed.
- Mixed-run terminal metadata must fail closed.
- Stale terminal metadata must fail closed.
- Missing timestamp or timestamp_utc must fail closed.
- Inconsistent timestamp or timestamp_utc metadata must fail closed.
- Failed run state must fail closed for capture eligibility unless separately
  authorized.
- Cancelled run state must fail closed for capture eligibility unless
  separately authorized.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absent declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- Terminal completion must not imply package completeness, immutable evidence,
  runtime capture, evaluation, promotion, broker/API authority, paper trading,
  or live trading.
- Run eligibility metadata that implies runtime log inspection, runtime
  artifact semantic inspection, artifact copying, package layout authority,
  package creation, manifest generation, deterministic serialization, hashing
  or integrity proof, storage, finalization, immutability, immutable evidence,
  runtime capture, evaluation, broker/API work, paper trading, or live trading
  must fail closed.

Required future test-only guards:

- Terminal completion vocabulary remains metadata-only unless separately
  authorized.
- Run eligibility vocabulary remains metadata-only unless separately
  authorized.
- Terminal completion cannot inspect runtime logs.
- Terminal completion cannot inspect runtime artifacts.
- Run eligibility cannot imply artifact copying.
- Run eligibility cannot imply package layout.
- Run eligibility cannot imply package creation.
- Run eligibility cannot imply manifest generation.
- Run eligibility cannot imply deterministic serialization.
- Run eligibility cannot imply hashing or integrity authority.
- Run eligibility cannot imply storage, finalization, or immutability.
- Run eligibility cannot imply immutable package evidence.
- Run eligibility cannot imply runtime capture.
- Run eligibility cannot imply evaluation, scoring, reporting, or promotion.
- Run eligibility cannot imply broker/API, execution, paper trading, or live
  trading authority.
- Missing terminal metadata fails closed.
- Duplicate terminal metadata fails closed.
- Malformed terminal metadata fails closed.
- Ambiguous terminal metadata fails closed.
- Stale terminal metadata fails closed.
- Mixed-run terminal metadata fails closed.
- Failed run statuses remain non-authorizing.
- Cancelled run statuses remain non-authorizing.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.

Future implementation stop conditions:

- Need real runtime logs.
- Need semantic runtime artifact inspection.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need uncontrolled filesystem reads.
- Need uncontrolled filesystem writes.
- Need artifact copying.
- Need package layout implementation.
- Need package creation.
- Need manifest generation.
- Need deterministic serialization.
- Need hashing or integrity proof.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need runtime capture.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Terminal completion and run eligibility authority is not runtime log access
authority, runtime artifact semantic inspection, artifact copying, package
layout authority, package creation, manifest generation, deterministic
serialization authority, hashing or integrity proof,
storage/finalization/immutability authority, immutable package evidence,
runtime capture, evaluation, promotion, broker authority, execution
permission, paper trading approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_TERMINAL_COMPLETION_RUN_ELIGIBILITY_AUTHORITY_GUARD`. That future
gate must be test-only and must not inspect runtime logs, inspect runtime
artifacts, edit production code, edit docs, touch VPS, call broker APIs,
inspect `.env`, change scheduler/systemd, approve paper trading, or approve
live trading.

## Package Layout Authority Contract

Package layout authority remains governance-only and is not implemented yet.
This contract defines a conceptual authority boundary after terminal
completion and run eligibility authority, before package creation, manifest
generation, deterministic serialization, hashing, storage, finalization,
immutable package evidence, runtime capture, or evaluation implementation can
be considered.

This contract does not approve tests, code, package layout modules, package
directory creation, package file creation, filesystem writes, artifact
copying, runtime log inspection, runtime artifact semantic inspection,
uncontrolled file reads, replay package creation, manifest generation,
deterministic serialization, hashing or integrity proof, storage,
finalization, immutability, immutable package evidence, runtime capture,
evaluation, promotion, broker work, paper trading, or live trading.

Package layout scope:

- Package layout means governed metadata that may later define the intended
  replay package structure, package identity boundaries, package sections,
  section names, and separation between mutable and immutable package areas.
- Artifact copying governs future copy eligibility for already-approved
  ingestion candidates. Terminal completion and run eligibility governs whether
  a run is complete enough for future capture consideration. Package layout
  governs intended future structure only. Package creation produces package
  output only under a later implementation gate. Manifest generation records
  package metadata only under a later implementation gate. Immutable evidence
  requires later hashing, storage, finalization, and immutability authority.
  Runtime capture records approved runtime evidence only under a later
  implementation gate. Evaluation compares evidence only under a later
  evaluation gate.
- Package layout authority may only define the intended future structure,
  sections, names, identity boundaries, and separation of mutable and
  immutable package areas.
- Package layout authority does not create package directories.
- Package layout authority does not create package files.
- Package layout authority does not copy artifacts.
- Package layout authority does not generate manifests.
- Package layout authority does not serialize package content.
- Package layout authority does not hash content.
- Package layout authority does not finalize storage.
- Package layout authority does not create immutable evidence.
- Package layout authority does not approve runtime capture.
- Package layout authority does not approve evaluation or promotion.
- Package layout metadata may describe a layout as declared, draft, blocked,
  absent, not applicable, missing, malformed, ambiguous, stale, mixed-run,
  blocked by sensitive data, or unknown, but those states do not grant
  downstream authority.

Package layout dependencies:

- Source Reference and Source Artifact Authority must be defined before layout
  metadata can bind package sections to governed source references or artifact
  classes.
- Provenance and Redaction Authority must be defined before layout metadata can
  be considered eligible for downstream planning.
- Runtime Artifact Discovery Authority must be defined before layout metadata
  can target discovered runtime artifact classes.
- Source Path Authority must be defined before layout metadata can refer to
  governed source path metadata.
- File Path Ingestion Authority must be defined before layout metadata can
  refer to ingestion candidates.
- Artifact Copying Authority must be defined before layout metadata can refer
  to copy candidate status.
- Terminal Completion and Run Eligibility Authority must be defined before
  layout metadata can target a capture-eligible run.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact semantic inspection.
- Uncontrolled file reads.
- Artifact copying.
- Filesystem writes.
- Package directory creation.
- Package file creation.
- Replay package creation.
- Manifest generation.
- Deterministic serialization.
- Hashing or integrity proof.
- Storage, finalization, or immutability.
- Immutable package evidence.
- Runtime capture.
- Evaluation, scoring, reporting, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual package layout vocabulary:

- `replay_package_layout`.
- `package_identity`.
- `package_sections`.
- `immutable_evidence_section`.
- `mutable_evaluation_section`.
- `artifact_section`.
- `manifest_section`.
- `provenance_section`.
- `redaction_section`.
- `layout_version`.
- `layout_status`.
- `package_root_concept`.
- `package_path_concept`.
- `section_boundary`.
- `downstream_output_boundary`.
- Explicit absence declaration.
- Explicit not-applicable declaration.
- Metadata-only package layout result.

This vocabulary is conceptual only. It does not create constants, types,
modules, directories, files, filesystem writes, artifact copies, complete
replay packages, manifests, canonical bytes, hashes, storage, immutable
evidence, runtime capture, evaluation inputs, broker authority, or trading
authority.

Required future package layout statuses:

- `layout_declared` means a package layout has been named conceptually, but
  package creation remains unauthorized until a later implementation gate
  explicitly approves it.
- `layout_draft` means a layout remains draft-only and non-authoritative for
  downstream package creation, immutable evidence, runtime capture, or
  evaluation.
- `layout_blocked` means layout metadata or policy blocks downstream package
  use and must fail closed.
- `absent` means layout evidence was explicitly declared absent under later
  governed rules.
- `not_applicable` means layout evidence is explicitly not applicable to the
  source reference, artifact class, run, or package section under later
  governed rules.
- `missing` means required layout metadata is missing.
- `malformed` means layout metadata is structurally invalid.
- `ambiguous` means layout metadata cannot identify exactly one governed
  package identity, version, section set, or section boundary.
- `stale` means layout metadata is not current enough for downstream use.
- `mixed_run` means layout metadata spans or conflicts with more than one run
  identity.
- `blocked_sensitive` means layout metadata or associated evidence is blocked
  by sensitive data exposure.
- `unknown` means layout status is unresolved and is not acceptable for
  downstream authority.

Unknown, missing, malformed, ambiguous, stale, mixed-run, sensitive, blocked,
or draft-only status must fail closed for downstream package creation,
immutable evidence, runtime capture, or evaluation authority unless separately
authorized.

Fail-closed handling:

- Missing layout status must fail closed.
- Unknown layout status must fail closed.
- Malformed layout metadata must fail closed.
- Ambiguous layout metadata must fail closed.
- Mixed-run layout metadata must fail closed.
- Stale layout metadata must fail closed.
- Missing layout version must fail closed.
- Unknown layout version must fail closed.
- Missing package identity must fail closed.
- Ambiguous package identity must fail closed.
- Missing section boundaries must fail closed.
- Overlapping mutable and immutable section boundaries must fail closed.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absent declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- Layout declaration must not imply package creation, manifest generation,
  deterministic serialization, hashing, storage, finalization, immutable
  evidence, runtime capture, evaluation, promotion, broker/API authority, paper
  trading, or live trading.
- Package layout metadata that implies runtime log inspection, runtime artifact
  semantic inspection, artifact copying, filesystem writes, package directory
  creation, package file creation, package creation, manifest generation,
  deterministic serialization, hashing or integrity proof, storage,
  finalization, immutability, immutable evidence, runtime capture, evaluation,
  broker/API work, paper trading, or live trading must fail closed.

Required future test-only guards:

- Package layout vocabulary remains metadata-only unless separately
  authorized.
- Package layout cannot inspect runtime logs.
- Package layout cannot inspect runtime artifacts.
- Package layout cannot imply artifact copying.
- Package layout cannot imply filesystem writes.
- Package layout cannot imply package directory creation.
- Package layout cannot imply package file creation.
- Package layout cannot imply package creation.
- Package layout cannot imply manifest generation.
- Package layout cannot imply deterministic serialization.
- Package layout cannot imply hashing or integrity authority.
- Package layout cannot imply storage, finalization, or immutability.
- Package layout cannot imply immutable package evidence.
- Package layout cannot imply runtime capture.
- Package layout cannot imply evaluation, scoring, reporting, or promotion.
- Package layout cannot imply broker/API, execution, paper trading, or live
  trading authority.
- Missing layout metadata fails closed.
- Malformed layout metadata fails closed.
- Ambiguous layout metadata fails closed.
- Stale layout metadata fails closed.
- Mixed-run layout metadata fails closed.
- Missing package identity fails closed.
- Ambiguous package identity fails closed.
- Overlapping mutable and immutable section boundaries fail closed.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.

Future implementation stop conditions:

- Need real runtime logs.
- Need semantic runtime artifact inspection.
- Need secrets.
- Need `.env` access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need uncontrolled filesystem reads.
- Need uncontrolled filesystem writes.
- Need artifact copying.
- Need package directory creation.
- Need package file creation.
- Need package creation.
- Need manifest generation.
- Need deterministic serialization.
- Need hashing or integrity proof.
- Need storage, finalization, or immutability.
- Need immutable evidence.
- Need runtime capture.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need VPS, runtime, service, scheduler, or systemd changes.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Package layout authority is not runtime log access authority, runtime artifact
semantic inspection, artifact copying, filesystem write authority, package
creation, manifest generation, deterministic serialization authority, hashing
or integrity proof, storage/finalization/immutability authority, immutable
package evidence, runtime capture, evaluation, promotion, broker authority,
execution permission, paper trading approval, or live trading approval.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_PACKAGE_LAYOUT_AUTHORITY_GUARD`. That future gate must be test-only
and must not inspect runtime logs, inspect runtime artifacts, edit production
code, edit docs, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## Package Creation Authority Contract

Package creation authority remains governance-only and is not implemented yet.
This contract defines a conceptual authority boundary after package layout
authority, before manifest generation, deterministic serialization, hashing,
storage, finalization, immutable package evidence, runtime capture, or
evaluation implementation can be considered.

This contract does not approve tests, code, package creation constants,
package builder types, package creation modules, package directories, package
files, package artifacts, manifest generation, deterministic serialization,
hashing or integrity implementation, storage, finalization, immutability,
immutable package evidence, runtime capture, evaluation, promotion, broker
work, runtime validation, scheduler or systemd changes, credential changes,
strategy changes, risk changes, execution changes, order submission, order
cancellation, flattening, cleanup, paper trading, or live trading.

Package creation authority scope:

- Package creation authority means governed metadata that may later describe
  when a future implementation is allowed to assemble a replay package from
  already-governed inputs into a controlled package output.
- Package creation authority may describe future package creation preconditions,
  input classes, lifecycle state boundaries, draft-only behavior, package
  identity requirements, package layout dependency, source artifact
  prerequisites, and downstream authority boundaries.
- Package layout authority defines intended structure only. Package creation
  authority may describe when that structure could be assembled by a future
  implementation, but it still does not create directories, files, artifacts,
  manifests, canonical bytes, hashes, storage records, immutable evidence,
  runtime capture output, evaluation output, or promotion output.
- Package creation authority remains metadata-only and non-authorizing until a
  separate future implementation gate explicitly approves executable package
  creation behavior.
- Package creation authority does not create package directories.
- Package creation authority does not create package files.
- Package creation authority does not copy artifacts.
- Package creation authority does not generate manifests.
- Package creation authority does not serialize package content.
- Package creation authority does not hash content.
- Package creation authority does not write storage.
- Package creation authority does not finalize packages.
- Package creation authority does not create immutable package evidence.
- Package creation authority does not approve runtime capture.
- Package creation authority does not approve evaluation or promotion.
- Package creation authority does not approve broker/API/TWS work, runtime
  validation, scheduler/systemd changes, credential changes, strategy changes,
  risk changes, execution changes, order submission, order cancellation,
  flattening, cleanup, paper trading, or live trading.

Package creation authority dependencies:

- Source Reference and Source Artifact Authority must be defined before package
  creation metadata can bind package inputs to governed source references or
  artifact classes.
- Provenance and Redaction Authority must be defined before package creation
  metadata can be considered eligible for downstream planning.
- Runtime Artifact Discovery Authority must be defined before package creation
  metadata can reference discovered runtime artifact classes.
- Source Path Authority must be defined before package creation metadata can
  refer to governed source path metadata.
- File Path Ingestion Authority must be defined before package creation
  metadata can refer to ingestion candidates.
- Artifact Copying Authority must be defined before package creation metadata
  can refer to copied artifacts.
- Terminal Completion and Run Eligibility Authority must be defined before
  package creation metadata can target a capture-eligible run.
- Package Layout Authority must be defined before package creation metadata can
  target package structure, package identity, section boundaries, or output
  shape.
- Downstream authorities are not granted by this contract.

Explicitly forbidden authority:

- Runtime log inspection.
- Runtime artifact semantic inspection.
- Uncontrolled file reads.
- Artifact copying.
- Filesystem writes.
- Package directory creation.
- Package file creation.
- Package artifact creation.
- Manifest generation.
- Deterministic serialization.
- Canonical byte generation.
- Hashing or integrity implementation.
- Storage, finalization, or immutability implementation.
- Immutable package evidence implementation.
- Runtime capture.
- Evaluation, scoring, reporting, attribution, or promotion.
- Broker/API/TWS/IBKR/Alpaca authority.
- Runtime validation.
- Scheduler or systemd changes.
- Credential or `.env` changes.
- Strategy, risk, or execution changes.
- Order submission.
- Order cancellation.
- Flattening, selling, cleanup, retry, or remediation.
- Execution permission.
- Paper trading authority.
- Live trading authority.

Allowed future conceptual package creation vocabulary:

- `package_creation_authority`.
- `package_creation_request`.
- `package_creation_plan`.
- `package_creation_status`.
- `package_creation_preconditions`.
- `package_creation_inputs`.
- `package_creation_output_boundary`.
- `draft_package_creation`.
- `package_identity_binding`.
- `package_layout_binding`.
- `package_section_assignment`.
- `package_lifecycle_state`.
- `package_creation_fail_closed_reason`.
- `documentation_authority_only`.
- `implementation_authority_required`.
- Metadata-only package creation authority result.

This vocabulary is conceptual only. It does not create constants, types,
modules, package directories, package files, package artifacts, manifests,
canonical bytes, serialized bytes, hashes, storage records, finalized packages,
immutable evidence, runtime capture, evaluation inputs, promotion paths, broker
authority, runtime authority, scheduler/systemd authority, credential
authority, strategy/risk/execution authority, order authority, or trading
authority.

Required future package creation statuses:

- `creation_declared` means package creation has been named conceptually, but
  executable package creation remains unauthorized until a later implementation
  gate explicitly approves it.
- `creation_planned` means package creation prerequisites are documented, but
  no package creation behavior is approved.
- `creation_blocked` means package creation metadata or policy blocks
  downstream package creation and must fail closed.
- `draft_only` means any future approved package creation may produce only
  draft, non-finalized, non-authoritative package output.
- `absent` means package creation evidence was explicitly declared absent
  under later governed rules.
- `not_applicable` means package creation evidence is explicitly not
  applicable to the source reference, artifact class, run, or package section
  under later governed rules.
- `missing` means required package creation metadata is missing.
- `malformed` means package creation metadata is structurally invalid.
- `ambiguous` means package creation metadata cannot identify exactly one
  governed package identity, layout, input set, lifecycle state, or output
  boundary.
- `stale` means package creation metadata is not current enough for downstream
  use.
- `mixed_run` means package creation metadata spans or conflicts with more than
  one run identity.
- `blocked_sensitive` means package creation metadata or associated evidence is
  blocked by sensitive data exposure.
- `unknown` means package creation status is unresolved and is not acceptable
  for downstream authority.

Unknown, missing, malformed, ambiguous, stale, mixed-run, sensitive, blocked,
planned-only, declared-only, or draft-only status must fail closed for manifest
generation, deterministic serialization, hashing, storage, finalization,
immutable package evidence, runtime capture, evaluation, promotion, broker
authority, paper trading, or live trading unless separately authorized.

Fail-closed handling:

- Missing package creation status must fail closed.
- Unknown package creation status must fail closed.
- Malformed package creation metadata must fail closed.
- Ambiguous package creation metadata must fail closed.
- Mixed-run package creation metadata must fail closed.
- Stale package creation metadata must fail closed.
- Missing package creation plan must fail closed.
- Unknown package creation plan must fail closed.
- Missing package identity must fail closed.
- Ambiguous package identity must fail closed.
- Missing package layout binding must fail closed.
- Missing source artifact authority must fail closed.
- Missing provenance must fail closed.
- Invalid provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Sensitive-data markers must fail closed.
- Absent declarations must be explicit and non-authorizing.
- Not-applicable declarations must be explicit and non-authorizing.
- Any ambiguity between documentation authority and implementation authority
  must fail closed.
- Any ambiguity between draft package creation and finalized immutable evidence
  must fail closed.
- Package creation declaration must not imply manifest generation,
  deterministic serialization, hashing, storage, finalization, immutable
  evidence, runtime capture, evaluation, promotion, broker/API authority,
  runtime validation, scheduler/systemd authority, credential authority,
  strategy/risk/execution authority, order authority, paper trading, or live
  trading.
- Package creation metadata that implies runtime log inspection, runtime
  artifact semantic inspection, artifact copying, filesystem writes, package
  directory creation, package file creation, manifest generation,
  deterministic serialization, hashing or integrity proof, storage,
  finalization, immutability, immutable evidence, runtime capture, evaluation,
  broker/API work, runtime validation, scheduler/systemd changes, credential
  changes, strategy/risk/execution changes, order submission, order
  cancellation, flattening, cleanup, paper trading, or live trading must fail
  closed.

Required future test-only guards:

- Package creation vocabulary remains metadata-only unless separately
  authorized.
- Documentation authority cannot imply implementation authority.
- Package creation authority cannot inspect runtime logs.
- Package creation authority cannot inspect runtime artifacts.
- Package creation authority cannot imply uncontrolled file reads.
- Package creation authority cannot imply artifact copying.
- Package creation authority cannot imply filesystem writes.
- Package creation authority cannot imply package directory creation.
- Package creation authority cannot imply package file creation.
- Package creation authority cannot imply package artifact creation.
- Package creation authority cannot imply manifest generation.
- Package creation authority cannot imply deterministic serialization.
- Package creation authority cannot imply hashing or integrity authority.
- Package creation authority cannot imply storage, finalization, or
  immutability.
- Package creation authority cannot imply immutable package evidence.
- Package creation authority cannot imply runtime capture.
- Package creation authority cannot imply evaluation, scoring, reporting,
  attribution, or promotion.
- Package creation authority cannot imply broker/API, execution, paper
  trading, or live trading authority.
- Package creation authority cannot imply runtime validation,
  scheduler/systemd, credential, strategy, risk, execution, order submission,
  order cancellation, flattening, or cleanup authority.
- Missing or ambiguous package identity fails closed.
- Missing or ambiguous layout binding fails closed.
- Missing, malformed, ambiguous, stale, or mixed-run package creation metadata
  fails closed.
- Absent declarations remain explicit and non-authorizing.
- Not-applicable declarations remain explicit and non-authorizing.

Future implementation stop conditions:

- Need package creation code, constants, types, modules, or builders.
- Need package directories.
- Need package files.
- Need package artifact paths.
- Need manifest paths.
- Need hash paths.
- Need storage paths.
- Need promotion paths.
- Need real runtime logs.
- Need semantic runtime artifact inspection.
- Need secrets.
- Need `.env` or credential access.
- Need broker/API/TWS/IBKR/Alpaca access.
- Need runtime validation.
- Need scheduler or systemd changes.
- Need strategy, risk, execution, or config behavior changes.
- Need uncontrolled filesystem reads.
- Need uncontrolled filesystem writes.
- Need artifact copying.
- Need manifest generation.
- Need deterministic serialization.
- Need canonical byte generation.
- Need hashing or integrity proof.
- Need storage, finalization, or immutability.
- Need immutable package evidence.
- Need runtime capture.
- Need evaluation, scoring, reporting, attribution, or promotion.
- Need order submission, order cancellation, flattening, selling, cleanup,
  retry, or remediation.
- Need paper trading or live trading authority.

Downstream non-authority boundaries:

Package creation authority is not runtime log access authority, runtime
artifact semantic inspection, artifact copying, filesystem write authority,
package artifact creation, manifest generation, deterministic serialization
authority, hashing or integrity proof, storage/finalization/immutability
authority, immutable package evidence, runtime capture, evaluation, promotion,
broker authority, runtime validation, scheduler/systemd authority, credential
authority, strategy/risk/execution authority, order authority, execution
permission, paper trading approval, or live trading approval.

Required future validation evidence:

- Future validation must distinguish documentation authority from
  implementation authority.
- Future validation must prove that no code path, runtime path, package
  artifact path, manifest path, hash path, storage path, or promotion path was
  created or changed unless a separate implementation gate explicitly approved
  that work.
- Future validation must prove package creation metadata remains
  non-authorizing for immutable evidence, runtime capture, evaluation,
  promotion, broker/API work, runtime validation, scheduler/systemd changes,
  credential changes, strategy changes, risk changes, execution changes,
  order submission, order cancellation, flattening, cleanup, paper trading, or
  live trading.

Proposed next gate:

After this docs-only contract is committed and reviewed, the next safe gate is
`TEST_ONLY_PACKAGE_CREATION_AUTHORITY_GUARD`. That future gate must be
test-only and must not inspect runtime logs, inspect runtime artifacts, edit
production code, edit docs, touch VPS, call broker APIs, inspect `.env`, change
scheduler/systemd, approve paper trading, or approve live trading.

## Runtime Capture Authority Contract

Runtime capture authority remains governance-only and is not implemented yet.
This contract does not approve tests, code, runtime capture constants, runtime
capture types, runtime capture modules, source artifact discovery, source path
ingestion, artifact copying, filesystem reads, filesystem writes, runtime
artifact ingestion, replay package creation, manifest generation, canonical
byte generation, hashing or integrity validation, storage, finalization,
evaluation, broker work, execution permission, or live trading.

Runtime capture rules must be source-controlled before implementation.
Already-loaded dictionaries and `ReplayInputBundle` remain the only current
accepted replay inputs. Path-like runtime artifact inputs remain forbidden
until a separate implementation gate approves source path authority. No
runtime artifact capture, source artifact discovery, source path ingestion,
file path ingestion, artifact copying, filesystem read/write, manifest
generation, package creation, storage, or finalization is approved by this
contract.

Required future source artifact authority:

- Source artifact authority must be explicitly governed before capture.
- Source reference authority must be explicitly governed before capture.
- Source path authority must be explicitly governed before capture.
- Runtime artifact discovery authority must be explicitly governed before
  capture.
- File path ingestion authority must be explicitly governed before capture.
- Artifact copying authority must be explicitly governed before capture.
- Eligible runtime artifact vocabulary must be explicitly governed before
  capture.
- Unknown source references, unknown source paths, unclear artifact ownership,
  unapproved runtime locations, ungoverned discovery, and unapproved artifact
  copying must fail closed.

Eligible future runtime artifacts, subject to later gates:

- JSONL event streams.
- `last_run_report.json`, only as derived operational summary evidence matched
  to JSONL `run_id`.
- `order_state.json`, only as separate operational state evidence with explicit
  provenance or explicit absence.
- Observations, only when run-filtered, append-only, and provenance-tagged.
- Runtime visibility evidence, only as observed/readiness evidence with
  explicit provenance or explicit absence/not-applicable status.
- Config or code metadata.
- Market input evidence.
- Strategy input/output evidence.
- Portfolio/risk state evidence.
- Broker-visible state evidence, only as observed evidence and never as broker
  authority.
- Reconciliation/risk evidence.

Required future runtime artifact evidence boundaries:

- JSONL event streams remain canonical event chronology.
- Terminal completion event requirements must be explicit before runtime
  capture can treat a run as capture-eligible or authoritative.
- `last_run_report.json` remains a derived operational summary and cannot
  alone create replay package authority.
- Observations remain separate append-only evidence and must be run-filtered
  before future capture.
- Runtime visibility remains observed/readiness evidence only and cannot
  create broker authority, execution authority, cleanup authority, submit
  readiness, or live trading authority.
- Broker-visible state evidence remains observed evidence only and never broker
  authority.

Required future dependency rules:

- Package layout authority must exist before runtime capture can target replay
  package shape.
- Package creation authority must exist before runtime capture can produce
  replay package output.
- Manifest schema authority must exist before runtime capture can populate
  manifest-shaped metadata.
- Deterministic serialization authority must exist before runtime capture can
  rely on canonical bytes.
- Hashing and integrity validation must exist before runtime capture can rely
  on hash or integrity status.
- Storage and finalization authority must exist before runtime capture can
  persist captured artifacts.
- Runtime capture must remain separate from manifest generation.
- Runtime capture must remain separate from package creation.
- Runtime capture must remain separate from storage and finalization.
- Runtime capture must remain separate from evaluation and promotion.

Required future capture eligibility rules:

- Runtime capture inputs must have strict `run_id` alignment.
- Terminal completion is required before runtime capture can treat a run as
  capture-eligible.
- Missing `run_id` must fail closed.
- Mixed-`run_id` artifacts must fail closed.
- Stale artifacts must fail closed.
- Missing artifacts must fail closed unless explicitly declared absent or not
  applicable.
- Ambiguous artifacts must fail closed.
- Malformed artifacts must fail closed.
- Runtime visibility ambiguity must fail closed.
- Missing absent or not-applicable declarations must fail closed.

Required future provenance and redaction rules:

- Provenance must be explicit before runtime capture.
- Provenance must be recorded per source artifact and package section when
  capture is later approved.
- Source path or source reference authority must be explicit before capture.
- Capture timestamp must be recorded when capture is later approved.
- Decision timestamp must be recorded for decision-relevant artifacts when
  applicable.
- Redaction status must be explicit before runtime capture.
- Redaction and sanitization status must be explicit before capture, storage,
  indexing, or package creation.
- Missing provenance must fail closed.
- Missing redaction status must fail closed.
- Invalid redaction status must fail closed.
- Broker/account-sensitive identifiers require explicit safe handling.
- Sensitive data exposure must stop runtime capture, storage, indexing,
  package creation, evaluation, and finalization.

Required absent and not-applicable declarations:

- Absent artifacts require deterministic declarations.
- Not-applicable artifacts require deterministic declarations.
- Absent and not-applicable states must remain distinguishable.
- Missing declarations must fail closed.

Runtime capture execution boundaries:

- Runtime capture must not mutate runtime state.
- Runtime capture must not call `main.py`.
- Runtime capture must not stop or start timers.
- Runtime capture must not call broker/API/TWS/Alpaca/IBKR.
- Runtime capture must not respond to or remediate blocked buy/sell signals.
- Runtime capture must not submit, cancel, flatten, sell, cleanup, retry,
  remediate, or otherwise affect broker state.
- Runtime capture must not approve live trading.

Runtime capture cannot authorize manifest authority, manifest generation,
replay package creation, package authority, package completeness, complete
replay package status, finalized immutable replay package status, deterministic
serialization, canonical byte generation, hashing or integrity validation,
storage, finalization, evaluation, attribution, promotion, broker work,
execution permission, strategy or risk behavior changes, cleanup, flatten,
sell, cancel, remediation, or live trading.
`build_draft_replay_envelope(...)` remains draft scaffold evidence only.
`build_replay_package(...)` mapper scaffold completeness remains distinct from
complete replay package authority. Runtime capture cannot become
broker-visible truth, runtime truth, package truth, manifest truth, hash truth,
storage truth, evaluation truth, promotion truth, execution permission, or live
trading authority.

Runtime capture stop conditions:

- Need runtime capture constants.
- Need runtime capture types.
- Need runtime capture code.
- Need runtime capture modules.
- Need source artifact discovery.
- Need source path ingestion.
- Need file path ingestion.
- Need artifact copying.
- Need filesystem reads or writes.
- Need runtime artifact ingestion.
- Need replay package creation.
- Need package directories.
- Need storage paths.
- Need manifest generation.
- Need canonical byte generation.
- Need deterministic serialization.
- Need hashing or integrity validation.
- Need storage, finalization, or immutability.
- Need evaluation, attribution, or promotion.
- Need broker/API/TWS/Alpaca/IBKR.
- Need `main.py`.
- Missing package layout authority.
- Missing package creation authority.
- Missing manifest schema authority.
- Missing deterministic serialization authority.
- Missing hashing or integrity authority.
- Missing storage or finalization authority.
- Missing source artifact authority.
- Missing source path or source reference authority.
- Missing runtime artifact discovery authority.
- Missing file path ingestion authority.
- Missing artifact copying authority.
- Missing eligible runtime artifact vocabulary.
- Missing canonical `run_id`.
- Missing `run_id`.
- Mixed `run_id`.
- Missing terminal completion.
- Stale artifact.
- Missing artifact without absent or not-applicable declaration.
- Ambiguous artifact.
- Malformed artifact.
- Unknown source reference.
- Missing provenance.
- Missing redaction status.
- Invalid redaction state.
- Sensitive data exposure.
- Runtime visibility ambiguity.
- Implied manifest authority.
- Implied package creation authority.
- Implied package completeness.
- Implied hash or integrity authority.
- Implied storage or finalization authority.
- Implied evaluation or promotion authority.
- Implied broker authority.
- Implied execution permission.
- Implied live trading authority.

## Replay Package Envelope Schema Planning

The replay package envelope is a docs-only schema planning record. It is not
implemented.

## Replay Mapper and Schema Governance Rebase

The current offline mapper and schema remain scaffold-level only.

Current mapper boundary:

- The mapper is an offline in-memory scaffold.
- It accepts already-loaded dictionaries only.
- It does not implement file path ingestion.
- It does not implement runtime capture.
- It does not implement writer behavior.
- It does not implement storage, immutability, hashing, manifest, or integrity
  enforcement.
- It does not implement evaluation, attribution, experiment registry, or
  promotion logic.

Current schema boundary:

- The schema is a planning scaffold, not an authoritative production replay
  package schema.
- Current schema constants and helper shapes must not be interpreted as
  implemented package governance.
- Event JSONL remains canonical for current `run_id` alignment.
- Event-only fixtures remain incomplete, evidence-only, non-authoritative, and
  not complete replay packages.
- Mixed event `run_id` values and mismatched report, state, observation, or
  runtime visibility evidence keep scaffold output incomplete.

Scaffold completeness boundary:

- Current `complete` status means only that tracked in-memory buckets are
  present and aligned under current scaffold rules.
- Current `complete` status does not mean immutable replay package
  completeness.
- Current `complete` status does not authorize evaluation, promotion, runtime
  capture, writer behavior, storage, broker work, strategy or risk behavior
  changes, or live trading.
- Present and absent markers are provisional and too coarse for future package
  authority.

Future governance must define absent, not-applicable, disabled, unavailable,
stale, redacted, untrusted, and unknown semantics before complete replay
packages can be authoritative.

Missing prerequisites before complete replay package authority include:

- Implemented package schema and migration policy.
- File ingestion rules, if any.
- Writer authority gate.
- Package layout gate.
- Runtime capture gate.
- Storage, finalization, immutability, retention, and discovery rules.
- Hashing, manifest, and integrity enforcement.
- Provenance enforcement.
- Redaction enforcement.
- Section-level required-field validation.
- Status vocabulary governance.
- As-of eligibility checks.
- Portfolio/risk state capture implementation.
- Broker-visible state capture implementation, if used.
- Evaluation, attribution, experiment, and promotion gates.

Current mapper and schema outputs cannot authorize:

- Complete replay package status.
- Runtime capture.
- File ingestion.
- Writer behavior.
- Storage.
- Hashing or manifest enforcement.
- Evaluation.
- Attribution.
- Promotion.
- Broker/API/TWS/IBKR/Alpaca work.
- Execution permission.
- Strategy or risk behavior changes.
- Live trading.

Purpose:

- Standardize package identity.
- Standardize schema versioning.
- Standardize references to package evidence sections.
- Standardize integrity and immutability markers.
- Standardize section status.
- Preserve explicit authority boundaries.

Proposed top-level sections:

- `package_identity`
- `schema`
- `source_control`
- `run_identity`
- `replay_window`
- `environment_classification`
- `package_status`
- `configuration_references`
- `market_input_references`
- `strategy_decision_references`
- `portfolio_risk_snapshot_references`
- `broker_visible_state_references`
- `reconciliation_risk_references`
- `event_order_references`
- `attribution`
- `integrity`
- `immutability`
- `authority_boundary`
- `out_of_scope`

Required `package_identity` fields:

- `package_id`
- `package_created_at`
- `package_producer`
- `parent_package_ids`
- `related_package_ids`

Required `schema` fields:

- `replay_package_schema_version`
- `schema_status`
- `schema_migration_policy`
- `compatible_reader_min_version`

Required `source_control` fields:

- `commit_sha`
- `branch_or_release`
- `worktree_status`
- `dirty_worktree_indicator`
- `source_control_remote`

Required `run_identity` fields:

- `run_id`
- `trigger_source`
- `runtime_entrypoint`
- `dirty_worktree_indicator`
- `operator_or_automation_classification`

Required `replay_window` fields:

- `window_start`
- `window_end`
- `timezone`
- `calendar_assumptions`
- `market_session_assumptions`

Required `environment_classification` fields:

- `environment_name`
- `environment_type`
- `broker_endpoint_classification`
- `runtime_visibility_enabled`
- `secrets_excluded`

Required `package_status` fields:

- `status`
- `completeness_status`
- `section_statuses`
- `invalidated_reason`
- `correction_references`

Required reference sections:

- `configuration_references`: references to sanitized runtime configuration,
  feature flags, and governed policy versions.
- `market_input_references`: references to provider identity, symbol, timeframe
  or window, candle bundle, returned candle count, adjustment assumptions, and
  data warnings.
- `strategy_decision_references`: references to strategy identifier, strategy
  version, parameter version, input payload, signal result, action proposal,
  validation result, and strategy evaluation timestamp.
- `portfolio_risk_snapshot_references`: references to portfolio snapshot
  identifier, snapshot schema version, position/exposure records, saturation
  records, and data freshness status.
- `broker_visible_state_references`: references to observed-only broker state,
  provider status, observation timestamp, freshness, errors, and safe account
  scope where approved.
- `reconciliation_risk_references`: references to reconciliation evidence,
  risk-governance decision, applicable caps, pass/block/defer/manual-review
  results, ambiguity markers, and decision timestamps.
- `event_order_references`: references to ordered event stream identifier,
  stable event identifiers, stage names, timestamps, terminal event, early-stop
  markers, and out-of-order/correction markers.

Required `attribution` fields:

- `baseline_version_reference`
- `candidate_version_reference`
- `difference_cause`
- `difference_cause_status`
- `unknown_or_ambiguous_cause`
- `attribution_notes_reference`

Required `integrity` fields:

- `content_hash`
- `section_hashes`
- `hash_algorithm`
- `required_section_check`
- `terminal_event_check`
- `schema_validation_status`

Required `immutability` fields:

- `finalized`
- `finalized_at`
- `append_only_corrections`
- `correction_references`
- `annotation_references`

Required `authority_boundary` fields:

- `evidence_only`
- `non_authoritative`
- `no_runtime_mutation`
- `no_execution_authority`
- `no_broker_authority`
- `no_strategy_behavior_change`
- `no_secret_material`

Required `out_of_scope` fields:

- `replay_writer_implementation`
- `runtime_capture_implementation`
- `jsonl_observation_schema_changes`
- `main_py_changes`
- `broker_live_api_calls`
- `ibkr_tws`
- `alpaca_calls`
- `vps_validation`
- `strategy_behavior_changes`
- `risk_reconciliation_behavior_changes`
- `execution_sell_trim_rebalance_resize_promotion_behavior`

Future required gates:

- Schema implementation gate.
- Runtime capture gate.
- Storage and immutability gate.
- Integrity validation gate.
- Attribution gate.
- Evaluation tooling gate.
- Promotion workflow gate.

This envelope schema planning does not approve replay writer implementation,
runtime capture implementation, JSONL or observation schema changes, `main.py`
changes, broker/live/API calls, IBKR/TWS work, Alpaca calls, VPS validation,
strategy behavior changes, risk/reconciliation behavior changes, execution,
sell, trim, rebalance, resize, or promotion behavior.

## Replay Sample Eligibility Contract

This contract classifies future replay samples before any artifact copying,
replay package writer, runtime capture, storage, immutability, or evaluation
lane is approved.

### `EVENT_STREAM_REPLAY_FIXTURE`

An `EVENT_STREAM_REPLAY_FIXTURE` is an event JSONL-only fixture.

It is valid only for reviewing:

- event ordering
- stage coverage
- terminal outcome
- market, strategy, risk, and reconcile sequencing

It is not a complete replay package. It does not approve strategy promotion,
evaluation authority, runtime capture, replay writer implementation, artifact
storage, broker authority, API work, or live trading.

### Future Controlled Event-Stream Fixture Intake Planning

This is a docs-only planning record for possible future event JSONL-only
fixture intake. It does not approve artifact copying, fixture file creation,
replay package creation, file ingestion, writer implementation, runtime
capture, storage, immutability, evaluation, broker/API work, strategy
promotion, or live trading.

Fixture classification:

- `EVENT_STREAM_REPLAY_FIXTURE` remains event JSONL-only.
- It is useful for event ordering, stage coverage, terminal outcome, and
  market, strategy, risk, and reconcile sequencing review.
- It is not a complete replay package.
- It cannot authorize strategy promotion, evaluation, runtime capture, writer
  implementation, broker/API work, or live trading.

Candidate eligibility for a future proposed event-stream fixture:

- One canonical `run_id`.
- All events share the same `run_id`.
- Ordered `event_id` values.
- Timestamps present.
- Terminal completion event present.
- `schema_version` present.
- `event_type`, `stage`, and `status` present.
- No mixed-run events.
- No manual edits unless explicitly recorded by future provenance rules.

Future provenance requirements:

- Source environment.
- Source commit, if known.
- Original file path.
- Capture timestamp or filesystem timestamp.
- Reason for selection.
- Whether the source was VPS, local, or other.
- Whether the artifact is copied, referenced, or only reviewed.
- Explicit statement that copying is not approved by this plan.

Fixture classes to consider as examples only, not approved intake:

- Market-closed block fixture.
- After-hours block fixture.
- Market-open strategy-evaluated fixture.
- Risk-blocked fixture.
- Reconciliation-mismatch fixture.
- Duplicate-order-blocked fixture.
- Insufficient-market-data fixture.

Future intake gate requirements before any fixture is copied into the repo or a
fixture directory:

- Separate explicit artifact-intake gate.
- Exact source path named.
- Target repo path named.
- Provenance metadata defined.
- Redaction and sanitization review completed.
- No secrets, account identifiers, credentials, or sensitive broker details.
- No derived artifacts paired unless `run_id` alignment is proven.
- No complete replay package classification unless contract requirements are
  satisfied.

Stop conditions:

- Event stream has mixed `run_id` values.
- Terminal completion is missing.
- Event schema is ambiguous.
- Source path or provenance is unclear.
- Artifact contains secrets or sensitive account data.
- Derived artifacts are mismatched.
- Intake would imply evaluation or promotion authority.

### Future Risk-Blocked Fixture Intake Gate Planning

This is a docs-only planning record for the first future explicit
artifact-intake gate. It does not approve copying now, fixture file creation
now, replay package creation, file ingestion, writer implementation, runtime
capture, storage, immutability, evaluation, broker/API work, strategy
promotion, or live trading.

Purpose:

- The first fixture class is a risk-blocked event-stream fixture.
- It is selected because it exercises market, data, strategy, duplicate, risk,
  reconcile, and completion sequencing while ending safely blocked.
- It remains `EVENT_STREAM_REPLAY_FIXTURE` only.
- It is not a complete replay package.

Candidate source set examples only:

- `logs/run_2026-05-29T19:45:04Z_8b7033.jsonl`
- `logs/run_2026-05-29T19:30:05Z_678e3b.jsonl`
- `logs/run_2026-05-29T19:15:08Z_2d98e5.jsonl`

A future artifact-intake gate must select exactly one candidate before any
copying. That gate must name the exact source path and target repo path before
copying.

Required pre-copy verification for the future gate:

- Source environment.
- Source commit, if known.
- Original source path.
- Filesystem or capture timestamp.
- Reason for selection.
- All events share one `run_id`.
- Ordered event IDs.
- Timestamps present.
- `schema_version` present.
- `event_type`, `stage`, and `status` present.
- Terminal completion event present.
- Expected 10-stage sequence present: startup, config, market session, fetch,
  market input captured, strategy evaluated, duplicate check, risk check,
  reconcile, completion.
- Final block reason is `projected_exposure_exceeds_max_position_size`.
- No derived artifacts paired unless `run_id` alignment is proven.
- No complete replay package classification claimed.

Redaction and sensitivity review for the future gate:

- No secrets.
- No credentials.
- No account identifiers.
- No sensitive broker details.
- No unapproved broker/API data exposure.
- No manual edits unless provenance records them.

Stop conditions:

- Mixed `run_id` values.
- Missing completion event.
- Ambiguous schema.
- Source path unclear.
- Target path unclear.
- Source commit or provenance unclear beyond allowed classification.
- Sensitive data present.
- Derived artifacts mismatched.
- Fixture would imply evaluation, promotion, runtime capture, broker/API, or
  live-trading authority.

### Future Risk-Blocked Artifact Intake Authorization Planning

This is a docs-only authorization plan for a future explicit artifact-copy
gate using the verified risk-blocked candidate. It does not approve copying
now, fixture creation now, replay package creation, file ingestion, writer
implementation, runtime capture, storage, immutability, evaluation, broker/API
work, strategy promotion, or live trading.

Candidate identity:

- Source environment: VPS.
- Source path: `logs/run_2026-05-29T19:45:04Z_8b7033.jsonl`.
- Source verification HEAD: `19c3e70`.
- `run_id`: `run_2026-05-29T19:45:04Z_8b7033`.
- SHA256:
  `8c68bb94ea663997874b28c705820b78ca45808cd5fd4a36363582bdcc72aca4`.
- File size: 3633 bytes.
- Birth timestamp: 2026-05-29 19:45:04 UTC.
- Modify timestamp: 2026-05-29 19:45:05 UTC.

Fixture classification:

- `EVENT_STREAM_REPLAY_FIXTURE`.
- Incomplete and non-authoritative.
- Not a complete replay package.
- No derived artifacts paired.
- No evaluation or promotion authority.

Future target path requirement:

- No file is created now.
- If no target convention exists before the copy gate, the next gate must
  define the exact target repo path before copying.
- Proposed future convention only:
  `tests/fixtures/replay/event_streams/risk_blocked/run_2026-05-29T19:45:04Z_8b7033.jsonl`.

Future copy gate requirements:

- Reconfirm VPS HEAD or record if the source environment changed.
- Reconfirm the source file exists.
- Recompute SHA256 and match the recorded hash.
- Reconfirm no sensitive key hits.
- Reconfirm event count, `run_id`, stage sequence, terminal completion, and
  terminal reason.
- Name the exact target repo path.
- Copy exactly one file.
- Preserve file content byte-for-byte.
- Record copied status.
- Run only appropriate non-runtime validation, such as SHA256 comparison and
  git diff checks.
- Avoid Python and tests unless a separate test gate is explicitly approved.

Stop conditions:

- Source file missing.
- SHA256 mismatch.
- `run_id` mismatch.
- Stage sequence mismatch.
- Terminal reason mismatch.
- Sensitive data detected.
- Target path unclear.
- More than one artifact would be copied.
- Derived artifacts would be paired.
- Copy would imply replay package completeness.
- Copy would imply evaluation, promotion, broker/API, runtime capture, writer,
  or live-trading authority.

### Source-Controlled Event-Stream Fixture Inventory

The following event-stream fixture is intentionally source-controlled:

- Path:
  `tests/fixtures/replay/event_streams/risk_blocked/run_2026-05-29T19:45:04Z_8b7033.jsonl`
- Classification: `EVENT_STREAM_REPLAY_FIXTURE`.
- Status: source-controlled fixture.
- SHA256:
  `8c68bb94ea663997874b28c705820b78ca45808cd5fd4a36363582bdcc72aca4`.
- `run_id`: `run_2026-05-29T19:45:04Z_8b7033`.
- Event count: 10.
- Terminal reason: `projected_exposure_exceeds_max_position_size`.

Authority boundary:

- The fixture is incomplete and non-authoritative.
- The fixture is not a complete replay package.
- The fixture has no paired `run_report`, `order_state`, observations, or
  runtime-visibility artifacts.
- The fixture does not authorize evaluation, strategy promotion, broker/API
  work, runtime capture, writer implementation, storage, or live trading.

Ignore-rule note:

- The broad `.gitignore` `*.jsonl` rule would hide future JSONL fixture
  candidates.
- This fixture is intentionally source-controlled despite that broad ignore
  behavior.
- Future JSONL fixture additions must be explicitly reviewed and force-added
  only through an approved artifact-intake gate.
- This inventory entry does not change `.gitignore`.

### First Guarded Event-Stream Fixture Phase Closeout

The first controlled event-stream fixture phase is closed.

Closed phase scope:

- Planned, authorized, copied, source-controlled, inventoried,
  hash/structure guarded, mapper-compatibility guarded, pushed, synced to VPS,
  and settled under the Alpaca timer baseline.

Fixture:

- Path:
  `tests/fixtures/replay/event_streams/risk_blocked/run_2026-05-29T19:45:04Z_8b7033.jsonl`
- SHA256:
  `8c68bb94ea663997874b28c705820b78ca45808cd5fd4a36363582bdcc72aca4`.
- Classification: `EVENT_STREAM_REPLAY_FIXTURE`.
- Fixture shape: event-only, incomplete, evidence-only, non-authoritative, and
  not a complete replay package.

Guard tests:

- `tests/test_offline_replay_mapper.py::test_risk_blocked_event_stream_fixture_guard`
- `tests/test_offline_replay_mapper.py::test_risk_blocked_event_stream_fixture_maps_as_incomplete_evidence_only_package`

Mapper boundary:

- Current mapper input remains in-memory loaded dictionaries only.
- No file ingestion is approved.

Authority boundary:

- No execution authority.
- No broker authority.
- No replay-based promotion authority.

Deferred future gates:

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

### `PARTIAL_OR_MISALIGNED_SAMPLE`

A `PARTIAL_OR_MISALIGNED_SAMPLE` is any bundle with missing required artifacts
or mixed `run_id` artifacts.

This includes any case where `order_state.json`, `last_run_report.json`,
observations, or runtime visibility do not align to the event JSONL `run_id`.
It also includes any case where those sections are missing and have not been
explicitly recorded as absent, not applicable, or not enabled.

A `PARTIAL_OR_MISALIGNED_SAMPLE` must not be classified as complete.

### `COMPLETE_REPLAY_PACKAGE_CANDIDATE`

A `COMPLETE_REPLAY_PACKAGE_CANDIDATE` requires one canonical `run_id`.

Minimum requirements:

- aligned event JSONL for the canonical `run_id`
- terminal completion event in that event JSONL
- `last_run_report.json` aligned to the same `run_id`
- `order_state.json` aligned to the same `run_id` or explicitly recorded as
  absent or not applicable
- observations filtered to the same `run_id` or explicitly recorded as absent
- runtime visibility from matching report or event data, or explicitly
  recorded as absent or not enabled
- every absent or not-applicable section named in package status evidence

Integrity and immutability may remain deferred unless a later storage gate
approves hashing, finalization, correction handling, retention, and storage
rules.

### Strict `run_id` Alignment Rules

- Every event in the event JSONL must share the same `run_id`.
- `last_run_report.json` `run_id` must match the event JSONL `run_id`.
- `order_state.json` `run_id` must match the event JSONL `run_id`, or the
  section must be recorded as absent or not applicable.
- Observation rows may be included only when their `run_id` matches the event
  JSONL `run_id`.
- Runtime visibility must come from matching report or event data, or be
  recorded as absent or not enabled.
- Mixed-run artifacts classify as `PARTIAL_OR_MISALIGNED_SAMPLE`.
- `last_run_report.json` and `order_state.json` are derived summaries; the
  event JSONL remains the source of truth.

### Forbidden Assumptions

- An event-only sample is not a complete replay package.
- The latest `order_state.json` must not be assumed to belong to a candidate
  run without matching `run_id` evidence.
- Observations must not be bulk-included without `run_id` filtering.
- Runtime visibility absence must not be interpreted as clean broker state.
- Replay package output does not authorize strategy evaluation, strategy
  promotion, runtime capture, artifact writer implementation, storage,
  broker/API work, live trading, or production behavior changes.
- This docs-only contract does not approve copying VPS runtime artifacts.

## Offline Replay Mapper Implementation Planning

The replay package implementation shape remains pure offline mapper only.
The current scaffold and tests exist. This planning record does not approve
runtime integration, artifact writing, storage, broker/live/API work, strategy
behavior changes, VPS validation, or replay-based promotion decisions.

The mapper may consume existing artifacts only by explicit file path or as
already-loaded dictionaries supplied by a caller:

- Event JSONL.
- `last_run_report.json`.
- Observation JSONL.
- Order state JSON.
- Runtime visibility summaries already present in reports or events.

The mapper must not import or call:

- `main.py`.
- `config.py`.
- Broker modules.
- Alpaca modules.
- IBKR modules.
- Runtime writers.
- `event_logger` write functions.
- `observation_logger` append functions.
- `reporting` persist functions.
- `state_manager` write functions.

The mapper must not mutate runtime state, production artifacts, broker
state, order state, observation files, event logs, reports, configuration, or
environment variables. It must not change JSONL, report, observation, order
state, runtime visibility, strategy, risk, reconciliation, or execution
schemas. It must not become a runtime-integrated writer.

The current mapper uses the event stream as the canonical `run_id` source.
`run_report` cannot override the event `run_id`. Mixed event `run_id` values,
mismatched `run_report`, mismatched `order_state`, mismatched observations, or
mismatched runtime visibility keep the package incomplete.

Current mapper complete status is conservative: all tracked sections must be
present and aligned. Future absent/not-applicable completeness semantics remain
a separate gate.

Sidecar artifact writing remains deferred until a separate storage and
immutability gate approves writer scope, output location, finalization rules,
hashing rules, correction handling, and retention expectations.

Initial future code location, if later approved:

- `tools/replay/`

Initial future implementation units, if later approved:

- Replay package schema constants or dataclasses.
- Offline mapper from existing artifact dictionaries.
- Validation-only completeness checks.
- In-memory envelope builder.

Out of scope for the offline mapper planning gate:

- Artifact writer.
- Storage.
- Hashing or integrity enforcement.
- Runtime capture.
- Runtime integration.
- Broker/live/API work.
- Alpaca calls.
- IBKR/TWS work.
- Credential or `.env` handling.
- Strategy behavior changes.
- Risk or reconciliation behavior changes.
- Execution, sell, trim, rebalance, resize, promotion, or order behavior.
- Replay-based promotion decisions.

Future gates required before implementation:

- Offline mapper schema implementation gate.
- Offline mapper test gate.
- Storage and immutability gate before any artifact writer.
- Integrity validation gate before hash enforcement.
- Attribution gate before candidate comparison.
- Evaluation tooling gate before package sets can inform governance.
- Promotion workflow gate before replay output can affect production behavior.

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
