# D11.62 IBKR Prerequisite Path Selection

## Scope and Decision

D11.62 is a source-controlled path-selection gate for the two prerequisites
identified by D11.61:

- bounded VPS endpoint evidence; or
- formal LOCAL_MAC-only criteria revision.

It reviews source-controlled criteria and evidence only. It does not approve a
criteria revision, approve IBKR primary eligibility, run endpoint inspection,
run market testing, run VPS proof, connect to IBKR/TWS/Gateway, import broker
API code, run protocol probes, send broker endpoint traffic, mutate runtime,
timer, service, systemd, TWS, Gateway, openclaw-gateway, or VPS state, open
Unit 12, or authorize account/order/execution activity.

Decision: select the formal LOCAL_MAC criteria revision path. Source-controlled
evidence already contains accepted `LOCAL_MAC_ONLY` historical diagnostic
evidence, while the VPS endpoint evidence path has no validated VPS-accessible
IBKR market-data endpoint and would require resolving endpoint architecture
questions before deciding whether the current `LOCAL_MAC_ONLY` architecture is
sufficient.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_PREREQUISITE_PATH_SELECTION` |
| `source_commit` | `eb54ef6d8affb13ec8f6909208b0a8c1de729bde` |
| `d11_61_vps_validation` | `81 passed in 3.42s` |
| `d11_61_decision` | `DUAL_PREREQUISITE_REQUIRED` |
| `d11_60_decision` | `BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION` |
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
| `vps_endpoint_evidence_path` | `NOT_SELECTED` |
| `local_mac_criteria_revision_path` | `SELECTED` |
| `d11_62_decision` | `LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED` |
| `next_permissible_gate` | `D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION` |

## Source-Controlled Criteria Used

The active rule remains
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`.

D11.62 does not modify production provider-selection code. No existing
source-controlled D11 criteria require a production provider-selection code
change in this path-selection gate.

## Accepted Evidence

D11.57 accepted Mac-local IBKR historical diagnostic evidence:

- `mac_local_historical_diagnostic_evidence=ACCEPTED`
- `all_symbols_d11_countable=true`
- `all_symbols_freshness_classification=clean`
- all five symbols were clean/countable: `AAPL`, `MSFT`, `NVDA`, `TSLA`, and
  `MSTR`
- `selected_endpoint_context=LOCAL_MAC`
- `selected_endpoint_type=TWS_PAPER`
- `selected_mac_local_endpoint=127.0.0.1:7497`
- `endpoint_scope=LOCAL_MAC_ONLY`

This accepted evidence does not validate VPS `127.0.0.1:7497`.

## Unresolved VPS Evidence

Source-controlled evidence still records:

- no validated VPS-accessible IBKR market-data endpoint;
- VPS `127.0.0.1:7497` was not listening during the prior failed proof;
- `18789` and `18791` are not approved IBKR market-data endpoints unless a
  separate source-controlled criteria approval exists;
- no source-controlled proof that a VPS process can safely reach an approved
  broker market-data endpoint.

Required localhost facts:

- `127.0.0.1` is process-context local.
- LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`.
- Prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
  `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`.
- Prior VPS failure is not a proven TWS issue and not a proven IB Gateway
  issue.
- No future VPS proof may target `127.0.0.1:7497` unless that endpoint is
  observed listening in the VPS process context and separately authorized.
- No future proof may target `18789` or `18791` as market-data endpoints unless
  source-controlled evidence explicitly approves them.

## Path Selection Analysis

Path A, VPS endpoint evidence, is not selected. The current source-controlled
state does not support collecting bounded VPS endpoint evidence as the cleaner
next path because the only previously authorized VPS `127.0.0.1:7497` target
was not listening in the VPS process context, `18789` and `18791` are observed
only and not approved market-data endpoints, and there is no validated
VPS-accessible IBKR market-data endpoint. D11.62 must not rely on guessed
endpoints, invalid VPS `127.0.0.1:7497`, unapproved `18789`/`18791`
market-data use, runtime mutation, broker connection, protocol probe, or
market-data request.

Path B, LOCAL_MAC criteria revision, is selected. The selected endpoint
architecture is `LOCAL_MAC_ONLY`, accepted IBKR historical diagnostic evidence
already exists from `LOCAL_MAC`, and a formal criteria revision can evaluate
whether that evidence supersedes, narrows, or replaces the separate VPS proof
requirement without broker traffic, runtime mutation, account/order/execution
authority, or inventing a VPS endpoint. This path preserves fail-closed status
until a later gate explicitly approves any criteria revision.

Path C, blocked/no path selected, is not selected because Path B is
institutionally supportable as a source-controlled next gate.

## D11.63 Boundary

D11.63 is defined as a formal criteria revision gate:

```text
D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION
```

D11.63 must evaluate whether `LOCAL_MAC_ONLY` accepted historical diagnostic
evidence can supersede, narrow, or replace
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.

D11.63 must preserve no account/order/execution authority, preserve Unit 12 as
blocked unless separately opened, add focused boundary tests before any
approval, and must not run broker traffic, endpoint inspection, market testing,
VPS proof, protocol probing, or runtime mutation.

## Fail-Closed Boundary

D11.62 selects a path only; it does not approve the criteria revision.

```text
d11_62_decision=LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED
vps_endpoint_evidence_path=NOT_SELECTED
local_mac_criteria_revision_path=SELECTED
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
```

D11.62 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.62 records no package capture, replay, scoring, candidate generation,
strategy, risk, execution, VPS proof run, VPS market test, protocol probe,
endpoint inspection, broker endpoint traffic, runtime mutation, timer mutation,
service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

D11.62 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.
