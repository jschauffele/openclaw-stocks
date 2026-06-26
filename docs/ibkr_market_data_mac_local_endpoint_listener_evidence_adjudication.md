# D11.54 Mac-Local Endpoint Listener Evidence Adjudication

## Scope and Adjudication Status

D11.54 is a source-controlled adjudication of operator Mac-local endpoint
listener evidence only. It records the compact local-listener inspection result
authorized by D11.53. It does not run endpoint inspection, does not run market
testing, does not connect to IBKR/TWS/Gateway, does not import broker API code,
does not send traffic to any endpoint, does not select or switch endpoints,
does not approve IBKR as primary, does not complete D11, and does not unblock
Unit 12.

| Field | Value |
| --- | --- |
| `adjudication_status` | `MAC_LOCAL_ENDPOINT_LISTENER_EVIDENCE_ADJUDICATION` |
| `source_commit` | `62ce269f9105f38f6ac9bde69e4263a8a282491c` |
| `source_commit_message` | `62ce269 Authorize D11 Mac-local endpoint inspection` |
| `d11_53_vps_validation` | `73 passed in 2.28s` |
| `observed_mac_local_tws_paper_listener` | `true` |
| `observed_mac_local_tws_paper_port` | `7497` |
| `observed_mac_local_tws_process` | `Trader Workstation JavaApplicationStub` |
| `observed_mac_local_tws_live_listener` | `false` |
| `observed_mac_local_gateway_live_listener` | `false` |
| `observed_mac_local_gateway_paper_listener` | `false` |
| `candidate_mac_local_endpoint` | `127.0.0.1:7497` |
| `endpoint_selection_authorized` | `false` |
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

D11.53 is locked as committed, pushed, and VPS-validated with
`73 passed in 2.28s`. It authorized only
`LOCAL_LISTENER_INSPECTION_ONLY`; broker API import, broker connect,
market-data requests, account/order/execution authority, endpoint selection,
Mac-local market testing, VPS market testing, proof rerun, protocol probing, and
endpoint switching remained unauthorized.

## Operator Listener Evidence

The operator listener command was local-listener inspection only. The source
state during inspection was `62ce269f9105f38f6ac9bde69e4263a8a282491c`
(`62ce269 Authorize D11 Mac-local endpoint inspection`).

The compact filtered listener output showed:

```text
COMMAND=JavaAppli
PID=13194
USER=openclawcontrol
TCP *:7497 (LISTEN)
```

Process identity evidence showed:

```text
/Users/openclawcontrol/Applications/Trader Workstation/Trader Workstation.app/Contents/MacOS/JavaApplicationStub
```

No listener was shown for official IBKR ports `7496`, `4001`, or `4002` in the
compact filtered listener output.

## Endpoint Context Adjudication

Port `7497` matches the official IBKR paper TWS default adjudicated in D11.52.
The observed process path identifies Trader Workstation JavaApplicationStub.
This resolves the prior endpoint ambiguity for Mac-local context only.

This evidence does not retroactively make the VPS `127.0.0.1:7497` endpoint
valid. `127.0.0.1` on VPS and `127.0.0.1` on Mac are different process
contexts. The prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.54 records `candidate_mac_local_endpoint=127.0.0.1:7497`, but
`endpoint_selection_authorized=false`. Mac-local market testing remains
unauthorized. Broker API import/connect remains unauthorized. Market-data
requests remain unauthorized. Account/order/execution authority remains false.

Any future endpoint selection must be separately source-controlled after this
local listener evidence is reviewed.

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

D11.54 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.54 forbids endpoint selection, market-test authority, VPS proof authority,
protocol-probe authority, endpoint-switch authority, broker API import/connect,
sending traffic to broker or gateway ports, market-data requests,
account/order/execution authority, package capture, replay, scoring, candidate
generation, timer/service/systemd or runtime mutation, gateway mutation,
strategy/risk/execution authority, D11 completion authority, and Unit 12
opening authority.

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
endpoint_selection_authorized=false
mac_local_market_test_authorized=false
vps_market_test_authorized=false
vps_proof_authority=false
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
d11_completion_authority=false
unit_12_opening_authority=false
```

The next permissible gate is a separately source-controlled Mac-local endpoint
selection decision or Mac-local market-test preflight. Neither is authorized by
D11.54.
