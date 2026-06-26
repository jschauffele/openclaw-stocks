# D11.59 IBKR VPS Proof Requirement Route Adjudication

## Scope and Decision

D11.59 is a source-controlled route adjudication for the remaining IBKR primary
market-data eligibility blocker after D11.58 VPS validation. It reviews
existing source-controlled D11 criteria and evidence only. It does not run
endpoint inspection, market testing, VPS proof, protocol probes, broker
endpoint traffic, package capture, replay, scoring, candidate generation,
strategy, risk, execution, account/order/execution work, or live trading. It
does not connect to IBKR/TWS/Gateway, import broker API code, or mutate
runtime, timer, service, systemd, TWS, Gateway, openclaw-gateway, or VPS state.

Decision: the VPS proof requirement remains active, but a future proof cannot
reuse invalid VPS-local `127.0.0.1:7497` by assumption. The next route is a
future source-controlled safe preflight only.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_VPS_PROOF_REQUIREMENT_ROUTE_ADJUDICATION` |
| `source_commit` | `874544fb1b860bf753d788f20bf3f143b027ff11` |
| `d11_58_vps_validation` | `78 passed in 2.39s` |
| `d11_58_result` | `BLOCKED_CRITERIA_UNRESOLVED` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |
| `account_order_execution_authority` | `false` |
| `mac_local_historical_diagnostic_evidence` | `ACCEPTED` |
| `all_symbols_d11_countable` | `true` |
| `all_symbols_freshness_classification` | `clean` |
| `selected_endpoint_context` | `LOCAL_MAC` |
| `selected_endpoint_type` | `TWS_PAPER` |
| `selected_mac_local_endpoint` | `127.0.0.1:7497` |
| `endpoint_scope` | `LOCAL_MAC_ONLY` |
| `vps_127_0_0_1_7497_validated` | `false` |
| `prior_vps_failure` | `VPS_LOCALHOST_CONTEXT_MISMATCH / AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `vps_proof_requirement_route` | `REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED` |
| `next_permissible_gate` | `D11.60_SOURCE_CONTROLLED_VPS_PROOF_SAFE_PREFLIGHT_OR_FORMAL_LOCAL_MAC_CRITERIA_REVISION` |

## Source-Controlled Rule

The exact source-controlled rule requiring the remaining proof is
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`.

D11.58 confirmed this rule remains unresolved. D11.59 does not find an existing
source-controlled rule that retires or narrows the requirement for the selected
`LOCAL_MAC_ONLY` architecture. Therefore D11.59 does not approve IBKR primary
eligibility and does not supersede the old rule.

## Compatibility With Selected Endpoint Architecture

The selected endpoint architecture is:

- `selected_endpoint_context=LOCAL_MAC`
- `selected_endpoint_type=TWS_PAPER`
- `selected_mac_local_endpoint=127.0.0.1:7497`
- `endpoint_scope=LOCAL_MAC_ONLY`

This architecture is compatible with accepted Mac-local diagnostic evidence,
but it is not by itself compatible with a VPS proof target. The selected
endpoint is valid only in the Mac-local process context. It does not validate
VPS `127.0.0.1:7497`.

D11.57 accepted Mac-local historical diagnostic evidence:

- `mac_local_historical_diagnostic_evidence=ACCEPTED`
- `all_symbols_d11_countable=true`
- `all_symbols_freshness_classification=clean`
- symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, and `MSTR`

That evidence remains accepted, but it does not retire the separate VPS proof
criterion.

## VPS Localhost Mismatch

VPS `127.0.0.1:7497` must not be reused as a proof target because:

- `127.0.0.1` is process-context local;
- VPS `127.0.0.1:7497` was not listening;
- the previous VPS proof failed from the VPS process context;
- the failure is `VPS_LOCALHOST_CONTEXT_MISMATCH` /
  `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`;
- the failure remains `NOT_PROVEN_TWS_ISSUE` and
  `NOT_PROVEN_IB_GATEWAY_ISSUE`.

A future VPS proof cannot target `127.0.0.1:7497` unless that endpoint is
observed listening in the VPS process context and separately authorized by a
future source-controlled preflight.

## Next Route

The next permissible gate is:

```text
D11.60_SOURCE_CONTROLLED_VPS_PROOF_SAFE_PREFLIGHT_OR_FORMAL_LOCAL_MAC_CRITERIA_REVISION
```

That future gate may choose one of two source-controlled routes:

1. A safe VPS-proof preflight that identifies an explicitly validated
   VPS-accessible endpoint. The endpoint must not be guessed and must not be
   `127.0.0.1:7497` unless observed listening in the VPS process context and
   separately authorized.
2. A formal source-controlled criteria revision that retires or narrows VPS
   proof for a `LOCAL_MAC_ONLY` market-data architecture, with the exact old
   rule superseded and the supporting evidence stated.

D11.59 authorizes neither route to execute. It records only the route
adjudication and fail-closed next gate.

## Authority Boundaries Preserved

D11.59 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.59 records no package capture, replay, scoring, candidate generation,
strategy, risk, execution, VPS proof run, VPS market test, protocol probe,
endpoint inspection, broker endpoint traffic, runtime mutation, timer mutation,
service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

D11.59 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

Preserved statuses:

```text
IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED
D11_INSUFFICIENT
UNIT_12_BLOCKED
PACKAGE_CAPTURE=BLOCKED
VPS_RUNTIME=NOT_TOUCHED
```
