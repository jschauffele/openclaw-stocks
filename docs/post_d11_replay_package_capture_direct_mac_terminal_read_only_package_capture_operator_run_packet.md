# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Operator Run Packet

This packet records the completed bounded LOCAL_MAC package-capture operator
run. It is a run-record/adjudication packet only. It does not rerun package
capture, does not rerun `produce-read-only-artifacts`, does not modify produced
artifacts, and does not add `logs`, `run_reports`, `last_run_report.json`,
`replay_packages`, or `order_state.json` to git.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET` |
| `source_commit` | `f0df62f029ded48418df401e7997e85a994d7b0c` |
| `local_head` | `f0df62f029ded48418df401e7997e85a994d7b0c` |
| `origin_main` | `f0df62f029ded48418df401e7997e85a994d7b0c` |
| `expected_commit` | `f0df62f029ded48418df401e7997e85a994d7b0c` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN` |
| `prior_authorization_packet_commit` | `f0df62f029ded48418df401e7997e85a994d7b0c` |
| `prior_vps_validation` | `PASS_head_matches_expected_f0df62f`; `PASS_head_origin_main_aligned`; `137 tests passed` |
| `operator_run_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET_PACKAGE_CAPTURE_COMPLETED` |
| `operator_stdout_final_classification` | `DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMPLETED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_ARTIFACT_ADJUDICATION_PACKET` |

## Operator Command

The operator run executed this LOCAL_MAC command:

```sh
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator capture-local-read-only-package --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --artifact-runtime-commit ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea --expected-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --expected-last-run-report-sha256 fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 --authorize-direct-mac-terminal-read-only-package-capture
```

## Preflight And Run Evidence

| Check | Result |
| --- | --- |
| `head_matches_expected` | `PASS_head_matches_expected` |
| `origin_main_matches_expected` | `PASS_origin_main_matches_expected` |
| `target_replay_package_absent_before_run` | `PASS_target_replay_package_absent` |
| `order_state_json_absent_before_run` | `PASS_order_state_json_absent` |
| `git_status_short_clean` | `PASS clean` |
| `log_artifact_exists` | `PASS` |
| `run_report_artifact_exists` | `PASS` |
| `last_run_report_artifact_exists` | `PASS` |
| `log_sha256_matches` | `PASS 7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_report_sha256_matches` | `PASS fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_sha256_matches` | `PASS fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_byte_identical_to_run_report` | `PASS BYTE_IDENTICAL` |
| `log_expected_commit_matches_artifact_runtime_commit` | `PASS ac75080419e910c39f1a2683641a603f8a8999a1` |
| `log_actual_head_matches_artifact_runtime_commit` | `PASS ac75080419e910c39f1a2683641a603f8a8999a1` |
| `run_report_expected_commit_matches_artifact_runtime_commit` | `PASS ac75080419e910c39f1a2683641a603f8a8999a1` |
| `run_report_origin_main_matches_artifact_runtime_commit` | `PASS ac75080419e910c39f1a2683641a603f8a8999a1` |
| `package_directory_absent_before_run` | `PASS` |
| `order_state_absent_excluded_not_bound` | `PASS order_state_json=ABSENT_EXCLUDED_NOT_BOUND` |

## Authority Boundary

| Field | Value |
| --- | --- |
| `source_context` | `LOCAL_MAC_ONLY` |
| `operator_surface` | `DIRECT_MAC_TERMINAL` |
| `read_only_package_capture_authority` | `true` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `tws_api_network_runtime_action` | `false` |
| `vps_action` | `false` |
| `replay_executed` | `false` |
| `scoring_executed` | `false` |
| `candidate_generation_executed` | `false` |
| `unit_12_action` | `false` |
| `order_state_bound` | `false` |
| `vps_package_write_authority_used` | `false` |
| `execution_mode_vps_used` | `false` |
| `package_capture_executed` | `true` |

## Package Artifact

| Field | Value |
| --- | --- |
| `replay_package_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001` |
| `manifest_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001/manifest.json` |
| `manifest_sha256` | `882b126344c818e3eacee4d6d8af6c9e289b922171d73534ce583559ed7ec694` |
| `post_run_inventory` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001/manifest.json` |
| `git_tracking_boundary` | `DO_NOT_ADD_REPLAY_PACKAGES_TO_GIT` |
| `generated_artifacts_git_tracked` | `false` |

The package artifact exists locally and must not be added to git.

## Manifest Schema Observations

| Field | Value |
| --- | --- |
| `manifest_top_level_keys` | `artifact_runtime_commit, authority, input_artifacts, package_capture, run_id` |
| `manifest_top_level_run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `manifest_top_level_final_classification` | `None` |
| `manifest_top_level_package_path` | `None` |
| `manifest_missing_top_level_final_classification_blocker` | `false` |
| `manifest_missing_top_level_package_path_blocker` | `false` |

The operator stdout final classification is the run classification:
`DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMPLETED`. The observed manifest
top-level `final_classification=None` and `package_path=None` are recorded as
schema facts only. They are not blockers because no inspected
source-controlled requirement requires those values as top-level manifest keys
for this packet.

## Source Artifact Stability

| Artifact | Post-run SHA-256 |
| --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |

Source artifacts remained hash-stable after the operator run.

## Post-Run Absence And Non-Actions

| Field | Value |
| --- | --- |
| `order_state_json_after_run` | `ABSENT` |
| `order_state_json_still_absent_after_run` | `PASS_order_state_json_still_absent` |
| `replay_package_git_add_performed_by_this_packet` | `false` |
| `artifact_modification_by_this_packet` | `false` |
| `artifact_git_add_performed_by_this_packet` | `false` |
| `package_capture_rerun_by_this_packet` | `false` |
| `produce_read_only_artifacts_rerun_by_this_packet` | `false` |
| `replay_executed_by_this_packet` | `false` |
| `scoring_executed_by_this_packet` | `false` |
| `candidate_generation_executed_by_this_packet` | `false` |
| `broker_tws_api_network_runtime_action_by_this_packet` | `false` |
| `vps_action_by_this_packet` | `false` |
| `unit_12_action_by_this_packet` | `false` |
| `commit_performed_by_this_packet` | `false` |
| `push_performed_by_this_packet` | `false` |

## Next Gate

The exact next permissible gate is:

`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_ARTIFACT_ADJUDICATION_PACKET`
