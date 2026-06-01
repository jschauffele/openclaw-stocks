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

## Replay Package Envelope Schema Planning

The replay package envelope is a docs-only schema planning record. It is not
implemented.

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
