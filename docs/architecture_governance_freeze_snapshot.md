# Architecture Governance Freeze Snapshot

## Snapshot

Current HEAD: `09c4b2e Docs: define runtime orchestration drift risks`

This snapshot records the post-report-metadata-governance architecture state. It is docs-only governance evidence. It does not approve new runtime wiring, broker behavior, execution behavior, observation emission, JSONL emission, or production activation.

## Completed Governance Phases

Completed deterministic strategy architecture and governance phases:

- Strategy Library Scaffold
- Strategy Library Validation Hardening
- Strategy Architecture Docs Evidence
- Regime Classifier Scaffold
- Regime Classifier Validation Hardening
- Regime Classifier Docs Evidence
- Strategy Router Scaffold
- Strategy Router Validation Hardening
- Strategy Router Docs Evidence
- Strategy Integration Docs Planning
- Strategy Integration Scaffold
- Strategy Integration Validation Hardening
- Strategy Integration Docs Evidence
- Runtime Integration Boundary Planning
- Runtime Strategy Seam Scaffold
- Runtime Strategy Seam Validation Hardening
- Runtime Strategy Seam Docs Evidence
- Main Runtime Metadata Contract Planning
- Runtime Strategy Metadata Adapter Scaffold
- Runtime Strategy Metadata Adapter Docs Evidence
- Reporting and Observation Metadata Planning
- Report-Only Strategy Metadata Schema Planning
- Report-Only Strategy Metadata Scaffold
- Report-Only Strategy Metadata Evidence
- Reporting Integration Boundary Planning
- Report Metadata Assembly Boundary Planning
- Metadata Failure Boundary Planning
- Drift-Risk Governance
- Report-Only Strategy Metadata Implementation
- Report Metadata Implementation Evidence
- Report Metadata Schema Governance
- Replay Authority Boundary Planning
- Runtime Orchestration Drift-Risk Planning

## Approved `strategy_architecture` Scope

Approved scope:

- report-only `strategy_architecture` metadata assembly in `main.py`
- assembly after already-fetched closes are available
- assembly before report persistence
- use of the existing metadata chain:
  1. `build_runtime_strategy_metadata()`
  2. `build_strategy_architecture_metadata()`
  3. `build_orchestration_strategy_architecture_payload()`
- report nesting under `orchestration.strategy_architecture`
- fail-open runtime/report persistence behavior on metadata `ValueError`
- fail-closed metadata behavior by omitting invalid or partial metadata

Current report-only fields:

- `regime_id`
- `selected_strategy_id`
- `routing_reason`
- `eligible_strategy_ids`
- `rejected_strategy_ids`
- `source`

`source` is fixed to `runtime_strategy_seam`.

## Prohibited And Unapproved Scope

The following remain unapproved:

- signal generation changes
- action proposal changes
- strategy execution
- risk sizing changes
- broker behavior changes
- order behavior changes
- submit, cancel, flatten, retry, resubmit, or remediation behavior
- state-write changes
- observation emission of `strategy_architecture`
- JSONL emission of `strategy_architecture`
- `reporting.py` ownership of metadata assembly or validation
- `last_run_report.json` schema expansion beyond the current report-only payload
- runtime wiring beyond the current metadata-only report assembly
- replay-authoritative use of `strategy_architecture`
- external consumption of `strategy_architecture`

## Replay Authority Status

Current `strategy_architecture` metadata is report-only descriptive evidence.

It is not replay-authoritative and is not replay-sufficient.

Replay-authoritative evolution remains deferred. A future replay-authoritative promotion requires separate approval for schema versioning, exact input snapshot or stable input reference, closes used, lookback and threshold evidence, strategy catalog identity or hash, classifier/router rule versioning, deterministic serialization, backward compatibility, migration policy, persisted JSON replay-stability tests, and a decision about whether replay authority belongs in JSONL/event sourcing rather than report-only persistence.

## JSONL And Observation Status

JSONL and observation emission remain explicitly out of scope.

Current approved status:

- no `strategy_architecture` JSONL event emission
- no `strategy_architecture` observation emission
- no observation schema change
- no event schema change for `strategy_architecture`
- JSONL and observation eligibility remain separate and unapproved

## `reporting.py` Ownership Boundary

`reporting.py` remains pass-through report construction and persistence.

Approved reporting boundary:

- accept the supplied `orchestration` object
- include it in the report payload
- call report persistence through `write_run_report()`

Not approved for `reporting.py`:

- metadata assembly
- metadata validation
- replay validation
- observation emission
- JSONL emission
- strategy, risk, broker, order, or execution policy

## `main.py` Orchestration Status

`main.py` is currently the runtime sequencing authority.

This is acceptable for now. Immediate refactor is not approved.

Current `main.py` responsibilities include:

- configuration load and runtime config fan-out
- broker adapter creation
- run ID and event logger initialization
- runtime visibility summary insertion into report config
- data config validation
- killswitch, config, market-session, market-data, strategy, duplicate, risk, reconciliation, dry-run, submit, and completion gates
- report-only strategy metadata assembly
- event, observation, report, and state persistence timing

Future extraction must be pressure-driven, not speculative.

## Current Drift Risks

Current drift risks recorded in `docs/architecture_drift_risk_register.md`:

- Source-inspection contract tests: resolved and superseded by behavior-based tests.
- Strategy Architecture Schema Expansion Without Governance: open.
- Strategy Architecture Mistaken As Replay-Authoritative: open.
- Runtime Orchestration Complexity Accumulation: open.

## Approved Future Seam Candidates

The following are recorded as future seam candidates only. They do not approve implementation:

- completion/persistence coordinator
- orchestration payload builder
- runtime coordinator or use-case layer
- run-context/config snapshot builder
- event/observation boundary wrapper

Extraction remains gated by concrete pressure such as duplicated persistence behavior, ordering bugs, report/event coupling, unstable orchestration tests, or materially larger runtime lifecycle branching.

## Validation Status

Targeted validation evidence for the current report metadata implementation:

- `venv/bin/python -m pytest test_main_strategy_architecture_metadata.py -q`
- `8 passed, 1 warning`

Raw local `main.py` validation remains inconclusive without local credentials because broker construction occurs before dry-run can avoid `TradingClient` construction.

Approved validation method for the report metadata gate is the targeted pytest harness.

## Locked Governance Principles

Currently locked governance principles:

- Strategy metadata remains report-only descriptive evidence.
- `strategy_architecture` metadata must not affect signal, action, risk, broker, order, state, execution, observation, or JSONL behavior.
- Metadata failure must fail open for runtime/report persistence and fail closed for metadata itself.
- Invalid or partial metadata must be omitted.
- `reporting.py` remains pass-through and must not own metadata assembly, metadata validation, or replay validation.
- JSONL and observation eligibility remain deferred behind separate gates.
- Schema versioning is not required for the current payload, but becomes required before nontrivial expansion, replay-authoritative use, JSONL/observation emission, or external consumption.
- Future metadata expansion must be additive unless a schema-version gate is separately approved.
- Backward compatibility policy must be documented before metadata expansion.
- `main.py` remains the runtime sequencing authority until a separate, test-first extraction gate is approved.
