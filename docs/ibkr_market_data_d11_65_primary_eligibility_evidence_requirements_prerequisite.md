# D11.65 IBKR Primary Eligibility Evidence Requirements Prerequisite

## Scope and Decision

D11.65 is a source-controlled prerequisite packet defining the exact evidence
requirements that must be satisfied before IBKR primary eligibility can be
reconsidered.

It defines requirements only. It does not collect evidence, perform broker/TWS/
API/runtime/network/service/scheduler/systemd/credential/VPS actions, run
market-session diagnostics, submit/cancel/flatten/sell/clean up broker
positions, generate package captures, runtime reports, diagnostic reports,
replay output, scoring output, or candidate-generation output, open Unit 12,
approve IBKR primary eligibility, imply broker submit readiness, imply live
trading readiness, or create operational commands for broker, TWS, runtime,
VPS, scheduler, systemd, credentials, package capture, replay, scoring,
candidate generation, or live trading.

Decision: evidence-requirements prerequisite recorded fail-closed.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE` |
| `source_commit` | `cee9f5237e2ff220d4230fabd1d905be90e79b9a` |
| `d11_64_decision` | `BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED` |
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
| `d11_65_decision` | `EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED` |
| `evidence_collected` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `next_permissible_gate` | `D11.66_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN` |

## Evidence Requirements Table

| Requirement | Classification | Required before reconsideration |
| --- | --- | --- |
| Historical data availability evidence | Already satisfied by prior source-controlled evidence | D11.57 accepted LOCAL_MAC historical diagnostic evidence: all five symbols were clean/countable. Before reconsideration, a source-controlled gate must state whether this evidence is diagnostic-only or may contribute to a bounded primary-eligibility evidence bundle. |
| Endpoint locality evidence | Source-controlled documentation/test requirement | A source-controlled prerequisite must state whether `LOCAL_MAC_ONLY` endpoint locality can support any primary-eligibility reconsideration path, and must preserve that LOCAL_MAC `127.0.0.1:7497` is not VPS `127.0.0.1:7497`. |
| VPS production/runtime reachability evidence | Future VPS evidence requirement | If a future path relies on VPS production/runtime eligibility, a separate source-controlled authorization gate must first define safe read-only VPS evidence boundaries. D11.65 does not authorize or collect VPS evidence. |
| Broker-coupling evidence | Source-controlled documentation/test requirement | A source-controlled criteria/evidence gate must resolve whether `broker_coupled=true` can ever be compatible with D11 primary eligibility while preserving no account/order/execution authority. |
| Provider primary-eligibility evidence | Source-controlled documentation/test requirement | A source-controlled gate must define the non-runtime requirements for moving `ibkr_market_data_candidate` from `candidate` toward any future reconsideration. D11.65 does not approve `approved_primary`. |
| `candidate_can_count_for_d11` evidence | Source-controlled documentation/test requirement | A source-controlled gate must prove the candidate satisfies, or explicitly revises, the current `candidate_can_count_for_d11` criteria. Current source does not satisfy it. |
| Broker submit readiness evidence | Explicitly out of scope for D11 primary eligibility | Broker submit readiness is not required to define market-data primary eligibility and remains unapproved. Any future submit-readiness work requires a separate authority gate. |
| Live trading readiness evidence | Explicitly out of scope for D11 primary eligibility | Live trading readiness is not required to define market-data primary eligibility and remains unapproved. Any future live-trading work requires a separate authority gate. |
| Unit 12 opening prerequisites | Explicitly out of scope for D11 primary eligibility | Unit 12 opening is not authorized by D11.65. Any future Unit 12 opening requires a separate gate after D11 sufficiency is explicitly established. |

## Blocker-to-Requirement Mapping

| D11.64 blocker | D11.65 evidence requirement |
| --- | --- |
| `separate_vps_read_only_freshness_proof_required_before_primary_eligibility` remains unrevised | `candidate_can_count_for_d11` and provider primary-eligibility evidence requirements must be satisfied or explicitly revised by source-controlled criteria before reconsideration. |
| `ibkr_market_data_candidate` is not `approved_primary` | Provider primary-eligibility evidence requirement. |
| `ibkr_market_data_candidate` remains `d11_primary_eligible=false` | `candidate_can_count_for_d11` evidence requirement. |
| `ibkr_market_data_candidate` remains `broker_coupled=true` | Broker-coupling evidence requirement. |
| LOCAL_MAC historical evidence does not validate VPS production/runtime eligibility | VPS production/runtime reachability evidence requirement if VPS eligibility remains part of any future path. |
| LOCAL_MAC historical evidence does not establish broker submit readiness | Broker submit readiness is explicitly out of scope for D11 primary eligibility and remains unapproved. |
| LOCAL_MAC historical evidence does not establish live trading readiness | Live trading readiness is explicitly out of scope for D11 primary eligibility and remains unapproved. |
| Unit 12 remains closed | Unit 12 opening prerequisites are explicitly out of scope and remain blocked. |

## Already-Satisfied Evidence

Already satisfied by prior source-controlled evidence:

- D11.57 accepted `mac_local_historical_diagnostic_evidence=ACCEPTED`.
- All five symbols were `all_symbols_d11_countable=true`.
- All five symbols had `all_symbols_freshness_classification=clean`.
- The selected endpoint was `selected_endpoint_context=LOCAL_MAC`,
  `selected_endpoint_type=TWS_PAPER`, and
  `selected_mac_local_endpoint=127.0.0.1:7497`.
- The selected endpoint scope was `endpoint_scope=LOCAL_MAC_ONLY`.

This evidence remains historical data availability and endpoint locality
evidence only. It does not approve provider primary eligibility, validate VPS
production/runtime reachability, prove broker submit readiness, prove live
trading readiness, open Unit 12, or complete D11.

## Still-Missing Evidence

Still missing before IBKR primary eligibility can be reconsidered:

- source-controlled governance mapping from historical data availability to
  any allowable primary-eligibility evidence bundle;
- source-controlled endpoint locality rule for `LOCAL_MAC_ONLY` evidence;
- source-controlled broker-coupling adjudication for `broker_coupled=true`;
- source-controlled provider primary-eligibility evidence for changing
  candidate-only status;
- source-controlled proof that `candidate_can_count_for_d11` is satisfied or
  has been explicitly revised by a later governance gate;
- future VPS production/runtime reachability evidence, if a future path keeps a
  VPS requirement;
- separate future authorization for any broker/TWS evidence, if later required.

## Fail-Closed Criteria

IBKR primary eligibility must remain `NOT_APPROVED` if any of these remain
true:

- `candidate_can_count_for_d11` is not satisfied and has not been explicitly
  revised by source-controlled criteria;
- `ibkr_market_data_candidate` remains `d11_primary_candidate_status=candidate`;
- `ibkr_market_data_candidate` remains `d11_primary_eligible=false`;
- `ibkr_market_data_candidate` remains `broker_coupled=true` without a
  source-controlled compatibility adjudication;
- the only accepted evidence is historical LOCAL_MAC diagnostic evidence;
- VPS production/runtime reachability is required by the active criteria but
  remains unvalidated;
- any required source-controlled evidence-requirements mapping is missing;
- Unit 12 opening, broker submit readiness, or live trading readiness is being
  implied rather than separately authorized.

D11 must remain `D11_INSUFFICIENT` while IBKR primary eligibility remains
`NOT_APPROVED`. Unit 12 must remain `UNIT_12_BLOCKED` unless a later separate
gate explicitly opens it.

## Disqualifiers

These are explicit disqualifiers for approving IBKR primary eligibility:

- approving from the LOCAL_MAC lane name, option order, prior assistant
  expectation, or user framing;
- treating historical data availability as provider primary eligibility;
- treating LOCAL_MAC `127.0.0.1:7497` as VPS `127.0.0.1:7497`;
- treating `18789` or `18791` as approved market-data endpoints without a
  separate source-controlled approval;
- treating broker submit readiness or live trading readiness as implied by
  market-data evidence;
- modifying production provider-selection behavior inside this gate;
- collecting new runtime, broker, TWS, VPS, scheduler, systemd, credential,
  package-capture, replay, scoring, candidate-generation, or live-trading
  evidence inside this gate.

## Next Gate

The exact next permissible gate is:

```text
D11.66_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN
```

D11.66 may authorize only a source-controlled read-only evidence authorization
plan. It must not activate runtime, activate broker systems, open Unit 12,
approve IBKR primary eligibility, imply broker submit readiness, imply live
trading readiness, or create operational commands for broker, TWS, runtime,
VPS, scheduler, systemd, credentials, package capture, replay, scoring,
candidate generation, or live trading.

## Status Preserved

```text
d11_65_decision=EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED
evidence_collected=false
runtime_broker_vps_scheduler_systemd_credential_action=false
production_provider_selection_behavior_changed=false
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
account_order_execution_authority=false
```

D11.65 records no broker/TWS/API/runtime/network/service/scheduler/systemd/
credential/VPS authority; no market-session diagnostic authority; no package
capture; no runtime report; no diagnostic report; no replay output; no scoring
output; no candidate-generation output; no strategy, risk, execution,
provider-selection runtime behavior, scheduler, credential, or environment
change authority; no submit, cancel, flatten, sell, cleanup, broker submit
readiness, live-trading readiness, Unit 12 opening, or IBKR primary eligibility
approval.
