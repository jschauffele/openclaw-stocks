# First Manual IBKR Read-Only Runtime Visibility Smoke Evidence

## Scope

This note documents the first successful manual localhost paper-only read-only IBKR runtime visibility smoke.

This evidence proves read-only runtime visibility only. It does not prove IBKR execution readiness.

## Command

```bash
./.venv-ibkr312/bin/python manual_ibkr_read_only_runtime_visibility_smoke.py --host 127.0.0.1 --port 7497 --client-id 9117 --symbol AAPL --timeout 5 --disconnect-timeout 2
```

## Runtime Visibility Summary

| Field | Value |
| --- | --- |
| `runtime_visibility_blocking` | `false` |
| `runtime_visibility_reason` | `runtime_visibility_clear` |
| `provider_name` | `IBKRReadOnlyRuntimeProvider` |
| `provider_status` | `enabled` |
| `broker_state` | `clean` |

## Connection Evidence

| Field | Value |
| --- | --- |
| `connection_completion_source` | `callback` |
| `connection_result.passed` | `true` |
| `connection_result.reason` | `connect_ready` |
| `next_valid_id` | `1` |

## Broker State Evidence

| Field | Value |
| --- | --- |
| `open_buy_order_count` | `0` |
| `open_buy_order_qty` | `0` |
| `position.found` | `false` |
| `position.qty` | `0` |
| `position.reason` | `no_position` |

## Shutdown Evidence

| Field | Value |
| --- | --- |
| `disconnect_result.passed` | `true` |
| `disconnect_result.reason` | `disconnect_complete` |
| `connect_state` | `disconnected` |
| `shutdown_state` | `complete` |
| `thread_state.thread_state` | `stopped` |

## Safety Boundary

The smoke used the dedicated manual read-only runtime visibility harness.

Confirmed boundaries:

- `main.py` was not used.
- `broker_factory.py` was not used.
- No submit behavior was used.
- No cancel behavior was used.
- No flatten behavior was used.
- No remediation behavior was used.
- No VPS was used.
- No runtime visibility enforcement was enabled.

## Interpretation

This successful smoke establishes that the guarded read-only IBKR runtime visibility path can connect to localhost paper TWS, receive `nextValidId`, read open-order and position state, classify the broker state as `clean`, and disconnect cleanly.

This result should remain evidence for read-only observability only. It must not be treated as approval to enable strategy-driven IBKR execution.

## Direct Mac Terminal Read-Only State Smoke Evidence

### Execution Context

This evidence was produced from `DIRECT_MAC_TERMINAL`. It must not be
transferred to `CODEX_LOCAL`, `VPS`, or `CODEX_VPS` without separate
context-specific evidence.

### Command

```bash
./.venv-ibkr312/bin/python manual_ibkr_read_only_runtime_visibility_smoke.py --host 127.0.0.1 --port 7497 --client-id 9117 --symbol AAPL --timeout 5 --disconnect-timeout 2
```

### Endpoint

| Field | Value |
| --- | --- |
| `execution_context` | `DIRECT_MAC_TERMINAL` |
| `host` | `127.0.0.1` |
| `port` | `7497` |
| `client_id` | `9117` |
| `symbol` | `AAPL` |

### Lifecycle Result

| Field | Value |
| --- | --- |
| `connection_result.passed` | `true` |
| `connection_result.reason` | `connect_ready` |
| `connection_result.message` | `next_valid_id` |
| `connection_completion_source` | `callback` |
| `next_valid_id` | `1` |

### Read-Only State Result

| Field | Value |
| --- | --- |
| `runtime_visibility_blocking` | `false` |
| `runtime_visibility_reason` | `runtime_visibility_clear` |
| `provider_name` | `IBKRReadOnlyRuntimeProvider` |
| `broker_state` | `clean` |

### Open-Order Snapshot

| Field | Value |
| --- | --- |
| `open_order_snapshot.passed` | `true` |
| `open_buy_order_count` | `0` |
| `open_buy_order_qty` | `0` |

### Position Snapshot

| Field | Value |
| --- | --- |
| `position_snapshot.found` | `false` |
| `position_snapshot.qty` | `0` |
| `position_snapshot.reason` | `no_position` |

### Disconnect And Thread Cleanup

| Field | Value |
| --- | --- |
| `disconnect_result.passed` | `true` |
| `disconnect_result.reason` | `disconnect_complete` |
| `shutdown_state` | `complete` |
| `thread_state` | `stopped` |

### Forbidden Behavior Absent

Confirmed absent:

- `main.py` execution
- VPS work
- scheduled IBKR runtime activation
- submit behavior
- reconciliation behavior
- order cancel behavior
- flatten behavior
- retry or resubmit behavior
- remediation behavior
- live trading

### Boundary

This evidence proves only direct-Mac-terminal read-only IBKR paper runtime
visibility. It does not approve submit, reconciliation, `main.py`, VPS work,
scheduled IBKR activation, broker routing, bridge or tunnel work, or live
trading.

Future IBKR read-only runtime visibility activation is governed by
`docs/runtime_visibility_architecture_decision.md`. That contract remains
observation-only and does not bypass the managed AAPL long `1` paper hold
state, authorize submit readiness, or approve cleanup, flatten, sell, cancel,
retry, resubmit, remediation, scheduled IBKR runtime, `broker_factory.py`,
`config.py`, `main.py`, systemd changes, VPS work, or live trading.

Any future read-only visibility dry run must also follow the operator contract
in `docs/runtime_visibility_architecture_decision.md`. The approving record
must name the execution context, exact environment surface, exact command, stop
conditions, expected report fields, evidence fields to capture, and rollback or
no-op posture before execution. This evidence file does not approve `.env`
changes, VPS work, systemd changes, broker/API/TWS access, `main.py`, runtime
activation, submit readiness, cleanup, flatten, sell, cancel, retry,
remediation, or live trading.
