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

The successful AAPL BUY left the paper account with expected AAPL long `1`
state. Future IBKR submit gates must account for this managed non-flat state
before any further submit smoke is approved.

## Post-Submit Managed Non-Flat State

The current `DIRECT_MAC_TERMINAL` read-only IBKR Paper observation at commit
`1eaad94` confirms that the successful submit smoke still leaves AAPL long `1`
as a managed non-flat paper state.

| Field | Value |
| --- | --- |
| `symbol` | `AAPL` |
| `open_buy_order_count` | `0` |
| `open_buy_order_qty` | `0` |
| `position.found` | `true` |
| `position.qty` | `1` |
| `position.side` | `long` |
| `broker_state` | `non_flat_position` |
| `runtime_visibility_blocking` | `true` |
| `runtime_visibility_reason` | `IBKRReadOnlyRuntimeProvider:broker_state_non_flat_position` |
| `connection_result.passed` | `true` |
| `disconnect_result.passed` | `true` |
| `shutdown_state` | `complete` |
| `thread_state` | `stopped` |

Classification: PASS / EXPECTED MANAGED BLOCKING STATE.

This managed state is intentionally blocking for future IBKR submit smokes
until an explicit hold, cleanup, or flatten decision is recorded. OpenClaw must
not automatically cancel, flatten, sell, retry, resubmit, or remediate this
paper position. No submit, cancel, flatten, sell, cleanup, broker remediation,
`main.py`, VPS, or scheduled IBKR runtime occurred during this read-only
observation.

## Managed Paper Hold Decision

Institutional decision: HOLD AAPL long `1` as managed IBKR Paper state for now.

This hold decision records the current next-state for the expected non-flat
paper position left by the successful submit smoke. Open AAPL buy orders remain
`0`, runtime visibility blocks future submit smoke because
`broker_state=non_flat_position`, Alpaca scheduled baseline is active and
settled, IBKR scheduled runtime is not active, and no live trading is approved.

Do not flatten, sell, cancel, retry, resubmit, or remediate this managed paper
position. Future IBKR submit smoke remains blocked until this hold state is
intentionally changed through a separate explicit cleanup or flatten gate.

This is not approval for live trading, scheduled IBKR runtime, cleanup,
flatten, sell, cancel, retry, resubmit, broker remediation, or another IBKR
submit smoke.

## Managed Paper State And Smoke-State Guard

This guard controls any future work after the successful paper submit smoke
left AAPL long `1`.

AAPL long `1` is a managed non-flat IBKR Paper hold state. It is not clean
readiness. It blocks future submit-smoke precondition approval unless the state
is separately resolved or explicitly governed by an operator-approved
disposition gate.

Stale local smoke-state files, including `.local/ibkr_smoke_last_state.json`
and archived smoke states, must not be archived, deleted, or treated as cleaned
as a shortcut while current broker truth is non-flat. Local smoke state must be
reconciled against current read-only broker truth. `--cleanup-stale-state-only`
must not be used to bypass a non-flat broker state; it is valid only when
current read-only `broker_state` is clean and the active lane explicitly
approves stale-state handling.

Any future state review must start read-only. `DIRECT_MAC_TERMINAL` is the
preferred context for local TWS Paper visibility unless another context has
been explicitly proven. Read-only visibility is evidence only and cannot
approve submit, cleanup, flatten, sell, cancel, retry, remediation, broker
activation, scheduled runtime, or live trading.

Clean-readiness criteria before any future submit-smoke precondition approval:

- no open buy orders
- no unmanaged or unresolved positions
- current broker truth reports `broker_state=clean`
- local smoke-state file is absent, safe, or explicitly reconciled by a
  source-controlled workflow
- repo and evidence state are current and documented
- separate explicit operator approval names the submit-smoke lane

Stop conditions:

- current broker truth is non-flat and the active lane is not an explicit
  operator-approved disposition plan
- stale local smoke state conflicts with current broker truth
- any action path implies order construction, submit, cancel, flatten, sell,
  cleanup, retry, remediation, or position change
- execution context is unclear or unproven

Cleanup, flatten, sell, cancel, retry, remediation, submit smoke, `.env`
changes, scheduled runtime changes, broker activation, and live trading each
require separate explicit gates. This guard records no current approval for any
of those actions.

## Boundary

This evidence is scoped to the exact `DIRECT_MAC_TERMINAL` paper-submit run
above. It does not transfer to `CODEX_LOCAL`, `VPS`, or `CODEX_VPS` without
separate context-specific evidence.

This record does not approve production routing, scheduled execution,
`main.py`, `broker_factory.py`, live accounts, live ports, bridge or tunnel
work, or any remediation behavior.
