# Execution Use-Case Boundary Decision

## Decision

Execution authority belongs to use cases and orchestration, not broker adapters.

Broker adapters are low-level plugins. They normalize broker mechanics and expose broker capabilities, but they do not decide whether execution is allowed.

Strategy and risk policy remain above execution adapters. Business rules such as allowed symbols, buying power checks, duplicate protection, projected exposure, dry-run behavior, and manual review policy belong outside broker plugins.

## Adapter Boundary

Broker adapters may:

- build broker-specific order payloads
- submit broker-specific orders when instructed
- normalize broker responses
- expose broker read snapshots
- manage broker lifecycle mechanics

Broker adapters must not:

- authorize execution
- bypass strategy or risk policy
- own retry policy
- own remediation policy
- own manual-review policy
- decide whether unresolved reconciliation permits future execution

Native broker mechanics such as sockets, callbacks, request IDs, order IDs, and native payload shapes stay inside broker infrastructure.

## Use-Case Boundary

Execution use cases coordinate the higher-level workflow:

- accepted trade intent
- risk and duplicate checks
- broker state reconciliation
- order preparation
- submit result handling
- uncertain-submit reconciliation
- reporting and event logging
- manual-review outcomes

Use cases may depend on broker adapter protocols, but broker adapters must not depend on use-case policy.

## Runtime Visibility

Runtime visibility remains a separate observability control plane. It must not authorize execution, route orders, or become an execution dependency.

## Activation

Initial execution activation must remain paper-only and isolated.

Fake-broker and use-case tests should precede any IBKR integration. IBKR execution must not be wired into production broker selection until the use-case boundary, paper-only validation, and architecture review are complete.
