# IBKR Paper Submit Smoke Evidence

## Scope

This note records a successful manual localhost paper-only IBKR submit smoke
from `DIRECT_MAC_TERMINAL`.

This is evidence for regular-session IBKR paper submit mechanics only. It does
not approve scheduled runtime activation, VPS execution, `main.py`, production
broker routing, live trading, retry, resubmit, cancel, flatten, or remediation
behavior.

## Successful Regular-Session Paper Submit

### Execution Context

| Field | Value |
| --- | --- |
| `commit` | `d2be842` |
| `execution_context` | `DIRECT_MAC_TERMINAL` |
| `harness` | `manual_ibkr_submit_reconciliation_smoke.py` |
| `host` | `127.0.0.1` |
| `port` | `7497` |
| `client_id` | `9116` |
| `symbol` | `AAPL` |
| `qty` | `1` |
| `order_type` | `market` |

### Command

```bash
./.venv-ibkr312/bin/python manual_ibkr_submit_reconciliation_smoke.py --host 127.0.0.1 --port 7497 --client-id 9116 --timeout 15 --symbol AAPL --qty 1 --order-type market --regular-session-confirmed
```

### Pre-Submit Evidence

| Field | Value |
| --- | --- |
| `last_run_state` | `None` |
| `connection_result.passed` | `true` |
| `connection_result.reason` | `connect_ready` |
| `connection_result.message` | `next_valid_id` |
| `next_valid_id` | `11` |
| `pre_submit_open_order_snapshot.passed` | `true` |
| `pre_submit_open_order_snapshot.open_buy_order_qty` | `0` |
| `pre_submit_open_order_snapshot.open_buy_order_count` | `0` |
| `pre_submit_open_order_snapshot.reason` | `open_buy_orders_loaded` |
| `pre_submit_position_snapshot.found` | `false` |
| `pre_submit_position_snapshot.qty` | `0` |
| `pre_submit_position_snapshot.reason` | `no_position` |
| `pre_submit_broker_state` | `clean` |
| `market_order_regular_session_confirmed` | `true` |

### Submit Evidence

| Field | Value |
| --- | --- |
| `order_ref` | `OPENCLAW_SMOKE_MARKET_20260529133232` |
| `submitted_at` | `20260529-13:32:32` |
| `allocated_order_id` | `11` |
| `raw_submit_result.order_status` | `submitted` |
| `raw_submit_result.broker_status` | `PreSubmitted` |
| `raw_submit_result.is_terminal` | `false` |

### Execution Evidence

| Field | Value |
| --- | --- |
| `execDetails.order_id` | `11` |
| `execDetails.client_id` | `9116` |
| `execDetails.perm_id` | `314160415` |
| `execDetails.symbol` | `AAPL` |
| `execDetails.side` | `BOT` |
| `execDetails.shares` | `1.0` |
| `execDetails.cumulative_qty` | `1.0` |
| `execDetails.avg_price` | `314.29` |
| `execDetails.price` | `314.29` |
| `execDetails.time` | `20260529  06:32:32` |

### Final Broker-State Evidence

| Field | Value |
| --- | --- |
| `final_open_order_snapshot.passed` | `true` |
| `final_open_order_snapshot.open_buy_order_qty` | `0` |
| `final_open_order_snapshot.open_buy_order_count` | `0` |
| `final_open_order_snapshot.reason` | `open_buy_orders_loaded` |
| `final_position_snapshot.found` | `true` |
| `final_position_snapshot.qty` | `1` |
| `final_position_snapshot.raw_qty` | `1.0` |
| `final_position_snapshot.side` | `long` |
| `final_position_snapshot.reason` | `position_found` |
| `final_broker_state` | `non_flat_position` |

### Reconciliation Evidence

| Field | Value |
| --- | --- |
| `submit_became_reconciliation_required` | `false` |
| `reconciliation_not_invoked` | `true` |

### Shutdown Evidence

| Field | Value |
| --- | --- |
| `disconnect_joined` | `true` |
| `disconnect_result.passed` | `true` |
| `disconnect_result.reason` | `disconnect_complete` |
| `connect_state` | `disconnected` |
| `shutdown_state` | `complete` |
| `thread_state` | `stopped` |

## Classification

- PASS for regular-session IBKR paper submit mechanics.
- EXPECTED_NON_FLAT_POSITION after successful BUY fill.
- No open-order residue observed.
- No reconciliation was invoked because submit did not become
  reconciliation-required.
- No scheduled runtime, no VPS, no `main.py`, and no live trading occurred.

## Boundary

This evidence is scoped to the exact `DIRECT_MAC_TERMINAL` paper-submit run
above. It does not transfer to `CODEX_LOCAL`, `VPS`, or `CODEX_VPS` without
separate context-specific evidence.

This record does not approve production routing, scheduled execution,
`main.py`, `broker_factory.py`, live accounts, live ports, bridge or tunnel
work, or any remediation behavior.
