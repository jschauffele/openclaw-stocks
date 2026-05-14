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
