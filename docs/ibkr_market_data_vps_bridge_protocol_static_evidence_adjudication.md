# D11.48 VPS Bridge/Protocol Static Evidence Adjudication

## Scope and Adjudication Status

D11.48 is the source-controlled adjudication of D11.47 VPS static provenance
evidence. The evidence is static identity/provenance evidence only. It is not a
proof run, not protocol approval, not endpoint approval, not provider approval,
and not market-data proof evidence.

| Field | Value |
| --- | --- |
| `adjudication_status` | `STATIC_PROVENANCE_EVIDENCE_ADJUDICATED` |
| `static_evidence_file_path` | `/tmp/d11_47_static_evidence_20260625T202035Z.txt` |
| `static_evidence_file_existed` | `true` |
| `static_evidence_line_count` | `30022` |
| `static_evidence_byte_count` | `3132489` |
| `static_evidence_sha256` | `26c21cdf1a3af3e4e15e8e7e8e9c9c3f3ce24c806c97110ede6a1a9050b2676c` |
| `source_commit_after_evidence_collection` | `3592b3068fd6bce0296d28db6ddd579ae90e8574` |
| `source_commit_message` | `3592b30 Define D11 VPS bridge protocol static evidence` |
| `d11_47_vps_validation` | `67 passed in 1.67s` |
| `openclaw_gateway_command_v` | `empty` |
| `openclaw_gateway_binary` | `NOT_FOUND` |
| `openclaw_gateway_binary_on_path` | `false` |
| `npm_global_openclaw_package_observed` | `true` |
| `npm_global_openclaw_package` | `openclaw@2026.3.24` |
| `node_version` | `v24.13.0` |
| `npm_version` | `11.6.2` |
| `openclaw_gateway_service_found` | `false` |
| `repo_reference_search_too_broad` | `true` |
| `package_source_provenance_complete` | `false` |
| `protocol_semantics_proven` | `false` |
| `bridge_protocol_approved` | `false` |
| `proof_endpoint_approved` | `false` |
| `proof_rerun_authorized` | `false` |
| `provider_approval_evidence` | `false` |
| `market_data_proof_evidence` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.47 is locked as committed, pushed, and VPS-validated. Static evidence was
collected without rerunning the VPS proof, without protocol probing, without
traffic to `18789`, `18791`, or `7497`, without endpoint switch, and without
gateway/runtime/service/systemd mutation.

## Evidence Adjudication

The static evidence file existed at
`/tmp/d11_47_static_evidence_20260625T202035Z.txt` with `30022` lines,
`3132489` bytes, and SHA-256
`26c21cdf1a3af3e4e15e8e7e8e9c9c3f3ce24c806c97110ede6a1a9050b2676c`.
The source state remained `3592b3068fd6bce0296d28db6ddd579ae90e8574`
(`3592b30 Define D11 VPS bridge protocol static evidence`).

The evidence did not find an `openclaw-gateway` binary on PATH:
`openclaw_gateway_command_v` was empty and
`openclaw_gateway_binary=NOT_FOUND`. It did observe the npm global package
`openclaw@2026.3.24`, `node_version=v24.13.0`, and `npm_version=11.6.2`.
`openclaw-gateway.service` could not be found. The repository reference output
was too broad/noisy for protocol approval.

The evidence does not complete package/source provenance and does not prove
protocol semantics. It does not approve a bridge protocol, proof endpoint,
provider, or market-data proof.

## Decision Boundary and Closed Authorities

D11.48 does not approve `18789` or `18791` as proof endpoints. It does not
authorize proof rerun, protocol probing, endpoint switch, or
account/order/execution access. It forbids treating static package/source
identity, npm package observation, service absence, noisy repo references, or
open TCP liveness as approved protocol/bridge semantics.

D11.48 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.48 does not authorize account, position, margin, buying-power, portfolio,
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

The next permissible gate is a source-controlled negative-path decision or a
new source-controlled provenance/protocol plan that resolves the missing binary
and noisy-reference limitations without opening protocol probing, proof rerun,
endpoint switching, or operational authority.
