# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Runtime-Commit-Aligned Artifact Adjudication Packet

This is the source-controlled runtime-commit-aligned artifact adjudication
packet for the DIRECT_MAC_TERMINAL / LOCAL_MAC read-only artifact-production
artifacts from run ID `post_d11_direct_mac_read_only_artifacts_001`.

The corrected alignment rule from the prior remediation packet is applied:
artifact byte evidence must align to the artifact-production runtime commit
recorded in the artifact evidence, not to later documentation/adjudication
commits. Under that rule, the artifacts are adjudicated clean.

This packet is artifact adjudication only. It does not rerun
`produce-read-only-artifacts`, does not modify produced artifacts, does not add
`logs`, `run_reports`, `last_run_report.json`, `replay_packages`, or
`order_state.json` to git, does not execute package capture, does not create
`replay_packages`, does not execute replay, scoring, candidate generation,
broker/TWS/API/network/runtime work, VPS work, Unit 12 work,
scheduler/service/systemd/timer work, credential/env work, or
live-trading/account/order/execution work.

Decision: artifacts adjudicated clean under the runtime-commit-aligned rule.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET` |
| `source_commit` | `bf1ab29063e38b222946dff93cc7ea4c0b044409` |
| `branch` | `main` |
| `local_head` | `bf1ab29063e38b222946dff93cc7ea4c0b044409` |
| `origin_main` | `bf1ab29063e38b222946dff93cc7ea4c0b044409` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET_READY_FOR_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_RETRY` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_bf1ab29` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `131 tests passed` |
| `runtime_commit_aligned_artifact_adjudication_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET_ARTIFACTS_ADJUDICATED_CLEAN` |
| `corrected_alignment_rule_applied` | `true` |
| `alignment_rule` | `ARTIFACT_BYTES_ALIGN_TO_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_NOT_LATER_DOCUMENTATION_COMMITS` |
| `artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_runtime_commit_internal_alignment` | `PASS` |
| `documentation_lineage_commit_after_operator_run_packet` | `f65222c59a244f8a784565295f699001a0027ded` |
| `documentation_lineage_commit_blocked_adjudication_packet` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b` |
| `documentation_lineage_commit_alignment_remediation_packet` | `bf1ab29063e38b222946dff93cc7ea4c0b044409` |
| `documentation_lineage_commits_are_artifact_runtime_anchors` | `false` |
| `run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `run_id_alignment` | `PASS_post_d11_direct_mac_read_only_artifacts_001` |
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
| `produced_artifacts_added_to_git` | `false` |
| `package_capture_has_been_run` | `false` |
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
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET` |

## Corrected Alignment Rule Applied

The corrected rule is applied:

```text
Artifact byte evidence must align to the artifact-production runtime commit
recorded in the artifact evidence. Artifact byte evidence must not be required
to align to later documentation/adjudication commits.
```

The artifact runtime commit anchor is:

```text
ac75080419e910c39f1a2683641a603f8a8999a1
```

The documentation lineage commits are:

- `f65222c59a244f8a784565295f699001a0027ded`;
- `8191b9f7af769f734d77dc0a564ca74ae3b6286b`;
- `bf1ab29063e38b222946dff93cc7ea4c0b044409`.

These commits are documentation lineage commits, not artifact runtime anchors.

## Artifact Runtime Commit Alignment

| Runtime Evidence | Observed Value | Result |
| --- | --- | --- |
| Artifact `expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `PASS` |
| Artifact `actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `PASS` |
| Artifact `origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `PASS` |

## Artifact Hash Adjudication

| Artifact | Expected SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` | `PASS` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `PASS` |
| `last_run_report.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `PASS` |

## last_run_report Identity

`last_run_report.json` is byte-identical and hash-identical to
`run_reports/post_d11_direct_mac_read_only_artifacts_001.json`.

## Absence And Git Boundary Adjudication

| Check | Result |
| --- | --- |
| `replay_packages` | `PASS_ABSENT_replay_packages` |
| `order_state.json` | `PASS_ABSENT_order_state.json` |
| Produced artifacts added to git | `false` |

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

This runtime-commit-aligned artifact adjudication packet performed no rerun, did
not modify produced artifacts, did not add produced artifacts to git, did not
execute package capture, did not create `replay_packages`, did not execute
replay, scoring, or candidate generation, did not perform
broker/TWS/API/network/runtime action, did not perform VPS action, did not
perform Unit 12 action, did not change production code, did not commit, and did
not push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET
```
