# D11.60 IBKR VPS Proof Safe Preflight Or LOCAL_MAC Criteria Revision

## Scope and Decision

D11.60 is a source-controlled decision artifact for the remaining IBKR primary
market-data eligibility blocker:
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.
It reviews existing source-controlled D11 criteria and evidence only. It does
not run endpoint inspection, market testing, VPS proof, protocol probes, broker
endpoint traffic, package capture, replay, scoring, candidate generation,
strategy, risk, execution, account/order/execution work, or live trading. It
does not connect to IBKR/TWS/Gateway, import broker API code, or mutate
runtime, timer, service, systemd, TWS, Gateway, openclaw-gateway, or VPS state.

Decision: fail closed. Existing source-controlled evidence identifies no
validated VPS-accessible proof target, and existing source-controlled criteria
do not support retiring or narrowing the VPS proof requirement for the selected
`LOCAL_MAC_ONLY` architecture.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_VPS_PROOF_SAFE_PREFLIGHT_OR_LOCAL_MAC_CRITERIA_REVISION` |
| `source_commit` | `002602313f022ea2581cd7d30d3453aca9b4f50f` |
| `d11_59_vps_validation` | `79 passed in 2.77s` |
| `d11_59_route` | `REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED` |
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
| `vps_proof_safe_target_status` | `NO_VALIDATED_TARGET` |
| `local_mac_criteria_revision_status` | `NOT_SUPPORTED` |
| `d11_60_decision` | `BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION` |
| `next_permissible_gate` | `D11.61_SOURCE_CONTROLLED_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE` |

## Source-Controlled Rule

The exact source-controlled rule requiring the remaining proof is
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`.

D11.60 does not modify production provider selection code. No existing
source-controlled D11 rule explicitly requires a code change in this gate.

## VPS Target Review

D11.60 finds no source-controlled, validated, VPS-accessible endpoint that can
support a future VPS proof without guessing.

Rejected proof targets:

- VPS `127.0.0.1:7497`: rejected unless separate source-controlled evidence
  later shows `127.0.0.1:7497` is listening in the VPS process context and a
  later gate separately authorizes that target.
- VPS `127.0.0.1:18789` and `127.0.0.1:18791`: not approved market-data
  endpoints. Existing D11.45 through D11.49 evidence classifies them as
  liveness/provenance-only paths without approved bridge/protocol semantics or
  market-data proof authority.

Required localhost facts:

- `127.0.0.1` is process-context local.
- LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`.
- The prior VPS proof failed because VPS `127.0.0.1:7497` was not listening.
- The prior failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
  `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue and
  not a proven IB Gateway issue.

A future VPS proof cannot target `127.0.0.1:7497` unless that endpoint is
observed listening in the VPS process context and separately authorized.

## LOCAL_MAC Criteria Revision Review

D11.60 finds no source-controlled basis to retire or narrow the VPS proof
requirement for the selected `LOCAL_MAC_ONLY` architecture.

D11.57 accepted Mac-local historical diagnostic evidence:

- `mac_local_historical_diagnostic_evidence=ACCEPTED`
- `all_symbols_d11_countable=true`
- `all_symbols_freshness_classification=clean`
- symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, and `MSTR`
- `selected_endpoint_context=LOCAL_MAC`
- `selected_endpoint_type=TWS_PAPER`
- `selected_mac_local_endpoint=127.0.0.1:7497`
- `endpoint_scope=LOCAL_MAC_ONLY`

That evidence remains accepted but does not supersede
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.

## Fail-Closed Decision

D11.60 chooses Option C:

```text
d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION
vps_proof_safe_target_status=NO_VALIDATED_TARGET
local_mac_criteria_revision_status=NOT_SUPPORTED
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
```

What is missing:

- no validated VPS-accessible endpoint suitable for market-data proof;
- no source-controlled approval for `18789` or `18791` as market-data proof
  endpoints;
- no source-controlled evidence that VPS `127.0.0.1:7497` is listening;
- no source-controlled basis to retire or narrow the VPS proof requirement for
  `LOCAL_MAC_ONLY` evidence.

The next permissible gate is:

```text
D11.61_SOURCE_CONTROLLED_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE
```

That future gate may only create source-controlled prerequisite evidence for a
validated VPS-accessible endpoint or a formal criteria revision. It must not
run proof, inspect endpoints, probe protocols, connect to broker endpoints,
mutate runtime, open Unit 12, or approve IBKR primary eligibility unless a
separate later gate explicitly authorizes that outcome.

## Authority Boundaries Preserved

D11.60 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.60 records no package capture, replay, scoring, candidate generation,
strategy, risk, execution, VPS proof run, VPS market test, protocol probe,
endpoint inspection, broker endpoint traffic, runtime mutation, timer mutation,
service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

D11.60 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.
