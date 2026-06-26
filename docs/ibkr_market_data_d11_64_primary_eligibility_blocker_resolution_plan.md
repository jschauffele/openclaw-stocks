# D11.64 IBKR Primary Eligibility Blocker Resolution Plan

## Scope and Decision

D11.64 is a source-controlled blocker-resolution plan for the unresolved IBKR
primary-eligibility blocker recorded in D11.63:

```text
D11.64_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN
```

It reviews committed D11 criteria, accepted LOCAL_MAC evidence, provider
candidate metadata, prior VPS endpoint evidence, and D11.63 fail-closed
adjudication only. It does not perform broker/TWS/API/runtime/network/service/
scheduler/systemd/credential/VPS actions, does not run market-session
diagnostics, does not submit/cancel/flatten/sell/clean up broker positions,
does not generate package captures, runtime reports, diagnostic reports,
replay output, scoring output, or candidate-generation output, and does not
change strategy, risk, execution, provider-selection runtime behavior,
scheduler behavior, credentials, or environment files.

Decision: blocker-resolution plan only. D11.64 does not approve IBKR primary
eligibility, does not progress D11, and does not open Unit 12. It records the
missing evidence classes and defines a safe source-controlled next gate.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN` |
| `source_commit` | `ac78409fa0c81c97f2a357671cbc55fd55988f4b` |
| `d11_63_decision` | `BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE` |
| `criteria_revision_result` | `NOT_APPROVED` |
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
| `d11_64_decision` | `BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED` |
| `next_permissible_gate` | `D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE` |

## Source-Controlled Blockers

D11.64 identifies these exact blockers before IBKR primary eligibility can be
reconsidered:

1. `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`
   remains in `D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`; D11.63 did not revise
   it.
2. `candidate_can_count_for_d11` is not satisfied because the source
   `ibkr_market_data_candidate` is not `approved_primary`.
3. `ibkr_market_data_candidate` remains `d11_primary_eligible=false`.
4. `ibkr_market_data_candidate` remains `broker_coupled=true`.
5. LOCAL_MAC historical evidence does not validate VPS production/runtime
   eligibility.
6. LOCAL_MAC historical evidence does not establish broker submit readiness.
7. LOCAL_MAC historical evidence does not establish live trading readiness.
8. Unit 12 remains closed and no separate source-controlled gate opens it.

No source-controlled contradiction was found. Therefore D11.64 preserves
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`, and
`UNIT_12_BLOCKED`.

## Evidence Classes and Missing Evidence

| Evidence class | Current source-controlled status | Missing before reconsideration |
| --- | --- | --- |
| Historical data availability evidence | Supported for the D11.57 LOCAL_MAC historical diagnostic: all five symbols were clean/countable. | Governance must state whether this evidence can be used only as diagnostic availability evidence or can contribute to a future primary-eligibility evidence bundle. |
| Endpoint locality evidence | Supported only for LOCAL_MAC `127.0.0.1:7497` / `TWS_PAPER`; `127.0.0.1` is process-context local. | Source-controlled prerequisite must decide whether LOCAL_MAC-only endpoint locality is acceptable for any bounded primary-eligibility evidence path. |
| Broker-coupling evidence | Not resolved; `ibkr_market_data_candidate` remains `broker_coupled=true`. | Future source-controlled evidence or criteria must resolve whether a broker-coupled market-data provider can ever count for D11 primary eligibility without account/order/execution authority. |
| Provider primary-eligibility evidence | Not resolved; candidate remains `candidate`, `d11_primary_eligible=false`, and does not satisfy `candidate_can_count_for_d11`. | Future source-controlled criteria/evidence must define the exact non-runtime requirements for moving from candidate-only to reconsideration. |
| VPS production/runtime eligibility evidence | Not resolved; VPS `127.0.0.1:7497` is unvalidated and prior VPS failure remains active. | Future VPS/runtime evidence would require a separate source-controlled authorization gate and remains closed in D11.64. |
| Broker submit readiness evidence | Not supported and not requested. | Any broker submit readiness evidence would require a separate future authority gate and remains closed in D11.64. |
| Live trading readiness evidence | Not supported and not requested. | Any live trading readiness evidence would require a separate future authority gate and remains closed in D11.64. |

## Governance vs Future Evidence Blockers

Governance/documentation blockers:

- no adopted criteria revision for replacing, narrowing, or retaining
  `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`
  in a way that clearly maps LOCAL_MAC historical evidence to primary
  eligibility reconsideration;
- no source-controlled evidence-requirements packet defining the minimum
  non-runtime evidence bundle needed before reconsideration;
- no source-controlled decision separating historical data availability from
  provider primary eligibility for a broker-coupled LOCAL_MAC-only candidate.

Future runtime, broker, VPS, or market-session evidence blockers:

- VPS production/runtime eligibility evidence is absent;
- broker submit readiness evidence is absent;
- live trading readiness evidence is absent;
- any future endpoint, runtime, broker, VPS, scheduler, systemd, credential,
  package capture, replay, scoring, candidate generation, or market-session
  diagnostic evidence requires a separate authorization gate.

D11.64 does not perform those future evidence captures and does not create
commands for them.

## Safe Next Gate Sequence

D11.64 defines this source-controlled next gate sequence:

1. `D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`
   must define the minimum evidence requirements for any future IBKR primary
   eligibility reconsideration. It must remain source-controlled, non-runtime,
   non-broker, non-VPS, and non-market-session.
2. A later gate may adjudicate whether a governance-only criteria packet is
   enough to reconsider the blocker or whether separately authorized runtime,
   VPS, broker, or market-session evidence would be required.
3. Any later runtime, VPS, broker, scheduler, systemd, credential,
   package-capture, replay, scoring, candidate-generation, submit-readiness, or
   live-trading evidence gate must be separately authorized and remains closed
   by D11.64.

The exact next permissible gate is:

```text
D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE
```

That next gate is a narrowly scoped source-controlled evidence-requirements
prerequisite. It is not runtime activation, broker activation, Unit 12 opening,
or IBKR primary eligibility approval.

## Fail-Closed Boundary

```text
d11_64_decision=BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
```

D11.64 does not modify production provider-selection behavior. If a future
gate finds that production provider-selection behavior must change before
eligibility can be reconsidered, that gate must classify the required behavior
change as separately scoped and must not perform it implicitly.

## Authorities Still Closed

D11.64 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.64 keeps closed broker/TWS/API/runtime/network/service/scheduler/systemd/
credential/VPS actions; market-session diagnostics; package capture; runtime
reports; diagnostic reports; replay output; scoring output; candidate
generation; strategy behavior changes; risk behavior changes; execution
behavior changes; provider-selection runtime behavior changes; scheduler
behavior changes; credential or environment file changes; submit, cancel,
flatten, sell, cleanup, broker submit readiness, live trading readiness, Unit
12 opening, and IBKR primary eligibility approval.

Process defect avoided: D11.64 does not infer approval from lane name, option
order, prior assistant expectation, or user framing.
