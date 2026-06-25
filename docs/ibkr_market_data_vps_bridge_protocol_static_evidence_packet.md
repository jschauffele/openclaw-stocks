# D11.47 VPS Bridge/Protocol Static Evidence Packet

## Scope and Evidence Status

D11.47 is a source-controlled bridge/protocol static evidence-collection packet
only. It defines read-only static evidence needed to identify
`openclaw-gateway` package, source, and protocol provenance. It does not run the
proof, connect to IBKR/TWS/Gateway, switch the proof endpoint to `18789` or
`18791`, run a protocol probe, send traffic to `18789`, `18791`, or `7497`,
mutate `openclaw-gateway`, or change provider, D11, Unit 12, package-capture,
runtime, strategy, risk, execution, or trading status.

| Field | Value |
| --- | --- |
| `evidence_packet_status` | `BRIDGE_PROTOCOL_STATIC_EVIDENCE_DEFINED` |
| `current_validated_source_commit` | `2d68d0d3d5ca72be0fd39c751148bd4d1c392c9b` |
| `d11_46_vps_validation` | `66 passed in 1.89s` |
| `proof_rerun_authorized` | `false` |
| `proof_endpoint_approved` | `false` |
| `protocol_probe_authorized` | `false` |
| `openclaw_gateway_protocol_approved` | `false` |
| `provider_approval_evidence` | `false` |
| `market_data_proof_evidence` | `false` |
| `endpoint_liveness_confirmed_for_18789` | `true` |
| `endpoint_liveness_confirmed_for_18791` | `true` |
| `endpoint_liveness_confirmed_for_7497` | `false` |
| `port_18789_classification` | `OPEN_LIVENESS_ONLY` |
| `port_18791_classification` | `OPEN_LIVENESS_ONLY` |
| `port_7497_classification` | `CLOSED_OR_REFUSED` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.47 preserves D11.46: liveness on `18789` and `18791` is identity/liveness
only, `7497` is closed/refused, package/source identity is not protocol
approval, service identity is not protocol approval, and liveness is not
protocol approval.

## Future Read-Only Static Evidence Commands

The future evidence collection context must be `VPS`. The commands below are
read-only static identity/provenance commands only:

```text
git status --short
git rev-parse HEAD
git log -1 --oneline
which openclaw-gateway
command -v openclaw-gateway
readlink -f "$(command -v openclaw-gateway)"
file "$(command -v openclaw-gateway)"
ls -l "$(command -v openclaw-gateway)"
if command -v dpkg >/dev/null 2>&1; then dpkg -S "$(command -v openclaw-gateway)"; fi
if command -v npm >/dev/null 2>&1; then npm root -g; fi
if command -v npm >/dev/null 2>&1; then npm list -g --depth=0; fi
if command -v node >/dev/null 2>&1; then node --version; fi
if command -v npm >/dev/null 2>&1; then npm --version; fi
if command -v systemctl >/dev/null 2>&1; then systemctl status openclaw-gateway --no-pager; fi
rg -n "openclaw-gateway|18789|18791|7497|WebSocket|websocket|http|HTTP|rpc|RPC|proxy|tunnel|IBKR|market data|market-data" .
```

`systemctl status openclaw-gateway --no-pager`, if available, is
service-identity evidence only and not service mutation. The repository search
must be repo-only static search.

## Explicitly Forbidden Evidence Collection

D11.47 does not authorize protocol probing or traffic to `18789`, `18791`, or
`7497`. The future static evidence collection must not use:

```text
curl
nc
telnet
/dev/tcp
protocol handshake
broker API import or connect
```

D11.47 forbids treating package/source identity as protocol approval, service
identity as protocol approval, or liveness as protocol approval. It forbids
switching the proof command to `18789` or `18791`.

## Future Decision Boundary

Package/source provenance evidence is required before any protocol decision.
Protocol semantics evidence is required before any bridge approval. Separate
source-controlled protocol-probe approval is required before any traffic is
sent to `18789` or `18791`.

Any later protocol probe must be separately source-controlled, non-mutating,
fail-closed, and must preserve no account, position, margin, buying-power,
portfolio, order, balance, execution, cleanup, flatten, sell, cancel, or
live-trading queries; no gateway/runtime/service/systemd mutation; and no
package capture, replay, scoring, candidate generation, strategy, risk,
execution, or trading authority.

## Closed Authorities

D11.47 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.47 does not authorize account, position, margin, buying-power, portfolio,
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

The next permissible gate is source-controlled adjudication of static
package/source/provenance evidence or a source-controlled negative-path
decision. It is not proof rerun authorization and not protocol-probe
authorization.
