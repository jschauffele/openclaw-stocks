# Architecture Governance Freeze Snapshot

## Snapshot

Canonical head: `791bcbe Docs: capture architecture governance freeze snapshot`

This snapshot records the current frozen architectural state. It is a
governance note only. It does not approve runtime wiring, execution behavior,
test behavior, or production activation beyond the boundaries already present
at the canonical head.

## Current Frozen Boundaries

`main.py` remains the production orchestration owner.

It retains authority over:

- orchestration sequencing
- side-effect timing
- early returns
- event, report, and observation persistence timing
- state-write timing
- completion control flow
- strategy, risk, duplicate, and reconciliation decision placement

Broker adapters remain mechanical plugins. They may build broker-specific
payloads, submit when instructed, normalize broker responses, expose broker read
snapshots, and manage native lifecycle mechanics. They must not authorize
execution, bypass strategy or risk policy, own retry or remediation policy, or
decide whether unresolved reconciliation permits future execution.

Runtime visibility remains observability and readiness metadata only.
`runtime_visibility_blocking` may be calculated and reported, but it is not an
execution gate.

## Current Detached Seams

The current detached seams are:

- `execution_use_case.py`, which models broker-agnostic execution request and
  outcome behavior without production orchestration integration
- runtime visibility providers and orchestration, which can produce reportable
  read-only metadata without owning execution decisions
- manual IBKR read-only runtime visibility smoke tooling, which proves
  observability only
- manual IBKR submit-reconciliation smoke tooling, which remains outside the
  production `main.py` execution path

These seams are allowed to exist as isolated design and evidence surfaces. They
are not approval to move production control flow into them.

## Current Approved Runtime Behavior

The approved runtime behavior remains the existing `main.py` flow:

- load configuration
- create the supported production broker adapter through `broker_factory.py`
- build and attach runtime visibility metadata for reporting only
- validate configuration and market data
- generate and validate strategy signal
- run risk and duplicate checks
- reconcile broker position and open-order state before submit
- handle dry-run or paper-submit behavior
- run submit reconciliation when broker submission becomes uncertain
- persist events, reports, observations, and state from the current
  orchestration branches

Runtime visibility metadata may appear in reports, but production strategy,
risk, submit, cancel, flatten, remediation, reconciliation, and completion
behavior must not branch on runtime visibility blocking state.

## Current Deferred Areas

The following areas remain deferred:

- production integration of `execution_use_case.py`
- IBKR execution activation through `broker_factory.py`
- strategy-driven IBKR execution
- runtime visibility enforcement
- retry policy
- remediation policy
- cancel, flatten, or resubmit behavior
- full presenter extraction
- full mapper extraction
- full terminal report builder extraction
- any broader relocation of `main.py` terminal branches

Deferred means not approved for implementation without a separate architecture
review.

## Current Orchestration Ownership Posture

The orchestration ownership posture is conservative. `main.py` may be pressured,
but it remains the boundary owner for sequencing, side effects, terminal
branches, and run completion.

Narrow helpers may be considered later only when they receive already-decided
facts and return pure payloads or notes. They must not create a second
orchestration layer or hide execution policy inside formatting code.

## `execution_use_case.py` Status

`execution_use_case.py` is present as a broker-agnostic use-case skeleton and
testable model. It accepts already-approved trade intent and maps execution
outcomes for dry-run, paper-submit, and uncertain-submit reconciliation cases.

It remains frozen and detached from runtime orchestration. It must not become
part of production broker selection, production submit routing, or completion
control without a separate explicit review.

## Runtime Visibility Status

Runtime visibility is observed-only.

Approved behavior:

- read-only providers may expose broker-adjacent diagnostics
- runtime visibility summary may be calculated
- `runtime_visibility_blocking` and reason fields may be reported
- manual read-only IBKR evidence may document observability readiness

Not approved:

- blocking trades
- permitting trades
- routing orders
- changing risk or duplicate decisions
- triggering cancel, flatten, retry, resubmit, or remediation behavior
- becoming a dependency for execution completion

## Presenter And Mapper Status

Presenter and mapper pressure is classified as medium.

No presenter or mapper extraction is approved yet. Future helpers may only
build already-decided dictionaries or notes, such as event payloads, report
notes, or observation fields.

Presenter and mapper helpers must not own strategy policy, risk policy,
duplicate policy, reconciliation policy, runtime visibility policy, broker
calls, order construction, order submission, state writes, persistence,
retries, remediation, cancel behavior, flatten behavior, resubmit behavior, or
completion control flow.

## Reconciliation Ownership Status

Reconciliation currently has two distinct meanings that must stay separated:

- pre-submit broker-state reconciliation in `main.py`, which can block the
  current order attempt based on existing position and open-order facts
- uncertain-submit reconciliation, which evaluates broker state after a submit
  acknowledgement becomes uncertain

`main.py` owns production reconciliation placement, event/report persistence,
and completion behavior. Reconciliation helpers and workflows may provide
facts, normalized results, or isolated smoke evidence, but they do not decide
future execution authority or own remediation policy.

## `broker_factory.py` Status

`broker_factory.py` remains execution-isolated and production-supported only for
the currently configured Alpaca adapter path.

IBKR execution must not be added to production broker selection until a
separate architecture review approves the execution boundary, disabled-by-
default configuration gates, fake-native tests, paper-only smoke evidence,
submit reconciliation evidence, operator controls, and rollback posture.

Runtime visibility provider construction must not change broker construction or
execution routing.

## Pressures That Could Justify Reopening Boundaries Later

The following pressures may justify a future boundary review:

- repeated event payload mapping duplicates the same already-decided facts
- report or observation field construction becomes error-prone while remaining
  pure formatting
- terminal branches become difficult to audit because formatting obscures
  control flow
- fake-broker execution use-case tests expose a stable contract that can reduce
  production risk
- IBKR paper-only validation produces enough evidence to review a disabled
  integration gate
- runtime visibility produces stable false-positive and false-negative handling
  requirements suitable for an enforcement design
- reconciliation evidence shows a narrow reusable result model that does not
  move policy ownership

These pressures justify review only. They do not pre-approve implementation.

## Changes Explicitly Not Approved

The freeze does not approve:

- moving production orchestration out of `main.py`
- wiring `execution_use_case.py` into production runtime
- adding IBKR to `broker_factory.py`
- using runtime visibility to block, permit, or route trades
- turning `runtime_visibility_blocking` into execution authorization
- moving strategy, risk, duplicate, reconciliation, or runtime visibility
  policy into presenters or mappers
- moving persistence or state writes into presenters or mappers
- adding retry, remediation, cancel, flatten, or resubmit behavior
- enabling strategy-driven IBKR execution
- treating read-only IBKR visibility evidence as execution readiness
- treating manual smoke tooling as production activation

## Canonical Commits Associated With The Freeze State

- `f03922a Docs: define presenter mapper boundary`
- `26f722d Test: cover execution outcome report event compatibility`
- `e682cc7 Architecture: add broker-agnostic execution use-case skeleton`
- `c44284c Docs: define broker-agnostic execution use-case model`
- `8a309d5 Docs: define execution use-case boundaries`
- `410fd2a Docs: separate IBKR visibility and execution architecture`
- `ee70248 Docs: define runtime visibility architecture boundaries`
- `1ce660a Docs: record first IBKR read-only visibility smoke evidence`
- `a4223a7 Architecture: add manual IBKR read-only visibility smoke harness`
- `ea7167f Architecture: add guarded IBKR read-only visibility provider scaffold`
