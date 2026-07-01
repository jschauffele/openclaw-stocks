# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Surface Remediation Packet

This packet records the source-controlled remediation of the missing LOCAL_MAC
read-only package-capture command surface. It does not execute package capture,
does not create `replay_packages`, does not rerun `produce-read-only-artifacts`,
does not modify produced artifacts, and does not add `logs`, `run_reports`,
`last_run_report.json`, `replay_packages`, or `order_state.json` to git.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET` |
| `source_commit` | `42a72f0814b49c31500031e83e1c737cdee8c8a3` |
| `local_head` | `42a72f0814b49c31500031e83e1c737cdee8c8a3` |
| `origin_main` | `42a72f0814b49c31500031e83e1c737cdee8c8a3` |
| `branch` | `main` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER` |
| `prior_concrete_blocker` | `NO_SUPPORTED_LOCAL_MAC_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE` |
| `vps_validation` | `PASS_head_matches_expected_42a72f0`; `PASS_head_origin_main_aligned`; `134 tests passed` |
| `remediation_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET_READY_FOR_COMMAND_RESOLUTION_RETRY` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET` |

## Remediated Command Surface

The remediation adds the LOCAL_MAC-only package-capture command surface below:

```sh
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator capture-local-read-only-package --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --artifact-runtime-commit ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea --expected-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --expected-last-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --authorize-direct-mac-terminal-read-only-package-capture
```

| Field | Value |
| --- | --- |
| `remediated_command_surface` | `capture-local-read-only-package` |
| `local_authorization_flag` | `--authorize-direct-mac-terminal-read-only-package-capture` |
| `vps_authorization_flag_accepted` | `false` |
| `execution_mode_vps_used` | `false` |
| `package_execution_orchestrator_main_delegation` | `false` |
| `supported_package_capture_command_resolved` | `true` |
| `future_expected_package_output_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_packages_created_by_this_gate` | `false` |

The command is LOCAL_MAC only. It does not delegate through `--execution-mode
vps`, does not call `package_execution_orchestrator.main`, and does not require,
accept, or reinterpret `--authorize-vps-package-write`. That VPS flag remains
authority-bearing for the legacy VPS surface only.

The command surface validates already-adjudicated read-only artifacts before a
later authorized operator run can write a bounded local replay package. The
command must fail closed unless the requested `run_id`, source commit,
artifact-runtime commit, artifact hashes, `replay_packages/<run_id>` absence,
and `order_state.json` absence are all satisfied.

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
| `replay_packages_current_state` | `ABSENT` |
| `order_state_json_current_state` | `ABSENT` |

## Boundary Adjudication

| Boundary | Adjudication |
| --- | --- |
| `source_artifact_mutation` | `PROHIBITED` |
| `artifact_git_add` | `PROHIBITED` |
| `order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND` |
| `order_state_read_write_require_bind` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `broker_tws_api_network_runtime_action_by_this_gate` | `false` |
| `vps_action_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `unit_12_action_by_this_gate` | `false` |
| `scheduler_service_systemd_timer_mutation` | `false` |
| `credential_env_mutation` | `false` |
| `strategy_risk_execution_behavior_change` | `false` |
| `provider_selection_or_broker_behavior_change` | `false` |
| `commit_performed_by_this_gate` | `false` |
| `push_performed_by_this_gate` | `false` |

No package capture was executed in this packet. No replay package was created.
`replay_packages` remains absent. `order_state.json` remains absent. The
previously produced artifacts were not modified and were not added to git.

## Command Resolution Retry

The exact next permissible gate is:

`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET`

That gate may retry command resolution against this remediated source surface.
It must still not execute package capture unless a later bounded operator-run
gate explicitly authorizes execution.
