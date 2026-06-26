# D11.50 Post-VPS Negative-Path Routing Decision

## Scope and Routing Decision Status

D11.50 is a source-controlled routing decision only. It routes away from the
current VPS bridge/protocol path after D11.49 VPS validation confirmed that no
current VPS endpoint can be used for D11 countable market-data proof. It is
evidence/routing documentation, not proof execution, not market testing, not a
Mac-local market-test authorization, not VPS proof rerun authorization, not
protocol-probe authorization, not endpoint-switch authorization, not IBKR
primary approval, not D11 completion, and not Unit 12 unblocking.

| Field | Value |
| --- | --- |
| `routing_status` | `POST_VPS_NEGATIVE_PATH_ROUTING_DECISION` |
| `current_validated_source_commit` | `ce132ae4334f2e9c315fbfdd9133affc1f070be5` |
| `d11_49_vps_validation` | `69 passed in 1.75s` |
| `vps_bridge_path_closed` | `true` |
| `current_vps_endpoint_available_for_countable_proof` | `false` |
| `next_route` | `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY` |
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

D11.49 is locked as committed, pushed, and VPS-validated with
`69 passed in 1.75s`. Its result remains controlling:
`VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`,
`current_vps_bridge_path_approved=false`,
`current_18789_endpoint_approved=false`,
`current_18791_endpoint_approved=false`,
`current_7497_endpoint_available=false`,
`proof_rerun_authorized=false`, `protocol_probe_authorized=false`,
`endpoint_switch_authorized=false`, `bridge_protocol_approved=false`,
`provider_approval_evidence=false`, `market_data_proof_evidence=false`, and
`d11_completion_authority=false`.

## Routing Decision

The current VPS bridge/protocol path is closed. Ports `18789` and `18791` are
not approved endpoints. Port `7497` remains unavailable from the VPS proof
context. No current VPS endpoint can be used for D11 countable market-data
proof.

The next valid route is `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`. D11.50 does not
authorize a Mac-local market test yet, does not authorize a VPS market test,
does not authorize a proof rerun, does not authorize a protocol probe, and does
not authorize an endpoint switch.

Any future Mac-local market test requires a separately source-controlled
preflight gate before execution. That future preflight gate must include an
explicit date and session window, explicit TWS/manual operator readiness
boundary, explicit historical-market-data-only command, explicit compact output
handling, expected commit, clean worktree requirement, and no
account/order/execution authority.

## Preserved Status and Closed Authorities

D11.50 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.50 forbids account, position, margin, buying-power, portfolio, order,
balance, or execution queries; order placement, modification, routing,
cancellation, cleanup, flattening, selling, or live trading; package capture;
replay; scoring; candidate generation; timer, service, systemd, or runtime
mutation; gateway mutation; strategy, risk, or execution changes; proof rerun;
endpoint switch; protocol probe; or market-test authority.

Closed authority flags remain:

```text
vps_runtime=NOT_TOUCHED
timer_service=NOT_TOUCHED
package_capture=false
replay=false
scoring=false
candidate_generation=false
broker_api_authority=false
account_query_authority=false
order_authority=false
execution_authority=false
cleanup_authority=false
flatten_authority=false
sell_authority=false
cancel_authority=false
live_trading_authority=false
mac_local_market_test_authorized=false
vps_market_test_authorized=false
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
d11_completion_authority=false
```

The next permissible gate is a separately source-controlled Mac-local IBKR
evidence-review or preflight decision. It must remain documentation/preflight
only unless it explicitly authorizes a bounded historical-market-data-only
Mac-local command under the required session, operator-readiness, output,
commit, clean-worktree, and no-account/order/execution boundaries.
