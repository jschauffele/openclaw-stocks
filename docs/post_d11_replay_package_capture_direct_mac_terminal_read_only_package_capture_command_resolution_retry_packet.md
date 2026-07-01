# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Resolution Retry Packet

This packet retries package-capture command resolution after the LOCAL_MAC
read-only command surface remediation. It resolves the future operator-run
command only. It does not execute package capture, does not create
`replay_packages`, does not rerun `produce-read-only-artifacts`, does not modify
produced artifacts, and does not add `logs`, `run_reports`,
`last_run_report.json`, `replay_packages`, or `order_state.json` to git.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET` |
| `source_commit` | `f2034397f862b5a44bad53d8dc36896e20d175d3` |
| `local_head` | `f2034397f862b5a44bad53d8dc36896e20d175d3` |
| `origin_main` | `f2034397f862b5a44bad53d8dc36896e20d175d3` |
| `branch` | `main` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET_READY_FOR_COMMAND_RESOLUTION_RETRY` |
| `prior_blocker_commit` | `42a72f0814b49c31500031e83e1c737cdee8c8a3` |
| `authorization_packet_commit` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b` |
| `artifact_adjudication_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef` |
| `vps_validation` | `PASS_head_matches_expected_f203439`; `PASS_head_origin_main_aligned`; `135 tests passed` |
| `command_resolution_retry_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET` |

## Resolved Command

The remediated command surface resolves the future LOCAL_MAC operator-run
command as:

```sh
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator capture-local-read-only-package --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --artifact-runtime-commit ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea --expected-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --expected-last-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --authorize-direct-mac-terminal-read-only-package-capture
```

| Field | Value |
| --- | --- |
| `resolved_future_operator_command` | `.venv-312/bin/python -m tools.ops.gate_d_market_session_operator capture-local-read-only-package --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --artifact-runtime-commit ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea --expected-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --expected-last-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --authorize-direct-mac-terminal-read-only-package-capture` |
| `resolved_command_surface` | `capture-local-read-only-package` |
| `local_authorization_flag` | `--authorize-direct-mac-terminal-read-only-package-capture` |
| `supported_package_capture_command_resolved` | `true` |
| `package_capture_execution_authorized_by_this_packet` | `false` |
| `package_capture_executed_by_this_packet` | `false` |
| `replay_packages_created_by_this_packet` | `false` |

The resolved command does not include `--execution-mode vps`, does not include
`--authorize-vps-package-write`, does not invoke
`package_execution_orchestrator`, does not add broker/account/order/execution
authority, and does not bind `order_state.json`.

## Input Anchors

| Field | Value |
| --- | --- |
| `run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_path` | `last_run_report.json` |
| `last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_identity` | `BYTE_IDENTICAL_AND_HASH_IDENTICAL_TO_RUN_REPORT` |
| `expected_future_package_output_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001` |
| `replay_packages_current_state` | `ABSENT` |
| `order_state_json_current_state` | `ABSENT` |

## Boundaries

| Boundary | Adjudication |
| --- | --- |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_package_created_by_this_gate` | `false` |
| `produce_read_only_artifacts_rerun_by_this_gate` | `false` |
| `artifact_files_modified_by_this_gate` | `false` |
| `artifact_git_add_performed_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `unit_12_action_by_this_gate` | `false` |
| `broker_tws_api_network_runtime_action_by_this_gate` | `false` |
| `vps_action_by_this_gate` | `false` |
| `scheduler_service_systemd_timer_mutation` | `false` |
| `credential_env_mutation` | `false` |
| `strategy_risk_execution_behavior_change` | `false` |
| `provider_selection_or_broker_behavior_change` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND` |
| `commit_performed_by_this_gate` | `false` |
| `push_performed_by_this_gate` | `false` |

`replay_packages` remains absent. `order_state.json` remains absent. This
packet resolves the future command but does not execute it.

## Next Gate

The exact next permissible gate is:

`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET`

That gate may authorize a bounded future operator run. It must not infer
package-capture execution authority from this command-resolution retry packet.
