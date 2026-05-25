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
