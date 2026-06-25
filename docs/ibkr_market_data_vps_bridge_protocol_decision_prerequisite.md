# D11.46 VPS Bridge/Protocol Decision Prerequisite

## Scope and Gate Status

D11.46 is a source-controlled bridge/protocol decision prerequisite gate only.
It defines what evidence would be required before any later approval could
classify an `openclaw-gateway` port as an approved read-only IBKR market-data
bridge. It does not run the proof, connect to IBKR/TWS/Gateway, switch the
proof endpoint to `18789` or `18791`, mutate `openclaw-gateway`, or change
provider, D11, Unit 12, package-capture, runtime, strategy, risk, execution, or
trading status.

| Field | Value |
| --- | --- |
| `gate_status` | `BRIDGE_PROTOCOL_DECISION_PREREQUISITE_REQUIRED` |
| `current_validated_source_commit` | `73b3b22297ba82d61eb915351349eb758589724a` |
| `d11_45_vps_validation` | `65 passed in 0.23s` |
| `proof_rerun_authorized` | `false` |
| `proof_endpoint_approved` | `false` |
| `openclaw_gateway_protocol_approved` | `false` |
| `provider_approval_evidence` | `false` |
| `market_data_proof_evidence` | `false` |
| `endpoint_liveness_confirmed_for_18789` | `true` |
| `endpoint_liveness_confirmed_for_18791` | `true` |
| `endpoint_liveness_confirmed_for_7497` | `false` |
| `openclaw_gateway_identity_confirmed` | `true` |
| `openclaw_gateway_pid` | `846` |
| `openclaw_gateway_executable` | `/usr/bin/node` |
| `openclaw_gateway_pwd` | `/root` |
| `openclaw_gateway_cmdline` | `openclaw-gateway` |
| `port_18789_classification` | `OPEN_LIVENESS_ONLY` |
| `port_18791_classification` | `OPEN_LIVENESS_ONLY` |
| `port_7497_classification` | `CLOSED_OR_REFUSED` |
| `source_commit_during_d11_44_evidence` | `7ca0f2904f4d3b7376df0d699d2bc6d6bd128a4b` |
| `d11_44_evidence_timestamp_utc` | `2026-06-25 15:29:39 UTC` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.46 preserves the D11.45 adjudication: open TCP liveness on `18789` and
`18791` is not protocol approval, provider approval, endpoint approval, or
market-data proof evidence. `127.0.0.1:7497` remains closed/refused from the
VPS context. `openclaw-gateway` identity is confirmed only as a Node process at
`/usr/bin/node`, working directory `/root`, cmdline `openclaw-gateway`.

## Future Evidence Required Before Any Bridge Approval

Before any later gate can classify an `openclaw-gateway` port as an approved
read-only IBKR market-data bridge, the future evidence must be separately
source-controlled and must establish all of the following without mutating
gateway/runtime/service/systemd state:

1. The `openclaw-gateway` package/source provenance, including repository,
   installed package identity, version or commit, launch path, and owner.
2. The protocol exposed on `127.0.0.1:18789` and `127.0.0.1:18791`.
3. Whether either port exposes IBKR API, HTTP, WebSocket, RPC, proxy, tunnel,
   or other bridge semantics.
4. Whether the bridge can perform historical market-data read-only requests
   without account, position, margin, buying-power, portfolio, order, balance,
   execution, cleanup, flatten, sell, cancel, or live-trading authority.
5. The exact command boundary for any future protocol probe.
6. Separate source-controlled approval before executing any protocol probe.
7. A non-mutating, fail-closed protocol-probe design.
8. A clear negative path: if protocol semantics cannot be proven
   source-controlled, abandon VPS-local proof or create a separate tunnel
   prerequisite.

Any future protocol probe must be separately source-controlled before execution.
It must not query account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, or live-trading state. It
must not mutate gateway, runtime, timer, service, systemd, package capture,
replay, scoring, candidate generation, strategy, risk, execution, or trading
behavior.

## Decision Boundary and Closed Authorities

D11.46 does not approve `18789` or `18791` as proof endpoints and does not
authorize a proof rerun. D11.46 forbids treating liveness as bridge/protocol
approval and forbids switching the proof command to `18789` or `18791`.

D11.46 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.46 does not authorize account, position, margin, buying-power, portfolio,
order, balance, or execution queries; order placement, modification, routing,
cancellation, cleanup, flattening, selling, or live trading; package capture;
replay; scoring; candidate generation; timer, service, systemd, or runtime
mutation; gateway start/stop/restart/reload, enable/disable, kill, or mutation;
or strategy, risk, or execution changes.

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
d11_completion_authority=false
```

The next permissible gate is a source-controlled bridge/protocol evidence
packet or a source-controlled negative-path decision to abandon VPS-local proof
or create a separate tunnel prerequisite. It is not proof rerun authorization.
