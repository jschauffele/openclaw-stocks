# D11.44 VPS Endpoint/Context Operator Evidence Packet

## Scope and Evidence Status

D11.44 is a source-controlled operator endpoint/context evidence packet only.
It defines the exact future read-only operator evidence needed to decide among
the D11.43 endpoint/context paths. It does not run the proof, connect to
IBKR/TWS/Gateway, choose a replacement endpoint, authorize proof rerun, mutate
`openclaw-gateway`, or change provider, D11, Unit 12, package-capture, runtime,
strategy, risk, execution, or trading status.

| Field | Value |
| --- | --- |
| `evidence_packet_status` | `OPERATOR_ENDPOINT_CONTEXT_EVIDENCE_DEFINED` |
| `current_validated_source_commit` | `3905f9ab4cf993103ff9aaa3c4619851ba00ae2d` |
| `d11_43_vps_validation` | `63 passed in 1.10s` |
| `proof_rerun_authorized` | `false` |
| `endpoint_replacement_selected` | `false` |
| `proof_command_allowed` | `false` |
| `ibkr_tws_gateway_connection_allowed` | `false` |
| `account_order_execution_access_allowed` | `false` |
| `gateway_mutation_allowed` | `false` |
| `root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH` |
| `authorized_endpoint_status` | `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `observed_gateway_context` | `OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791` |
| `desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE` |
| `broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE` |
| `prior_failed_vps_endpoint` | `127.0.0.1:7497` |
| `observed_openclaw_gateway_ports` | `127.0.0.1:18789; 127.0.0.1:18791` |
| `openclaw_gateway_ports_approved_as_proof_endpoints` | `false` |
| `endpoint_liveness_is_provider_approval_evidence` | `false` |
| `open_tcp_port_is_approved_read_only_ibkr_market_data_bridge` | `false` |
| `execution_context_for_future_evidence` | `VPS` |
| `future_evidence_is_read_only_process_port_identity_only` | `true` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.44 preserves the D11.42/D11.43 corrected labels and audit facts. The proof
ran from VPS, targeted `127.0.0.1:7497` from the VPS process context, and that
endpoint refused connection. No listener was observed on `127.0.0.1:7497`.
`openclaw-gateway` was present as a Node process and was observed listening on
`127.0.0.1:18789` and `127.0.0.1:18791`; those ports are observed only and are
not approved proof endpoints.

Existing doctrine states `127.0.0.1` means loopback of the current process
context and that VPS and `CODEX_LOCAL` IBKR socket paths are not valid for
Mac-local TWS evidence without separate execution-context proof.

## Future Read-Only Operator Evidence Commands

The future evidence collection context must be `VPS`. The evidence collection
must not run the proof command, connect to IBKR/TWS/Gateway, query account,
order, or execution state, or mutate `openclaw-gateway`, runtime, timer,
service, systemd, package capture, replay, scoring, candidate generation,
strategy, risk, execution, or trading behavior.

The operator evidence packet must capture the current source commit expected
before evidence collection and these read-only commands:

```text
git status --short
git rev-parse HEAD
git log -1 --oneline
ss -ltnp | grep -E '(:18789|:18791|:7497)'
ps -fp <openclaw_gateway_pid>
readlink -f /proc/<openclaw_gateway_pid>/exe
pwdx <openclaw_gateway_pid>
tr '\0' ' ' < /proc/<openclaw_gateway_pid>/cmdline
rg -n "openclaw-gateway|18789|18791|7497" .
```

If raw TCP checks are included later, they must be classified as endpoint
liveness only. Endpoint liveness is not protocol approval, provider approval,
or market-data proof evidence. An open TCP port must not be treated as proof
that the port is an approved read-only IBKR market-data bridge.

## Decision Boundary

D11.44 must not choose a new endpoint. It must not authorize changing a future
proof command to `127.0.0.1:18789` or `127.0.0.1:18791` until a later
source-controlled approval identifies the protocol and bridge semantics,
explains why the selected port is the approved read-only bridge, and proves the
bridge preserves all closed authorities.

The future operator evidence must decide among exactly these paths:

1. Approved `openclaw-gateway` bridge path, only after the port identity,
   protocol semantics, read-only market-data contract, and authority boundaries
   are source-controlled and approved.
2. Separately source-controlled tunnel prerequisite path, only after tunnel
   endpoint, lifecycle owner, command boundary, security posture, read-only
   scope, proof evidence, stop conditions, and forbidden authority expansion
   are source-controlled.
3. Abandon VPS-local proof and return to Mac-local IBKR evidence only,
   preserving the doctrine that VPS and `CODEX_LOCAL` loopback sockets do not
   prove Mac-local TWS reachability.

Until a later source-controlled approval selects one path, no endpoint
replacement is selected and no proof rerun is authorized.

## Closed Authorities

D11.44 does not approve IBKR, complete D11, unblock Unit 12, open package
capture, or open trading authority. It does not authorize account, position,
margin, buying-power, portfolio, order, balance, or execution queries; order
placement, modification, routing, cancellation, flattening, selling, or live
trading; package capture; replay; scoring; candidate generation; timer,
service, systemd, or runtime mutation; gateway start/stop/restart/reload,
enable/disable, kill, or mutation; or strategy, risk, or execution changes.

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

The next permissible gate is a source-controlled adjudication of the operator
endpoint/context evidence. It is not proof rerun authorization and not
authority to mutate gateway, runtime, timer, service, systemd, package capture,
replay, scoring, candidate generation, account/order queries, execution, or
live trading.
