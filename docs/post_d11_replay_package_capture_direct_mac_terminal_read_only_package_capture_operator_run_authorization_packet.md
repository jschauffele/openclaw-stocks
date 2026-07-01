# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Operator Run Authorization Packet

This packet authorizes exactly one future bounded LOCAL_MAC package-capture
operator run using the resolved command from the command-resolution retry
packet. It does not execute package capture, does not create `replay_packages`,
does not rerun `produce-read-only-artifacts`, does not modify produced
artifacts, and does not add `logs`, `run_reports`, `last_run_report.json`,
`replay_packages`, or `order_state.json` to git.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET` |
| `source_commit` | `db269ead5d981777f2e45397109e0c5a1259e6c4` |
| `local_head` | `db269ead5d981777f2e45397109e0c5a1259e6c4` |
| `origin_main` | `db269ead5d981777f2e45397109e0c5a1259e6c4` |
| `branch` | `main` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION` |
| `artifact_adjudication_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef` |
| `package_capture_authorization_commit` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b` |
| `command_surface_blocker_commit` | `42a72f0814b49c31500031e83e1c737cdee8c8a3` |
| `command_surface_remediation_commit` | `f2034397f862b5a44bad53d8dc36896e20d175d3` |
| `command_resolution_retry_commit` | `db269ead5d981777f2e45397109e0c5a1259e6c4` |
| `vps_validation` | `PASS_head_matches_expected_db269ea`; `PASS_head_origin_main_aligned`; `136 tests passed` |
| `operator_run_authorization_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET` |

## Authorized Future Operator Command

This packet authorizes only one later LOCAL_MAC operator attempt using this
command:

```sh
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator capture-local-read-only-package --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --artifact-runtime-commit ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea --expected-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --expected-last-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --authorize-direct-mac-terminal-read-only-package-capture
```

| Field | Value |
| --- | --- |
| `authorized_future_operator_command` | `.venv-312/bin/python -m tools.ops.gate_d_market_session_operator capture-local-read-only-package --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --artifact-runtime-commit ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea --expected-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --expected-last-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --authorize-direct-mac-terminal-read-only-package-capture` |
| `authorized_attempt_count` | `1` |
| `source_context` | `LOCAL_MAC_ONLY` |
| `operator_surface` | `DIRECT_MAC_TERMINAL` |
| `expected_commit_for_future_operator_run` | `db269ead5d981777f2e45397109e0c5a1259e6c4_UNLESS_SUPERSEDED_BY_LATER_PACKET` |
| `package_capture_execution_by_this_packet` | `false` |
| `replay_package_created_by_this_packet` | `false` |

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

## Future Operator-Run Boundaries

The future operator run must fail closed unless all of these conditions hold:

- LOCAL_MAC only.
- `EXPECTED_COMMIT` equals `db269ead5d981777f2e45397109e0c5a1259e6c4` unless a later packet supersedes it.
- HEAD, origin/main, and expected commit align.
- Worktree is clean before execution.
- The log, run report, and last run report hashes match exactly.
- The artifact runtime commit anchor matches `ac75080419e910c39f1a2683641a603f8a8999a1`.
- `replay_packages/post_d11_direct_mac_read_only_artifacts_001` is absent before execution.
- `order_state.json` is absent and is not read, written, required, or bound.
- The command does not use `--execution-mode vps`.
- The command does not use `--authorize-vps-package-write`.
- The command does not call `package_execution_orchestrator.main`.
- The command does not touch broker/account/order/execution state.
- The command does not modify source artifacts.
- The command does not add `logs`, `run_reports`, `last_run_report.json`, `replay_packages`, or `order_state.json` to git.

## Authorization Scope

| Boundary | Adjudication |
| --- | --- |
| `package_capture_operator_run_authorized` | `ONE_FUTURE_BOUNDED_LOCAL_MAC_ATTEMPT_ONLY` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_package_created_by_this_gate` | `false` |
| `produce_read_only_artifacts_rerun_by_this_gate` | `false` |
| `artifact_files_modified_by_this_gate` | `false` |
| `artifact_git_add_performed_by_this_gate` | `false` |
| `replay_authorized` | `false` |
| `scoring_authorized` | `false` |
| `candidate_generation_authorized` | `false` |
| `unit_12_authorized` | `false` |
| `broker_tws_api_network_runtime_action_authorized` | `false` |
| `vps_runtime_action_authorized` | `false` |
| `scheduler_service_systemd_timer_mutation_authorized` | `false` |
| `credential_env_mutation_authorized` | `false` |
| `strategy_risk_execution_behavior_change_authorized` | `false` |
| `provider_selection_or_broker_behavior_change_authorized` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND` |
| `commit_performed_by_this_gate` | `false` |
| `push_performed_by_this_gate` | `false` |

No package capture was executed by this packet. No replay package was created by
this packet. `replay_packages` remains absent. `order_state.json` remains
absent.

## Next Gate

The exact next permissible gate is:

`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET`

That next gate is the only gate that may perform the one bounded package-capture
operator attempt, and only if its fresh preflight still satisfies every
authorization boundary above.
