# Runtime Visibility Architecture Decision

## Decision

Runtime visibility is observability and readiness metadata only. It may report broker-adjacent state, but it does not grant execution authority.

The `runtime_visibility_blocking` field is calculated and reportable. It is not enforceable yet and must not drive trading behavior.

## Boundary

Runtime visibility providers must remain read-only. A provider may expose read methods such as `read_broker_state()` or `get_runtime_diagnostics()`.

Runtime visibility must not:

- submit orders
- build orders
- cancel orders
- flatten positions
- remediate broker state
- retry execution
- resubmit orders
- route strategy decisions

`broker_factory.py` remains execution-isolated. Runtime visibility must not change broker construction or execution routing.

`main.py` may attach runtime visibility metadata to reports, but it must not branch strategy, risk, submit, cancel, flatten, or reconciliation behavior on `runtime_visibility_blocking`.

## Activation

Manual-only runtime visibility remains the default until scheduled or runtime provider activation is separately reviewed.

Read-only visibility evidence proves only observability/readiness metadata behavior. It is not approval for strategy-driven IBKR execution.

## IBKR Read-Only Runtime Visibility Activation Contract

Future IBKR read-only runtime visibility activation means observation only. It
may collect and report broker-visible state such as connection readiness,
open-order state, position state, broker-state classification, disconnect
state, and runtime-thread state.

It is not IBKR execution runtime activation. It is not submit readiness. It is
not authority to clean up, flatten, sell, cancel, retry, resubmit, remediate,
route orders, enable live trading, or bypass any execution gate.

IBKR read-only visibility must not bypass the managed AAPL long `1` paper hold
state. While that managed non-flat state remains active, future IBKR submit
smokes remain blocked unless a separate explicit cleanup or flatten gate
records a different decision.

IBKR read-only visibility must not alter the Alpaca scheduled baseline. It must
not change strategy, risk, execution, reconciliation, broker construction,
state writes, observations, systemd behavior, or scheduled runtime behavior.

This contract does not authorize changes to `broker_factory.py`, `config.py`,
`main.py`, systemd service or timer files, `.env`, runtime state files, logs,
or any Python runtime implementation. Any future code or config change requires
a separate test-only or implementation gate before work begins.

Any future activation path must remain deterministic, source-controlled,
auditable, and separately approved. The approval must name the exact files,
configuration surface, command or validation path, stop conditions, rollback
posture, and evidence required before and after activation.

## Future IBKR Read-Only Visibility Dry-Run Operator Contract

A future IBKR read-only visibility dry run is observation-only. It is not IBKR
execution runtime activation. It is not submit readiness. It is not authority
to clean up, flatten, sell, cancel, retry, resubmit, remediate, route orders,
enable live trading, or bypass any execution gate.

`runtime_visibility_blocking=true` is evidence only. It may identify observed
broker state that would require operator review, but it must not permit, deny,
route, submit, cancel, flatten, sell, retry, remediate, or clean up anything.

The managed AAPL long `1` paper position remains a held non-flat paper state.
It is not clean submit readiness. A read-only visibility dry run must report
that state as evidence only and must not change the hold decision.

Before any future dry run is executed, the approving record must name:

- execution context
- exact environment surface
- exact command
- stop conditions
- expected report fields
- evidence fields to capture
- rollback or no-op posture

Expected report evidence is limited to observation fields such as
`orchestration.runtime_visibility.runtime_visibility_reports`,
`runtime_visibility_blocking`, `runtime_visibility_reason`, provider name,
provider status, connection readiness, open-order state, position state,
broker-state classification, disconnect state, shutdown state, and thread
state.

The following must remain absent from read-only visibility evidence:

- `submit_approved`
- `submit_attempted`
- `cleanup_approved`
- `flatten`
- `sell`
- `cancel`
- `retry`
- `remediation`
- `safe_to_submit`
- order construction or order ID fields
- submit or reconciliation state fields

This contract does not approve `.env` changes, VPS work, systemd changes,
scheduled behavior changes, broker/API/TWS access, `main.py` execution, runtime
activation, submit smoke, cleanup, flatten, sell, cancel, retry, remediation,
or live trading.

## Enforcement

Any enforcement behavior requires a separate explicit architecture review before implementation.

That review must define:

- whether runtime visibility may block trading
- which layer owns blocking authority
- stale-data handling
- false positive and false negative handling
- test coverage without broker side effects
- operator override and rollback behavior
- audit evidence required before and after blocking

Until that review is complete, runtime visibility remains observed-only.
