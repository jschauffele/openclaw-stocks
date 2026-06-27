# D11.67 Read-Only Evidence Preflight Design

## Scope and Decision

D11.67 is a source-controlled read-only evidence preflight design for possible
future evidence capture needed to address the D11.65/D11.66 IBKR primary
eligibility evidence requirements.

It is design-only. It does not authorize or perform evidence collection, does
not create executable evidence-capture commands, does not perform broker/TWS/
API/runtime/network/service/scheduler/systemd/credential/VPS actions, does not
run market-session diagnostics, does not submit/cancel/flatten/sell/clean up
broker positions, does not generate package captures, runtime reports,
diagnostic reports, replay output, scoring output, or candidate-generation
output, does not open Unit 12, does not approve IBKR primary eligibility, and
does not imply broker submit readiness or live trading readiness.

Decision: read-only evidence preflight design recorded fail-closed.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN` |
| `source_commit` | `fbef77a96eac9e7552ac739250113e328225c579` |
| `d11_66_classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN` |
| `d11_66_decision` | `READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED` |
| `d11_65_classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE` |
| `d11_65_decision` | `EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED` |
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
| `d11_67_decision` | `READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED` |
| `evidence_collected` | `false` |
| `evidence_collection_authorized` | `false` |
| `executable_evidence_capture_commands_created` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `next_permissible_gate` | `D11.68_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW` |

## Read-Only Evidence Preflight Design Table

| Design lane | Design boundary |
| --- | --- |
| LOCAL_MAC read-only evidence preflight design | May describe future LOCAL_MAC evidence shape only. It must preserve `LOCAL_MAC_ONLY` scope, no account/order/execution authority, no credentials, no TWS/Gateway mutation, and no evidence collection in D11.67. |
| VPS read-only evidence preflight design | May describe future VPS evidence shape only. It must preserve process-context locality, require separately approved endpoint status, reject guessed endpoints, and collect no VPS evidence in D11.67. |
| Broker/TWS read-only evidence preflight design | May describe future broker/TWS evidence shape only. It must preserve no account/order/execution authority, no submit readiness, no live trading readiness, no credential disclosure, and no broker/TWS evidence collection in D11.67. |
| Source-controlled documentation/test adjudication | May define docs/test-only criteria review paths. It must not imply runtime, broker, TWS, VPS, scheduler, systemd, credential, or market-session activity. |
| Evidence collection | Not authorized and not performed by D11.67. |
| Evidence adjudication | Not performed by D11.67; any future adjudication requires a separate source-controlled gate. |
| Provider primary eligibility | Remains `NOT_APPROVED`. |
| Runtime deployment eligibility | Not established. |
| Broker submit readiness | Not established and out of scope. |
| Live trading readiness | Not established and out of scope. |
| Unit 12 opening | Not authorized and remains `UNIT_12_BLOCKED`. |

## D11.66 Authorization Boundary to Preflight Design Mapping

| D11.66 authorization boundary | D11.67 preflight design |
| --- | --- |
| Already satisfied source-controlled records | Record D11.57 historical LOCAL_MAC evidence as already accepted; do not recollect it. |
| Future source-controlled documentation/test adjudication | Design a docs/test-only review lane with no runtime action. |
| Future LOCAL_MAC read-only evidence authorization | Design only: allowed fields, forbidden fields, source context, and fail-closed criteria must be defined by a later gate before capture. |
| Future VPS read-only evidence authorization | Design only: process context, endpoint approval status, and VPS safety boundaries must be defined by a later gate before capture. |
| Future broker/TWS read-only evidence authorization | Design only: read-only scope, no account/order/execution boundary, no credential disclosure, no submit readiness, and no live trading readiness must be defined by a later gate before capture. |
| Explicitly out-of-scope categories | Broker submit readiness, live trading readiness, and Unit 12 opening remain outside D11 primary eligibility and require separate future gates. |

## Allowed Design-Only Evidence Classes

D11.67 may describe these evidence classes in design form only:

- historical data availability evidence;
- endpoint locality evidence;
- source-controlled documentation/test adjudication evidence;
- LOCAL_MAC read-only evidence shape;
- VPS read-only evidence shape;
- broker/TWS read-only evidence shape;
- broker-coupling adjudication criteria;
- provider primary-eligibility criteria;
- `candidate_can_count_for_d11` criteria satisfaction or revision criteria.

No listed class is collected, authorized for collection, or adjudicated by
D11.67.

## Forbidden Evidence Classes and Forbidden Actions

Forbidden evidence classes and actions in D11.67:

- account, position, margin, buying-power, portfolio, order, execution, submit,
  cancel, flatten, sell, cleanup, broker submit readiness, or live trading
  readiness evidence;
- credential, token, session, account identifier, or secret evidence;
- package capture, runtime report, diagnostic report, replay output, scoring
  output, or candidate-generation output;
- market-session diagnostics;
- broker/TWS/API/runtime/network/service/scheduler/systemd/credential/VPS
  actions;
- TWS, Gateway, openclaw-gateway, runtime, service, timer, scheduler, systemd,
  credential, environment, strategy, risk, execution, or provider-selection
  runtime behavior mutation;
- executable evidence-capture commands.

## Required Preflight Safety Checks for a Later Gate

Before any future evidence capture could occur, a later source-controlled gate
must define:

- the exact evidence requirement being addressed;
- whether the context is documentation/test, LOCAL_MAC, VPS, or broker/TWS;
- allowed evidence fields and forbidden evidence fields;
- allowed process context and forbidden process context;
- endpoint approval status and localhost process-context treatment;
- no account/order/execution authority;
- no credential disclosure;
- no submit readiness and no live trading readiness;
- no runtime/service/scheduler/systemd mutation;
- no package capture, replay, scoring, or candidate generation;
- evidence freshness/timing expectations if applicable;
- paste-back or artifact format if applicable, without executable commands in
  D11.67;
- adjudication criteria;
- fail-closed result if evidence is absent, ambiguous, stale, outside scope, or
  indicates authority expansion.

D11.67 does not authorize those future checks to be executed.

## Fail-Closed Stop Criteria Before Evidence Capture

A later gate must stop before evidence capture if any of these are true:

- the evidence requirement is not mapped to a source-controlled criterion;
- the proposed source context is ambiguous;
- the proposed endpoint is guessed, unapproved, or process-context ambiguous;
- LOCAL_MAC `127.0.0.1:7497` is treated as VPS `127.0.0.1:7497`;
- `18789` or `18791` are treated as approved market-data endpoints without a
  separate source-controlled approval;
- the proposal includes account/order/execution, submit readiness, live trading
  readiness, credentials, package capture, replay, scoring, or candidate
  generation;
- the proposal includes runtime, service, scheduler, systemd, TWS, Gateway,
  openclaw-gateway, VPS, credential, strategy, risk, execution, environment, or
  provider-selection runtime behavior mutation;
- the proposal includes executable commands before a separate authorization
  packet explicitly permits them.

## Disqualifiers for Later Read-Only Evidence Capture Authorization

Any later read-only evidence capture authorization is disqualified if it:

- uses lane name, option order, prior assistant expectation, or user framing as
  approval evidence;
- implies evidence collection from this design packet;
- modifies production provider-selection behavior;
- treats broker-coupled candidate status as resolved without
  source-controlled evidence;
- treats historical data availability as provider primary eligibility;
- implies runtime deployment eligibility, broker submit readiness, live trading
  readiness, D11 sufficiency, Unit 12 opening, or IBKR primary eligibility
  approval.

## Localhost and Broker-Coupling Boundaries

`127.0.0.1` is process-context local. LOCAL_MAC `127.0.0.1:7497` is not
equivalent to VPS `127.0.0.1:7497`. D11.67 does not validate VPS
`127.0.0.1:7497`.

The prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue and
not a proven IB Gateway issue. `18789` and `18791` remain not approved
market-data endpoints unless separately approved by source-controlled criteria.

The broker-coupled candidate blocker remains active:
`ibkr_market_data_candidate` remains `broker_coupled=true`,
`d11_primary_eligible=false`, and `d11_primary_candidate_status=candidate`.
`candidate_can_count_for_d11` remains unsatisfied.

## Next Gate

The exact next permissible gate is:

```text
D11.68_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW
```

D11.68 may only review this source-controlled preflight design. It must not be
runtime activation, broker activation, submit readiness, live trading, package
capture, replay, scoring, candidate generation, actual evidence execution, or
IBKR primary eligibility approval.

## Status Preserved

```text
d11_67_decision=READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED
evidence_collected=false
evidence_collection_authorized=false
executable_evidence_capture_commands_created=false
runtime_broker_vps_scheduler_systemd_credential_action=false
production_provider_selection_behavior_changed=false
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
account_order_execution_authority=false
```

D11.67 records no broker/TWS/API/runtime/network/service/scheduler/systemd/
credential/VPS authority; no market-session diagnostic authority; no package
capture; no runtime report; no diagnostic report; no replay output; no scoring
output; no candidate-generation output; no strategy, risk, execution,
provider-selection runtime behavior, scheduler, credential, or environment
change authority; no submit, cancel, flatten, sell, cleanup, broker submit
readiness, live-trading readiness, Unit 12 opening, evidence collection, or
IBKR primary eligibility approval.
