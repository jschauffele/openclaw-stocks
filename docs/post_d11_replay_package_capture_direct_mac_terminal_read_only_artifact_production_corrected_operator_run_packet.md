# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Corrected Operator Run Packet

This is the source-controlled run-record/adjudication packet for the corrected
DIRECT_MAC_TERMINAL / LOCAL_MAC bounded read-only artifact-production operator
run.

The corrected operator run used module execution from the repository root and
completed read-only artifact production for the single authorized run ID
`post_d11_direct_mac_read_only_artifacts_001`.

This packet is run-record/adjudication only. It does not rerun
`produce-read-only-artifacts`, does not execute package capture, does not
execute replay, scoring, candidate generation, broker/TWS/API/network/runtime
work, VPS work, Unit 12 work, scheduler/service/systemd/timer work,
credential/env work, or live-trading/account/order/execution work.

Decision: completed read-only artifact production.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET` |
| `source_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `branch` | `main` |
| `local_head` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_CORRECTED_OPERATOR_RUN` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_ac75080` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `128 tests passed` |
| `corrected_operator_run_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET_COMPLETED_READ_ONLY_ARTIFACT_PRODUCTION` |
| `run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `origin_main_observed` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `origin_main_aligned` | `true` |
| `status_short` | `clean` |
| `source_context` | `LOCAL_MAC_ONLY` |
| `operator_surface` | `DIRECT_MAC_TERMINAL` |
| `read_only_authority` | `true` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `tws_api_network_runtime_action` | `false` |
| `vps_action` | `false` |
| `package_capture_executed` | `false` |
| `replay_executed` | `false` |
| `scoring_executed` | `false` |
| `candidate_generation_executed` | `false` |
| `unit_12_action` | `false` |
| `order_state_bound` | `false` |
| `operator_run_final_classification` | `DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED` |
| `produce_read_only_artifacts_rerun_by_this_gate` | `false` |
| `artifact_production_performed_by_this_packet` | `false` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `broker_tws_api_network_runtime_action_by_this_gate` | `false` |
| `vps_action_by_this_gate` | `false` |
| `unit_12_action_by_this_gate` | `false` |
| `scheduler_service_systemd_timer_mutation` | `false` |
| `credential_env_mutation` | `false` |
| `strategy_risk_execution_behavior_change` | `false` |
| `provider_selection_or_broker_behavior_change` | `false` |
| `production_code_changed_by_this_gate` | `false` |
| `commit_performed_by_this_gate` | `false` |
| `push_performed_by_this_gate` | `false` |
| `log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_path` | `last_run_report.json` |
| `last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `post_run_log_artifact_inventory` | `PRESENT_logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `post_run_run_report_inventory` | `PRESENT_run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `post_run_last_run_report_inventory` | `PRESENT_last_run_report.json` |
| `post_run_replay_packages_inventory` | `ABSENT_replay_packages` |
| `post_run_order_state_inventory` | `ABSENT_order_state.json` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET` |

## Corrected Operator Run Command

The corrected operator run used this command shape:

```sh
git fetch origin main
test "$(git rev-parse --abbrev-ref HEAD)" = "main"
test -z "$(git status --short)"
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
EXPECTED_COMMIT="$(git rev-parse HEAD)"
test "$EXPECTED_COMMIT" = "$(git rev-parse origin/main)"
echo "EXPECTED_COMMIT=$EXPECTED_COMMIT"
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production
```

## Observed Run Evidence

| Evidence | Value |
| --- | --- |
| `RUN_ID` | `post_d11_direct_mac_read_only_artifacts_001` |
| `EXPECTED_COMMIT` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `ACTUAL_HEAD` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `ORIGIN_MAIN` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `ORIGIN_MAIN_ALIGNED` | `true` |
| `BRANCH` | `main` |
| `WORKTREE_CLEAN` | `true` |
| `STATUS_SHORT` | `clean` |
| `SOURCE_CONTEXT` | `LOCAL_MAC_ONLY` |
| `OPERATOR_SURFACE` | `DIRECT_MAC_TERMINAL` |
| `READ_ONLY_AUTHORITY` | `true` |
| `BROKER_SUBMIT_READINESS` | `NOT_APPROVED` |
| `LIVE_TRADING_READINESS` | `NOT_APPROVED` |
| `ACCOUNT_AUTHORITY` | `NONE` |
| `ORDER_AUTHORITY` | `NONE` |
| `EXECUTION_AUTHORITY` | `NONE` |
| `TWS_API_NETWORK_RUNTIME_ACTION` | `false` |
| `VPS_ACTION` | `false` |
| `PACKAGE_CAPTURE_EXECUTED` | `false` |
| `REPLAY_EXECUTED` | `false` |
| `SCORING_EXECUTED` | `false` |
| `CANDIDATE_GENERATION_EXECUTED` | `false` |
| `UNIT_12_ACTION` | `false` |
| `ORDER_STATE_BOUND` | `false` |
| `FINAL_CLASSIFICATION` | `DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED` |

## Produced Artifacts

| Artifact | Status | SHA-256 |
| --- | --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `PRESENT` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `PRESENT` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report.json` | `PRESENT` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |

## Post-Run Artifact Inventory

| Artifact | Status |
| --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `PRESENT_logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `PRESENT_run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `last_run_report.json` | `PRESENT_last_run_report.json` |
| `replay_packages` | `ABSENT_replay_packages` |
| `order_state.json` | `ABSENT_order_state.json` |

## Preserved Boundaries

This packet preserves:

- no rerun by this packet;
- no package capture;
- no replay;
- no scoring;
- no candidate generation;
- no Unit 12 action;
- no broker submit readiness;
- no live trading readiness;
- no account authority;
- no order authority;
- no execution authority;
- no broker/TWS/API/network/runtime action by this packet;
- no VPS runtime action;
- no scheduler/service/systemd/timer mutation;
- no credential/env mutation;
- no strategy/risk/execution behavior change;
- no provider-selection or broker behavior change;
- no production code change.

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
| Unit 12 implementation | `NOT_OPENED` |
| VPS action by this packet | `NOT_AUTHORIZED` |
| Bounded VPS execution | `NOT_AUTHORIZED` |

## No Rerun Or Forbidden Execution In This Gate

This corrected operator-run packet performed no rerun, no package capture, no
replay, no scoring, no candidate generation, no broker/TWS/API/network/runtime
action, no VPS action, no Unit 12 action, no production code change, no commit,
and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET
```
