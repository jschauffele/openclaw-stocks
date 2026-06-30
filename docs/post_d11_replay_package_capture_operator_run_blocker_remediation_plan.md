# Post-D11 Replay Package Capture Operator Run Blocker Remediation Plan

This is the source-controlled remediation plan gate for the blocker recorded in
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_PREFLIGHT_BLOCKER_RECORD`.

This packet is a plan only. It does not execute remediation, package capture,
replay, scoring, candidate generation, broker/TWS/API/network/runtime action,
VPS action, scheduler/service/systemd/timer action, credential or
environment-file action, production provider-selection runtime behavior
change, production package-capture/orchestrator behavior change, or Unit 12
implementation. It does not fix the blocker.

Decision: the blocker remediation plan is complete and ready for a later
source-controlled remediation authorization packet. That next packet may
authorize source-controlled remediation edits only. It must not execute package
capture unless a later bounded operator-run gate explicitly authorizes
execution.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN` |
| `source_commit` | `ae9469c9de44f275b25d61f80d88667648434e00` |
| `prior_blocker_record` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_PREFLIGHT_BLOCKER_RECORD` |
| `prior_blocker_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKED_PENDING_LOCAL_ARTIFACTS_AND_AUTHORITY_SURFACE_REMEDIATION` |
| `remediation_plan_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN_COMPLETED_READY_FOR_REMEDIATION_AUTHORIZATION_PACKET` |
| `artifact_remediation_separated_from_authority_surface_remediation` | `true` |
| `implementation_selected_by_this_gate` | `false` |
| `remediation_executed` | `false` |
| `package_capture_executed` | `false` |
| `replay_executed` | `false` |
| `scoring_executed` | `false` |
| `candidate_generation_executed` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_runtime_behavior_changed` | `false` |
| `package_capture_orchestrator_behavior_changed` | `false` |
| `unit_12_implemented_or_opened` | `false` |
| `commit_performed` | `false` |
| `push_performed` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `package_capture_execution` | `NOT_AUTHORIZED` |
| `replay_execution` | `NOT_AUTHORIZED` |
| `scoring_execution` | `NOT_AUTHORIZED` |
| `candidate_generation_execution` | `NOT_AUTHORIZED` |
| `strategy_risk_execution_changes` | `BLOCKED` |
| `scheduler_runtime_service_systemd_timer_changes` | `BLOCKED` |
| `credential_environment_changes` | `BLOCKED` |
| `production_runtime_provider_selection_runtime_changes` | `BLOCKED` |
| `production_package_capture_orchestrator_behavior_changes` | `NOT_AUTHORIZED_BY_THIS_GATE` |
| `vps_endpoint_approval` | `NOT_APPROVED` |
| `endpoint_18789_18791_approval` | `NOT_APPROVED` |
| `bridge_tunnel_proxy_approval` | `NOT_APPROVED` |
| `unit_12_implementation` | `NOT_OPENED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET` |

## Recorded Blocker Basis

The prior blocker record established three blocker families:

| Blocker family | Recorded facts | Plan adjudication |
| --- | --- | --- |
| Missing local artifact blocker | `logs=MISSING`, `run_reports=MISSING`, `replay_packages=MISSING`, `last_run_report.json=ABSENT`, and no eligible `run_id` can be selected. | Requires an artifact remediation path before any operator run can be attempted. |
| Authority-surface mismatch blocker | Authorization approved `LOCAL_MAC_ONLY`, while `tools/ops/gate_d_market_session_operator.py` requires `--authorize-vps-package-write` and delegates to `package_execution_orchestrator` with `--execution-mode vps`. | Requires an authority-surface remediation path before any operator run can be attempted. |
| `order_state` exclusion | `order_state_json=ABSENT_EXCLUDED_NOT_BOUND`. | Preserved. `order_state` remains absent/excluded/not-bound and must not be used to unblock this gate. |

## Artifact-Remediation Plan

Artifact remediation is separate from authority-surface remediation.

The missing-artifact blocker may be remediated only by a later authorization
packet that chooses one of these mutually exclusive paths:

| Option | Description | Boundary |
| --- | --- | --- |
| Prior market-session/runtime artifact gate | Authorize a separate prior gate to produce or approve scheduled runtime artifacts from which an eligible `run_id` can be selected. | That gate must not be package capture, replay, scoring, candidate generation, broker action, runtime mutation beyond its explicit scope, or Unit 12. |
| Deterministic existing-artifact discovery | Authorize source-controlled discovery from already-existing deterministic artifacts, if such artifacts exist and can be proved aligned. | Discovery must be read-only, must not create artifacts, and must fail closed if `logs/<run_id>.jsonl` and `run_reports/<run_id>.json` or `last_run_report.json` are absent. |
| Layout-only remediation | Authorize source-controlled layout criteria for `replay_packages` readiness without writing a package. | Directory creation must be either deferred to the later governed package-capture execution or separately authorized by a narrow layout gate. This plan does not authorize directory creation. |

The later remediation authorization packet must explicitly decide whether
`replay_packages` directory creation is:

- allowed only as part of a later governed package-capture execution after all
  preflight checks pass; or
- separately authorized by a non-package layout gate that creates or validates
  only the directory structure needed to prove no-overwrite behavior.

This plan recommends the safest next authorization packet scope: source-control
criteria and tests first, with no artifact creation and no package capture. Any
artifact generation must require a later, narrower operator-run or runtime
artifact gate.

## Authority-Surface Remediation Plan

Authority-surface remediation is separate from artifact remediation.

The current source-controlled command surface is:

```text
capture --run-id <run_id> --expected-commit <commit> --authorize-vps-package-write
```

and the current delegated package execution surface is:

```text
package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write
```

The authorization lineage approved `LOCAL_MAC_ONLY`. Therefore the next
remediation authorization packet must choose between these mutually exclusive
authority-surface remediation paths:

| Option | Description | Boundary |
| --- | --- | --- |
| LOCAL_MAC package-capture command surface | Authorize source-controlled remediation edits that introduce or select a command surface compatible with `LOCAL_MAC_ONLY`. | Must not execute package capture in the remediation gate and must not expand broker, runtime, replay, scoring, candidate-generation, VPS, or Unit 12 authority. |
| Bounded VPS execution authorization path | Preserve the current VPS execution surface and require a separate bounded VPS execution authorization gate before any operator run. | Must explicitly authorize real `/opt` reads and writes only if that later gate exists. This plan does not authorize VPS execution. |
| Legacy-name adjudication path | Treat `--authorize-vps-package-write` as legacy naming only if a later source-controlled remediation proves it does not carry VPS authority. | Until remediated, the flag is authority-bearing and must be treated as VPS package-write authority. |

This plan does not choose an implementation. It records that
`--authorize-vps-package-write` must be treated as authority-bearing until a
later remediation authorization packet either revises the command surface or
formally narrows the flag semantics in source control.

## order_state Adjudication

`order_state` remains absent/excluded/not-bound:

```text
order_state_json=ABSENT_EXCLUDED_NOT_BOUND
```

The source-controlled runtime artifact reader blocks `order_state.json` reads
pending a later explicit binding gate. The package writer blocks
`order_state.json` writes pending a later explicit binding gate. This
remediation plan does not authorize order-state binding, order-state reads,
order-state writes, account state access, portfolio state access, position
state access, or broker-visible state expansion.

## Remediation Authorization Packet Requirements

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET
```

That next gate must be an authorization packet only unless it explicitly
authorizes later bounded source-controlled remediation edits. It must not
execute package capture unless a later bounded operator-run gate explicitly
authorizes package-capture execution.

The next authorization packet must define:

- which artifact-remediation option is authorized, if any;
- which authority-surface remediation option is authorized, if any;
- whether remediation edits are docs/tests only or include a narrowly scoped
  non-runtime source-controlled command-surface change;
- whether `replay_packages` directory handling is deferred to governed package
  capture or separately authorized by a layout gate;
- whether `--authorize-vps-package-write` remains authority-bearing, is
  renamed, or is narrowed by source-controlled criteria;
- fail-closed conditions for missing `logs/<run_id>.jsonl`,
  `run_reports/<run_id>.json`, `last_run_report.json`, unsafe `run_id`, stale
  report alignment, existing `replay_packages/<run_id>`, or unresolved VPS
  authority surface;
- proof that replay, scoring, candidate generation, Unit 12, broker authority,
  runtime mutation, credential/env mutation, and production behavior changes
  remain blocked.

## Still-Unapproved Authorities

| Authority | Status |
| --- | --- |
| Broker submit readiness | `NOT_APPROVED` |
| Live trading readiness | `NOT_APPROVED` |
| Account authority | `NONE` |
| Order authority | `NONE` |
| Execution authority | `NONE` |
| Package capture execution | `NOT_AUTHORIZED` |
| Replay execution | `NOT_AUTHORIZED` |
| Scoring execution | `NOT_AUTHORIZED` |
| Candidate generation execution | `NOT_AUTHORIZED` |
| Strategy behavior changes | `BLOCKED` |
| Risk behavior changes | `BLOCKED` |
| Execution behavior changes | `BLOCKED` |
| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |
| Credential or environment-file changes | `BLOCKED` |
| Production runtime configuration changes | `BLOCKED` |
| Production provider-selection runtime behavior changes | `BLOCKED` |
| Production package-capture/orchestrator behavior changes | `NOT_AUTHORIZED_BY_THIS_GATE` |
| VPS endpoint approval | `NOT_APPROVED` |
| `18789` or `18791` endpoint approval | `NOT_APPROVED` |
| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |
| Unit 12 implementation | `NOT_OPENED` |

## No Execution Or Runtime Action

This remediation plan performed no remediation, no package capture, no replay,
no scoring, no candidate generation, no broker/TWS/API/network/runtime action,
no IBKR connection, no TWS/Gateway inspection, no VPS action, no
service/systemd/scheduler/timer/runtime command, no credential or
environment-file access, no account, portfolio, balance, position, order,
execution, trade, P&L, margin, buying-power, or credential-data access, no
broker position action, no strategy behavior change, no risk behavior change,
no execution behavior change, no scheduler behavior change, no production
runtime change, no production provider-selection runtime behavior change, no
production package-capture/orchestrator behavior change, no Unit 12
implementation, and no Unit 12 opening.

This remediation plan performed no commit and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET
```
