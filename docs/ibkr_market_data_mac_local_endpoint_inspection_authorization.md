# D11.53 Mac-Local Endpoint Inspection Authorization

## Scope and Authorization Status

D11.53 is a source-controlled Mac-local endpoint inspection authorization only.
It authorizes compact local listener inspection so the operator can determine
which official IBKR socket port is actually listening locally. It does not
authorize endpoint selection, Mac-local market testing, VPS market testing, VPS
proof rerun, protocol probing, endpoint switching, broker API import/connect,
market-data requests, account/order/execution access, IBKR primary approval,
D11 completion, or Unit 12 unblocking.

| Field | Value |
| --- | --- |
| `authorization_status` | `MAC_LOCAL_ENDPOINT_INSPECTION_AUTHORIZATION` |
| `current_validated_source_commit` | `6f50a0d1a795eed2ec69559c9b6ba61ed8875b18` |
| `d11_52_vps_validation` | `72 passed in 1.76s` |
| `mac_local_endpoint_inspection_authorized` | `true` |
| `mac_local_endpoint_selection_authorized` | `false` |
| `mac_local_market_test_authorized` | `false` |
| `vps_market_test_authorized` | `false` |
| `proof_rerun_authorized` | `false` |
| `protocol_probe_authorized` | `false` |
| `endpoint_switch_authorized` | `false` |
| `official_tws_live_default_port` | `7496` |
| `official_tws_paper_default_port` | `7497` |
| `official_gateway_live_default_port` | `4001` |
| `official_gateway_paper_default_port` | `4002` |
| `configured_port_must_match_client_port` | `true` |
| `allowed_inspection_mode` | `LOCAL_LISTENER_INSPECTION_ONLY` |
| `broker_api_import_authorized` | `false` |
| `broker_connect_authorized` | `false` |
| `market_data_request_authorized` | `false` |
| `account_order_execution_authority` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.52 is locked as committed, pushed, and VPS-validated with
`72 passed in 1.76s`. It adjudicated official IBKR endpoints as:
`official_tws_api_transport=TCP_SOCKET`,
`official_tws_live_default_port=7496`, `official_tws_paper_default_port=7497`,
`official_gateway_live_default_port=4001`,
`official_gateway_paper_default_port=4002`, and
`configured_port_must_match_client_port=true`.

The endpoint is not guessed. It must be observed locally and later matched to
configured TWS/Gateway socket settings before any separate source-controlled
endpoint selection or market-test preflight can exist.

## Authorized Inspection Boundary

D11.53 authorizes only `LOCAL_LISTENER_INSPECTION_ONLY`. The future operator
inspection command must be compact and may inspect only local listening sockets
and process identity for these official IBKR ports:

- `7496`
- `7497`
- `4001`
- `4002`

D11.53 does not authorize broker API import/connect, sending traffic to any
endpoint, `nc`, `curl`, `telnet`, `/dev/tcp`, Python socket connect, broker API
connect, protocol probes, market-data requests, endpoint selection, endpoint
switching, Mac-local market testing, VPS market testing, or proof rerun.

Any later endpoint selection must be separately source-controlled after local
listener evidence is reviewed.

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

D11.53 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.53 forbids endpoint selection, market-test authority, VPS proof authority,
protocol-probe authority, endpoint-switch authority, broker API import/connect,
sending traffic to broker or gateway ports, account/order/execution authority,
package capture, replay, scoring, candidate generation, timer/service/systemd
or runtime mutation, gateway mutation, strategy/risk/execution authority, D11
completion authority, and Unit 12 opening authority.

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
mac_local_endpoint_inspection_authorized=true
mac_local_endpoint_selection_authorized=false
mac_local_market_test_authorized=false
vps_market_test_authorized=false
vps_proof_authority=false
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
d11_completion_authority=false
unit_12_opening_authority=false
```

The next permissible gate is source-controlled adjudication of the future
operator local-listener evidence. D11.53 itself does not collect that evidence.
