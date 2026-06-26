# D11.55 Mac-Local Endpoint Selection Adjudication

## Scope and Selection Status

D11.55 is a source-controlled Mac-local endpoint selection adjudication for
future preflight planning only. It selects the Mac-local endpoint established by
D11.54 listener evidence. It does not run endpoint inspection, does not run
market testing, does not connect to IBKR/TWS/Gateway, does not import broker
API code, does not send traffic to any endpoint, does not run account/order/
execution commands, does not approve IBKR as primary, does not complete D11, and
does not unblock Unit 12.

| Field | Value |
| --- | --- |
| `adjudication_status` | `MAC_LOCAL_ENDPOINT_SELECTION_ADJUDICATION` |
| `source_commit` | `90545de3c6fcfb8ebacea282a751ae3305b78f26` |
| `d11_54_vps_validation` | `74 passed in 2.24s` |
| `selected_mac_local_endpoint` | `127.0.0.1:7497` |
| `selected_endpoint_context` | `LOCAL_MAC` |
| `selected_endpoint_type` | `TWS_PAPER` |
| `selected_endpoint_port` | `7497` |
| `selected_endpoint_basis` | `D11.54 observed Mac-local TWS paper listener evidence` |
| `endpoint_selection_authorized` | `true` |
| `mac_local_market_test_authorized` | `false` |
| `vps_market_test_authorized` | `false` |
| `proof_rerun_authorized` | `false` |
| `protocol_probe_authorized` | `false` |
| `endpoint_switch_authorized` | `false` |
| `broker_api_import_authorized` | `false` |
| `broker_connect_authorized` | `false` |
| `market_data_request_authorized` | `false` |
| `account_order_execution_authority` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.54 is locked as committed, pushed, and VPS-validated with
`74 passed in 2.24s`. It adjudicated
`observed_mac_local_tws_paper_listener=true`,
`observed_mac_local_tws_paper_port=7497`,
`observed_mac_local_tws_process=Trader Workstation JavaApplicationStub`, and
`candidate_mac_local_endpoint=127.0.0.1:7497`.

## Endpoint Selection

D11.54 observed Trader Workstation JavaApplicationStub listening on
`TCP *:7497`. Port `7497` matches the official IBKR paper TWS default
adjudicated in D11.52. D11.55 selects
`candidate_mac_local_endpoint=127.0.0.1:7497` as
`selected_mac_local_endpoint=127.0.0.1:7497`.

The selected endpoint is valid only for the `LOCAL_MAC` process context. This
selection does not validate VPS `127.0.0.1:7497`. The prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.55 authorizes endpoint selection only. It does not authorize Mac-local
market testing, broker API import/connect, market-data requests, account/order/
execution authority, VPS market testing, proof rerun, protocol probing, or
endpoint switching.

## Future Mac-Local Market-Test Preflight Requirements

Any later Mac-local market-test preflight must be separately source-controlled
and must include:

- Exact future date.
- Explicit regular-session window.
- Explicit diagnostic target at or after 7:00 AM Pacific / 10:00 AM Eastern.
- 6:55 AM Pacific readiness-check boundary only.
- Explicit expected source commit.
- Clean worktree requirement before and after.
- Explicit TWS/manual operator readiness boundary.
- Historical-market-data-only command.
- Explicit compact output handling.
- No account, position, margin, buying-power, portfolio, order, balance,
  execution, cleanup, flatten, sell, cancel, or live-trading authority.
- No package capture, replay, scoring, candidate generation, strategy, risk, or
  execution authority.

## Preserved Status and Closed Authorities

D11.55 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.55 forbids market-test authority, VPS proof authority, protocol-probe
authority, endpoint-switch authority, broker API import/connect, sending
traffic to broker or gateway ports, market-data requests, account/order/
execution authority, package capture, replay, scoring, candidate generation,
timer/service/systemd or runtime mutation, gateway mutation, strategy/risk/
execution authority, D11 completion authority, and Unit 12 opening authority.

Closed authority flags remain:

```text
vps_runtime=NOT_TOUCHED
timer_service=NOT_TOUCHED
package_capture=false
replay=false
scoring=false
candidate_generation=false
broker_api_authority=false
broker_api_import_authorized=false
broker_connect_authorized=false
market_data_request_authorized=false
account_query_authority=false
order_authority=false
execution_authority=false
account_order_execution_authority=false
cleanup_authority=false
flatten_authority=false
sell_authority=false
cancel_authority=false
live_trading_authority=false
endpoint_selection_authorized=true
mac_local_market_test_authorized=false
vps_market_test_authorized=false
vps_proof_authority=false
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
d11_completion_authority=false
unit_12_opening_authority=false
```

The next permissible gate is a separately source-controlled Mac-local
market-test preflight. D11.55 itself does not authorize the test.
