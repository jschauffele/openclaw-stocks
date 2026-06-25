# D11.49 VPS Bridge/Protocol Negative-Path Decision

## Scope and Decision Status

D11.49 is a source-controlled negative-path decision only. It closes the current
VPS bridge/protocol path for D11 countable market-data proof based on the D11.48
static provenance adjudication. It is not a new test plan, not proof rerun
authorization, not protocol-probe authorization, not endpoint-switch
authorization, not provider approval, and not D11 completion.

| Field | Value |
| --- | --- |
| `decision_status` | `VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION` |
| `current_validated_source_commit` | `3c49b5cdfcb1e135fcad10c4af7a8af9ce00ab32` |
| `d11_48_vps_validation` | `68 passed in 1.85s` |
| `current_vps_bridge_path_approved` | `false` |
| `current_18789_endpoint_approved` | `false` |
| `current_18791_endpoint_approved` | `false` |
| `current_7497_endpoint_available` | `false` |
| `proof_rerun_authorized` | `false` |
| `protocol_probe_authorized` | `false` |
| `endpoint_switch_authorized` | `false` |
| `bridge_protocol_approved` | `false` |
| `provider_approval_evidence` | `false` |
| `market_data_proof_evidence` | `false` |
| `d11_completion_authority` | `false` |
| `openclaw_gateway_binary_on_path` | `false` |
| `npm_global_openclaw_package_observed` | `true` |
| `openclaw_gateway_service_found` | `false` |
| `package_source_provenance_complete` | `false` |
| `repo_reference_search_too_broad` | `true` |
| `protocol_semantics_proven` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.48 is locked as committed, pushed, and VPS-validated with
`68 passed in 1.85s`. Its negative evidence remains controlling:
`openclaw_gateway_binary_on_path=false`,
`npm_global_openclaw_package_observed=true`,
`openclaw_gateway_service_found=false`,
`package_source_provenance_complete=false`,
`repo_reference_search_too_broad=true`, and
`protocol_semantics_proven=false`.

## Negative-Path Decision

The current VPS bridge/protocol path is not approved for market-data proof.
Ports `18789` and `18791` remain liveness-only/non-approved endpoints. Port
`7497` remains unavailable from the VPS proof context. No current VPS endpoint
can be used for D11 countable market-data proof.

This decision closes the immediate current path to proof rerun. It does not
create a replacement endpoint, does not authorize a proof rerun, does not
authorize a protocol probe, and does not authorize endpoint switching.

Any future bridge revival requires a separate source-controlled plan before any
traffic is sent. That future plan must include exact binary/source provenance,
exact protocol semantics, an explicit non-mutating probe boundary, explicit
operator-output compression, and separate authorization before any traffic to
`18789`, `18791`, `7497`, or any replacement endpoint.

## Preserved Status and Closed Authorities

D11.49 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.49 forbids account, position, margin, buying-power, portfolio, order,
balance, or execution queries; order placement, modification, routing,
cancellation, cleanup, flattening, selling, or live trading; package capture;
replay; scoring; candidate generation; timer, service, systemd, or runtime
mutation; gateway mutation; strategy, risk, or execution changes; proof rerun;
endpoint switch; or protocol-probe authority.

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
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
d11_completion_authority=false
```

The next permissible gate is either abandonment of the current VPS bridge path
for D11 countable proof or a separately source-controlled bridge revival plan
that satisfies the provenance, protocol, non-mutating probe, output-compression,
and pre-traffic authorization requirements above.
