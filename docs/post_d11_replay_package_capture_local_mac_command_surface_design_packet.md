# Post-D11 Replay Package Capture LOCAL_MAC Command Surface Design Packet

This is the source-controlled design packet for the concrete blocker:

```text
NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE
```

This packet is design-only. It does not implement production command-surface
changes, execute package capture, replay, scoring, candidate generation,
broker/TWS/API/network/runtime work, VPS work, scheduler/service/systemd/timer
work, credential or environment-file work, Unit 12 work, live-trading work, or
account/order/execution work.

Decision: the LOCAL_MAC command-surface design is complete and ready for a
future implementation edit packet.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET` |
| `source_commit` | `e869845e47f3982b7c74b8151665616964d9af97` |
| `prior_edit_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET` |
| `prior_edit_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER` |
| `concrete_blocker` | `NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE` |
| `design_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET` |
| `local_mac_command_surface_design_completed` | `true` |
| `production_command_surface_changes_implemented` | `false` |
| `package_capture_executed` | `false` |
| `replay_executed` | `false` |
| `scoring_executed` | `false` |
| `candidate_generation_executed` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `vps_action` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_runtime_behavior_changed` | `false` |
| `production_package_capture_orchestrator_behavior_changed` | `false` |
| `unit_12_action` | `false` |
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
| `production_package_capture_orchestrator_behavior_changes_in_this_gate` | `NOT_AUTHORIZED` |
| `bounded_vps_execution` | `NOT_AUTHORIZED` |
| `vps_endpoint_approval` | `NOT_APPROVED` |
| `endpoint_18789_18791_approval` | `NOT_APPROVED` |
| `bridge_tunnel_proxy_approval` | `NOT_APPROVED` |
| `unit_12_implementation` | `NOT_OPENED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET` |

## Inspected Source Basis

The inspected operator source currently exposes a `capture` command that
requires:

```text
--authorize-vps-package-write
```

The same command delegates to:

```text
package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write
```

The inspected orchestrator supports `tmp_path_test` and `vps` execution modes.
`tmp_path_test` is programmatic and synthetic-test scoped. `vps` is
authority-bearing and targets governed VPS roots when authorized. No current
source exposes a safe LOCAL_MAC package-capture command surface.

## LOCAL_MAC Command-Surface Design

The safe LOCAL_MAC package-capture command surface must be distinct from the
VPS package-write surface.

The future implementation edit packet should introduce a source-controlled
LOCAL_MAC-only operator surface such as:

```text
capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write
```

Equivalent names are acceptable only if they preserve the same authority
separation:

- no `--authorize-vps-package-write` requirement for LOCAL_MAC package capture;
- no delegation through `--execution-mode vps`;
- no real `/opt` VPS reads or writes;
- no VPS endpoint approval;
- no `18789` or `18791`;
- no bridge, tunnel, or proxy;
- no broker/TWS/API/network/runtime action.

The LOCAL_MAC authorization surface must use a distinct local-only
authorization token. For this design, `--authorize-vps-package-write` remains
authority-bearing and must not be treated as legacy-only or non-authority-
bearing.

## LOCAL_MAC Package Writing Versus VPS Package Writing

LOCAL_MAC package writing and VPS package writing must remain separate
authority surfaces.

| Surface | Design status |
| --- | --- |
| LOCAL_MAC package writing | Future implementation may add a local-only command and local-only authorization flag, scoped to already-existing LOCAL_MAC artifacts and source-controlled output-path checks. |
| VPS package writing | Remains unauthorized here. Any future VPS path must require a separate bounded VPS execution gate before real `/opt` reads or writes. |
| Legacy flag treatment | `--authorize-vps-package-write` remains authority-bearing until a later implementation proves otherwise and source-controls the narrowing. |

## Avoiding `--execution-mode vps`

The future LOCAL_MAC package-capture path must not call:

```text
package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write
```

A future implementation edit packet may choose one of these designs:

| Option | Design requirement |
| --- | --- |
| Expose existing local execution mode | Allowed only if source inspection finds an existing non-synthetic local execution mode that reads already-existing LOCAL_MAC artifacts and writes only to an approved LOCAL_MAC package output path. |
| Add new local execution mode | Allowed if the edit is source-controlled, fail-closed, covered by tests, and does not change strategy, risk, execution, provider-selection, scheduler, runtime, service, systemd, timer, credential, or environment behavior. |
| Bypass VPS orchestration through a local-only package writer path | Allowed only if it uses already-approved reader/writer primitives, local-only path controls, already-existing artifact bytes, no order-state binding, and no runtime or broker action. |
| Block | Required if none of the above can be implemented without unacceptable behavior drift or production package-capture/orchestrator authority expansion. |

The implementation edit packet must prefer LOCAL_MAC command-surface
reconciliation over VPS authorization.

## Artifact Fail-Closed Design

Artifact-path remediation remains fail-closed and non-creating.

Any future LOCAL_MAC operator-run reauthorization or operator-run preflight
must fail closed unless all of these conditions are true:

- no artifact creation occurs;
- no `run_id` is selected from absent artifacts;
- explicit `run_id` is supplied;
- supplied `run_id` is a safe path segment;
- `logs/<run_id>.jsonl` exists;
- `run_reports/<run_id>.json` or `last_run_report.json` exists;
- the report is aligned to the selected `run_id`;
- the selected JSONL has a terminal completion event;
- D13 market-session eligibility is evaluated from already-existing artifacts;
- `replay_packages/<run_id>` is absent;
- `replay_packages` is treated as an output target only, not proof of runtime
  artifact availability;
- expected commit is checked;
- worktree is checked;
- no mixed `run_id`, stale report, path traversal, overwrite, future, leaked,
  or post-decision evidence appears.

The design prohibits creation of:

- `logs/`;
- `run_reports/`;
- `replay_packages/`;
- `last_run_report.json`;
- `order_state.json`;
- any package artifact.

## Authority-Surface Design

The future implementation must preserve these authority boundaries:

- `--authorize-vps-package-write` remains authority-bearing unless a later
  implementation proves and source-controls narrower semantics;
- bounded VPS execution remains `NOT_AUTHORIZED` unless a later bounded VPS
  execution gate explicitly authorizes it;
- package capture execution remains `NOT_AUTHORIZED` until a later bounded
  operator-run reauthorization gate explicitly authorizes it;
- replay, scoring, candidate generation, Unit 12, broker/TWS/API/network/
  runtime, and VPS actions remain not authorized.

## order_state Adjudication

`order_state` remains absent/excluded/not-bound:

```text
order_state_json=ABSENT_EXCLUDED_NOT_BOUND
```

The future implementation must not read, write, create, bind, validate, infer,
or use `order_state`. It must not infer broker-visible state and must not use
order-state absence or presence to unblock package capture.

## Future Implementation Allowed Scope

If later approved, the implementation edit packet may change only:

- operator command surface;
- local-only package-capture preflight gating;
- local-only package output path control;
- local-only tests and docs;
- local-only command naming or parser wiring required to separate LOCAL_MAC
  package writing from VPS package writing.

The next gate may implement only source-controlled LOCAL_MAC command-surface
changes and associated fail-closed tests/docs. It must not execute package
capture.

## Future Implementation Prohibited Scope

The future implementation edit packet must not change:

- strategy behavior;
- risk behavior;
- execution behavior;
- broker behavior;
- provider-selection runtime behavior;
- scheduler/runtime/service/systemd/timer behavior;
- credentials or environment files;
- Unit 12;
- replay behavior;
- scoring behavior;
- candidate-generation behavior;
- broker submit readiness;
- live trading readiness;
- account/order/execution authority;
- VPS endpoint approval;
- `18789` or `18791` approval;
- bridge, tunnel, or proxy approval.

Replay, scoring, and candidate-generation behavior remain prohibited unless
later separately authorized.

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
| Production package-capture/orchestrator behavior changes in this gate | `NOT_AUTHORIZED` |
| Bounded VPS execution | `NOT_AUTHORIZED` |
| VPS endpoint approval | `NOT_APPROVED` |
| `18789` or `18791` endpoint approval | `NOT_APPROVED` |
| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |
| Unit 12 implementation | `NOT_OPENED` |

## No Execution Or Runtime Action

This design packet performed no implementation, no package capture, no replay,
no scoring, no candidate generation, no broker/TWS/API/network/runtime action,
no VPS action, no IBKR connection, no TWS/Gateway inspection, no
service/systemd/scheduler/timer/runtime command, no credential or
environment-file access, no account, portfolio, balance, position, order,
execution, trade, P&L, margin, buying-power, or credential-data access, no
broker position action, no strategy behavior change, no risk behavior change,
no execution behavior change, no scheduler behavior change, no production
runtime change, no production provider-selection runtime behavior change, no
production package-capture/orchestrator behavior change, no Unit 12 action, no
Unit 12 implementation, and no Unit 12 opening.

This design packet performed no commit and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET
```

That gate may implement only source-controlled LOCAL_MAC command-surface
changes and associated fail-closed tests/docs. It must not execute package
capture. Package capture remains `NOT_AUTHORIZED` until a later bounded
operator-run reauthorization gate explicitly authorizes it. Replay, scoring,
candidate generation, Unit 12, broker/TWS/API/network/runtime actions, and VPS
actions remain not authorized.
