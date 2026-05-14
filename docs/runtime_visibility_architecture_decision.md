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
