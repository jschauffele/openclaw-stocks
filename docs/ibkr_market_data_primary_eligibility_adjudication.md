# D11.58 IBKR Primary Market-Data Eligibility Adjudication

## Scope and Decision

D11.58 is a source-controlled IBKR primary market-data eligibility adjudication
after D11.57 VPS validation. It reviews existing source-controlled D11 criteria
and evidence only. It does not run endpoint inspection, market testing, VPS
proof, protocol probes, broker endpoint traffic, package capture, replay,
scoring, candidate generation, strategy, risk, execution, account/order/
execution work, or live trading. It does not connect to IBKR/TWS/Gateway and
does not mutate runtime, timer, service, systemd, TWS, Gateway, or VPS state.

Decision: fail closed. Existing source-controlled criteria do not clearly
support primary eligibility after D11.57 because the required separate VPS
read-only freshness proof remains unresolved and the accepted endpoint evidence
remains `LOCAL_MAC_ONLY`.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_PRIMARY_MARKET_DATA_ELIGIBILITY_ADJUDICATION` |
| `source_commit` | `4839f8ff3f09f746edcca3ab464a4771ae922f0d` |
| `d11_57_vps_validation` | `77 passed in 3.05s and 77 passed in 0.25s` |
| `mac_local_historical_diagnostic_evidence` | `ACCEPTED` |
| `all_symbols_d11_countable` | `true` |
| `all_symbols_freshness_classification` | `clean` |
| `selected_mac_local_endpoint` | `127.0.0.1:7497` |
| `selected_endpoint_context` | `LOCAL_MAC` |
| `selected_endpoint_type` | `TWS_PAPER` |
| `selected_endpoint_port` | `7497` |
| `endpoint_scope` | `LOCAL_MAC_ONLY` |
| `vps_127_0_0_1_7497_validated` | `false` |
| `prior_vps_failure` | `VPS_LOCALHOST_CONTEXT_MISMATCH / AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_primary_eligibility_adjudication` | `BLOCKED_CRITERIA_UNRESOLVED` |
| `d11_primary_candidate_status` | `candidate` |
| `d11_status` | `D11_INSUFFICIENT` |
| `account_order_execution_authority` | `false` |
| `package_capture` | `BLOCKED` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

## Source-Controlled Criteria Reviewed

D11.58 uses these existing source-controlled criteria and records:

- `market_data_provider_selection.py`:
  `D11_PRIMARY_PROVIDER_SELECTION_CRITERIA` includes
  `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.
- `market_data_provider_selection.py`: `candidate_can_count_for_d11` requires
  approved-primary status, `d11_primary_eligible=true`,
  `order_authority=false`, `execution_authority=false`, and
  `broker_coupled=false`.
- `docs/ibkr_market_data_repeatability_ledger_template.md`: the final
  provider-approval review must remain separate from D11 sufficiency, Unit 12,
  package inventory, candidate evidence, baseline-vs-candidate pairing,
  scoring, broker/API authority, order authority, and execution authority.
- D11.34 in `docs/replay_evaluation_implementation_prerequisite_map.md`:
  completed clean/countable repeatability evidence satisfied the D11.21
  repeatability requirement, but did not meet all primary-eligibility criteria
  because a separate VPS read-only freshness proof was not recorded.
- D11.56 preflight authorized a bounded future Mac-local historical
  market-data-only diagnostic and preserved no primary approval authority.
- D11.57 accepted Mac-local historical diagnostic evidence while preserving
  `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
  `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
  `VPS_RUNTIME=NOT_TOUCHED`.

## Evidence Accepted

D11.57 is committed, pushed, and VPS-validated twice:

- `77 passed in 3.05s`
- `77 passed in 0.25s`

D11.57 accepted Mac-local historical diagnostic evidence:

- `mac_local_historical_diagnostic_evidence=ACCEPTED`
- `all_symbols_d11_countable=true`
- `all_symbols_freshness_classification=clean`
- `diagnostic_date=2026-06-26`
- `authorized_utc=2026-06-26T14:00:00Z`
- `observed_run_utc=2026-06-26T14:00:26Z`
- `selected_mac_local_endpoint=127.0.0.1:7497`
- `selected_endpoint_context=LOCAL_MAC`
- `selected_endpoint_type=TWS_PAPER`
- `selected_endpoint_port=7497`

The accepted evidence includes all five symbols: `AAPL`, `MSFT`, `NVDA`,
`TSLA`, and `MSTR`. All five were clean and countable.

## Criteria Remaining Unresolved

Primary eligibility is not approved because these criteria remain unresolved:

- `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`
  is not satisfied by D11.57.
- The selected endpoint remains valid only for `LOCAL_MAC`; endpoint scope is
  `LOCAL_MAC_ONLY`.
- This adjudication does not validate VPS `127.0.0.1:7497`.
- The prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
  `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.
- `candidate_can_count_for_d11` is not satisfied because the existing source
  provider candidate remains broker-coupled and not approved primary.

Therefore:

```text
ibkr_primary_eligibility=NOT_APPROVED
d11_primary_eligibility_adjudication=BLOCKED_CRITERIA_UNRESOLVED
d11_primary_candidate_status=candidate
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
```

## Authority Boundaries Preserved

D11.58 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.58 records no package capture, replay, scoring, candidate generation,
strategy, risk, execution, VPS proof, VPS market test, broker endpoint traffic,
runtime mutation, timer mutation, service mutation, systemd mutation, TWS
mutation, Gateway mutation, Unit 12 opening, or live-trading authority.

Preserved statuses:

```text
IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED
D11_INSUFFICIENT
UNIT_12_BLOCKED
PACKAGE_CAPTURE=BLOCKED
VPS_RUNTIME=NOT_TOUCHED
```
