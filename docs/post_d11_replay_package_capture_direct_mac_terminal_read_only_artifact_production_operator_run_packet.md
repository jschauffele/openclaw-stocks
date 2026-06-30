# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Packet

This is the source-controlled run-record/adjudication packet for the attempted
DIRECT_MAC_TERMINAL / LOCAL_MAC bounded read-only artifact-production operator
run.

The operator attempted the authorized command, but the run failed before
artifact production because direct script invocation did not resolve the repo
root `tools` package import.

This packet is run-record/adjudication only. It does not authorize a rerun,
does not rerun `produce-read-only-artifacts`, does not change production code,
does not change command invocation, does not produce artifacts, does not execute
package capture, replay, scoring, candidate generation, broker/TWS/API/network/
runtime work, VPS work, Unit 12 work, scheduler/service/systemd/timer work,
credential/env work, or live-trading/account/order/execution work.

Decision: failed before artifact production with a concrete blocker.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET` |
| `source_commit` | `9de2ae86961fce1602895d0caa96063ed7dc2f27` |
| `branch` | `main` |
| `local_head` | `9de2ae86961fce1602895d0caa96063ed7dc2f27` |
| `origin_main` | `9de2ae86961fce1602895d0caa96063ed7dc2f27` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_OPERATOR_RUN` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_9de2ae8` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `125 tests passed` |
| `operator_run_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET_FAILED_BEFORE_ARTIFACT_PRODUCTION_WITH_CONCRETE_BLOCKER` |
| `concrete_blocker` | `DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT` |
| `attempted_run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `runtime_resolved_expected_commit` | `9de2ae86961fce1602895d0caa96063ed7dc2f27` |
| `attempted_command` | `.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production` |
| `observed_exception_type` | `ModuleNotFoundError` |
| `observed_exception_message` | `No module named 'tools'` |
| `failed_before_artifact_production` | `true` |
| `rerun_authorized_by_this_packet` | `false` |
| `production_code_changed_by_this_packet` | `false` |
| `command_invocation_changed_by_this_packet` | `false` |
| `log_artifact_status` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl=ABSENT` |
| `run_report_artifact_status` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json=ABSENT` |
| `last_run_report_status` | `last_run_report.json=ABSENT` |
| `replay_packages_status` | `replay_packages=ABSENT` |
| `order_state_status` | `order_state.json=ABSENT` |
| `produce_read_only_artifacts_rerun_by_this_gate` | `false` |
| `artifact_production_performed_by_this_gate` | `false` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `vps_action_by_this_gate` | `false` |
| `unit_12_action` | `false` |
| `commit_performed_by_this_gate` | `false` |
| `push_performed_by_this_gate` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `package_capture_execution` | `NOT_AUTHORIZED` |
| `runtime_artifact_production_execution_in_this_gate` | `NOT_PERFORMED` |
| `replay_execution` | `NOT_AUTHORIZED` |
| `scoring_execution` | `NOT_AUTHORIZED` |
| `candidate_generation_execution` | `NOT_AUTHORIZED` |
| `unit_12_implementation` | `NOT_OPENED` |
| `vps_action_authority` | `NOT_AUTHORIZED_BY_THIS_GATE` |
| `bounded_vps_execution` | `NOT_AUTHORIZED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET` |

## Operator Attempt Evidence

The operator attempted:

```text
.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production
```

The runtime-resolved `EXPECTED_COMMIT` was:

```text
9de2ae86961fce1602895d0caa96063ed7dc2f27
```

The observed traceback was:

```text
Traceback:
  File "/Users/openclawcontrol/Documents/openclaw-stocks/tools/ops/gate_d_market_session_operator.py", line 21, in <module>
    from tools.replay import capture_eligibility_guard
ModuleNotFoundError: No module named 'tools'
```

## Concrete Blocker

The concrete blocker is:

```text
DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT
```

The attempt failed before artifact production. This packet does not correct the
invocation context and does not authorize a rerun.

## Artifact Inventory After Failed Attempt

| Artifact | Status |
| --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `ABSENT` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `ABSENT` |
| `last_run_report.json` | `ABSENT` |
| `replay_packages` | `ABSENT` |
| `order_state.json` | `ABSENT` |

## No Rerun Or Execution In This Gate

This operator-run packet performed no rerun, no `produce-read-only-artifacts`
run, no artifact production, no package capture, no replay, no scoring, no
candidate generation, no broker/TWS/API/network/runtime action, no VPS action,
no Unit 12 action, no production code change, no command invocation change, no
commit, and no push.

## Still-Unapproved Authorities

| Authority | Status |
| --- | --- |
| Broker submit readiness | `NOT_APPROVED` |
| Live trading readiness | `NOT_APPROVED` |
| Account authority | `NONE` |
| Order authority | `NONE` |
| Execution authority | `NONE` |
| Runtime artifact production execution in this gate | `NOT_PERFORMED` |
| Package capture execution | `NOT_AUTHORIZED` |
| Replay execution | `NOT_AUTHORIZED` |
| Scoring execution | `NOT_AUTHORIZED` |
| Candidate generation execution | `NOT_AUTHORIZED` |
| Unit 12 implementation | `NOT_OPENED` |
| VPS action by this gate | `NOT_AUTHORIZED` |
| Bounded VPS execution | `NOT_AUTHORIZED` |

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET
```
