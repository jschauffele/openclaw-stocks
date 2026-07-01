# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Artifact Adjudication Packet

This is the source-controlled artifact adjudication packet for the
DIRECT_MAC_TERMINAL / LOCAL_MAC bounded read-only artifact-production artifacts
from run ID `post_d11_direct_mac_read_only_artifacts_001`.

The artifact existence checks, recorded SHA-256 checks, report alignment check,
absence checks, and read-only authority checks passed. The packet does not use
the clean passing decision because the required source-of-truth alignment check
did not pass: the produced artifact evidence records commit
`ac75080419e910c39f1a2683641a603f8a8999a1`, while this adjudication gate
requires expected-commit / actual-head / origin-main alignment to
`f65222c59a244f8a784565295f699001a0027ded`.

This packet is artifact adjudication only. It does not rerun
`produce-read-only-artifacts`, does not modify produced artifacts, does not add
produced artifacts to git, does not execute package capture, does not create
`replay_packages`, does not execute replay, scoring, candidate generation,
broker/TWS/API/network/runtime work, VPS work, Unit 12 work,
scheduler/service/systemd/timer work, credential/env work, or
live-trading/account/order/execution work.

Decision: blocked with a concrete source-of-truth alignment blocker.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET` |
| `source_commit` | `f65222c59a244f8a784565295f699001a0027ded` |
| `branch` | `main` |
| `local_head` | `f65222c59a244f8a784565295f699001a0027ded` |
| `origin_main` | `f65222c59a244f8a784565295f699001a0027ded` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET_COMPLETED_READ_ONLY_ARTIFACT_PRODUCTION` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_f65222c` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `129 tests passed` |
| `artifact_adjudication_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER` |
| `concrete_blocker` | `PRODUCED_ARTIFACT_COMMIT_ALIGNMENT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD` |
| `required_alignment_commit` | `f65222c59a244f8a784565295f699001a0027ded` |
| `observed_artifact_expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `observed_artifact_actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `observed_artifact_origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `commit_alignment_result` | `FAIL_REQUIRED_f65222c59a244f8a784565295f699001a0027ded_OBSERVED_ac75080419e910c39f1a2683641a603f8a8999a1` |
| `run_id_alignment` | `PASS_post_d11_direct_mac_read_only_artifacts_001` |
| `final_classification_alignment` | `PASS_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED` |
| `log_artifact_exists` | `true` |
| `log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `expected_log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `observed_log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `log_artifact_hash_result` | `PASS` |
| `run_report_artifact_exists` | `true` |
| `run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `expected_run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `observed_run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `run_report_artifact_hash_result` | `PASS` |
| `last_run_report_exists` | `true` |
| `last_run_report_path` | `last_run_report.json` |
| `expected_last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `observed_last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_hash_result` | `PASS` |
| `last_run_report_byte_identical_to_run_report` | `true` |
| `last_run_report_hash_identical_to_run_report` | `true` |
| `replay_packages_absence_result` | `PASS_ABSENT_replay_packages` |
| `order_state_absence_result` | `PASS_ABSENT_order_state.json` |
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
| `produce_read_only_artifacts_rerun_by_this_gate` | `false` |
| `artifact_files_modified_by_this_gate` | `false` |
| `artifact_git_add_performed_by_this_gate` | `false` |
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
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET` |

## Artifact Hash Adjudication

| Artifact | Expected SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` | `PASS` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `PASS` |
| `last_run_report.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `PASS` |

## Alignment Adjudication

| Check | Required | Observed | Result |
| --- | --- | --- | --- |
| `run_id` | `post_d11_direct_mac_read_only_artifacts_001` | `post_d11_direct_mac_read_only_artifacts_001` | `PASS` |
| `expected_commit` | `f65222c59a244f8a784565295f699001a0027ded` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `FAIL` |
| `actual_head` | `f65222c59a244f8a784565295f699001a0027ded` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `FAIL` |
| `origin_main` | `f65222c59a244f8a784565295f699001a0027ded` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `FAIL` |
| `final_classification` | `DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED` | `DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED` | `PASS` |

The passing clean adjudication decision is not used because source-of-truth
commit alignment failed.

## last_run_report Alignment

`last_run_report.json` is byte-identical and hash-identical to
`run_reports/post_d11_direct_mac_read_only_artifacts_001.json`.

## Absence Adjudication

| Artifact | Result |
| --- | --- |
| `replay_packages` | `PASS_ABSENT_replay_packages` |
| `order_state.json` | `PASS_ABSENT_order_state.json` |

## Authority Boundary Adjudication

| Authority | Status |
| --- | --- |
| Broker submit readiness | `NOT_APPROVED` |
| Live trading readiness | `NOT_APPROVED` |
| Account authority | `NONE` |
| Order authority | `NONE` |
| Execution authority | `NONE` |
| TWS/API/network runtime action | `false` |
| VPS action | `false` |
| Package capture executed | `false` |
| Replay executed | `false` |
| Scoring executed | `false` |
| Candidate generation executed | `false` |
| Unit 12 action | `false` |

## No Rerun Or Forbidden Execution In This Gate

This artifact adjudication packet performed no rerun, did not modify produced
artifacts, did not add produced artifacts to git, did not execute package
capture, did not create `replay_packages`, did not execute replay, scoring, or
candidate generation, did not perform broker/TWS/API/network/runtime action,
did not perform VPS action, did not perform Unit 12 action, did not change
production code, did not commit, and did not push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET
```
