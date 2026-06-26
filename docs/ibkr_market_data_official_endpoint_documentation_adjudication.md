# D11.52 Official IBKR Endpoint Documentation Adjudication

## Scope and Adjudication Status

D11.52 is a source-controlled adjudication of official IBKR endpoint
documentation only. It records the documented TWS API transport and default
TWS/IB Gateway socket ports for future Mac-local evidence review. It does not
authorize endpoint selection, endpoint inspection, Mac-local market testing, VPS
market testing, VPS proof rerun, protocol probing, endpoint switching,
TWS/Gateway connection commands, broker API import/connect,
account/order/execution access, IBKR primary approval, D11 completion, or Unit
12 unblocking.

| Field | Value |
| --- | --- |
| `adjudication_status` | `OFFICIAL_IBKR_ENDPOINT_DOCUMENTATION_ADJUDICATION` |
| `current_validated_source_commit` | `79e5d354c1bba7b1b3b45d1b3ec8267c5a32e052` |
| `d11_51_vps_validation` | `71 passed in 2.36s` |
| `official_tws_api_transport` | `TCP_SOCKET` |
| `official_tws_live_default_port` | `7496` |
| `official_tws_paper_default_port` | `7497` |
| `official_gateway_live_default_port` | `4001` |
| `official_gateway_paper_default_port` | `4002` |
| `configured_port_must_match_client_port` | `true` |
| `mac_local_endpoint_selection_authorized` | `false` |
| `mac_local_endpoint_inspection_authorized` | `false` |
| `mac_local_market_test_authorized` | `false` |
| `vps_market_test_authorized` | `false` |
| `proof_rerun_authorized` | `false` |
| `protocol_probe_authorized` | `false` |
| `endpoint_switch_authorized` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.51 is locked as committed, pushed, and VPS-validated with
`71 passed in 2.36s`. Its result remains controlling:
`MAC_LOCAL_IBKR_EVIDENCE_REVIEW_PREREQUISITE`,
`next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`,
`mac_local_evidence_review_authorized=true`,
`mac_local_market_test_authorized=false`,
`vps_market_test_authorized=false`, `proof_rerun_authorized=false`,
`protocol_probe_authorized=false`, and `endpoint_switch_authorized=false`.

## Sources Reviewed

- `https://interactivebrokers.github.io/tws-api/initial_setup.html`
- `https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/`
- `https://ibkrcampus.com/campus/trading-lessons/accessing-the-tws-python-api-source-code/`

The official IBKR documentation states that the TWS API uses a TCP socket
connection to Trader Workstation or IB Gateway. Official documentation records
default TWS socket ports as `7496` for live TWS and `7497` for paper TWS.
Official IBKR Campus training records defaults as live TWS `7496`, live IB
Gateway `4001`, simulated/paper TWS `7497`, and simulated/paper IB Gateway
`4002`.

IBKR documentation also states that socket ports can be changed. Therefore the
endpoint is not guessed: the API client port and the configured TWS/Gateway
socket port must match before any later source-controlled preflight can choose a
Mac-local endpoint.

## Future Gate Requirements

D11.52 does not authorize endpoint inspection yet. Any future Mac-local
endpoint-inspection gate must be separately source-controlled and must include:

- Exact expected source commit.
- Clean worktree requirement.
- Explicit operator-readiness boundary.
- Exact non-mutating inspection commands only.
- No broker API import/connect.
- No market-data request.
- No account/order/execution authority.

D11.52 does not authorize Mac-local market testing yet. Any future Mac-local
market-test preflight must be separately source-controlled and must include:

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

D11.52 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.52 forbids endpoint selection, endpoint inspection, market-test authority,
VPS proof authority, protocol-probe authority, endpoint-switch authority,
TWS/Gateway connection commands, broker API import/connect,
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
broker_api_import_connect_authorized=false
account_query_authority=false
order_authority=false
execution_authority=false
cleanup_authority=false
flatten_authority=false
sell_authority=false
cancel_authority=false
live_trading_authority=false
mac_local_endpoint_selection_authorized=false
mac_local_endpoint_inspection_authorized=false
mac_local_market_test_authorized=false
vps_market_test_authorized=false
vps_proof_authority=false
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
tws_gateway_connection_commands_authorized=false
d11_completion_authority=false
unit_12_opening_authority=false
```

The next permissible gate is a separately source-controlled Mac-local
endpoint-inspection prerequisite or a Mac-local market-test preflight. Neither
exists in D11.52.
