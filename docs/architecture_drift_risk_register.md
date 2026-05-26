# OpenClaw Architecture Drift-Risk Register

## Purpose

This register records known architecture drift risks before the project moves to the next gate.

The goal is to prevent temporary scaffolds, deferred boundaries, brittle tests, and known limitations from becoming permanent without explicit review.

Related governance documents:

- `docs/deterministic_strategy_architecture.md` is the chronological evidence and planning log.
- `docs/architecture_governance_freeze_snapshot.md` is the compact current approved-state snapshot.

## Register Rule

Any brittle scaffold, temporary test, deferred boundary, or known limitation must be recorded here before moving on to the next phase.

## Current Risks

### Strategy Architecture Schema Expansion Without Governance

Risk:

- Future `strategy_architecture` metadata expansion could add fields without a schema policy.
- Replay, report comparison, or downstream consumers could misinterpret changed fields if expansion is not versioned or documented.
- Tuple evidence fields may serialize to JSON arrays/lists, creating ambiguity if in-memory and persisted forms are not governed.

Current mitigation:

- `docs/deterministic_strategy_architecture.md` records current required and optional fields, deterministic field order, tuple/list serialization expectations, and the current `schema_version` boundary.
- Backward-compatibility and additive-expansion policy is documented in `docs/deterministic_strategy_architecture.md` under Report Metadata Schema Governance Planning.
- The first narrow schema-version expansion, `metadata_schema_version`, was implemented under a test-first gate as report-only descriptive metadata.
- The implementation preserved `main.py`, `reporting.py`, `runtime_strategy_seam.py`, JSONL, observation, broker, runtime, execution, risk, state, and order behavior boundaries.
- JSONL and observation eligibility remain deferred.

Future required action:

- Add `schema_version` and implement compatibility behavior in code before the first approved metadata expansion that requires versioning.
- Add behavior tests for any approved expansion that changes persisted report shape or consumer expectations.
- Keep future expansion additive unless a separate schema-version gate is approved.

Owner/context:

- Deterministic Strategy Architecture
- Report-only `strategy_architecture` metadata schema

Status:

- Open
- Requires review before metadata expansion

Related files:

- `runtime_strategy_metadata_adapter.py`
- `runtime_strategy_report_metadata.py`
- `docs/deterministic_strategy_architecture.md`

Promotion/removal condition:

- Close this risk only after a schema-version gate, tests, and compatibility policy are implemented for an actual expansion.

### Strategy Architecture Mistaken As Replay-Authoritative

Risk:

- Current `strategy_architecture` metadata could be mistaken as replay-authoritative before required replay guarantees exist.
- Report-only descriptive evidence does not currently include the full input snapshot, rule versions, schema version, catalog identity, migration policy, or persisted JSON replay-stability proof.
- Promoting it too early could make report evidence look like deterministic reconstruction authority when it is not.

Current mitigation:

- `docs/deterministic_strategy_architecture.md` classifies current `strategy_architecture` metadata as report-only descriptive evidence.
- Replay-authoritative evolution remains deferred.
- JSONL and observation eligibility remain separate and unapproved.

Future required action:

- Add a schema and replay contract before any replay-authoritative promotion.
- Define replay inputs, schema versioning, deterministic serialization, rule/catalog versioning, persistence authority, behavior tests, and migration policy.
- Decide whether replay authority belongs in JSONL/event sourcing rather than report-only persistence.

Owner/context:

- Deterministic Strategy Architecture
- Future `strategy_architecture` replay boundary

Status:

- Open
- Requires approval before replay-authoritative promotion

Related files:

- `runtime_strategy_metadata_adapter.py`
- `runtime_strategy_report_metadata.py`
- `reporting.py`
- `state_manager.py`
- `event_logger.py`
- `docs/deterministic_strategy_architecture.md`

Promotion/removal condition:

- Close this risk only when replay schema, replay behavior tests, persistence authority, and backward-compatible migration policy are approved.

### Runtime Orchestration Complexity Accumulation

Risk:

- `main.py` is currently the runtime sequencing authority.
- Sequencing responsibility includes config loading, broker adapter creation, data gates, strategy evaluation, metadata assembly, risk checks, reconciliation, reporting, eventing, and observations.
- Coordination density can make ordering dependencies brittle as more runtime metadata and lifecycle branches are added.
- Mutable shared `report_config` and duplicated early-exit persistence paths can increase drift risk.
- Broker creation currently occurs before dry-run isolation can fully avoid credential-dependent construction.

Current mitigation:

- Immediate refactor is not approved.
- Current sequencing in `main.py` is acceptable for now.
- `reporting.py` remains pass-through.
- Runtime visibility has provider/composer separation.
- Strategy metadata is separated into seams and adapters.
- Broker creation is behind `broker_factory.py`.
- Reconciliation workflow is partially separated.
- Event and observation modules are separated.

Future required action:

- Keep extraction pressure-driven, not speculative.
- Consider extraction only when duplicated persistence behavior increases, ordering bugs appear, report/event coupling increases, orchestration tests become unstable, or runtime lifecycle branching grows materially.
- Candidate future seams include completion/persistence coordinator, orchestration payload builder, runtime coordinator or use-case layer, run-context/config snapshot builder, and event/observation boundary wrapper.

Owner/context:

- Runtime orchestration
- Future `main.py` drift control

Status:

- Open
- Monitor before runtime expansion

Related files:

- `main.py`
- `reporting.py`
- `runtime_visibility_provider_composer.py`
- `runtime_visibility_orchestrator.py`
- `runtime_strategy_seam.py`
- `runtime_strategy_metadata_adapter.py`
- `runtime_strategy_report_metadata.py`
- `broker_factory.py`
- `ibkr_submit_reconciliation_workflow.py`
- `event_logger.py`
- `observation_logger.py`

Promotion/removal condition:

- Promote this risk to an implementation gate only after a concrete extraction trigger appears and a separate test-first refactor plan is approved.

### Manual Evidence Collection Process Drift

Risk:

- Manual candle hunting could be mistaken for an approved OpenClaw evidence workflow.
- Externally supplied close-sequence examples could be treated as sufficient without source, symbol, timeframe, date/time range, signal-window closes, follow-through closes, ambiguity notes, close-only status, reviewer decision, and review status.
- Evidence artifacts could be mistaken for tests or implementation approval before a separate evidence sufficiency checkpoint.
- An automated evidence collector could be introduced without a separate architecture/design gate or without isolation from runtime, broker, execution, risk, state, orders, production JSONL, observations, reporting, and `main.py`.

Current mitigation:

- `docs/strategy_3_close_trend_confirmation_evidence.md` records that manual candle hunting by the user is not an approved OpenClaw evidence workflow.
- `docs/strategy_3_close_trend_confirmation_evidence.md` records a docs-only architecture/design boundary for a possible future automated evidence collector.
- `docs/strategy_3_close_trend_confirmation_evidence.md` records a docs-only provider/data-access boundary requiring any future evidence provider to remain isolated under `tools/evidence/`.
- Future 3-close evidence gathering must be project-controlled, auditable, and separately gated.
- Evidence without provenance is not sufficient for any evidence sufficiency checkpoint.
- Evidence artifacts remain review inputs only, not tests.
- Any future collector must remain an isolated research/evidence utility and must avoid `main.py`, `config.py`, broker modules, risk, execution, state, reporting, observations, event/JSONL modules, runtime logs, reports, state files, production JSONL, and observation locations.
- Network/data access, implicit `.env` loading, direct `alpaca_data_provider.py` reuse, direct `data_engine.py` reuse, and `test_market_data.py` use remain blocked until a separate evidence-collection gate approves an exact provider and command.
- VPS-based evidence collection is not approved.
- Test planning and implementation remain blocked.

Future required action:

- Add a separate implementation gate before any project-controlled evidence collector is implemented.
- Add a separate evidence-collection gate before enabling a real provider, credentials, network/data access, or VPS execution.
- Keep any future collector isolated from `main.py`, broker submit paths, order APIs, runtime state, execution, risk, production JSONL, observations, and reporting.
- Run a separate evidence sufficiency checkpoint before any test-planning gate.

Owner/context:

- 3-close stronger trend confirmation evidence review
- Evidence provenance and process governance

Status:

- Open
- Requires review before evidence sufficiency or collector design

Related files:

- `docs/strategy_3_close_trend_confirmation_evidence.md`
- `docs/strategy_3_close_review.md`
- `docs/strategy_review_planning.md`

Promotion/removal condition:

- Close this risk only after evidence provenance rules are satisfied, any collector workflow is separately approved if needed, and evidence sufficiency is verified without approving tests or implementation prematurely.

### Portfolio/Risk Replay Contract Mistaken As Implementation

Risk:

- The docs-only portfolio/risk replay state contract could be mistaken for an implemented replay package schema or runtime capture path.
- The docs-only replay package envelope schema could be mistaken for an implemented replay writer, manifest format, runtime capture path, or storage format.
- Portfolio-state, broker-visible-state, reconciliation, risk-governance, exposure saturation, and event-order requirements could be treated as production data contracts before schema, storage, integrity validation, and attribution tooling exist.
- Broker-visible state capture requirements could be misread as approval for broker/live/API calls, IBKR execution, Alpaca trading, VPS validation, or runtime mutation.
- Evaluation outputs could be treated as promotion-grade evidence before replay package generation, attribution, and integrity controls are implemented.

Current mitigation:

- `docs/replay_package_specification.md` records the portfolio/risk replay state contract as planning only.
- `docs/replay_package_specification.md` records the replay package envelope schema as planning only.
- `docs/replayability_foundations.md`, `docs/portfolio_construction_architecture.md`, `docs/full_position_governance_models.md`, `docs/position_lifecycle_governance.md`, and `docs/evaluation_infrastructure_architecture.md` reference the contract as a prerequisite, not as implementation approval.
- The contract explicitly preserves that no implementation, strategy behavior change, broker/live/API work, VPS validation, execution activation, or production mutation is approved.
- IBKR execution remains deferred.
- The evidence/research pipeline remains parked as reusable infrastructure only after closure of the 3-close evidence phase.

Future required action:

- Add a separate replay package schema implementation gate before code.
- Add a separate replay package envelope implementation gate before any writer, manifest, storage, or runtime capture code.
- Add separate snapshot capture, storage, immutability, replay integrity, attribution, and evaluation engine gates before any output can support governance decisions.
- Add a separate broker-visible state capture gate if broker observations beyond currently approved read-only visibility are needed.
- Keep replay packages evidence-only until a promotion workflow gate is explicitly approved.

Owner/context:

- Portfolio/risk replay state contract
- Future deterministic evaluation and attribution infrastructure

Status:

- Open
- Requires implementation gates before replay or evaluation tooling

Related files:

- `docs/replay_package_specification.md`
- `docs/replayability_foundations.md`
- `docs/portfolio_construction_architecture.md`
- `docs/full_position_governance_models.md`
- `docs/position_lifecycle_governance.md`
- `docs/evaluation_infrastructure_architecture.md`

Promotion/removal condition:

- Close this risk only after the replay package schema, snapshot capture, storage, integrity validation, attribution, evaluation tooling, and promotion boundaries are implemented or explicitly rejected through separate gates.

## Resolved Risks

### Source-Inspection Contract Tests

Historical note:

- `test_main_strategy_architecture_metadata.py` previously used `inspect` and source-substring assertions as temporary architecture-contract tests.
- The metadata integration tests were converted to behavior-based tests using monkeypatches, spies, and intercepts.

Status:

- Resolved
- Superseded by behavior-based tests
- Not a current open drift risk

## Phase Transition Checklist

Before moving to a new implementation or runtime phase, check for:

- unresolved xfail or xpass tests
- source-inspection tests
- docs-only promises not yet backed by tests
- deferred runtime gates
- schema changes not yet approved
- observation or JSONL scope risks
- broker or runtime safety gates
