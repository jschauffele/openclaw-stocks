# OpenClaw Architecture Drift-Risk Register

## Purpose

This register records known architecture drift risks before the project moves to the next gate.

The goal is to prevent temporary scaffolds, deferred boundaries, brittle tests, and known limitations from becoming permanent without explicit review.

## Register Rule

Any brittle scaffold, temporary test, deferred boundary, or known limitation must be recorded here before moving on to the next phase.

## Current Risks

### Source-Inspection Contract Tests

Risk:

- `test_main_strategy_architecture_metadata.py` previously used `inspect` and source-substring assertions as temporary architecture-contract tests.

Current mitigation:

- The metadata integration tests were converted to behavior-based tests after implementation.
- The behavior-based tests use monkeypatches, spies, and intercepts to verify report persistence, observation isolation, JSONL isolation, reporting pass-through behavior, metadata builder order, and no second market data fetch.

Future required action:

- Keep report metadata integration tests behavior-based.
- Do not reintroduce source-inspection assertions as permanent runtime validation.

Owner/context:

- Deterministic Strategy Architecture
- Report-only `strategy_architecture` metadata integration

Status:

- Resolved
- Superseded by behavior-based tests

Related files:

- `test_main_strategy_architecture_metadata.py`
- `docs/deterministic_strategy_architecture.md`

Promotion/removal condition:

- This entry may be removed after the next governance review confirms no source-inspection assertions remain for report metadata integration.

### Strategy Architecture Schema Expansion Without Governance

Risk:

- Future `strategy_architecture` metadata expansion could add fields without a schema policy.
- Replay, report comparison, or downstream consumers could misinterpret changed fields if expansion is not versioned or documented.
- Tuple evidence fields may serialize to JSON arrays/lists, creating ambiguity if in-memory and persisted forms are not governed.

Current mitigation:

- `docs/deterministic_strategy_architecture.md` records current required and optional fields, deterministic field order, tuple/list serialization expectations, and the current `schema_version` boundary.
- JSONL and observation eligibility remain deferred.

Future required action:

- Document backward compatibility policy before metadata expansion.
- Add `schema_version` before nontrivial expansion, replay-authoritative use, JSONL or observation emission, or external consumption.
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

- Promote or remove this risk only after a schema governance gate defines versioning, backward compatibility, serialization rules, field ordering, and JSONL/observation eligibility for the next metadata expansion.

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

## Phase Transition Checklist

Before moving to a new implementation or runtime phase, check for:

- unresolved xfail or xpass tests
- source-inspection tests
- docs-only promises not yet backed by tests
- deferred runtime gates
- schema changes not yet approved
- observation or JSONL scope risks
- broker or runtime safety gates
