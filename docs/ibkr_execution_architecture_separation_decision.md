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

## IBKR Paper Activation Rollback And Operator Controls Plan

This plan defines the required safety posture before any future IBKR paper
runtime activation work touches `broker_factory.py` or `main.py`. It does not
approve broker routing. It does not approve `main.py` orchestration.
`broker_factory.py` remains closed, and `main.py` remains closed.

### Rollback Controls

IBKR paper runtime activation must be disabled by explicit configuration, not
by code removal or partial runtime state. The default state must remain
disabled, and any missing, invalid, live, non-localhost, or non-paper config
must fail closed before native API loading, broker connection, order
construction, or submit.

Rollback must return the production path to Alpaca-only broker routing. During
rollback, `OPENCLAW_BROKER=ibkr` must be unsupported unless a separately
approved activation gate is open. If IBKR routing has been enabled in a future
approved change, rollback must restore the explicit unsupported-broker failure
for IBKR and preserve the existing Alpaca path.

Rollback is required after any unsafe state, including unresolved
reconciliation, partially filled unresolved reconciliation, broker-state
ambiguity, unexpected open orders, non-flat positions, disconnect uncertainty,
runtime coordinator uncertainty, connect instability, repeated lifecycle
timeouts, stale callback state, or evidence loss. Rollback after reconciliation
uncertainty must preserve the no-retry, no-resubmit, and no-remediation policy
until an operator records the broker state and approves the next action.

Rollback after lifecycle or connect instability must happen before another
paper execution attempt. A failed connect, timed-out readiness callback, runtime
thread startup failure, runtime thread exception, disconnect join timeout, or
missing disconnect result must block future IBKR runtime execution until the
operator captures evidence and revalidates the localhost paper environment.

### Operator Controls

Before activation approval, the operator must complete a documented preflight.
The preflight must verify the active branch and commit, confirm
`broker_factory.py` and `main.py` are in the approved state, confirm
`OPENCLAW_IBKR_RUNTIME_ENABLED` is explicitly set for the intended paper test
only, and confirm `OPENCLAW_BROKER=ibkr` is still unsupported unless the
specific activation review has approved that gate.

The operator must verify localhost and paper-only constraints before any paper
execution: host must be `127.0.0.1`, `localhost`, or `::1`; port must be a paper
port; mode must be `paper_localhost`; account and model-code values must match
the intended paper account; client ID must be unique for the run; and all
connect, disconnect, and submit timeouts must be finite positive values.

The operator must verify clean broker state before submit. Clean state requires
no ambiguous open orders, no unexpected working orders for the symbol, no
non-flat position that conflicts with the planned test, no unsafe last-run
state, no unresolved reconciliation state, and no stale runtime state from a
previous run.

The operator must verify reconciliation state before and after any paper submit.
If submit acknowledgement becomes uncertain, the reconciliation workflow must
record execution, open-order, and position evidence. Manual review is required
for unresolved or partially filled unresolved outcomes. No retry, resubmit,
cancel, flatten, or remediation behavior is approved by this plan.

The operator must verify shutdown and disconnect evidence after every run.
Expected evidence includes disconnect joined, disconnect result passed,
connected state cleared, shutdown state complete, runtime thread stopped, and
no stale runtime coordinator authority remaining after the run.

The operator must complete post-run verification before any next IBKR run. The
post-run check must record final broker state, final reconciliation state,
manual-review status, open orders, positions, execution evidence, disconnect
evidence, and whether rollback is required before another attempt.

### Unsafe-State Blockers

Any of the following states must block IBKR paper runtime activation or further
paper execution until operator review is complete:

- stale runtime state from a prior run
- unresolved or partially filled unresolved reconciliation state
- open-order ambiguity or unexpected working orders
- non-flat position ambiguity
- disconnect uncertainty or missing disconnect result
- runtime coordinator uncertainty or runtime thread instability
- duplicate runtime authority, duplicate client ID ownership, or overlapping
  manual smoke/runtime execution
- missing callback, request, submit, reconciliation, or final-state evidence
- any config drift away from disabled-by-default, localhost, paper-only
  operation

### Observability And Operator Evidence Expectations

Before activation approval, evidence must exist for config validation,
config-to-assembly mapping, disabled assembly behavior, fake-native lifecycle
behavior, manual localhost connect smoke, manual paper submit/reconciliation
smoke, broker factory rejection while disabled, and `main.py` authority
absence.

During paper execution, runtime evidence must capture runtime mode, broker
name, host, port, client ID, connect result, readiness source, order ID,
submit status, reconciliation status, manual-review flag, final broker state,
disconnect result, runtime thread state, and all relevant callback/request
evidence. Observability must remain append-only and must not authorize
execution.

Before rollback approval, evidence must show the rollback trigger, last known
broker state, open-order state, position state, reconciliation state,
disconnect state, runtime coordinator state, operator decision, and the exact
configuration or code boundary that returned routing to Alpaca-only behavior.

## IBKR Paper Runtime Observability And Reporting Contract

This contract defines future IBKR paper runtime evidence requirements before
any `broker_factory.py` or `main.py` activation work. It is append-only
evidence only. It is observational only. It does not authorize execution, route
orders, retry, resubmit, cancel, flatten, remediate, or override `main.py`
control flow. Read-only visibility is not execution approval.

This contract does not approve `broker_factory.py` changes, does not approve
`main.py` changes, does not enable `OPENCLAW_BROKER=ibkr`, does not approve
production routing, does not require broker calls, and does not require TWS.

### Future IBKR Event Evidence Fields

Future IBKR paper runtime events must preserve the stable run-event envelope
and record IBKR evidence in payload fields. Required future event evidence
includes:

- `broker_name`
- `runtime_mode`
- `host`
- `port`
- `client_id`
- `runtime_enabled`
- `assembly_enabled`
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result.passed`
- `disconnect_result.reason`
- `shutdown_state`
- `order_id`
- `order_status`
- `submit_state`
- `submitted_at`
- `reconciliation_status`
- `manual_review_required`
- `terminal_for_run`
- `reconciliation_ambiguous`
- `filled_qty`
- `working_qty`
- `final_broker_state`
- `final_broker_state_reason`
- open-order snapshot summary
- position snapshot summary
- execution snapshot summary
- callback and request evidence counts or references

Events must be appended in the order the runtime observes these facts. Later
events may add evidence or corrections, but earlier events must not be
rewritten. Event evidence must never become a permit, block, retry,
remediation, routing, or orchestration decision by itself.

### Future IBKR Report Fields

Future run reports must include an `ibkr_runtime` object or equivalent
dedicated section when IBKR paper runtime evidence is relevant. Required future
report evidence includes:

- broker name
- runtime mode
- paper/local host
- paper port
- client ID
- enabled or disabled state
- lifecycle and connect result
- readiness source
- submit result
- order ID
- submit uncertainty state
- reconciliation result or status
- manual-review flag
- final broker state and reason
- disconnect and shutdown result
- evidence references
- rollback-required flag
- rollback reason

Report fields are derived summaries of event and broker-visible evidence. They
must not replace append-only event records, must not grant execution authority,
and must not be used to bypass `broker_factory.py` or `main.py` review gates.

### Observational Boundary

The IBKR observability contract may describe runtime, lifecycle, submit,
reconciliation, final-state, disconnect, and rollback evidence. It must remain
separate from execution authorization.

The following remain prohibited unless separately approved by architecture
review:

- using observability fields to enable IBKR routing
- using report fields to permit or deny execution
- using read-only visibility as execution approval
- retrying, resubmitting, canceling, flattening, or remediating from evidence
- changing `broker_factory.py`
- changing `main.py`
- enabling `OPENCLAW_BROKER=ibkr`
- requiring broker calls or TWS for contract validation
