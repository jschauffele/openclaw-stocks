# Post-D11 Replay Package Capture LOCAL_MAC Command Surface Implementation Edit Packet

This is the bounded source-controlled implementation edit packet authorized by
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET`.

This packet records source-controlled implementation edits only. It does not
execute package capture, replay, scoring, candidate generation,
broker/TWS/API/network/runtime work, VPS work, scheduler/service/systemd/timer
work, credential or environment-file work, Unit 12 work, live-trading work, or
account/order/execution work.

Decision: the LOCAL_MAC command-surface implementation edit is complete and
ready for a later operator-run reauthorization packet.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET` |
| `source_commit` | `69d4a5232bfc4b8a8b3f37ed6210df24d90eaa48` |
| `design_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET` |
| `design_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET` |
| `implementation_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET_COMPLETED_READY_FOR_OPERATOR_RUN_REAUTHORIZATION_PACKET` |
| `local_mac_command_surface_added` | `capture-local` |
| `local_authorization_flag` | `--authorize-local-package-write` |
| `vps_authorization_flag_required_for_local_path` | `false` |
| `vps_authorization_flag_accepted_as_local_authority` | `false` |
| `delegates_through_execution_mode_vps` | `false` |
| `package_capture_executed` | `false` |
| `replay_executed` | `false` |
| `scoring_executed` | `false` |
| `candidate_generation_executed` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `vps_action` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_runtime_behavior_changed` | `false` |
| `strategy_risk_execution_behavior_changed` | `false` |
| `broker_behavior_changed` | `false` |
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
| `bounded_vps_execution` | `NOT_AUTHORIZED` |
| `vps_endpoint_approval` | `NOT_APPROVED` |
| `endpoint_18789_18791_approval` | `NOT_APPROVED` |
| `bridge_tunnel_proxy_approval` | `NOT_APPROVED` |
| `unit_12_implementation` | `NOT_OPENED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET` |

## Implementation Summary

`tools/ops/gate_d_market_session_operator.py` now exposes a distinct LOCAL_MAC
operator command surface:

```text
capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write
```

The command surface:

- requires `--run-id`;
- requires `--expected-commit`;
- requires `--authorize-local-package-write`;
- does not require `--authorize-vps-package-write`;
- does not accept `--authorize-vps-package-write` as LOCAL_MAC authority;
- does not delegate through `--execution-mode vps`;
- does not call `package_execution_orchestrator.main`;
- does not write packages;
- does not execute package capture.

The existing VPS `capture` path remains isolated and unchanged. The
authority-bearing `--authorize-vps-package-write` flag remains scoped to that
VPS path and is not accepted by `capture-local`.

## Artifact Fail-Closed Implementation

`capture-local` uses source-controlled fail-closed preflight checks only. It
fails closed unless all required checks pass, including:

- current branch is `main`;
- HEAD equals `--expected-commit`;
- worktree is clean;
- remote `origin/main` equals `--expected-commit`;
- root filesystem check passes through the existing operator check path;
- service/timer state checks pass through the existing operator check path;
- `run_id` is supplied;
- `run_id` is a safe path segment;
- `logs/<run_id>.jsonl` exists;
- `run_reports/<run_id>.json` or `last_run_report.json` exists;
- `replay_packages/<run_id>` is absent;
- capture readiness is reproved from already-existing artifacts;
- `--authorize-local-package-write` is supplied;
- VPS package-write authority is not used;
- `--execution-mode vps` is not used;
- `order_state_json=ABSENT_EXCLUDED_NOT_BOUND` is preserved.

The command creates no artifacts. It does not create `logs/`, `run_reports/`,
`replay_packages/`, `last_run_report.json`, `order_state.json`, or any package
artifact. It does not select `run_id` from absent artifacts. `replay_packages`
remains an output target only and is not proof of runtime artifact
availability.

If all preflight checks pass, the command reports:

```text
LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED
```

This classification is readiness for a later reauthorization packet only. It
is not package-capture authorization.

If any preflight check fails, the command reports:

```text
LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED
```

## Authority-Surface Implementation

LOCAL_MAC package writing is now separated from VPS package writing at the
operator command-surface level.

The LOCAL_MAC command has a distinct authorization flag:

```text
--authorize-local-package-write
```

The VPS flag remains authority-bearing:

```text
--authorize-vps-package-write
```

Bounded VPS execution remains `NOT_AUTHORIZED`. A future VPS path, if ever
used, still requires a separate explicit bounded VPS authorization gate.

Package capture execution remains `NOT_AUTHORIZED` until a later bounded
operator-run reauthorization gate explicitly authorizes it.

## Command-Surface Adjudication

The prior concrete blocker is remediated at the command-surface level:

```text
NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE
```

The new `capture-local` path is LOCAL_MAC-only and fail-closed. It does not use
the existing VPS `capture` delegation path. It performs no package capture in
this gate.

The exact next gate may authorize only a bounded LOCAL_MAC operator-run
reattempt with fail-closed preflight criteria.

## order_state Adjudication

`order_state` remains absent/excluded/not-bound:

```text
order_state_json=ABSENT_EXCLUDED_NOT_BOUND
```

This implementation does not read, write, create, bind, validate, infer, or
use `order_state`. It does not infer broker-visible order state and does not
use `order_state` to unblock package capture.

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
| Bounded VPS execution | `NOT_AUTHORIZED` |
| VPS endpoint approval | `NOT_APPROVED` |
| `18789` or `18791` endpoint approval | `NOT_APPROVED` |
| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |
| Unit 12 implementation | `NOT_OPENED` |

## No Execution Or Runtime Action

This implementation edit packet performed no package capture, no replay, no
scoring, no candidate generation, no broker/TWS/API/network/runtime action, no
VPS action, no IBKR connection, no TWS/Gateway inspection, no
service/systemd/scheduler/timer/runtime command, no credential or
environment-file access, no account, portfolio, balance, position, order,
execution, trade, P&L, margin, buying-power, or credential-data access, no
broker position action, no strategy behavior change, no risk behavior change,
no execution behavior change, no scheduler behavior change, no production
runtime change, no production provider-selection runtime behavior change, no
Unit 12 action, no Unit 12 implementation, and no Unit 12 opening.

This implementation edit packet performed no commit and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET
```

That gate may authorize only a bounded LOCAL_MAC operator-run reattempt with
fail-closed preflight criteria. Package capture remains `NOT_AUTHORIZED` until
that later gate explicitly authorizes it. Replay, scoring, candidate
generation, Unit 12, broker/TWS/API/network/runtime actions, and VPS actions
remain `NOT_AUTHORIZED`.
