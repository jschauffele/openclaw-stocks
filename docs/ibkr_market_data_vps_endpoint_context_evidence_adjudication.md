# D11.45 VPS Endpoint/Context Evidence Adjudication

## Scope and Adjudication Status

D11.45 is the source-controlled adjudication for the D11.44 VPS operator
endpoint/context evidence. The evidence is identity/liveness only. It is not a
proof run, not protocol approval, not endpoint approval, not provider approval,
and not market-data proof evidence.

| Field | Value |
| --- | --- |
| `adjudication_status` | `OPERATOR_ENDPOINT_CONTEXT_EVIDENCE_ADJUDICATED` |
| `execution_context` | `VPS` |
| `source_commit_during_evidence_collection` | `7ca0f2904f4d3b7376df0d699d2bc6d6bd128a4b` |
| `source_commit_message` | `7ca0f29 Define D11 VPS endpoint context operator evidence` |
| `current_utc` | `2026-06-25 15:29:39 UTC` |
| `d11_44_vps_validation` | `64 passed in 1.27s` |
| `proof_rerun_authorized` | `false` |
| `endpoint_replacement_selected` | `false` |
| `provider_approval_evidence` | `false` |
| `market_data_proof_evidence` | `false` |
| `endpoint_liveness_confirmed_for_18789` | `true` |
| `endpoint_liveness_confirmed_for_18791` | `true` |
| `endpoint_liveness_confirmed_for_7497` | `false` |
| `openclaw_gateway_identity_confirmed` | `true` |
| `openclaw_gateway_protocol_approved` | `false` |
| `proof_endpoint_approved` | `false` |
| `root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH` |
| `authorized_endpoint_status` | `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `observed_gateway_context` | `OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791` |
| `desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE` |
| `broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

D11.44 is locked as committed, pushed, and VPS-validated. The D11.44 evidence
was collected on VPS without rerunning the proof, without changing endpoints,
without connecting to IBKR/TWS/Gateway, and without mutating gateway, runtime,
service, systemd, package capture, replay, scoring, candidate generation,
strategy, risk, execution, or trading behavior.

## Evidence Findings

The evidence captured these listening sockets:

| Endpoint | Status | Process | PID | FD | Classification |
| --- | --- | --- | --- | --- | --- |
| `127.0.0.1:18791` | `LISTEN` | `openclaw-gateway` | `846` | `29` | `OPEN_LIVENESS_ONLY` |
| `127.0.0.1:18789` | `LISTEN` | `openclaw-gateway` | `846` | `22` | `OPEN_LIVENESS_ONLY` |
| `[::1]:18789` | `LISTEN` | `openclaw-gateway` | `846` | `23` | `OPEN_LIVENESS_ONLY` |
| `127.0.0.1:7497` | `CLOSED_OR_REFUSED` | `none observed` | `none` | `none` | `NOT_LISTENING_ON_VPS` |

The evidence captured this process identity:

| Field | Value |
| --- | --- |
| `openclaw_gateway_pids` | `846` |
| `pid` | `846` |
| `command` | `openclaw-gateway` |
| `executable` | `/usr/bin/node` |
| `pwd` | `/root` |
| `cmdline` | `openclaw-gateway` |

The raw TCP liveness observations were:

```text
tcp_127_0_0_1_18789=OPEN_LIVENESS_ONLY
tcp_127_0_0_1_18791=OPEN_LIVENESS_ONLY
tcp_127_0_0_1_7497=CLOSED_OR_REFUSED
```

The open `18789` and `18791` endpoints are liveness observations only and are
not approved proof endpoints. D11.45 does not approve their protocol semantics,
does not approve them as an IBKR read-only market-data bridge, and does not
authorize switching a future proof command to either port.

## Source-Document Corrections

D11.45 records and preserves these source-document corrections:

- Correct the gateway label typo where the `18789` token was missing its final
  `9`; the corrected label is
  `OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`.
- Correct the repository search command typo where the `openclaw-gateway`
  token was missing its final `y`; the corrected command is
  `rg -n "openclaw-gateway|18789|18791|7497" .`.

The D11.44 evidence command line also exposed a future runbook formatting
defect:

```text
printf '--- pid=%s ---\n' "$pid"
-bash: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
```

The evidence still captured process identity. Future runbooks must avoid
leading dash `printf` format strings and use:

```text
printf '%s\n' "--- pid=$pid ---"
```

## Decision Boundary and Closed Authorities

D11.45 forbids treating open TCP liveness as approved protocol semantics,
approved bridge semantics, provider approval evidence, endpoint approval, or
market-data proof evidence. D11.45 forbids switching the proof command to
`18789` or `18791` without a later source-controlled bridge/protocol approval
that explains what the selected port is, what protocol it speaks, why it is the
approved read-only bridge, and why all authority boundaries remain closed.

D11.45 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.45 does not authorize account, position, margin, buying-power, portfolio,
order, balance, or execution queries; order placement, modification, routing,
cancellation, flattening, selling, or live trading; package capture; replay;
scoring; candidate generation; timer, service, systemd, or runtime mutation;
gateway start/stop/restart/reload, enable/disable, kill, or mutation; or
strategy, risk, or execution changes.

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

The next permissible gate is a source-controlled bridge/protocol decision or a
source-controlled decision to abandon VPS-local proof and return to Mac-local
IBKR evidence only. It is not proof rerun authorization.
