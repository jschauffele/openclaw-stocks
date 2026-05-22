# OpenClaw Architecture Drift-Risk Register

## Purpose

This register records known architecture drift risks before the project moves to the next gate.

The goal is to prevent temporary scaffolds, deferred boundaries, brittle tests, and known limitations from becoming permanent without explicit review.

## Register Rule

Any brittle scaffold, temporary test, deferred boundary, or known limitation must be recorded here before moving on to the next phase.

## Current Risks

### Temporary Source-Inspection Contract Tests

Risk:

- `test_main_strategy_architecture_metadata.py` uses `inspect` and source-substring assertions as temporary architecture-contract tests.
- Source-inspection tests can pass or fail for textual reasons that do not prove runtime behavior.
- If retained after implementation, they could create false confidence or brittle failures.

Current mitigation:

- The test scaffold is explicitly temporary and intended to define the future integration contract before implementation exists.
- The deterministic strategy architecture docs record that source-inspection assertions must not become permanent runtime validation.

Future required action:

- Replace source-inspection tests with behavior-based tests after implementation exists.
- Use monkeypatches, spies, or intercepts to verify behavior directly.
- Required replacement coverage:
  - intercept `persist_report()`
  - spy `append_observation()`
  - assert `log_event()` payloads do not include `strategy_architecture`
  - assert `reporting.py` pass-through behavior directly
  - assert metadata builders are called outside `reporting.py`
  - assert no second market data fetch occurs

Owner/context:

- Deterministic Strategy Architecture
- Future report-only `strategy_architecture` metadata integration

Status:

- Open
- Accepted only as pre-implementation scaffold

Related files:

- `test_main_strategy_architecture_metadata.py`
- `docs/deterministic_strategy_architecture.md`

Promotion/removal condition:

- Remove or rewrite this risk entry after source-inspection assertions are replaced by behavior-based tests and the replacement tests pass under the approved Python 3.12 validation environment.

## Phase Transition Checklist

Before moving to a new implementation or runtime phase, check for:

- unresolved xfail or xpass tests
- source-inspection tests
- docs-only promises not yet backed by tests
- deferred runtime gates
- schema changes not yet approved
- observation or JSONL scope risks
- broker or runtime safety gates
