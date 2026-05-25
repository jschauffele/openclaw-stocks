# Deterministic Strategy Architecture

## Governance Document Roles

This document is the chronological evidence and planning log for deterministic strategy architecture.

Related governance documents:

- `docs/architecture_drift_risk_register.md` is the active and resolved drift-risk source.
- `docs/architecture_governance_freeze_snapshot.md` is the compact current approved-state snapshot.

## Foundation Evidence

Current phase: Deterministic Strategy Architecture.

The deterministic strategy architecture foundation is established through completed gates:

- `b43bc3c Strategy: add deterministic strategy library scaffold`
- `a0c81f6 Strategy: harden strategy library metadata validation`
- `6772e68 Strategy: add deterministic regime classifier scaffold`
- `c10d477 Strategy: harden regime classifier validation`
- `c6d32a3 Strategy: add deterministic strategy router scaffold`
- `2abbc7e Strategy: harden strategy router validation`
- `75d60b3 Strategy: add deterministic strategy integration scaffold`
- `9b5ee1b Strategy: harden strategy integration validation`
- `641352a Strategy: add deterministic runtime strategy seam scaffold`
- `8d6c4aa Strategy: harden runtime strategy seam validation`

Python 3.12 validation evidence:

- `.venv-312/bin/python --version` reported `Python 3.12.13`
- `.venv-312/bin/python -m pytest test_strategy_library.py` reported `23 passed`
- `.venv-312/bin/python -m pytest test_regime_classifier.py` reported `36 passed`
- `.venv-312/bin/python -m pytest test_strategy_router.py` reported `31 passed`
- `.venv-312/bin/python -m pytest test_strategy_integration.py` reported `24 passed`
- `.venv-312/bin/python -m pytest test_runtime_strategy_seam.py` reported `26 passed`

`strategy_library.py` is a pure inner-policy metadata module. It follows the Clean Architecture Chapter 20 and Chapter 22 boundary: business rules and entities remain pure, dependencies point inward, and inner policy does not depend on outer mechanisms.

`test_strategy_library.py` validates strategy catalog behavior under Python 3.12. The tests cover stable strategy identity, immutable catalog data, duplicate rejection, validation hardening, lookup behavior, and forbidden outer-mechanism imports.

The current strategy metadata does not create broker, runtime, execution, risk, state, reporting, observation, or configuration authority. `execution_authority` remains `False`, and `broker_compatibility` remains empty.

`close_momentum_v1` is metadata only. It records the existing close-momentum strategy shape and observable fields, but it does not add new strategy behavior, routing, execution authority, broker compatibility, or runtime activation.

## Regime Classifier Evidence

`regime_classifier.py` is a pure deterministic inner-policy module. It uses frozen input and result dataclasses with dependency-free primitive values and no side effects.

Allowed regime IDs:

- `insufficient_data`
- `volatile`
- `uptrend`
- `downtrend`
- `sideways`
- `unknown`

`unknown` is reserved only for explicit result construction. It is not an invalid-input fallback. Invalid input raises `ValueError`.

The regime classifier does not route strategies, generate signals, size risk, submit orders, cancel orders, flatten positions, or perform remediation. It does not touch broker, runtime, config, state, observation, reporting, execution, risk, market data, file, environment, network, or VPS behavior.

`test_regime_classifier.py` validates deterministic regime classification under Python 3.12, including frozen dataclasses, allowed regime IDs, validation hardening, invalid input behavior, import isolation, and absence of execution, broker, order, routing, or strategy-selection fields.

## Strategy Router Evidence

`strategy_router.py` is a pure deterministic inner-policy module. It consumes `StrategyDefinition` and `RegimeClassificationResult` only, and it selects eligible strategy metadata only.

The router preserves catalog order for deterministic selection. It filters out execution-authorized metadata, broker-compatible metadata, non-active metadata, and metadata whose `allowed_regimes` do not include the current regime. Empty `allowed_regimes` remains metadata-level regime-agnostic.

The router validates routing evidence invariants, including evidence tuple shape, nonblank string strategy IDs, duplicate evidence IDs, eligible/rejected overlap, and selected-strategy consistency.

The router does not run strategies, generate signals, size risk, submit orders, cancel orders, flatten positions, or perform remediation. It does not touch broker, runtime, config, state, observation, reporting, execution, risk, market data, file, environment, network, or VPS behavior.

`test_strategy_router.py` validates deterministic router behavior under Python 3.12, including catalog-order selection, eligibility filtering, result evidence invariants, import isolation, and absence of signal, action, order, broker, execution, risk, runtime, state, observation, or reporting fields.

## Strategy Integration Evidence

`strategy_integration.py` is a pure deterministic orchestration/use-case-style module:

- Module: `strategy_integration.py`
- Tests: `test_strategy_integration.py`
- Purpose: connect `strategy_library`, `regime_classifier`, and `strategy_router` without runtime integration.

The integration input model contains dependency-free values only:

- `closes` tuple
- optional `lookback`
- optional `min_trend_percent`
- optional `volatility_percent`

The integration processing steps are deterministic and metadata-only:

1. Build the default strategy catalog.
2. Classify the regime from closes and thresholds.
3. Route eligible strategy metadata from the regime result.

The integration output model is a frozen metadata-only integration result with:

- `regime_id`
- `selected_strategy_id`
- routing reason
- `eligible_strategy_ids`
- `rejected_strategy_ids`
- no execution fields

Explicit integration boundaries:

- No signal generation.
- No strategy execution.
- No broker behavior.
- No runtime, config, risk, state, observation, or reporting behavior.
- No `main.py` integration.
- No order, action, submit, cancel, flatten, or remediation fields.
- No `strategy_engine.py` integration.
- No `signal_validator.py` integration.

`test_strategy_integration.py` validates deterministic orchestration under Python 3.12, including default catalog construction, regime classification, metadata routing, threshold propagation, input/result invariant hardening, import isolation, no file/env/network side effects, and absence of signal, action, order, broker, execution, risk, runtime, state, observation, or reporting fields.

Runtime integration planning may follow this docs evidence. Runtime integration code remains unapproved. Signal-engine scaffold remains deferred.

## Runtime Strategy Seam Evidence

`runtime_strategy_seam.py` is a pure metadata seam:

- Module: `runtime_strategy_seam.py`
- Tests: `test_runtime_strategy_seam.py`
- Scaffold completed at `641352a Strategy: add deterministic runtime strategy seam scaffold`
- Validation hardening completed at `8d6c4aa Strategy: harden runtime strategy seam validation`

The seam consumes already-available closes only. It calls `evaluate_strategy_integration()` only and returns metadata-only strategy architecture evidence.

The seam output contains:

- `regime_id`
- `selected_strategy_id`
- routing reason
- `eligible_strategy_ids`
- `rejected_strategy_ids`

`test_runtime_strategy_seam.py` validates the seam under Python 3.12 with `26 passed`. The tests cover metadata propagation, threshold propagation, frozen dataclasses, input/result invariant hardening, import isolation, repeated-call determinism, no file/env/network side effects, and absence of signal, action, order, broker, execution, risk, runtime, state, observation, or reporting fields.

Explicit runtime seam boundaries:

- At this point, no `main.py` integration existed.
- No runtime wiring exists.
- No signal generation.
- No strategy execution.
- No broker behavior.
- No risk sizing.
- No order actions.
- No submit, cancel, flatten, or remediation.
- No state writes.
- No observation or reporting changes.

Main runtime integration planning remains separate and unapproved.

## Runtime Integration Planning

Historical status: superseded by the later approved report-only `strategy_architecture` metadata implementation. Broader runtime wiring remains unapproved.

At this planning point, runtime integration planning was docs-only and `main.py` remained untouched.

No runtime wiring is approved. No runtime code is approved.

The first future runtime seam must be metadata-only and non-executing. Future code may read already-available closes only and may call `evaluate_strategy_integration()`. Future output must be metadata-only strategy architecture evidence.

Explicit runtime integration boundaries:

- No signal generation.
- No strategy execution.
- No broker behavior.
- No risk sizing.
- No order actions.
- No submit, cancel, flatten, or remediation.
- No state writes.
- No observation or reporting changes.
- `strategy_engine.py` remains unchanged.
- `signal_validator.py` remains unchanged.
- IBKR runtime activation remains deferred.
- Broker submission remains deferred.

Any future runtime integration code gate requires separate approval.

Current boundaries:

- No runtime wiring exists yet.
- At this point, no `main.py` integration existed yet.
- No broker, runtime, execution, risk, state, observation, or reporting dependency is approved for strategy metadata.
- Runtime integration code remains unapproved.
- Signal-engine scaffold remains deferred.

The next planned gate after this docs evidence is `RUNTIME_INTEGRATION_PLANNING`. Runtime planning must remain read-only until a separate implementation gate is approved.

`.venv-312` is a local-only Python 3.12 validation environment and must remain untracked.

## Main Runtime Integration Planning

Historical status: superseded by the approved report-only `strategy_architecture` metadata implementation recorded later in this document. The implementation uses `main.py` only for report-only metadata assembly and does not approve broader runtime wiring.

At this planning point, main runtime integration planning was docs-only and `main.py` remained untouched.

Runtime wiring remains unapproved. Future code may only consume closes already fetched by the current flow. Future code may call `build_runtime_strategy_metadata()` only, and output must remain metadata-only evidence.

Suggested future metadata surface only:

- `strategy_architecture.regime_id`
- `strategy_architecture.selected_strategy_id`
- `strategy_architecture.routing_reason`
- `strategy_architecture.eligible_strategy_ids`
- `strategy_architecture.rejected_strategy_ids`
- `strategy_architecture.source="runtime_strategy_seam"`

Metadata must not affect signal, action, risk, broker, order, state, observation, or reporting behavior.

Explicit main runtime integration boundaries:

- No signal generation.
- No strategy execution.
- No broker behavior.
- No risk sizing.
- No order actions.
- No submit, cancel, flatten, or remediation.
- No state writes.
- No observation or reporting changes are approved yet.
- `strategy_engine.py` remains unchanged.
- `signal_validator.py` remains unchanged.

Any future `main.py` code gate requires separate explicit approval.

Deferred items:

- `main.py` code changes
- runtime wiring
- reporting/observation schema changes
- signal-engine scaffold
- strategy execution
- risk sizing
- broker submission
- IBKR runtime activation

## Main Runtime Metadata Contract

Historical status: partially superseded by the approved report-only `strategy_architecture` metadata implementation recorded later in this document. The field contract remains relevant; the earlier not-yet-persisted/not-yet-reported status no longer describes the current approved state.

At this planning point, main runtime metadata planning was docs-only, `main.py` remained untouched, and runtime wiring remained unapproved.

Future metadata-only integration must be report/evidence only. Future code must not modify signal, action, risk, broker, order, state, observation, or reporting behavior.

Future code may only consume closes already fetched by the current flow. Future code may call `build_runtime_strategy_metadata()` only. If possible, future code should use a separate adapter/seam before any direct `main.py` integration.

Exact future metadata object name:

- `strategy_architecture`

Exact future metadata fields:

- `strategy_architecture.regime_id`
- `strategy_architecture.selected_strategy_id`
- `strategy_architecture.routing_reason`
- `strategy_architecture.eligible_strategy_ids`
- `strategy_architecture.rejected_strategy_ids`
- `strategy_architecture.source`

`strategy_architecture.source` must equal `runtime_strategy_seam`.

Persistence status:

- superseded for report-only metadata by `8fda85b Main: add report-only strategy architecture metadata`
- now report-persisted under `orchestration.strategy_architecture`
- not yet emitted in observations
- not yet emitted in JSONL events
- added to the normal run report payload when metadata assembly succeeds

Future persistence, reporting, observation, JSONL event, or `last_run_report.json` changes require separate approval.

Failure behavior:

- If `build_runtime_strategy_metadata()` raises `ValueError`, future code must fail closed for metadata only.
- Metadata failure must not alter signal generation.
- Metadata failure must not alter action proposal.
- Metadata failure must not alter risk checks.
- Metadata failure must not alter broker or order behavior.
- Metadata failure must not submit, cancel, flatten, or remediate.

`strategy_engine.py` remains unchanged. `signal_validator.py` remains unchanged.

Any future `main.py` code gate requires separate explicit approval.

Deferred items:

- `main.py` code changes
- runtime wiring
- reporting schema changes
- observation schema changes
- JSONL event changes
- `last_run_report.json` changes
- signal-engine scaffold
- strategy execution
- risk sizing
- broker submission
- IBKR runtime activation

## Runtime Strategy Metadata Adapter Evidence

`runtime_strategy_metadata_adapter.py` is a pure metadata adapter:

- Module: `runtime_strategy_metadata_adapter.py`
- Tests: `test_runtime_strategy_metadata_adapter.py`
- Scaffold completed at `0542959 Strategy: add runtime strategy metadata adapter scaffold`

Python 3.12 validation evidence:

- `.venv-312/bin/python --version` reported `Python 3.12.13`
- `.venv-312/bin/python -m pytest test_runtime_strategy_metadata_adapter.py` reported `18 passed`

The adapter transforms `RuntimeStrategySeamResult` into `StrategyArchitectureMetadata`.

Exact metadata object:

- `StrategyArchitectureMetadata`

Exact metadata fields:

- `regime_id`
- `selected_strategy_id`
- `routing_reason`
- `eligible_strategy_ids`
- `rejected_strategy_ids`
- `source`

`source` must equal `runtime_strategy_seam`.

The adapter preserves tuple evidence fields and validates metadata invariants, including non-empty metadata fields, source identity, tuple evidence shape, string strategy IDs, duplicate IDs, eligible/rejected overlap, and selected-strategy consistency.

Explicit metadata adapter boundaries:

- The adapter does not persist data.
- The adapter does not write reports.
- The adapter does not emit observations.
- The adapter does not emit JSONL events.
- The adapter does not modify `last_run_report.json`.
- The adapter does not touch `main.py`.
- The adapter does not affect signal, action, risk, broker, order, execution, state, observation, or reporting behavior.

Future persistence, reporting, observation, JSONL event, `last_run_report.json`, or `main.py` integration still requires separate approval. Main runtime integration remains unapproved.

## Reporting And Observation Metadata Planning

Historical status: superseded for report-only metadata by the approved implementation recorded later in this document.

`strategy_architecture` is now report-only metadata when assembly succeeds. It remains not emitted in observations and not emitted in JSONL events.

Reporting schema changes require separate approval. Observation schema changes require separate approval. JSONL event changes require separate approval. Additional `last_run_report.json` schema changes require separate approval. Broader `main.py` integration remains unapproved.

If later approved, report-only metadata should be considered before observation or JSONL emission because it is evidence-oriented and less operationally coupled. Observation and JSONL emission should remain deferred until report-only metadata is proven safe.

Metadata must never affect:

- signal generation
- action proposal
- risk checks
- broker behavior
- order behavior
- state writes
- execution behavior

`strategy_engine.py` remains unchanged. `signal_validator.py` remains unchanged.

Deferred items:

- `main.py` code changes
- `reporting.py` changes
- `observation_logger.py` changes
- JSONL event changes
- `last_run_report.json` changes
- runtime wiring
- signal-engine scaffold
- strategy execution
- risk sizing
- broker submission
- IBKR runtime activation

## Report-Only Metadata Schema Planning

Historical status: superseded by the approved report-only implementation recorded later in this document. The schema boundary remains relevant.

`strategy_architecture` is implemented as report-only metadata under `orchestration.strategy_architecture` when assembly succeeds.

If separately approved, the future first persistence target should be report-only. Report-only metadata should be considered before observation or JSONL emission because it is evidence-oriented and less operationally coupled.

Proposed future report nesting:

- `orchestration.strategy_architecture`

Proposed future fields copied from `StrategyArchitectureMetadata`:

- `orchestration.strategy_architecture.regime_id`
- `orchestration.strategy_architecture.selected_strategy_id`
- `orchestration.strategy_architecture.routing_reason`
- `orchestration.strategy_architecture.eligible_strategy_ids`
- `orchestration.strategy_architecture.rejected_strategy_ids`
- `orchestration.strategy_architecture.source`

`orchestration.strategy_architecture.source` must equal `runtime_strategy_seam`.

Report-only metadata must not be emitted to observations. Report-only metadata must not be emitted to JSONL events. Report-only metadata must not change `last_run_report.json` until separately approved.

Report-only metadata must not affect:

- signal generation
- action proposal
- risk checks
- broker behavior
- order behavior
- state writes
- execution behavior

`reporting.py` code changes require separate approval. Broader `main.py` integration remains unapproved. `observation_logger.py` changes remain deferred. JSONL event changes remain deferred.

Deferred items:

- `reporting.py` changes
- `observation_logger.py` changes
- JSONL event changes
- `last_run_report.json` changes
- `main.py` integration
- runtime wiring
- signal/action behavior
- risk sizing
- broker submission
- execution behavior
- IBKR runtime activation

## Report Metadata Assembly Planning

Historical status: superseded by the approved implementation recorded later in this document. The boundary that metadata assembly authority must not move into `reporting.py` remains current.

No new seam or adapter is needed before reporting integration planning.

The existing metadata chain is sufficient for a future report-only `strategy_architecture` payload:

1. `runtime_strategy_seam.py`
2. `runtime_strategy_metadata_adapter.py`
3. `runtime_strategy_report_metadata.py`

`reporting.py` must remain render/pass-through only. Future metadata assembly must occur before `persist_report()` is called, and metadata assembly authority must not move into `reporting.py`.

Current approval boundaries:

- Observation and JSONL emission remain explicitly out of scope.
- additional `last_run_report.json` schema changes remain unapproved.
- broader runtime and `main.py` integration remain unapproved.
- the later report-only metadata implementation is the only approved implementation scope.

Any future code gate must be separate, explicit, and test-first.

## Report Metadata Test Scaffold Limitation

Historical status: resolved and superseded.

`test_main_strategy_architecture_metadata.py` previously used `inspect` and source-substring assertions as a temporary architecture-contract scaffold. That limitation was acceptable only before implementation existed.

After implementation, the tests were converted to behavior-based tests using monkeypatches, spies, and intercepts.

Replacement coverage now expected to remain behavior-based:

- intercept `persist_report()`
- spy `append_observation()`
- assert `log_event()` payloads do not include `strategy_architecture`
- assert `reporting.py` pass-through behavior directly
- assert metadata builders are called outside `reporting.py`
- assert no second market data fetch occurs

Source-inspection assertions must not become permanent runtime validation.

## Metadata Failure Boundary Planning

Future `strategy_architecture` metadata assembly is optional and degradable.

Metadata assembly failure must fail open for runtime and report persistence. A metadata assembly failure must not block report persistence.

Metadata assembly failure must fail closed for metadata itself. Invalid or partial `strategy_architecture` metadata must not be persisted.

On metadata assembly failure, future implementation should omit `strategy_architecture` unless a separately approved metadata error surface is designed.

Metadata exceptions must remain isolated from:

- signal generation
- action proposal
- risk checks
- broker behavior
- order behavior
- state writes
- execution behavior
- observation behavior
- JSONL event behavior
- report persistence

Failure handling authority must not move into `reporting.py`. `reporting.py` remains render/pass-through only.

Observation and JSONL error emission remain out of scope.

Any future implementation gate must be separate, explicit, and test-first.

## Report-Only Strategy Metadata Evidence

`runtime_strategy_report_metadata.py` is a pure report-shaping seam:

- Module: `runtime_strategy_report_metadata.py`
- Tests: `test_runtime_strategy_report_metadata.py`
- Scaffold completed at `9304cb2 Strategy: add report-only strategy metadata scaffold`

Python 3.12 validation evidence:

- `.venv-312/bin/python --version` reported `Python 3.12.13`
- `.venv-312/bin/python -m pytest test_runtime_strategy_report_metadata.py` reported `15 passed`

The seam converts `StrategyArchitectureMetadata` into the future report-shaped `orchestration.strategy_architecture` payload.

Exact top-level payload:

- `strategy_architecture`

Exact nested fields:

- `regime_id`
- `selected_strategy_id`
- `routing_reason`
- `eligible_strategy_ids`
- `rejected_strategy_ids`
- `source`

`source` must equal `runtime_strategy_seam`. Tuple evidence fields are preserved.

Explicit report-only metadata boundaries:

- No persistence.
- No report write.
- No observation emission.
- No JSONL event emission.
- No `last_run_report.json` wiring.
- No `main.py` wiring.
- No `reporting.py` integration yet.

Future `reporting.py` integration requires separate approval. Observation, JSONL, and `main.py` integration remain deferred.

## Report-Only Strategy Metadata Implementation Evidence

Report-only `strategy_architecture` metadata implementation was completed and pushed in:

- `8fda85b Main: add report-only strategy architecture metadata`

Local `main` and `origin/main` were aligned at `8fda85b`.

Targeted validation:

- `venv/bin/python -m pytest test_main_strategy_architecture_metadata.py -q`
- `8 passed, 1 warning`

Implementation scope:

- report-only `strategy_architecture` metadata assembly in `main.py`
- assembly occurs before report persistence
- assembly uses the existing metadata chain:
  1. `build_runtime_strategy_metadata()`
  2. `build_strategy_architecture_metadata()`
  3. `build_orchestration_strategy_architecture_payload()`

Preserved boundaries:

- `reporting.py` remains pass-through only
- no JSONL emission
- no observation emission
- no broker, risk, execution, or order behavior changes
- no second market data fetch

Raw local `main.py` validation was inconclusive because local credentials were absent and broker construction occurs before dry-run can avoid `TradingClient` creation.

The approved validation method for this gate is the targeted pytest harness, not raw local `main.py`.

## Reporting Integration Planning

`reporting.py` currently has an `orchestration` passthrough field in the report construction path.

If separately approved, the first report-only strategy metadata may use the existing orchestration report nesting:

- `orchestration.strategy_architecture`

This may avoid changing `reporting.py` initially if the orchestration object is assembled before report construction.

Current approval boundaries:

- No `reporting.py` changes are approved yet.
- No `main.py` changes are approved yet.
- No persistence changes are approved yet.
- No `observation_logger.py` changes are approved.
- No JSONL or event changes are approved.
- No `last_run_report.json` schema changes are approved.

Future implementation must not affect:

- signal generation
- action proposal
- risk checks
- broker behavior
- order behavior
- state writes
- execution behavior

Observation and JSONL emission remain deferred. `strategy_engine.py` remains unchanged. `signal_validator.py` remains unchanged. Any code gate requires separate explicit approval.

Deferred items:

- `reporting.py` changes
- `main.py` integration
- runtime wiring
- `observation_logger.py` changes
- JSONL event changes
- `last_run_report.json` changes
- signal/action behavior
- risk sizing
- broker submission
- execution behavior
- IBKR runtime activation

## Report Metadata Schema Governance Planning

The current `strategy_architecture` payload is stable only as report-only descriptive evidence. It is not replay-authoritative, not replay-sufficient, and must not affect signal, action, risk, broker, order, state, execution, observation, or JSONL behavior.

The current report-only `strategy_architecture` payload does not require a `schema_version` yet.

`schema_version` becomes required before any of the following are approved:

- nontrivial metadata expansion
- field removal or rename
- meaning changes to existing fields
- replay-authoritative use
- JSONL emission
- observation emission
- external consumption

Current required fields:

- `regime_id`
- `routing_reason`
- `eligible_strategy_ids`
- `rejected_strategy_ids`
- `source`

Current optional fields:

- `selected_strategy_id`

`source` remains required and fixed to `runtime_strategy_seam` unless a separate source-governance gate approves otherwise.

The report-only payload must preserve this deterministic field order:

1. `regime_id`
2. `selected_strategy_id`
3. `routing_reason`
4. `eligible_strategy_ids`
5. `rejected_strategy_ids`
6. `source`

In memory, `eligible_strategy_ids` and `rejected_strategy_ids` remain tuples. Persisted JSON should be treated as arrays/lists after serialization.

JSONL and observation eligibility remain deferred behind separate approval gates.

### Backward Compatibility And Additive Expansion Policy

Backward compatibility must be documented before any metadata expansion gate is approved. This section is that policy for the current report-only payload.

Default expansion rule:

- Future metadata expansion must be additive by default.
- Additive expansion means new optional or required fields may be added without changing the meaning of existing fields.
- A separate schema-version gate is required for any non-additive change.

Field stability rules:

- Existing fields must not be renamed or removed without a separate schema-version gate.
- Existing field meanings must not be changed silently.
- Consumers must treat unknown fields as ignorable unless a separate consumption gate says otherwise.

Current field semantics:

- `selected_strategy_id` remains nullable because no eligible strategy is a valid routing outcome.
- `eligible_strategy_ids` and `rejected_strategy_ids` remain ordered deterministic evidence lists after JSON persistence. Order is evidence, not an unordered set.
- `source` remains required and fixed to `runtime_strategy_seam` unless a separate source-governance gate approves otherwise.

`schema_version` boundary:

- `schema_version` is not required for the current payload.
- `schema_version` becomes required before nontrivial expansion, field removal or rename, meaning changes, replay-authoritative use, JSONL or observation emission, or external consumption.

Reporting boundary:

- `reporting.py` remains pass-through report construction and persistence.
- `reporting.py` must not own compatibility logic, schema validation, migration, or replay validation for `strategy_architecture`.

Any future metadata expansion gate must cite this policy, define the additive change, and remain report-only unless separate runtime, JSONL, observation, or replay gates are approved.

## First Schema-Version Metadata Expansion Candidate Planning

Historical status: superseded by the approved report-only implementation recorded in the next section.

At this planning point, `strategy_architecture` report-only metadata remained unchanged and valid without `metadata_schema_version`.

First future expansion candidate:

- `metadata_schema_version`

Purpose:

- prepare controlled future expansion
- make future persisted report metadata easier to reason about
- avoid silent semantic drift
- support backward compatibility before any larger metadata expansion

If separately approved in a future implementation gate, `metadata_schema_version` would be the first additive field in the report-only `strategy_architecture` payload.

Candidate boundaries:

- `metadata_schema_version` would be report-only descriptive metadata.
- It must not affect signal, action, risk, broker, order, state, execution, observation, or JSONL behavior.
- It must not make `strategy_architecture` replay-authoritative.
- It must not approve external consumption.
- Current report-only metadata remains valid without `metadata_schema_version` until a separate implementation gate approves otherwise.

Future implementation validation requirements:

- prove `metadata_schema_version` appears only in the report payload
- prove `reporting.py` remains pass-through
- prove JSONL remains unchanged
- prove observations remain unchanged
- prove metadata failure remains fail-open for report persistence
- prove schema version metadata does not affect trading behavior

## Report-Only Metadata Schema Version Evidence

Report-only `metadata_schema_version` implementation was completed and pushed in:

- `32743bb Metadata: add report schema version`

Current source-of-truth HEAD after implementation:

- `32743bb Metadata: add report schema version`

`metadata_schema_version` is now implemented as report-only descriptive metadata.

Current schema-version behavior:

- `metadata_schema_version` value is deterministic: `"1"`
- `metadata_schema_version` appears first in `StrategyArchitectureMetadata`
- `metadata_schema_version` appears first in the nested `strategy_architecture` report payload

Targeted validation:

- Seam bundle: `61 passed`
- Main metadata: `8 passed, 1 warning`

Warning:

- `DeprecationWarning: websockets.legacy is deprecated`
- Classification: unrelated dependency deprecation, not a report metadata regression.

Preserved boundaries:

- no `main.py` changes
- no `reporting.py` changes
- no `runtime_strategy_seam.py` changes
- no JSONL emission
- no observation emission
- no broker, runtime, execution, risk, state, or order behavior changes
- no replay-authoritative use

## Replay Authority Boundary Planning

Current `strategy_architecture` metadata is report-only descriptive evidence. It is not replay-authoritative.

Current `strategy_architecture` metadata is not replay-sufficient. Replay-authoritative evolution remains deferred.

Required future guarantees before any replay-authoritative promotion:

- `schema_version`
- exact input snapshot or stable input reference
- closes used for classification and routing
- lookback and threshold evidence
- strategy catalog identity, version, or hash
- classifier and router rule versioning
- deterministic serialization rules
- backward compatibility and migration policy
- behavior tests proving persisted JSON replay stability
- decision whether replay authority belongs in JSONL/event sourcing rather than report-only persistence

`reporting.py` must remain pass-through and must not own replay validation.

JSONL and observation eligibility remains separate and unapproved.

## Runtime Orchestration Drift-Risk Planning

`main.py` is currently the runtime sequencing authority. This is acceptable for now.

Immediate refactor is not approved. Future extraction must be pressure-driven, not speculative.

Current architectural strengths:

- `reporting.py` remains pass-through.
- Runtime visibility has provider/composer separation.
- Strategy metadata is separated into seams and adapters.
- Broker creation is behind `broker_factory.py`.
- Reconciliation workflow is partially separated.
- Event and observation modules are separated.

Current orchestration risks:

- sequencing brittleness
- mutable shared `report_config`
- duplicated early-exit persistence paths
- growing coordination density
- broker creation before dry-run isolation

Future extraction triggers:

- duplicated persistence behavior increases
- ordering bugs appear
- report/event coupling increases
- orchestration tests become unstable
- runtime lifecycle branching grows materially

Future seam candidates:

- completion/persistence coordinator
- orchestration payload builder
- runtime coordinator or use-case layer
- run-context/config snapshot builder
- event/observation boundary wrapper

## Report Metadata Isolated Validation Evidence

Local `main` and `origin/main` were aligned at:

- `de3c40b Docs: consolidate governance architecture state`

Isolated seam validation:

- `venv/bin/python -m pytest test_runtime_strategy_seam.py test_runtime_strategy_metadata_adapter.py test_runtime_strategy_report_metadata.py -q`
- `59 passed`

Isolated main metadata validation:

- `venv/bin/python -m pytest test_main_strategy_architecture_metadata.py -q`
- `8 passed, 1 warning`

Prior combined-bundle failures were test-order and `sys.modules` contamination. The combined run imported `main` before the seam import-isolation assertions executed, so forbidden outer modules were already present in process-global module state.

There is no evidence of direct forbidden imports in the seam modules from the isolated seam validation.

Recommended validation order:

1. Run seam tests separately.
2. Run main metadata tests separately.

## Finalized Governance Targeted Local Validation Evidence

Validation commit:

- `f1eea4d Docs: correct freeze snapshot source head`

Local `main` and `origin/main` were aligned at `f1eea4d`.

Isolated validation order:

1. Runtime strategy seam bundle.
2. Main strategy architecture metadata test.

Runtime strategy seam bundle:

- `venv/bin/python -m pytest test_runtime_strategy_seam.py test_runtime_strategy_metadata_adapter.py test_runtime_strategy_report_metadata.py -q`
- `59 passed`

Main strategy architecture metadata test:

- `venv/bin/python -m pytest test_main_strategy_architecture_metadata.py -q`
- `8 passed, 1 warning`

Warning:

- `DeprecationWarning: websockets.legacy is deprecated`
- Classification: unrelated dependency deprecation, not a report metadata regression.

Git status after validation showed no tracked file changes.

This validation confirms the existing report-only `strategy_architecture` metadata behavior remains intact after governance consolidation.
