# D11.43 VPS Endpoint/Context Correction Gate

## Scope and Gate Status

D11.43 is a source-controlled endpoint/context correction gate only. It records
the post-D11.42 validation state and defines the next allowed operator evidence
needed before any bounded VPS read-only freshness proof retry can be authorized.
It does not run the proof, connect to IBKR/TWS/Gateway, choose a replacement
endpoint, mutate `openclaw-gateway`, or change provider, D11, Unit 12,
package-capture, runtime, strategy, risk, execution, or trading status.

| Field | Value |
| --- | --- |
| `gate_status` | `ENDPOINT_CONTEXT_CORRECTION_REQUIRED` |
| `current_validated_source_commit` | `de2fcb8efbc9843333f004db45c75c603c744312` |
| `d11_42_vps_validation` | `62 passed in 1.47s` |
| `proof_rerun_authorized` | `false` |
| `endpoint_replacement_selected` | `false` |
| `root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH` |
| `authorized_endpoint_status` | `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `observed_gateway_context` | `OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791` |
| `desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE` |
| `broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE` |
| `prior_authorized_endpoint` | `127.0.0.1:7497` |
| `prior_authorized_endpoint_context` | `VPS process context` |
| `prior_authorized_endpoint_listener_observed` | `false` |
| `observed_openclaw_gateway_process` | `Node process` |
| `observed_openclaw_gateway_ports` | `127.0.0.1:18789; 127.0.0.1:18791` |
| `openclaw_gateway_systemd_service_found` | `false` |
| `loopback_doctrine` | `127.0.0.1 means loopback of the current process context` |
| `vps_or_codex_local_socket_valid_for_mac_local_tws` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.42 is locked as committed, pushed, and VPS-validated. Its classification
remains `PROOF_RUN_BUT_NON_COUNTABLE` with zero countable market-data evidence.
The VPS proof ran from the VPS at the D11.42 commit, targeted `127.0.0.1:7497`
from the VPS process context, and that endpoint refused connection. Later VPS
audit showed no listener on `127.0.0.1:7497`, while `openclaw-gateway` was
present as a Node process on `127.0.0.1:18789` and `127.0.0.1:18791`.

Existing source-controlled doctrine states `127.0.0.1` means loopback of the
current process context. Existing doctrine also states VPS and `CODEX_LOCAL`
IBKR socket paths are not valid for Mac-local TWS evidence without separate
execution-context proof.

## Decision Boundary

D11.43 must not choose a new endpoint blindly. It does not authorize changing
the proof command from `127.0.0.1:7497` to `127.0.0.1:18789` or
`127.0.0.1:18791`.

The next allowed operator evidence must decide among exactly these paths:

1. Use the actual `openclaw-gateway` exposed local port only if a separate
   source-controlled approval explains what `127.0.0.1:18789` and/or
   `127.0.0.1:18791` are, why that port is the approved read-only bridge, what
   protocol and read-only market-data contract it exposes, and why it preserves
   all closed authorities.
2. Create a separately source-controlled tunnel prerequisite only if the tunnel
   design names the endpoint, lifecycle owner, command boundary, security
   posture, read-only scope, proof evidence, stop conditions, and forbidden
   authority expansion.
3. Abandon the VPS-local proof path and return to Mac-local IBKR evidence only,
   preserving the doctrine that VPS and `CODEX_LOCAL` loopback sockets do not
   prove Mac-local TWS reachability.

Until one of those paths is source-controlled and validated, the VPS proof must
not be rerun. Endpoint/context correction must be reviewed before another
bounded VPS read-only freshness proof authorization can exist.

## Closed Authorities

D11.43 does not approve IBKR, complete D11, unblock Unit 12, open package
capture, or open trading authority. It does not authorize account, position,
margin, buying-power, portfolio, order, balance, or execution queries; order
placement, modification, routing, cancellation, flattening, selling, or live
trading; package capture; replay; scoring; candidate generation; timer,
service, systemd, or runtime mutation; gateway start/stop/restart/reload,
enable/disable, or mutation; or strategy, risk, or execution changes.

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

The next permissible gate is a source-controlled operator endpoint/context
evidence packet selecting one of the three allowed paths above. It is not proof
rerun authorization and not authority to mutate gateway, runtime, timer,
service, systemd, package capture, replay, scoring, candidate generation,
account/order queries, execution, or live trading.
