# IBKR Execution Architecture Separation Decision

## Decision

IBKR runtime visibility and IBKR execution are separate control planes.

Runtime visibility remains observability and readiness metadata only. It may report broker-adjacent state, but it does not authorize or perform execution.

IBKR execution must not evolve by extending runtime visibility. Execution adapters, submit workflows, reconciliation workflows, and order-building logic remain separate from visibility providers.

## Boundaries

`runtime_visibility_blocking` is not execution authorization. It may be calculated and reported, but it must not permit, deny, or route orders.

Observability providers must never:

- submit orders
- build orders
- cancel orders
- flatten positions
- remediate broker state
- retry execution
- resubmit orders

`broker_factory.py` remains execution-isolated until a separate explicit future architecture review approves any IBKR execution integration.

## Detached Runtime Assembly Seam

`ibkr_runtime_assembly.py` is a detached construction seam for IBKR
infrastructure components. It exists to compose the IBKR adapter, callback
bridge, request coordinator, timeout injector, native lifecycle bundle, and
runtime coordinator in a reviewable way without granting production execution
authority.

The seam is disabled by default and fake-native testable. In disabled mode, it
must not require TWS, make broker calls, or load `ibapi`.

The seam does not enable `OPENCLAW_BROKER=ibkr`, does not change
`broker_factory.py` authority, does not grant `main.py` runtime authority, and
does not alter production orchestration.

Assembly guardrails remain restricted to localhost and paper ports. Near-term
future use should start with manual smoke harness migration. Production routing
through `broker_factory.py` remains later-only and requires explicit
architecture review.

### Smoke Harness Migration Status

`manual_ibkr_localhost_connect_smoke.py` is the first and only smoke harness
currently migrated to the detached runtime assembly seam.

`manual_ibkr_read_only_runtime_visibility_smoke.py` remains intentionally
unmigrated because it belongs to the runtime visibility control plane.

`manual_ibkr_submit_reconciliation_smoke.py` remains intentionally unmigrated
pending separate safety review. Any future submit/reconciliation migration is
higher risk and must be isolated.

Production routing remains disabled. `broker_factory.py` and `main.py` remain
unchanged. This note does not approve any additional smoke harness migration.

### Submit/Reconciliation Smoke Migration Plan

Any future migration of `manual_ibkr_submit_reconciliation_smoke.py` onto
`assemble_ibkr_runtime(...)` must be construction-only. The migration must not
move submit policy, reconciliation policy, safety checks, evidence recording,
or operator-control behavior into `ibkr_runtime_assembly.py`.

The following construction pieces may use `ibkr_runtime_assembly.py`:

- native API loading
- registry and request coordinator construction
- runtime coordinator construction
- adapter construction
- native wrapper and client bundle construction through injection hooks

The following behavior must remain bespoke and manual in the smoke harness:

- `RecordingReconciliationBridge`
- `RecordingReconciliationClient`
- `SubmitReconciliationSmokeWrapper`
- `ReconciliationSmokeRecorder`
- lock file single-flight behavior
- last-run unsafe-state refusal
- pre-submit broker-state checks
- submit attempt timing and persistence
- final broker-state query
- reconciliation workflow invocation
- no-retry, no-resubmit, and no-remediation policy

Required tests before any migration:

- recorder callback evidence is preserved
- recording client evidence is preserved
- unsafe last-run refusal is preserved
- lock behavior is preserved
- final-state write is preserved
- no production routing is enabled

This plan does not approve production routing. It also does not approve the
submit/reconciliation smoke migration by itself; any migration must be reviewed
as an isolated manual-harness change.

### Submit/Reconciliation Construction-Equivalence Test Plan

Before any future submit/reconciliation smoke migration to
`assemble_ibkr_runtime(...)`, the current fake-native test suite must establish
a pre-migration baseline for the manual construction path. The baseline must
capture recorder callback evidence, recording client request and place-order
evidence, wrapper callback routing, lock behavior, unsafe last-run refusal,
final broker-state persistence, disconnect evidence persistence, reconciliation
workflow invocation ordering, and production-routing absence.

Post-migration tests must prove construction equivalence without granting new
runtime authority. The migrated harness must still preserve:

- recorder callback evidence for order submission, open-order snapshots,
  position snapshots, and execution snapshots
- recording client evidence for `placeOrder`, `reqExecutions`,
  `reqAllOpenOrders`, `reqPositionsMulti`, and `cancelPositionsMulti`
- wrapper callback routing through the submit/reconciliation smoke wrapper,
  including nonfatal IBKR status handling
- lock file single-flight behavior before any submit path can proceed
- unsafe last-run refusal before connect, order construction, or submit
- final broker-state persistence after any attempted submit
- disconnect joined/passed/error evidence persistence in the last-run state
- reconciliation workflow invocation only after a submit result reports
  `reconciliation_required`
- no production routing through `broker_factory.py` or `main.py`
- no authority expansion beyond construction reuse inside the manual smoke
  harness

The post-migration assertions must compare the same fake-native scenarios used
by the pre-migration baseline. They must prove that using the assembly seam only
changes component construction, not submit policy, reconciliation policy,
operator controls, recorder evidence, or final-state safety behavior.

Rollback is required if any equivalence assertion breaks, if the migration
requires changing `broker_factory.py` or `main.py`, if fake-native tests require
TWS or broker calls, if recorder evidence becomes less specific, if unsafe
last-run or lock behavior weakens, or if reconciliation workflow ordering
changes. A rollback returns the submit/reconciliation smoke to bespoke manual
construction and keeps `assemble_ibkr_runtime(...)` limited to lower-authority
manual harnesses.

## Activation Requirements

IBKR execution activation requires its own:

- config namespace
- disabled-by-default gates
- unit tests
- fake-native integration tests
- paper-only manual smoke evidence
- submit reconciliation evidence
- architecture review

Paper-only isolated execution validation must occur before any broader production integration or strategy-driven IBKR execution path.

Read-only IBKR visibility evidence is not execution readiness approval.

## Controlled Paper Activation Readiness Checklist

This checklist defines the gates required before any IBKR paper runtime routing
is enabled through `broker_factory.py` or `main.py`. Completing the checklist
does not approve activation by itself. Activation still requires explicit
architecture approval.

- IBKR config namespace requirements
  - define IBKR-specific host, port, client ID, timeout, disconnect timeout,
    account, model code, order ID, and mode settings
  - keep IBKR configuration separate from Alpaca configuration
  - document paper-only defaults and forbidden live-routing values
- disabled-by-default activation gate
  - require an explicit IBKR enablement flag
  - default all IBKR runtime routing to disabled
  - fail closed when required IBKR config is missing or invalid
- fake-native test requirements
  - cover adapter construction without TWS or broker calls
  - cover lifecycle connect, timeout, callback, disconnect, and stale callback
    behavior
  - cover order build, submit acknowledgement, submit timeout, rejection, and
    reconciliation-required outcomes
  - cover authority boundaries proving `main.py` and `broker_factory.py`
    remain unchanged until explicitly approved
- manual localhost connect-smoke evidence
  - prove localhost paper connection only
  - record `nextValidId` readiness
  - record deterministic timeout behavior
  - record disconnect and runtime-thread shutdown evidence
- manual paper submit/reconciliation evidence
  - prove paper-only order submission path under operator control
  - record pre-submit broker-state checks
  - record order ID, submit result, timeout path, and final broker state
  - record execution, open-order, and position snapshot evidence when submit
    acknowledgement is uncertain
- submit uncertainty and reconciliation behavior requirements
  - define terminal statuses and manual-review statuses
  - preserve no-retry, no-resubmit, no-remediation behavior unless separately
    approved
  - fail closed on unresolved or partially resolved reconciliation
  - prevent future execution after unsafe last-run state until operator review
- rollback/operator controls
  - define how to disable IBKR routing immediately
  - define operator preflight commands and smoke commands
  - define cleanup requirements for open orders, non-flat positions, and
    unresolved reconciliation
  - define rollback to the current Alpaca-only broker factory path
- logging, reporting, and observability requirements
  - emit clear lifecycle, submit, reconciliation, and completion events
  - preserve append-only observability intent
  - include IBKR runtime mode, broker name, order ID, reconciliation status,
    manual-review flag, and final broker-state evidence in reports
  - avoid treating runtime visibility as execution authorization
- `broker_factory.py` review gate
  - review any addition of `ibkr` to supported broker selection separately
  - require disabled-by-default behavior and fake-native coverage before merge
  - preserve explicit unsupported-broker failure when IBKR is not enabled
- `main.py` orchestration review gate
  - review any IBKR production orchestration branch separately
  - preserve existing strategy, risk, duplicate, reconciliation, event,
    report, observation, and state-write sequencing
  - avoid moving execution authority into broker adapters or visibility
    providers
- architecture approval requirement
  - require explicit approval before enabling IBKR routing
  - require paper-only activation before any broader production or live-routing
    consideration
  - document rollback posture and operator ownership before activation
