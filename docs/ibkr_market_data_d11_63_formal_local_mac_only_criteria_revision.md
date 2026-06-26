# D11.63 Formal LOCAL_MAC-Only IBKR Criteria Revision

## Scope and Decision

D11.63 is a source-controlled criteria-revision adjudication for the path
selected by D11.62:

```text
D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION
```

It reviews committed D11 criteria, accepted LOCAL_MAC evidence, provider
candidate metadata, and prior VPS endpoint evidence only. It does not run
broker/TWS/API/runtime/network/service/scheduler/systemd/credential/VPS work,
does not run market-session diagnostics, does not create package captures,
runtime reports, diagnostic reports, replay output, scoring output, or
candidate-generation output, and does not change strategy, risk, execution,
provider-selection runtime behavior, scheduler behavior, credentials, or
environment files.

Decision: fail closed. D11.63 does not revise IBKR primary-eligibility
criteria because the inspected evidence supports historical LOCAL_MAC data
availability only, not provider primary eligibility. The source-controlled
provider candidate remains `d11_primary_eligible=false`, `broker_coupled=true`,
and `d11_primary_candidate_status=candidate`, so approving primary eligibility
would require a production behavior or provider-candidate contract change that
is out of scope for this gate.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_LOCAL_MAC_ONLY_CRITERIA_REVISION_ADJUDICATION` |
| `source_commit` | `94fdbbe93ff4b9d4b46018a3a9cef211dd142049` |
| `d11_62_decision` | `LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED` |
| `d11_62_next_gate` | `D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION` |
| `criteria_revision_result` | `NOT_APPROVED` |
| `d11_63_decision` | `BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE` |
| `primary_eligibility_revision` | `NOT_REVISED` |
| `separate_vps_proof_rule_revision` | `NOT_REVISED` |
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
| `next_permissible_gate` | `D11.64_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN` |

## Source-Controlled Criteria Reviewed

D11.63 reviewed these source-controlled records:

- `market_data_provider_selection.py`:
  `D11_PRIMARY_PROVIDER_SELECTION_CRITERIA` still includes
  `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.
- `market_data_provider_selection.py`: `candidate_can_count_for_d11` requires
  `d11_primary_candidate_status=approved_primary`,
  `d11_primary_eligible=true`, `order_authority=false`,
  `execution_authority=false`, and `broker_coupled=false`.
- `market_data_provider_selection.py`: `ibkr_market_data_candidate` remains
  `d11_primary_candidate_status=candidate`, `d11_primary_eligible=false`,
  `broker_coupled=true`, `order_authority=false`, and
  `execution_authority=false`.
- D11.57 accepted only Mac-local historical diagnostic evidence.
- D11.58 failed closed on primary eligibility because the VPS proof rule,
  `LOCAL_MAC_ONLY` endpoint scope, VPS `127.0.0.1:7497` validation gap, and
  provider candidate status remained unresolved.
- D11.61 required a formal LOCAL_MAC criteria-revision packet before any
  LOCAL_MAC-only revision could be adopted.
- D11.62 selected this formal criteria-revision path but did not approve a
  revision.

## Evidence Separation

D11.63 distinguishes these evidence classes:

| Evidence class | D11.63 adjudication |
| --- | --- |
| Historical data availability evidence | Supported only for the D11.57 LOCAL_MAC diagnostic: all five symbols were clean/countable. |
| Endpoint locality evidence | Supported only for LOCAL_MAC `127.0.0.1:7497` / `TWS_PAPER`; `127.0.0.1` remains process-context local. |
| Provider primary eligibility | Not supported; the source candidate remains candidate-only, not primary eligible, and broker-coupled. |
| Runtime deployment eligibility | Not supported; LOCAL_MAC evidence does not validate VPS production/runtime eligibility. |
| Broker submit readiness | Not supported; D11.63 grants no account/order/execution authority. |
| Live trading readiness | Not supported; D11.63 grants no live-trading authority. |

Accepted LOCAL_MAC historical evidence remains accepted:

- `mac_local_historical_diagnostic_evidence=ACCEPTED`
- `all_symbols_d11_countable=true`
- `all_symbols_freshness_classification=clean`
- symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, and `MSTR`
- `selected_endpoint_context=LOCAL_MAC`
- `selected_endpoint_type=TWS_PAPER`
- `selected_mac_local_endpoint=127.0.0.1:7497`
- `endpoint_scope=LOCAL_MAC_ONLY`

That evidence does not validate VPS `127.0.0.1:7497`, does not validate
runtime deployment, does not approve provider primary eligibility, does not
prove broker submit readiness, and does not prove live trading readiness.

## Criteria Revision Adjudication

D11.63 does not revise
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.

The accepted LOCAL_MAC evidence is strong enough to show historical data
availability through a local TWS paper endpoint for the diagnostic window. It
is not strong enough to replace the primary-eligibility criteria because:

- it is endpoint-locality evidence for the `LOCAL_MAC` process context only;
- it does not validate a VPS-accessible endpoint or production runtime path;
- it does not change the source provider candidate from `candidate` to
  `approved_primary`;
- it does not change `d11_primary_eligible=false`;
- it does not resolve the source candidate remaining `broker_coupled=true`;
- it does not establish broker submit readiness or live trading readiness;
- approving primary eligibility would require a production provider-selection
  behavior or candidate-contract change, which is out of scope.

The limited criteria change that could be considered in a future gate would
need to specify whether LOCAL_MAC-only market-data availability can count as a
bounded diagnostic evidence class. D11.63 does not adopt that change because
the current source-controlled criteria still lack a provider-eligibility rule
that separates LOCAL_MAC historical availability from primary provider
approval.

## VPS and Localhost Boundaries Preserved

`127.0.0.1` is process-context local. LOCAL_MAC `127.0.0.1:7497` is not
equivalent to VPS `127.0.0.1:7497`.

The prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue and
not a proven IB Gateway issue. VPS `127.0.0.1:7497` remains unvalidated.

`18789` and `18791` remain not approved market-data endpoints unless a
separate source-controlled criteria approval exists.

D11.63 preserves separation between LOCAL_MAC evidence and VPS production or
runtime eligibility.

## Unresolved Risks and Blockers

Unresolved blockers:

- no adopted criteria revision for replacing or narrowing
  `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`;
- no source-controlled provider-candidate state satisfying
  `candidate_can_count_for_d11`;
- `ibkr_market_data_candidate` remains `broker_coupled=true`;
- `ibkr_market_data_candidate` remains `d11_primary_eligible=false`;
- no VPS production/runtime eligibility evidence;
- no broker submit readiness evidence;
- no live trading readiness evidence.

Process defect avoided: D11.63 does not infer approval from the LOCAL_MAC lane
name, option order, prior expected outcome, or user framing.

## Fail-Closed Result

```text
d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE
criteria_revision_result=NOT_APPROVED
primary_eligibility_revision=NOT_REVISED
separate_vps_proof_rule_revision=NOT_REVISED
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
```

The exact next permissible gate is:

```text
D11.64_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN
```

That future gate may plan source-controlled blocker resolution only. It must
not imply broker/TWS/API/runtime/network/service/scheduler/systemd/credential/
VPS actions, market-session diagnostics, package capture, replay, scoring,
candidate generation, strategy/risk/execution behavior changes,
provider-selection runtime behavior changes, account/order/execution
authority, Unit 12 opening, broker submit readiness, or live trading readiness.

## Authority Boundaries Preserved

D11.63 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.63 records no broker/TWS/API/runtime/network/service/scheduler/systemd/
credential/VPS authority; no market-session diagnostic authority; no package
capture; no runtime report; no diagnostic report; no replay output; no scoring
output; no candidate-generation output; no strategy, risk, execution,
provider-selection runtime behavior, scheduler, credential, or environment
change authority; no submit, cancel, flatten, sell, cleanup, or live-trading
authority; and no Unit 12 opening.

D11.63 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.
