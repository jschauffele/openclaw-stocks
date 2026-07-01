# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Artifact Alignment Remediation Packet

This is the source-controlled artifact-alignment remediation packet for the
blocked DIRECT_MAC_TERMINAL / LOCAL_MAC read-only artifact adjudication.

The prior adjudication blocked because it required produced artifact
expected-commit / actual-head / origin-main evidence to equal the then-current
documentation source-of-truth commit. That requirement would create an infinite
documentation-commit loop: every packet committed after artifact production
advances source control, while the artifact bytes remain correctly anchored to
the commit that produced them.

This packet remediates the alignment rule. Artifact byte evidence must align to
the artifact-production runtime commit recorded in the artifacts. Later
source-controlled packets are documentation/adjudication lineage commits and
must not be required to equal the artifact runtime commit.

This packet is alignment-rule remediation only. It does not rerun
`produce-read-only-artifacts`, does not modify produced artifacts, does not add
`logs`, `run_reports`, `last_run_report.json`, `replay_packages`, or
`order_state.json` to git, does not execute package capture, does not create
`replay_packages`, does not execute replay, scoring, candidate generation,
broker/TWS/API/network/runtime work, VPS work, Unit 12 work,
scheduler/service/systemd/timer work, credential/env work, or
live-trading/account/order/execution work.

Decision: ready for runtime-commit-aligned artifact adjudication retry.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET` |
| `source_commit` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b` |
| `branch` | `main` |
| `local_head` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b` |
| `origin_main` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER` |
| `prior_concrete_blocker` | `PRODUCED_ARTIFACT_COMMIT_ALIGNMENT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_8191b9f` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `130 tests passed` |
| `artifact_alignment_remediation_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET_READY_FOR_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_RETRY` |
| `remediated_alignment_rule` | `ARTIFACT_BYTES_ALIGN_TO_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_NOT_LATER_DOCUMENTATION_COMMITS` |
| `artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_expected_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_actual_head_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `artifact_origin_main_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| `corrected_operator_run_packet_commit` | `f65222c59a244f8a784565295f699001a0027ded` |
| `blocked_adjudication_packet_commit` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b` |
| `documentation_lineage_commits_are_artifact_runtime_anchors` | `false` |
| `run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `run_id_rule` | `MUST_MATCH_post_d11_direct_mac_read_only_artifacts_001` |
| `log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_path` | `last_run_report.json` |
| `last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report_alignment_rule` | `MUST_BE_BYTE_IDENTICAL_AND_HASH_IDENTICAL_TO_RUN_REPORT` |
| `replay_packages_rule` | `MUST_REMAIN_ABSENT` |
| `order_state_json_rule` | `MUST_REMAIN_ABSENT` |
| `artifact_git_add_rule` | `MUST_NOT_ADD_PRODUCED_ARTIFACTS_TO_GIT` |
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
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET` |

## Remediated Alignment Rule

The corrected artifact-alignment rule is:

```text
Artifact byte evidence must align to the artifact-production runtime commit
recorded in the artifact evidence, not to later documentation/adjudication
source-control commits.
```

For `post_d11_direct_mac_read_only_artifacts_001`, the runtime commit anchor is:

```text
ac75080419e910c39f1a2683641a603f8a8999a1
```

The retry adjudication must verify:

1. artifact hashes match the recorded hashes;
2. run ID matches `post_d11_direct_mac_read_only_artifacts_001`;
3. artifact `expected_commit`, `actual_head`, and `origin_main` are internally
   aligned to `ac75080419e910c39f1a2683641a603f8a8999a1`;
4. later packet commits `f65222c59a244f8a784565295f699001a0027ded` and
   `8191b9f7af769f734d77dc0a564ca74ae3b6286b` are documentation lineage
   commits, not artifact runtime anchors;
5. `replay_packages` remains absent;
6. `order_state.json` remains absent;
7. no produced artifacts are added to git.

## Artifact Runtime Commit Anchor

| Runtime Evidence | Required Value |
| --- | --- |
| Artifact production runtime commit | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| Artifact `expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| Artifact `actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1` |
| Artifact `origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1` |

## Documentation Lineage Commits

| Documentation Commit | Role |
| --- | --- |
| `f65222c59a244f8a784565295f699001a0027ded` | Corrected operator-run packet documentation/source-of-truth commit after runtime artifact production |
| `8191b9f7af769f734d77dc0a564ca74ae3b6286b` | Blocked artifact-adjudication packet documentation/source-of-truth commit |

These commits are documentation lineage commits. They are not artifact runtime
anchors and must not be required to equal artifact byte evidence.

## Artifact Hashes To Preserve

| Artifact | SHA-256 |
| --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |
| `last_run_report.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` |

## Preserved Boundaries

This packet preserves:

- no `produce-read-only-artifacts` rerun;
- no produced artifact modification;
- no produced artifact git-add;
- no package capture;
- no `replay_packages` creation;
- no replay;
- no scoring;
- no candidate generation;
- no Unit 12 action;
- no broker submit readiness;
- no live trading readiness;
- no account authority;
- no order authority;
- no execution authority;
- no broker/TWS/API/network/runtime action;
- no VPS runtime action;
- no scheduler/service/systemd/timer mutation;
- no credential/env mutation;
- no strategy/risk/execution behavior change;
- no provider-selection or broker behavior change;
- no production code change.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET
```
