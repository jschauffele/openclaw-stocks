# D11.51 Mac-Local IBKR Evidence-Review Prerequisite

## Scope and Prerequisite Status

D11.51 is a source-controlled Mac-local evidence-review prerequisite only. It
authorizes documentation/evidence review for the Mac-local route selected by
D11.50. It does not authorize market testing, VPS proof, TWS/Gateway connection
commands, broker API import/connect, proof rerun, protocol probing, endpoint
switching, account/order/execution access, IBKR primary approval, D11
completion, or Unit 12 unblocking.

| Field | Value |
| --- | --- |
| `prerequisite_status` | `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_PREREQUISITE` |
| `current_validated_source_commit` | `cf7e9bb0a62c1d6e94524b0f7597090fe80596c6` |
| `d11_50_vps_validation` | `70 passed in 0.21s` |
| `vps_bridge_path_closed` | `true` |
| `current_vps_endpoint_available_for_countable_proof` | `false` |
| `next_route` | `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY` |
| `mac_local_evidence_review_authorized` | `true` |
| `mac_local_market_test_authorized` | `false` |
| `vps_market_test_authorized` | `false` |
| `proof_rerun_authorized` | `false` |
| `protocol_probe_authorized` | `false` |
| `endpoint_switch_authorized` | `false` |
| `tws_gateway_connection_commands_authorized` | `false` |
| `broker_api_import_connect_authorized` | `false` |
| `account_order_execution_access_authorized` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.50 is locked as committed, pushed, and VPS-validated with
`70 passed in 0.21s`. Its routing decision remains controlling:
`POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`, `vps_bridge_path_closed=true`,
`current_vps_endpoint_available_for_countable_proof=false`,
`next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`,
`mac_local_market_test_authorized=false`,
`vps_market_test_authorized=false`, `proof_rerun_authorized=false`,
`protocol_probe_authorized=false`, and `endpoint_switch_authorized=false`.

The VPS bridge/protocol path remains closed. No current VPS endpoint can be used
for D11 countable market-data proof. The only active next route is Mac-local
IBKR evidence review.

D11.51 does not authorize TWS/Gateway connection commands. It does not authorize
broker API import/connect. It does not authorize proof rerun. It does not
authorize account/order/execution access.

## Future Mac-Local Market-Test Preflight Requirements

D11.51 does not authorize Mac-local market testing yet. Any future Mac-local
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

D11.51 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.51 forbids market-test authority, VPS proof authority, protocol-probe
authority, endpoint-switch authority, account/order/execution authority,
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
broker_api_import_connect_authorized=false
account_query_authority=false
order_authority=false
execution_authority=false
cleanup_authority=false
flatten_authority=false
sell_authority=false
cancel_authority=false
live_trading_authority=false
mac_local_evidence_review_authorized=true
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
market-test preflight decision. Until that exists, the active route remains
Mac-local IBKR evidence review only.
