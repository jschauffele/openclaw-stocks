# D11.66 IBKR Primary Eligibility Read-Only Evidence Authorization Plan

## Scope and Decision

D11.66 is a source-controlled read-only evidence authorization plan for the
IBKR primary-eligibility evidence requirements recorded in D11.65.

It defines authorization boundaries only. It does not collect evidence,
authorize actual read-only evidence capture, perform broker/TWS/API/runtime/
network/service/scheduler/systemd/credential/VPS actions, run market-session
diagnostics, submit/cancel/flatten/sell/clean up broker positions, generate
package captures, runtime reports, diagnostic reports, replay output, scoring
output, or candidate-generation output, open Unit 12, approve IBKR primary
eligibility, imply broker submit readiness, imply live trading readiness, or
create executable evidence-capture commands.

Decision: read-only evidence authorization plan recorded fail-closed.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN` |
| `source_commit` | `3e66732e4cfbcb454fb72d9036bcb1921c0b24b2` |
| `d11_65_classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE` |
| `d11_65_decision` | `EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED` |
| `d11_64_decision` | `BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED` |
| `d11_63_decision` | `BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE` |
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
| `d11_66_decision` | `READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED` |
| `evidence_collected` | `false` |
| `actual_read_only_evidence_capture_authorized` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `executable_evidence_capture_commands_created` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `next_permissible_gate` | `D11.67_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN` |

## Authorization Plan Table

| D11.65 requirement category | Authorization boundary |
| --- | --- |
| Already satisfied by source-controlled prior records | No new authorization. D11.57 historical LOCAL_MAC evidence remains accepted as historical data availability and endpoint locality evidence only. |
| Future source-controlled documentation/test adjudication | May be handled by a future docs/test-only gate with no runtime, broker, TWS, VPS, scheduler, systemd, credential, or market-session activity. |
| Future LOCAL_MAC read-only evidence authorization | Requires a later source-controlled preflight design gate that states the evidence target, source context, authority boundary, fields allowed, fields forbidden, and adjudication criteria. D11.66 does not authorize capture. |
| Future VPS read-only evidence authorization | Requires a later source-controlled preflight design gate that first resolves process context, approved endpoint status, and VPS safety boundaries. D11.66 does not authorize VPS evidence capture. |
| Future broker/TWS read-only evidence authorization | Requires a later source-controlled preflight design gate that proves read-only scope, no account/order/execution authority, no credential disclosure, no submit readiness, and no live trading readiness. D11.66 does not authorize broker/TWS evidence capture. |
| Explicitly out of scope for D11 primary eligibility | Broker submit readiness, live trading readiness, and Unit 12 opening remain outside D11 primary eligibility and require separate future gates. |

## D11.65 Requirement to Authorization Boundary Mapping

| D11.65 requirement | D11.66 authorization boundary |
| --- | --- |
| Historical data availability evidence | Already satisfied by prior source-controlled evidence; no new capture authorized. |
| Endpoint locality evidence | Documentation/test adjudication may define whether LOCAL_MAC-only locality can contribute to reconsideration; no endpoint inspection authorized. |
| VPS production/runtime reachability evidence | Future VPS read-only evidence authorization would require separate preflight design; no VPS action authorized. |
| Broker-coupling evidence | Documentation/test adjudication must define whether `broker_coupled=true` is compatible with primary eligibility; no broker action authorized. |
| Provider primary-eligibility evidence | Documentation/test adjudication must define criteria for moving from candidate-only status; no provider runtime behavior change authorized. |
| `candidate_can_count_for_d11` evidence | Documentation/test adjudication must prove satisfaction or explicit criteria revision; no production provider-selection behavior change authorized. |
| Broker submit readiness evidence | Explicitly out of scope for D11 primary eligibility; no submit-readiness evidence authorization. |
| Live trading readiness evidence | Explicitly out of scope for D11 primary eligibility; no live-trading evidence authorization. |
| Unit 12 opening prerequisites | Explicitly out of scope for this gate; Unit 12 remains blocked. |

## Already-Satisfied Evidence

Already satisfied by prior source-controlled evidence:

- D11.57 accepted `mac_local_historical_diagnostic_evidence=ACCEPTED`.
- All five symbols were `all_symbols_d11_countable=true`.
- All five symbols had `all_symbols_freshness_classification=clean`.
- The selected endpoint was `selected_endpoint_context=LOCAL_MAC`,
  `selected_endpoint_type=TWS_PAPER`, and
  `selected_mac_local_endpoint=127.0.0.1:7497`.
- The selected endpoint scope was `endpoint_scope=LOCAL_MAC_ONLY`.

This remains historical data availability and endpoint locality evidence only.
It is not evidence adjudication for provider primary eligibility, runtime
deployment eligibility, broker submit readiness, live trading readiness, or
Unit 12 opening.

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
- future LOCAL_MAC read-only evidence authorization design, if a future path
  requires more LOCAL_MAC read-only evidence;
- future VPS read-only evidence authorization design, if a future path keeps a
  VPS requirement;
- future broker/TWS read-only evidence authorization design, if later required.

## Future Evidence Categories

Future evidence categories remain separated:

- source-controlled documentation/test adjudication;
- future LOCAL_MAC read-only evidence authorization;
- future VPS read-only evidence authorization;
- future broker/TWS read-only evidence authorization;
- explicitly out-of-scope broker submit readiness;
- explicitly out-of-scope live trading readiness;
- explicitly out-of-scope Unit 12 opening.

## Authorization Preconditions

Before any future read-only evidence capture could be authorized, a later gate
must define all of the following:

- the exact evidence requirement being addressed;
- the source context: documentation/test, LOCAL_MAC, VPS, or broker/TWS;
- the allowed evidence fields;
- the forbidden evidence fields;
- the read-only authority boundary;
- the process-context boundary for any localhost endpoint;
- the endpoint approval status for any endpoint reference;
- the no-account/order/execution boundary;
- the no-credential-disclosure boundary;
- the no-runtime/service/scheduler/systemd mutation boundary;
- the evidence adjudication criteria;
- the fail-closed result if evidence is absent, ambiguous, or outside scope.

D11.66 does not satisfy these preconditions for any actual evidence capture.

## Authorization Disqualifiers

Any future read-only evidence authorization is disqualified if it:

- includes executable commands in the authorization-plan gate;
- implies evidence collection before a separate preflight design gate;
- targets VPS `127.0.0.1:7497` without process-context-local listening
  evidence and separate authorization;
- treats LOCAL_MAC `127.0.0.1:7497` as equivalent to VPS `127.0.0.1:7497`;
- treats `18789` or `18791` as approved market-data endpoints without a
  separate source-controlled approval;
- permits account, order, execution, submit, cancel, flatten, sell, cleanup,
  broker submit readiness, or live trading readiness;
- permits runtime, service, scheduler, systemd, credential, TWS, Gateway,
  openclaw-gateway, or VPS mutation;
- modifies production provider-selection behavior;
- implies IBKR primary eligibility approval, D11 sufficiency, or Unit 12
  opening.

## Boundary Separation

D11.66 preserves the difference between:

- read-only evidence authorization: a future source-controlled permission
  boundary, not granted by D11.66;
- evidence collection: not performed and not authorized by D11.66;
- evidence adjudication: a later source-controlled review, not performed by
  D11.66;
- provider primary eligibility: remains `NOT_APPROVED`;
- runtime deployment eligibility: not established;
- broker submit readiness: not established and out of scope;
- live trading readiness: not established and out of scope;
- Unit 12 opening: not authorized and remains blocked.

## Next Gate

The exact next permissible gate is:

```text
D11.67_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN
```

D11.67 may create only a source-controlled read-only evidence preflight design.
It must not execute evidence capture, activate runtime, activate broker
systems, open Unit 12, approve IBKR primary eligibility, imply broker submit
readiness, imply live trading readiness, or create executable commands for
broker, TWS, runtime, VPS, scheduler, systemd, credentials, package capture,
replay, scoring, candidate generation, or live trading.

## Status Preserved

```text
d11_66_decision=READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED
evidence_collected=false
actual_read_only_evidence_capture_authorized=false
runtime_broker_vps_scheduler_systemd_credential_action=false
executable_evidence_capture_commands_created=false
production_provider_selection_behavior_changed=false
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
account_order_execution_authority=false
```

D11.66 records no broker/TWS/API/runtime/network/service/scheduler/systemd/
credential/VPS authority; no market-session diagnostic authority; no package
capture; no runtime report; no diagnostic report; no replay output; no scoring
output; no candidate-generation output; no strategy, risk, execution,
provider-selection runtime behavior, scheduler, credential, or environment
change authority; no submit, cancel, flatten, sell, cleanup, broker submit
readiness, live-trading readiness, Unit 12 opening, or IBKR primary eligibility
approval.
