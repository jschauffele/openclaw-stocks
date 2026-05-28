# IBKR Execution Architecture Separation Decision

## Decision

IBKR runtime visibility and IBKR execution are separate control planes.

Runtime visibility remains observability and readiness metadata only. It may report broker-adjacent state, but it does not authorize or perform execution.

IBKR execution must not evolve by extending runtime visibility. Execution adapters, submit workflows, reconciliation workflows, and order-building logic remain separate from visibility providers.

## Connection Context Guard

IBKR/TWS localhost evidence is scoped to the execution context that produced it.
`127.0.0.1` means the loopback interface of the current process context, not
automatically the user's Mac GUI TWS context. See
`docs/ibkr_tws_connection_context_matrix.md` before interpreting any
`localhost` IBKR/TWS result from `DIRECT_MAC_TERMINAL`, `CODEX_LOCAL`, `VPS`,
or `CODEX_VPS`.

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

## Localhost Connect-Smoke Approval Runbook

This runbook defines the approval boundary for a future local manual
`manual_ibkr_localhost_connect_smoke.py` run. It does not approve running the
smoke yet. The actual smoke run requires separate explicit approval.

The future smoke is local-only and paper-only. It may connect only to TWS or
IB Gateway running in paper mode on a localhost host. Approved hosts are
`127.0.0.1`, `localhost`, and `::1`. Approved paper ports are `7497` and
`4002`. The operator must use a unique client ID for the run so it cannot
collide with another TWS or IB Gateway session.

The expected command is:

```bash
venv/bin/python manual_ibkr_localhost_connect_smoke.py
```

Operator preflight before any separately approved run:

- verify the repository branch and commit
- verify the tracked worktree is clean
- verify TWS or IB Gateway is manually confirmed to be in paper mode
- verify the configured endpoint is localhost-only
- verify the configured port is an approved paper port
- verify no live routing is enabled
- verify the command is only the manual localhost connect smoke
- verify no VPS execution is involved

Expected evidence from the future run:

- `nextValidId` readiness
- connect result
- connection completion source
- timeout behavior if TWS or IB Gateway is unavailable
- disconnect result
- runtime thread and disconnect-join evidence
- nonfatal IBKR status codes handled without false failure
- no submit or reconciliation evidence

The following remain prohibited:

- submit
- reconciliation
- market data
- strategy or risk paths
- state writes
- observations
- VPS execution
- production routing
- `main.py` runtime activation
- normal runtime config activation
- `broker_factory.py` activation

Stop conditions for the future run:

- live account or live routing is detected
- host is not localhost
- port is not an approved paper port
- connection result is ambiguous
- readiness times out
- disconnect or runtime-thread shutdown is uncertain
- any submit, reconciliation, order, or broker-state evidence appears
- any production or runtime configuration activation is required

This runbook does not approve submit or reconciliation. It does not approve
`main.py`, `broker_factory.py`, or `config.py` changes. It does not approve
production routing, VPS execution, or any future smoke execution without a
separate approval checkpoint.

### Localhost Connect-Smoke Pass Evidence

The local paper IBKR localhost connect smoke was run with permitted local
socket execution:

```bash
venv/bin/python manual_ibkr_localhost_connect_smoke.py
```

The result was `CONNECT_SMOKE_PASS`. The terminal lifecycle result reported
`BrokerLifecycleResult` with `passed=True`, `reason=connect_ready`,
`message=next_valid_id`, and `connected=True`. Shutdown evidence reported
`disconnect_joined=True`, `connect_state=disconnected`,
`shutdown_state=complete`, and `thread_state=stopped`. The command exited with
status 0. `git status --short` showed only the pre-existing untracked
`.local/` and `.venv-ibkr312/` directories.

Prior connect failures should be treated as sandbox, local permission, or
timing related. They are not evidence of an OpenClaw harness failure. The
successful run did not run `main.py`, did not perform any VPS action, did not
change files or environment variables, did not submit or reconcile orders, and
did not run market data, strategy, risk, state-write, or observation paths.

This evidence does not approve submit or reconciliation. It does not approve
runtime activation. It does not approve live routing.

## Submit/Reconciliation Report-Only And Preflight-Only Approval Runbook

This runbook defines the approval boundary for future manual broker-state
`--report-only` or `--preflight-only` use of
`manual_ibkr_submit_reconciliation_smoke.py`. It documents the future modes but
does not approve running either mode yet.

The only future modes covered by this runbook are:

- `--report-only`
- `--preflight-only`

This runbook does not approve submit. It does not approve reconciliation
activation. It does not approve `placeOrder`. It does not approve retry,
resubmit, cancel, flatten, or remediation behavior.

Operator preflight required before any separately approved run:

- local execution only
- paper TWS or paper IB Gateway only
- API socket already confirmed ready
- no live routing
- correct account and paper mode manually confirmed
- clean tracked worktree
- current commit verified
- no `main.py` runtime activation
- no `broker_factory.py` or `config.py` changes

For `--report-only`, a future separately approved run may read the manual
harness last-run state and may query paper broker state. It may query execution
snapshots only for report evidence tied to existing last-run state, such as a
previous `submitted_at`. It must preserve the existing last-run state and must
not write a replacement last-run state.

Expected `--report-only` evidence:

- last-run state loaded from the manual harness state file
- paper broker open-order snapshot
- paper broker position snapshot
- optional execution snapshot only when prior last-run state provides the
  required submitted-at evidence
- report-only marker
- disconnect and runtime-thread shutdown evidence
- unchanged manual harness last-run state
- no submit, order, or reconciliation workflow evidence

`--report-only` stop conditions:

- live account or live session ambiguity
- non-localhost endpoint or non-paper port
- stale unsafe last-run state that cannot be interpreted safely
- open-order ambiguity
- unexpected non-flat position
- execution snapshot ambiguity
- any submit or order evidence
- any reconciliation workflow invocation
- any production runtime path touched

For `--preflight-only`, a future separately approved run may check paper broker
open orders and positions only. It must skip submit, skip order construction
for routing, skip `placeOrder`, and skip reconciliation workflow activation. It
may write manual harness state under `.local` only if that state write is
explicitly approved in the separate run approval.

Expected clean `--preflight-only` state:

- paper broker open-order snapshot is unambiguous
- no open buy orders for the smoke symbol
- paper broker position snapshot is unambiguous
- position for the smoke symbol is flat or absent
- submit was not attempted
- no order ID or order status is present
- no reconciliation status is present
- no manual review is required
- final broker state is `clean`

Unsafe `--preflight-only` states:

- any open buy order for the smoke symbol
- any ambiguous open-order snapshot
- any non-flat position for the smoke symbol
- any ambiguous position snapshot
- stale unsafe last-run state requiring operator cleanup
- any disconnect or runtime-thread shutdown uncertainty

`--preflight-only` stop conditions:

- live account or live session ambiguity
- non-localhost endpoint or non-paper port
- open-order ambiguity
- unexpected non-flat position
- stale unsafe last-run state
- execution snapshot ambiguity
- any submit or order evidence
- any reconciliation workflow invocation
- any production runtime path touched

The following remain forbidden for both modes:

- live IBKR or live TWS
- VPS execution
- production routing
- `main.py` execution
- market data
- strategy or risk paths
- production state writes
- observations
- submit
- reconciliation activation
- `placeOrder`
- retry, resubmit, cancel, flatten, or remediation behavior

If any rollback or stop condition occurs, the run must be classified as failed
or uncertain, the operator must stop immediately, and no further IBKR
submit/reconciliation work may continue until a separate review resolves the
evidence. This runbook does not change production authority and does not approve
any future runtime activation.

### Submit/Reconciliation Report-Only Pass Evidence

The local paper IBKR report-only broker-state check was run with:

```bash
venv/bin/python manual_ibkr_submit_reconciliation_smoke.py --host 127.0.0.1 --port 7497 --client-id 9116 --report-only
```

The result was `REPORT_ONLY_PASS` with exit status 0. `git status --short`
showed only the pre-existing untracked `.local/` and `.venv-ibkr312/`
directories.

Evidence from the run:

- `last_run_state=None`
- `connection_result.passed=True`
- `connection_result.reason=connect_ready`
- `connection_result.message=next_valid_id`
- `next_valid_id=9`
- `pre_submit_open_order_snapshot.passed=True`
- `pre_submit_open_order_snapshot.open_buy_order_qty=0`
- `pre_submit_open_order_snapshot.open_buy_order_count=0`
- `pre_submit_open_order_snapshot.reason=open_buy_orders_loaded`
- `pre_submit_position_snapshot.passed=True`
- `pre_submit_position_snapshot.found=False`
- `pre_submit_position_snapshot.qty=0`
- `pre_submit_position_snapshot.reason=no_position`
- `pre_submit_broker_state=clean`
- `submit_reconciliation_report_only=True`
- `callback_count=17`
- expected broker-state reads occurred: `reqAllOpenOrders`,
  `reqPositionsMulti`, and `cancelPositionsMulti`
- `disconnect_result.passed=True`
- `disconnect_result.reason=disconnect_complete`
- `connect_state=disconnected`
- `shutdown_state=complete`
- `thread_state=stopped`

No submit occurred. No `placeOrder` occurred. No reconciliation workflow was
activated. No market data, strategy, risk, production state writes, or
observations occurred. `main.py` was not executed. No VPS action occurred.

This evidence does not approve `--preflight-only`. It does not approve submit
or reconciliation. It does not approve runtime activation or live routing.

### Submit/Reconciliation Preflight-Only Pass Evidence

The local paper IBKR preflight-only broker-state check was run with:

```bash
venv/bin/python manual_ibkr_submit_reconciliation_smoke.py --host 127.0.0.1 --port 7497 --client-id 9116 --preflight-only
```

The result was `PREFLIGHT_ONLY_PASS` with exit status 0. `git status --short`
showed only the pre-existing untracked `.local/` and `.venv-ibkr312/`
directories.

Evidence from the run:

- `last_run_state=None`
- `connection_result.passed=True`
- `connection_result.reason=connect_ready`
- `connection_result.message=next_valid_id`
- `next_valid_id=9`
- `pre_submit_open_order_snapshot.passed=True`
- `pre_submit_open_order_snapshot.open_buy_order_qty=0`
- `pre_submit_open_order_snapshot.open_buy_order_count=0`
- `pre_submit_open_order_snapshot.reason=open_buy_orders_loaded`
- `pre_submit_position_snapshot.passed=True`
- `pre_submit_position_snapshot.found=False`
- `pre_submit_position_snapshot.qty=0`
- `pre_submit_position_snapshot.reason=no_position`
- `pre_submit_broker_state=clean`
- `submit_reconciliation_preflight_only=True`
- expected broker-state reads occurred: `reqAllOpenOrders`,
  `reqPositionsMulti`, and `cancelPositionsMulti`
- `disconnect_result.passed=True`
- `disconnect_result.reason=disconnect_complete`
- `connect_state=disconnected`
- `shutdown_state=complete`
- `thread_state=stopped`

The manual harness state file `.local/ibkr_smoke_last_state.json` was written
as expected for preflight-only with:

- `submit_attempted=false`
- `order_id=null`
- `order_status=null`
- `reconciliation_status=null`
- `manual_review_required=false`
- `final_broker_state=clean`
- `final_broker_state_reason=no_open_orders_or_position`
- `disconnect_joined=true`
- `disconnect_passed=true`

No submit occurred. No `placeOrder` occurred. No reconciliation workflow was
activated. No market data, strategy, risk, production state writes, or
observations occurred. `main.py` was not executed. No VPS action occurred.

This evidence does not approve actual submit. It does not approve
reconciliation activation. It does not approve runtime activation or live
routing.

## Controlled Submit/Reconciliation Approval Runbook

This runbook defines the approval boundary for any future controlled paper
submit/reconciliation smoke using `manual_ibkr_submit_reconciliation_smoke.py`.
It does not approve running submit now.

Current prerequisite evidence:

- `--report-only` passed and evidence is documented.
- `--preflight-only` passed and evidence is documented.
- Broker state was clean.
- `.local/ibkr_smoke_last_state.json` records `submit_attempted=false`, no
  order fields, no reconciliation status, and `final_broker_state=clean`.

Approval status:

- this runbook does not approve running submit yet
- this runbook does not approve runtime activation
- this runbook does not approve `main.py`, `broker_factory.py`, or `config.py`
  changes
- this runbook does not approve live routing

Required future operator preflight before `placeOrder`:

- local-only execution
- paper TWS or paper IB Gateway only
- localhost paper port only
- no live routing
- exact current commit verified
- clean tracked worktree
- API socket already confirmed ready
- paper account and mode manually confirmed
- client ID approved and unique
- clean broker state immediately before submit
- `.local` last-run state reviewed and safe

Required future command fields:

- exact command must be approved before run
- exact symbol
- exact quantity
- exact order type
- exact limit price if limit order
- exact client ID
- exact timeout settings if relevant

Allowed future `placeOrder` scope:

- one manual harness order only
- paper only
- no retry
- no resubmit
- no cancel
- no flatten
- no remediation

Expected future submit evidence:

- `submitted_at`
- `order_id`
- `order_status`
- `order_ref`
- `submit_attempted=true`
- submit result classification
- callback evidence
- final broker-state evidence
- `.local/ibkr_smoke_last_state.json` persistence

Reconciliation rules:

- reconciliation workflow may run only if submit result requires
  reconciliation
- reconciliation must remain manual-harness scoped
- unresolved or ambiguous reconciliation requires manual review
- no automatic retry or remediation
- no continuation after unsafe state

Stop conditions:

- live account or live session ambiguity
- non-localhost endpoint
- non-paper port
- open-order ambiguity
- unexpected non-flat position
- stale unsafe last-run state
- `placeOrder` ambiguity
- submit timeout
- missing order ID
- ambiguous order status
- unresolved reconciliation
- disconnect uncertainty
- any production runtime path touched

Explicit no-go:

- no actual submit now
- no `placeOrder` now
- no reconciliation activation now
- no runtime activation
- no VPS action
- no `main.py` changes
- no `broker_factory.py` changes
- no `config.py` changes
- no market data
- no strategy or risk paths
- no production state writes
- no observations
- no live routing

If a future controlled submit/reconciliation smoke is approved, that approval
must name the exact command and values, explicitly authorize the single
paper-only `placeOrder`, and restate the stop conditions before execution.

### Controlled Submit Cleanup Evidence

The first controlled IBKR paper submit smoke was run exactly once with:

```bash
venv/bin/python manual_ibkr_submit_reconciliation_smoke.py --host 127.0.0.1 --port 7497 --client-id 9116 --timeout 15 --symbol AAPL --qty 1 --order-type market
```

The run created paper order ID `9` for `AAPL` buy quantity `1` as a market
order. The result was `CONTROLLED_SUBMIT_UNCERTAIN` because order ID `9`
remained open with broker status `PreSubmitted`. A read-only inspection
confirmed `POST_SUBMIT_READ_ONLY_OPEN_ORDER`: order ID `9` still appeared open,
`open_buy_order_qty=1`, `open_buy_order_count=1`, AAPL position remained `0`,
and fills remained `0`.

The repository had no cancel-only OpenClaw manual harness path. The manual
harness and adapter did not provide a tested cleanup path for `cancelOrder`, and
the safety baseline intentionally preserved no retry, no resubmit, no cancel,
no flatten, and no remediation behavior. The operator therefore used the TWS
paper UI to cancel order ID `9` manually instead of using bot code.

A final report-only verification produced `POST_MANUAL_CANCEL_CLEAN`:

- order ID `9` no longer appeared open
- `open_buy_order_qty=0`
- `open_buy_order_count=0`
- AAPL position remained `0`
- fills remained `0`
- `pre_submit_broker_state=clean`
- report-only verification exited with status 0

The local manual harness state file `.local/ibkr_smoke_last_state.json` still
contains historical stale state from the original submit run, including
`final_broker_state=open_orders`. That file must not be treated as current
broker truth after the manual TWS cancellation. The current broker truth is the
final report-only verification showing no open order, no position, and no
fills.

No runtime activation occurred. `main.py` was not executed. No strategy, risk,
market data, production state-write, or observation path ran. No VPS action
occurred.

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

## Broker Factory IBKR Activation Review Plan

`broker_factory.py` remains closed now. `main.py` remains closed now. This
plan defines the criteria required before IBKR can ever be added to broker
selection, but it does not approve that change.

Adding `ibkr` to `SUPPORTED_BROKERS` requires explicit architecture approval.
Until that approval exists, `OPENCLAW_BROKER=ibkr` must continue to fail closed
with the explicit unsupported-broker error.

Any future IBKR broker factory support must be disabled by default. A future
enabled path must require `OPENCLAW_IBKR_RUNTIME_ENABLED=true`, valid
paper-localhost config, and the existing config-to-assembly mapping. Invalid,
missing, live, non-localhost, or non-paper config must reject before factory
construction can return an IBKR adapter.

Future broker factory construction must remain construction-only. It must not
connect, submit, run the native runtime loop, load live broker state, call
broker APIs, create orders, retry, resubmit, cancel, flatten, or remediate. It
must be fake-native testable without TWS or broker calls.

Alpaca behavior must remain unchanged. The existing Alpaca factory path,
supported-broker behavior, and adapter construction semantics must remain
stable while any future IBKR path is reviewed.

Rollback must restore Alpaca-only routing and the explicit unsupported-broker
failure for `OPENCLAW_BROKER=ibkr`. Rollback must not depend on partial runtime
state or operator memory.

### Required Future Broker Factory Tests

Before any broker factory activation work is approved, tests must prove:

- Alpaca factory behavior is unchanged
- disabled IBKR still rejects
- invalid IBKR config rejects
- enabled fake-native IBKR factory construction does not connect, run, submit,
  or call broker APIs
- factory construction makes no broker calls
- factory construction requires no TWS
- `main.py` is not imported and gains no orchestration authority
- rollback restores explicit unsupported-broker failure for IBKR

### Broker Factory No-Go Boundaries

The following remain prohibited by this plan:

- changing `broker_factory.py` now
- changing `main.py` now
- enabling `OPENCLAW_BROKER=ibkr` now
- adding production routing
- making broker calls
- requiring TWS
- changing strategy, risk, execution, or reconciliation behavior

## Main IBKR Orchestration Review Plan

`main.py` remains closed now. `broker_factory.py` remains closed now. No IBKR
orchestration is approved by this plan.

`main.py` is the production orchestration authority. It owns the ordered
runtime flow for configuration loading, broker construction, market-session
checks, data fetch, strategy evaluation, risk checks, duplicate protection,
pre-submit reconciliation, order construction, submit handling, uncertain-submit
reconciliation, event logging, report persistence, observation logging, state
writes, and terminal completion.

Any future IBKR branch in `main.py` requires explicit architecture approval.
The review must happen after the broker factory activation gate is separately
approved, because `main.py` must not become the first place where IBKR broker
selection is enabled.

### Required Future Main Review Areas

Before any IBKR orchestration work is approved, the review must define:

- where IBKR lifecycle and connect happen in the run sequence
- where IBKR runtime config validation happens
- where broker factory selection happens
- where market-session checks remain separate from broker lifecycle state
- where submit uncertainty and reconciliation handling occur
- where manual-review terminal states are written
- where append-only event logging occurs
- where `last_run_report.json` IBKR fields are populated
- where rollback-required states are set
- where state writes are allowed
- where state writes are prohibited

IBKR lifecycle and connect must not occur before configuration has passed
fail-closed validation and broker selection has passed the approved
`broker_factory.py` gate. Market-session checks must remain market-session
checks only; they must not become IBKR lifecycle authorization.

Submit/reconciliation uncertainty must preserve the current separation between
submit acknowledgement, reconciliation workflow evidence, manual-review
classification, report persistence, observation logging, state writes, and
completion events. Manual-review terminal states must be explicit and must
prevent hidden retry or resubmit behavior.

### Main Flow Preservation Requirements

Any future IBKR orchestration branch must preserve:

- existing strategy evaluation flow
- risk checks
- duplicate protection
- reconciliation sequencing
- append-only event ordering
- report persistence
- observation logging
- no-retry, no-resubmit, and no-remediation posture
- Alpaca regression path

The Alpaca path must remain behaviorally unchanged. Any IBKR branch must not
move shared strategy, risk, duplicate, reconciliation, reporting, observation,
or completion behavior unless a separate architecture review approves that
change.

### Required Future Main Tests

Before any `main.py` IBKR orchestration work is approved, tests must prove:

- Alpaca main path is unchanged
- disabled IBKR path does not run
- enabled fake-native IBKR path does not submit unless explicitly in approved
  paper mode
- unresolved reconciliation produces manual-review or blocking state
- completion event appears exactly once
- report contains IBKR runtime evidence fields
- rollback-required state is recorded when unsafe state occurs

### Main No-Go Boundaries

The following remain prohibited by this plan:

- changing `main.py` now
- changing `broker_factory.py` now
- enabling `OPENCLAW_BROKER=ibkr` now
- adding production routing
- making broker calls
- requiring TWS
- changing strategy, risk, execution, or reconciliation logic

## IBKR Activation Sequencing Summary

This sequencing summary ties the existing IBKR activation gates into a strict
ordered path before any future `broker_factory.py` or `main.py` implementation
work. It does not approve activation.

The required sequence is:

1. Keep `OPENCLAW_BROKER=ibkr` unsupported and keep `main.py` closed.
2. Preserve inert IBKR runtime config defaults and fail-closed validation.
3. Preserve config-to-assembly mapping with no native load or runtime
   authority.
4. Preserve disabled assembly behavior and fake-native construction coverage.
5. Preserve manual localhost connect-smoke evidence.
6. Preserve submit/reconciliation smoke evidence and construction-equivalence
   baseline.
7. Complete `broker_factory.py` activation review before any
   `SUPPORTED_BROKERS` change.
8. Add broker factory support only if explicitly approved, disabled by default,
   fake-native tested, and construction-only.
9. Complete `main.py` orchestration review after broker factory approval.
10. Add main orchestration only if explicitly approved, paper-only,
    rollback-aware, append-only observable, and no retry, resubmit, or
    remediation behavior is introduced.
11. Require manual paper evidence and rollback/operator approval before broader
    runtime use.

`broker_factory.py` remains closed. `main.py` remains closed.
`OPENCLAW_BROKER=ibkr` remains unsupported. No production routing is approved.
No broker calls or TWS are required by this sequence. No strategy, risk,
execution, or reconciliation behavior changes are approved by this sequence.

## First Main IBKR Fake-Native Orchestration Test Contract

Before any future `main.py` IBKR implementation work, the first main-path test
contract must prove that IBKR cannot move from factory construction into
runtime orchestration without an explicit future approval gate. This contract
does not approve `main.py` implementation.

The first future test should be named:

`test_ibkr_main_path_blocks_before_orchestration_when_not_approved`

The test must prove:

- `main.py` does not import `ibkr_runtime_config` directly
- `main.py` does not import `ibkr_runtime_assembly` directly
- `main.py` uses `create_broker_adapter` as broker selection authority
- `OPENCLAW_BROKER=ibkr` cannot proceed into market data, strategy, risk,
  reconciliation, or submit unless a future explicit orchestration approval
  gate exists
- fake-native IBKR construction does not become execution
- completion event appears exactly once
- result is blocked or error, not success
- reason is explicit, such as `ibkr_runtime_orchestration_disabled`
- no order submission event exists
- no reconciliation event exists
- no retry, resubmit, cancel, flatten, or remediation behavior occurs
- Alpaca path behavior remains unchanged

Later tests, not approved by this contract, should separately cover:

- enabled fake-native dry-run IBKR path
- IBKR lifecycle and connect evidence
- IBKR `ibkr_runtime` report section
- IBKR rollback-required state
- unresolved reconciliation manual-review state

The following remain explicitly prohibited by this contract:

- implementing `main.py` IBKR orchestration now
- making broker calls
- requiring TWS
- adding production routing
- adding live routing
- changing strategy, risk, execution, or reconciliation behavior

## Enabled Fake-Native IBKR Dry-Run Path Test Contract

This later-not-now contract defines the next main-path test boundary before any
future `main.py` IBKR orchestration implementation. It does not approve
`main.py` implementation, broker routing, lifecycle connection, submit,
reconciliation activation, or production routing.

The future test should be named:

`test_ibkr_main_path_enabled_fake_native_dry_run_stays_non_executing`

The test must prove:

- IBKR path is explicitly enabled only by approved config
- runtime mode is paper and local only
- fake-native construction does not occur unless separately approved by a
  construction evidence gate
- no live broker calls occur
- no TWS is required
- no connect, run, or submit occurs unless separately approved by a later
  lifecycle gate
- no order is submitted
- no retry, resubmit, cancel, flatten, or remediation behavior occurs
- append-only events capture IBKR runtime evidence
- the run report includes an `ibkr_runtime` section or equivalent evidence
  section
- result remains blocked, dry-run, or otherwise non-executing unless later
  execution approval exists
- rollback-required state is recorded if unsafe state occurs
- Alpaca path remains unchanged

The test contract must clearly separate these authorities:

- fake-native construction: remains separate from this pre-lifecycle reporting
  gate and must not be claimed unless it actually occurs
- lifecycle and connect evidence: remains a separate later gate before any
  connect or runtime loop behavior
- dry-run reporting: may record observational IBKR runtime evidence without
  execution authority
- actual submit and reconciliation authority: remains prohibited until a
  separate approval gate defines submit, uncertainty, manual-review, rollback,
  and no-remediation behavior

The following remain explicitly prohibited by this contract:

- implementing `main.py` IBKR orchestration now
- changing `broker_factory.py`
- making broker calls
- requiring TWS
- adding production routing
- adding live routing
- activating submit or reconciliation
- changing strategy, risk, execution, or reconciliation behavior

## IBKR Non-Executing Dry-Run Result And Report Contract

This contract defines the future result and reporting model for a non-executing
IBKR dry-run path before any fake-native construction test or `main.py`
orchestration implementation is approved. It does not approve `main.py`
implementation.

The approved future non-executing result model is:

- `result`: `blocked`
- `reason`: `ibkr_runtime_lifecycle_not_approved`

The result is `blocked`, not `dry_run` or `success`, because the future test is
allowed to prove config intent and reporting evidence only. It must not imply
that IBKR lifecycle, connect, submit, reconciliation, or execution authority has
been approved.

Non-executing dry-run is config-intent and reporting evidence only. It must not
construct the IBKR assembly, claim fake-native construction, connect, run the
native loop, submit an order, invoke reconciliation, retry, resubmit, cancel,
flatten, remediate, or change strategy, risk, execution, or reconciliation
behavior. The Alpaca path must remain unchanged.

### Required `ibkr_runtime` Report Section

The future report must include an `ibkr_runtime` section or equivalent
dedicated evidence section with these fields:

- `broker_name`
- `runtime_enabled`
- `assembly_enabled`
- `runtime_mode`
- `host`
- `port`
- `client_id`
- `fake_native`
- `lifecycle_approved`
- `connect_approved`
- `submit_approved`
- `reconciliation_approved`
- `connect_attempted`
- `run_loop_started`
- `submit_attempted`
- `reconciliation_attempted`
- `result`
- `reason`
- `rollback_required`
- `rollback_reason`

For this non-executing gate, the expected values are:

- `broker_name`: `ibkr`
- `runtime_enabled`: `true`
- `assembly_enabled`: `false`
- `runtime_mode`: `paper_localhost`
- `fake_native`: `false`
- `lifecycle_approved`: `false`
- `connect_approved`: `false`
- `submit_approved`: `false`
- `reconciliation_approved`: `false`
- `connect_attempted`: `false`
- `run_loop_started`: `false`
- `submit_attempted`: `false`
- `reconciliation_attempted`: `false`
- `result`: `blocked`
- `reason`: `ibkr_runtime_lifecycle_not_approved`

The following fields must remain absent while no lifecycle, connect, or submit
authority exists:

- `connect_result`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result`
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

Fields deferred until lifecycle approval:

- `connect_result`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result`
- `shutdown_state`

Fields deferred until submit/reconciliation approval:

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

## IBKR Lifecycle/Connect Evidence Test Contract

This contract defines the first future lifecycle/connect evidence gate before
any `main.py` lifecycle/connect implementation is approved. It does not approve
`main.py` changes, broker calls, TWS usage, production routing, live routing,
submit authority, or reconciliation authority.

The future test should be named:

`test_ibkr_main_path_fake_native_lifecycle_connect_records_evidence_without_submit`

The test must prove that lifecycle/connect evidence can be recorded with
fake-native components only, without real broker calls and without converting
IBKR runtime reporting into submit or reconciliation authority. The result must
remain `blocked` unless a later execution approval gate exists. The Alpaca path
must remain unchanged.

The following fields may first appear only in this lifecycle/connect evidence
gate:

- `connect_result`
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result`
- `disconnect_result.passed`
- `disconnect_result.reason`
- `shutdown_state`

The future test must require:

- fake-native components only
- no real IBKR or TWS connection
- no broker calls
- no TWS requirement
- no submit
- no reconciliation
- no `order_id`
- no `order_status`
- no `submit_state`
- no `filled_qty`
- no `working_qty`
- no `final_broker_state`
- no retry, resubmit, cancel, flatten, or remediation behavior
- append-only lifecycle/connect evidence
- `result` remains `blocked` unless later execution approval exists
- Alpaca path remains unchanged

The contract separates these authorities:

- config intent: may report requested IBKR runtime config and paper-localhost
  intent without construction or connection evidence
- assembly construction: may be claimed only when the assembly is actually
  constructed, and remains separate from lifecycle/connect authority
- lifecycle/connect evidence: may record fake-native connect/run/disconnect
  evidence only after this gate is separately approved and implemented
- submit/reconciliation authority: remains prohibited until a separate approval
  gate defines order submission, uncertainty handling, final broker-state
  evidence, manual-review states, rollback behavior, and no-remediation policy

The following remain explicitly prohibited by this contract:

- implementing `main.py` IBKR lifecycle/connect orchestration now
- changing `broker_factory.py`
- making real IBKR or TWS connections
- making broker calls
- requiring TWS
- adding production routing
- adding live routing
- activating submit or reconciliation
- changing strategy, risk, execution, or reconciliation behavior

## Fake-Native Lifecycle Activation Boundary

Fake-native lifecycle/connect evidence activation is currently
test-patched/manual-harness-only. It is not a normal runtime configuration
feature and is not approved for deployed runtime activation.

Deployed `main.py` must remain fail-closed at
`ibkr_runtime_lifecycle_not_approved` unless a separately approved
fake-native injection path supplies actual fake-native lifecycle evidence.
Current runtime configuration must not activate fake-native lifecycle evidence
through normal deployed execution.

Fake-native lifecycle evidence is not production-runtime activation. It is not
real IBKR or TWS activation. It does not approve broker calls, market data,
strategy, risk, order submission, state writes, observations, retry, resubmit,
cancel, flatten, remediation, submit authority, or reconciliation authority.

The `ibkr_runtime_submit_not_approved` result is allowed only after actual
fake-native lifecycle evidence exists and only under a separately approved
activation gate. It remains a blocked state and does not authorize submit or
reconciliation behavior.

## Main Fake-Native Lifecycle Consumption Plan

The local manual fake-native lifecycle evidence smoke has passed. It proved
operator-visible fake-native connect readiness and disconnect evidence outside
`main.py`, with no runtime loop, broker calls, submit, reconciliation, market
data, strategy, risk, state writes, observations, real IBKR, or TWS.

That evidence remains manual-harness/test-patched only. Normal runtime config
must not activate fake-native lifecycle/connect evidence. Deployed `main.py`
must continue to block with `ibkr_runtime_lifecycle_not_approved` whenever no
explicitly injected fake-native lifecycle evidence exists.

`main.py` may consume fake-native lifecycle/connect evidence only through a
separately approved explicit injection/test gate. Any future `main.py` path
must remain fail-closed unless that injection gate is present. The
`ibkr_runtime_submit_not_approved` reason is valid only after actual
fake-native lifecycle evidence exists, and it remains a blocked non-submitting
result.

Future tests for any `main.py` consumption path must prove:

- a patched `main.py` test injects fake-native lifecycle evidence explicitly
- no normal environment or config path enables fake-native evidence
- no broker calls occur
- no TWS is required
- no real IBKR connection occurs
- no submit occurs
- no reconciliation occurs
- no market data path runs
- no strategy or risk path runs
- no state writes occur
- no observations are written
- the Alpaca path remains unchanged

This plan does not approve `main.py` changes, `broker_factory.py` changes,
`config.py` changes, runtime config activation, real IBKR/TWS, broker calls,
submit/reconciliation activation, production routing, or VPS actions.

## Controlled Main Fake-Native Lifecycle Consumption Approval Design

Before any future `main.py` code may consume fake-native IBKR
lifecycle/connect evidence, the consumption path must be approved as an
explicit injection/test gate. The injected evidence may be supplied only by a
test-owned or operator-approved fake-native provider that returns already
constructed lifecycle/connect evidence fields. `main.py` must not construct
real native IBKR dependencies, load `ibapi`, connect to TWS, or infer evidence
from normal runtime configuration.

Normal config must remain blocked because `OPENCLAW_IBKR_RUNTIME_ENABLED`
expresses runtime intent only. It does not prove that fake-native lifecycle
operations occurred, and it must not by itself create construction, connect,
disconnect, readiness, submit, reconciliation, or broker-call evidence. If no
explicit injected fake-native lifecycle evidence is present, `main.py` must
remain fail-closed with:

- `result`: `blocked`
- `reason`: `ibkr_runtime_lifecycle_not_approved`

An approved injected fake-native lifecycle evidence path may produce:

- `result`: `blocked`
- `reason`: `ibkr_runtime_submit_not_approved`

That reason is valid only after actual fake-native lifecycle/connect evidence
exists. It does not approve submit, reconciliation, production routing, real
IBKR/TWS connectivity, broker calls, market data, strategy, risk, state writes,
observations, retry, resubmit, cancel, flatten, or remediation behavior.

Allowed report evidence fields after approved injection are limited to:

- `assembly_enabled`
- `fake_native`
- `connect_attempted`
- `run_loop_started`
- `connect_result`
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result`
- `disconnect_result.passed`
- `disconnect_result.reason`
- `shutdown_state`

The following submit/reconciliation fields must remain absent:

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

Future approval tests must prove:

- no-injection runtime config remains `ibkr_runtime_lifecycle_not_approved`
- `OPENCLAW_IBKR_RUNTIME_ENABLED=true` does not activate fake-native evidence
  by itself
- injected fake-native lifecycle evidence explicitly produces
  `ibkr_runtime_submit_not_approved`
- no market data, strategy, risk, submit, reconciliation, state writes, or
  observations occur
- no real IBKR connection, TWS dependency, broker call, retry, resubmit,
  cancel, flatten, or remediation occurs
- the Alpaca path remains unchanged

If fake-native lifecycle evidence becomes reachable through normal runtime
configuration or environment variables without an explicit approved injection
gate, the change must be rolled back to the fail-closed
`ibkr_runtime_lifecycle_not_approved` behavior before any further IBKR runtime
work continues.

This design does not approve `main.py` changes, `broker_factory.py` changes,
`config.py` changes, runtime activation, normal config activation of
fake-native evidence, real IBKR/TWS, broker calls, submit/reconciliation,
production routing, or VPS actions.

## Future Fake-Native Lifecycle Provider Injection Design

A runtime-accessible fake-native lifecycle provider should exist only if a
future architecture review explicitly approves `main.py` consuming
fake-native lifecycle/connect evidence outside the current patched-test path.
Until then, the provider does not exist as a runtime capability.

If approved later, the safest design is an explicit injected provider object or
callable, not an environment variable and not a normal config flag. The
provider would be supplied only by a test harness or separately approved
operator harness. Its sole responsibility would be to return already produced
fake-native lifecycle/connect evidence fields. It must not load native IBKR
dependencies, create real IBKR clients, connect to TWS, submit orders, request
broker state, invoke reconciliation, or run market/strategy/risk/state or
observation paths.

Normal config remains blocked because `OPENCLAW_IBKR_RUNTIME_ENABLED=true`
only declares runtime intent. It is not evidence that fake-native connect,
readiness, or disconnect occurred. It must not cause `main.py` to construct
fake-native components, synthesize lifecycle evidence, or change the result
from `ibkr_runtime_lifecycle_not_approved` to
`ibkr_runtime_submit_not_approved`.

The preferred provider boundary is:

- default provider: absent
- no provider present: fail closed with `ibkr_runtime_lifecycle_not_approved`
- explicit test/operator provider present: may return fake-native lifecycle
  evidence
- provider output accepted only if it contains the approved lifecycle/connect
  fields and no submit/reconciliation fields
- provider failure, missing fields, or unexpected submit/reconciliation fields:
  fail closed with `ibkr_runtime_lifecycle_not_approved`

Required tests before any implementation:

- default runtime config has no provider and remains
  `ibkr_runtime_lifecycle_not_approved`
- `OPENCLAW_IBKR_RUNTIME_ENABLED=true` does not install or activate a provider
- injected fake-native provider output produces
  `ibkr_runtime_submit_not_approved`
- provider output comes from the existing fake-native lifecycle helper or
  manual smoke evidence path
- malformed provider output fails closed
- provider output containing submit/reconciliation fields fails closed
- no market data, strategy, risk, submit, reconciliation, state writes, or
  observations occur
- no real IBKR, TWS, broker calls, retry, resubmit, cancel, flatten, or
  remediation occurs
- Alpaca path remains unchanged

This provider design does not approve implementation. It does not approve
`main.py` changes, `broker_factory.py` changes, `config.py` changes, runtime
activation, normal config activation of fake-native evidence, real IBKR/TWS,
broker calls, submit/reconciliation, production routing, or VPS actions.

## Future Fake-Native Lifecycle Provider Acceptance-Test Contract

Before any future provider implementation may touch `main.py`, the acceptance
tests must be written and must fail against the unimplemented provider
boundary. The tests define the approval boundary; they do not approve runtime
activation.

Required future tests:

- no provider default remains blocked with
  `ibkr_runtime_lifecycle_not_approved`
- `OPENCLAW_IBKR_RUNTIME_ENABLED=true` does not install or activate a provider
- normal config or environment variables cannot reach
  `ibkr_runtime_submit_not_approved`
- injected test-owned provider can return lifecycle/connect evidence from the
  fake-native smoke/helper path
- injected provider success remains blocked with
  `ibkr_runtime_submit_not_approved`
- malformed provider output fails closed for:
  - `None`
  - non-dict output
  - missing required lifecycle fields
  - wrong field types
  - provider exception
- provider output containing submit/reconciliation fields fails closed
- no trading paths run in success or rejection cases:
  - no data/fetch event
  - no strategy evaluation
  - no risk check
  - no submit
  - no reconciliation
  - no order-state write
  - no observation write
- Alpaca path remains unchanged

Provider output must fail closed if it includes any submit/reconciliation
field, including:

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

This acceptance-test contract does not approve code changes, `main.py`
changes, `broker_factory.py` changes, `config.py` changes, runtime activation,
normal config/environment provider activation, real IBKR/TWS, broker calls,
submit/reconciliation, production routing, or VPS actions.

## Future Manual Injected-Provider Validation Plan

This plan defines a future manual/operator-controlled validation gate for the
fake-native lifecycle provider boundary. It does not approve runtime activation
or normal runtime access to fake-native lifecycle evidence.

Validation must be manual/operator-controlled only. It must use an explicit
patched or injected provider that supplies fake-native lifecycle/connect
evidence already produced by the approved helper or manual smoke path. Normal
configuration and environment variables must remain blocked. In particular,
`OPENCLAW_IBKR_RUNTIME_ENABLED=true` must not install, select, or activate a
provider.

The no-provider deployed/runtime behavior must remain:

- `result`: `blocked`
- `reason`: `ibkr_runtime_lifecycle_not_approved`

The injected-provider validation behavior may be:

- `result`: `blocked`
- `reason`: `ibkr_runtime_submit_not_approved`

Injected-provider validation must not require real IBKR, TWS, broker calls, a
native runtime loop, submit, reconciliation, market data, strategy evaluation,
risk checks, order-state writes, observations, retry, resubmit, cancel,
flatten, or remediation.

Injected-provider evidence must include the approved lifecycle/connect fields:

- `assembly_enabled`
- `fake_native`
- `connect_attempted`
- `run_loop_started`
- `connect_result`
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result`
- `disconnect_result.passed`
- `disconnect_result.reason`
- `shutdown_state`

Injected-provider evidence must not include submit or reconciliation fields,
including:

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

Rollback rule: if injected fake-native lifecycle evidence becomes reachable
through normal configuration, environment variables, default runtime execution,
or any path other than an explicitly approved patched/manual validation
provider, the gate must be considered failed. The expected rollback is to
remove or disable the provider access path and restore the no-provider
`ibkr_runtime_lifecycle_not_approved` behavior before any further IBKR runtime
work proceeds.

This plan does not approve code changes, tests, `main.py` changes,
`broker_factory.py` changes, `config.py` changes, runtime activation, VPS
actions, real IBKR/TWS, broker calls, submit/reconciliation, or production
routing.

## Future Manual Injected-Provider Validation Runbook

This runbook defines the manual/operator-controlled sequence for a future
injected fake-native IBKR provider validation. It does not approve running the
validation, code changes, runtime activation, or production routing. Future
injected-provider validation requires separate approval before execution.

Allowed future operator steps:

1. Confirm the no-provider baseline:
   - `result`: `blocked`
   - `reason`: `ibkr_runtime_lifecycle_not_approved`
   - no lifecycle evidence fields are produced through normal configuration or
     environment variables
2. Generate fake-native lifecycle evidence using only the approved manual
   smoke/helper path.
3. Inject that evidence through an explicit patched provider boundary in a
   controlled validation harness.
4. Confirm injected-provider behavior:
   - `result`: `blocked`
   - `reason`: `ibkr_runtime_submit_not_approved`
5. Confirm no trading paths ran.

The following remain prohibited for this runbook:

- normal configuration or environment provider activation
- `OPENCLAW_IBKR_RUNTIME_ENABLED=true` installing or selecting a provider
- real IBKR or TWS
- broker calls
- submit or reconciliation
- market data, strategy, or risk paths
- state writes or observations
- `main.py`, `broker_factory.py`, or `config.py` changes

Expected injected-provider evidence fields:

- `assembly_enabled`
- `fake_native`
- `connect_attempted`
- `run_loop_started`
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result.passed`
- `disconnect_result.reason`
- `shutdown_state`

Rollback and stop conditions:

- injected evidence is reachable through normal configuration or environment
  variables
- the no-provider path returns `ibkr_runtime_submit_not_approved`
- any submit or reconciliation field appears
- any broker or TWS call is required
- any market data, strategy, risk, state write, or observation path runs

If any stop condition occurs, the validation must be considered failed. The
expected rollback is to restore the no-provider
`ibkr_runtime_lifecycle_not_approved` behavior before further IBKR runtime work
continues.

### Local Manual Injected-Provider Validation Evidence

The local patched-provider validation was run through the test harness. It
printed `manual injected-provider validation passed` and exited with status 0.
`git status --short` remained clean except for the pre-existing untracked
`.local/` and `.venv-ibkr312/` directories.

The baseline no-provider path remained blocked at
`ibkr_runtime_lifecycle_not_approved`. The injected provider path remained
blocked at `ibkr_runtime_submit_not_approved`. No submit or reconciliation
occurred. No market data, strategy, risk, state writes, observations, broker
calls, or real IBKR/TWS activity occurred.

This evidence does not approve runtime activation. It does not approve normal
configuration or environment provider activation. It does not approve VPS
execution.

## IBKR Post-Lifecycle/Connect Blocked Result Contract

This contract defines the blocked result after fake-native lifecycle/connect
evidence exists while submit and reconciliation remain unapproved. It does not
approve `main.py` implementation, broker calls, TWS usage, production routing,
live routing, submit authority, or reconciliation authority.

The approved post-lifecycle/connect non-executing result model is:

- `result`: `blocked`
- `reason`: `ibkr_runtime_submit_not_approved`

`ibkr_runtime_lifecycle_not_approved` is used before lifecycle/connect evidence
is approved. `ibkr_runtime_submit_not_approved` is used after lifecycle/connect
evidence exists but submit and reconciliation remain prohibited.

Lifecycle/connect evidence does not grant submit authority. It does not grant
reconciliation authority. It does not authorize market data, strategy, risk,
order submission, state writes, observations, retry, resubmit, cancel, flatten,
or remediation behavior.

The post-lifecycle/connect report and event evidence may include:

- `connect_result`
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- `run_thread_state`
- `disconnect_joined`
- `disconnect_result`
- `disconnect_result.passed`
- `disconnect_result.reason`
- `shutdown_state`

The following fields must remain absent until a separate submit/reconciliation
approval gate exists:

- `order_id`
- `order_status`
- `submit_state`
- `submitted_at`
- `reconciliation_status`
- `manual_review_required`
- `filled_qty`
- `working_qty`
- `final_broker_state`

The following remain explicitly prohibited by this contract:

- implementing `main.py` IBKR lifecycle/connect orchestration now
- changing `broker_factory.py`
- making real IBKR or TWS connections
- making broker calls
- requiring TWS
- adding production routing
- adding live routing
- activating submit or reconciliation
- changing strategy, risk, execution, or reconciliation behavior
