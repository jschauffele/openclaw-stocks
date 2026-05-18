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
