# OpenClaw Phase 1-2 Blueprint

This document is planning-only.

It covers near-term planning for Phase 1 and Phase 2 work in the local repo.
It does not authorize implementation, deployment, or runtime changes by itself.

## Purpose

Use this document for:

- Phase 1 backlog
- Phase 2 backlog
- sequencing between near-term work items
- scope boundaries for near-term planning

Do not use this document for:

- runtime status tracking
- deployment instructions
- long-range platform doctrine
- cross-phase roadmap summaries

## Planning context

Phase 1 focuses on stability-facing planning around the current bot workflow.
Phase 2 focuses on architecture-hardening planning around the local refactor.

The goal of this document is to keep the next set of work items clear, ordered, and limited in scope.

## Phase 1: Core Bot Stability

### Objective

Make the current paper-trading bot easier to operate, explain, and validate.

### Backlog

#### P1-1: VPS runbook completion

Goal:
Turn the existing operator checklist into a tighter runbook for repeatable use.

Affected areas:

- operator runbooks
- checklist wording
- status/reference docs

Deliverables:

- pre-open checklist
- live-session checklist
- post-run verification checklist
- escalation notes for common failure modes

Depends on:

- current operator workflow remaining stable enough to document cleanly

Done means:

- an operator can follow the runbook without guessing what to do next

#### P1-2: Run outcome classification

Goal:
Make every bot run end in a clearly named outcome with a clear reason trail.

Deliverables:

- stable run result taxonomy
- stable blocked/error/success reason taxonomy
- clearer note payload standards in reports

Depends on:

- report persistence remaining the source of truth for run summaries

Done means:

- blocked, failed, and successful runs are easy to compare over time

#### P1-3: Session and broker diagnostics hardening

Goal:
Make session-state and broker-state failures faster to diagnose.

Affected areas:

- session diagnostics
- broker diagnostics
- report detail quality

Deliverables:

- clearer session status logging
- clearer broker call error context
- explicit timestamps and broker state snapshots where useful

Depends on:

- preserving current execution semantics while diagnostics improve

Done means:

- session and broker surprises are easier to explain from logs and reports

#### P1-4: Risk path visibility

Goal:
Make every risk rejection obvious and auditable.

Affected areas:

- risk rejection reporting
- reconciliation notes
- projected exposure visibility

Deliverables:

- explicit risk rejection reasons
- clearer reconciliation notes
- more uniform estimated-cost and projected-position reporting

Depends on:

- risk checks staying deterministic

Done means:

- each rejected order attempt has a clean explanation trail

#### P1-5: State persistence confidence checks

Goal:
Make duplicate protection and run persistence easier to validate across repeated runs.

Affected areas:

- state persistence
- report persistence
- repeat-run validation checks

Deliverables:

- documented state invariants
- repeat-run validation checks
- clearer expectations around persisted files

Depends on:

- state file format staying stable enough to validate

Done means:

- operators can trust that repeated runs preserve the expected safeguards

#### P1-6: Deterministic guardrail test plan

Goal:
Define the first test matrix for configuration, duplicate, risk, and session guardrails.

Affected areas:

- risk guardrails
- state guardrails
- session guardrails
- preflight validation

Deliverables:

- test case inventory
- implementation priority order
- expected pass and fail cases

Depends on:

- guardrails being documented clearly enough to encode as tests

Done means:

- the team knows which guardrails must be test-covered first

### Sequencing

Recommended order:

1. P1-1 VPS runbook completion
2. P1-2 run outcome classification
3. P1-3 session and broker diagnostics hardening
4. P1-4 risk path visibility
5. P1-5 state persistence confidence checks
6. P1-6 deterministic guardrail test plan

Why this order:

- operator clarity comes first
- observability comes before deeper cleanup
- test planning is easier after outcomes and failure modes are named clearly

### Phase 1 boundaries

Do not fold these into Phase 1:

- live strategy experimentation
- ML scoring in the runtime path
- multi-broker expansion beyond groundwork already underway
- research-oriented redesign of the strategy path
- feature-store or backtesting infrastructure
- scale work before the current bot workflow is easier to operate and explain

## Phase 2: Architecture Hardening

### Objective

Make the local refactor easier to reason about, safer to change, and easier to extend.

### Backlog

#### P2-1: Layer contract audit

Goal:
Audit current module boundaries and identify where business rules still leak across layers.

Affected areas:

- entrypoint composition
- orchestration boundaries
- infrastructure-facing dependencies
- configuration ownership

Deliverables:

- current dependency map
- leak list
- direction for each confirmed leak

Depends on:

- the current refactor shape staying stable enough to inspect

Done means:

- the team can point to where policy ends and infrastructure begins

#### P2-2: Broker port consolidation

Goal:
Stabilize the broker interface so core logic depends on internal contracts instead of Alpaca-shaped objects.

Affected areas:

- broker contracts
- broker-facing internal models
- Alpaca adapter translation
- execution-to-broker integration

Deliverables:

- explicit broker port surface
- normalized internal broker models
- clearer separation between adapter translation and use-case logic

Planning context:

- the broker port already exists
- normalized broker-facing models already exist
- Alpaca translation already has a dedicated adapter path
- broker-facing calls have started moving away from direct Alpaca-shaped usage

Depends on:

- surrounding execution semantics staying stable during cleanup

Done means:

- broker-specific assumptions are isolated and visible

#### P2-3: Runtime configuration discipline

Goal:
Separate runtime settings, validated config, and environment loading more cleanly.

Affected areas:

- runtime settings
- configuration validation
- environment-backed configuration flow
- runtime assembly

Deliverables:

- clearer ownership of defaults, validation, and runtime assembly
- less implicit config behavior
- simpler configuration flow for tests and internal documentation

Depends on:

- env-backed config remaining the current configuration source

Done means:

- configuration behavior is predictable and easier to explain

#### P2-4: Reporting and state ports

Goal:
Move report persistence and run-state persistence toward clearer ports and stable internal shapes.

Affected areas:

- report input contracts
- state persistence boundaries
- orchestration-to-persistence interactions

Deliverables:

- cleaner report input contracts
- clearer state persistence boundaries
- less orchestration code knowing storage details

Depends on:

- Phase 1 outcome taxonomy becoming stable enough to build on

Done means:

- persistence can evolve without forcing large orchestration edits

#### P2-5: Compatibility cleanup plan

Goal:
Identify stale modules, compatibility shims, and older flow remnants that should be deprecated deliberately.

Affected areas:

- stale compatibility paths
- legacy entrypoint remnants
- architecture reference docs

Deliverables:

- deprecation list
- keep/remove/replace decision for each stale path
- no-surprise cleanup order

Depends on:

- architecture docs matching actual usage closely enough to guide cleanup

Done means:

- compatibility cleanup work becomes intentional instead of reactive

#### P2-6: Testable use-case seams

Goal:
Define stable seams for unit and integration tests around orchestration and guardrails.

Affected areas:

- orchestration test seams
- guardrail test seams
- report-facing seams
- dependency fixture strategy

Deliverables:

- proposed unit-test seams
- proposed integration-test seams
- fixture strategy for broker and market data dependencies

Depends on:

- clearer ports and contracts from P2-2 through P2-4

Done means:

- future testing work can grow without reworking the architecture first

### Sequencing

Recommended order:

1. P2-1 layer contract audit
2. P2-2 broker port consolidation
3. P2-3 runtime configuration discipline
4. P2-4 reporting and state ports
5. P2-5 compatibility cleanup plan
6. P2-6 testable use-case seams

Why this order:

- understand leaks first
- stabilize external-facing contracts next
- simplify config and persistence boundaries after that
- define test seams around the cleaner structure

### Phase 2 boundaries

Do not fold these into Phase 2:

- a full IBKR adapter
- historical data lake or feature-store infrastructure
- backtesting engines inside the production package structure
- research modules calling live execution flows directly
- autonomous model promotion
- abstractions that do not support a known near-term architecture need
