# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Artifact Adjudication Packet

This packet adjudicates the local runtime-only replay package artifact produced
by the bounded LOCAL_MAC package-capture operator run. It does not modify the
package artifact, source artifacts, or generated runtime artifacts. It does not
add `replay_packages`, `logs`, `run_reports`, `last_run_report.json`, or
`order_state.json` to git.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_ARTIFACT_ADJUDICATION_PACKET` |
| `source_commit` | `7fa98bccd0c1390466f33d699503b4a21413fa26` |
| `local_head` | `7fa98bccd0c1390466f33d699503b4a21413fa26` |
| `origin_main` | `7fa98bccd0c1390466f33d699503b4a21413fa26` |
| `branch` | `main` |
| `head_origin_main_aligned` | `true` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET_PACKAGE_CAPTURE_COMPLETED` |
| `prior_operator_run_packet_commit` | `7fa98bccd0c1390466f33d699503b4a21413fa26` |
| `prior_vps_validation` | `PASS_HEAD_MATCHES_EXPECTED_7fa98bc`; `PASS_HEAD_ORIGIN_MAIN_ALIGNED`; `138 passed in 6.69s`; `PASS_DIFF_CHECK` |
| `fresh_local_precheck` | `PASS_HEAD_MATCHES_OPERATOR_RUN_PACKET_CLOSE`; `PASS_HEAD_ORIGIN_MAIN_ALIGNED`; `PASS_MANIFEST_EXISTS`; `PASS_ORDER_STATE_ABSENT`; `PASS_NO_ARTIFACTS_TRACKED` |
| `artifact_adjudication_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_ARTIFACT_ADJUDICATION_PACKET_ACCEPTED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_LEDGER_RECORD_PACKET` |

## Manifest Adjudication

| Field | Value |
| --- | --- |
| `manifest_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001/manifest.json` |
| `manifest_exists` | `true` |
| `manifest_sha256` | `882b126344c818e3eacee4d6d8af6c9e289b922171d73534ce583559ed7ec694` |
| `manifest_runtime_evidence_only` | `true` |
| `manifest_git_add_authorized` | `false` |
| `manifest_git_tracked` | `false` |

The manifest exists locally as runtime evidence only. It must not be added to
git by this packet.

## Manifest Schema Observations

| Field | Value |
| --- | --- |
| `manifest_top_level_keys` | `artifact_runtime_commit, authority, input_artifacts, package_capture, run_id` |
| `manifest_top_level_run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `manifest_top_level_final_classification` | `None` |
| `manifest_top_level_package_path` | `None` |
| `manifest_missing_top_level_final_classification_blocker` | `false` |
| `manifest_missing_top_level_package_path_blocker` | `false` |

The manifest top-level `final_classification=None` and `package_path=None` are
schema observations. They are not blockers for this adjudication because no
inspected source-controlled requirement explicitly requires top-level manifest
`final_classification` or top-level `package_path` for this local runtime-only
package-capture artifact.

## Source Artifact Hash Adjudication

| Artifact | SHA-256 | Adjudication |
| --- | --- | --- |
| `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea` | `MATCHES_OPERATOR_RUN_PACKET` |
| `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `MATCHES_OPERATOR_RUN_PACKET` |
| `last_run_report.json` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09` | `MATCHES_OPERATOR_RUN_PACKET` |

The source artifact hashes are stable and match the operator-run packet
evidence. The artifact runtime commit remains
`ac75080419e910c39f1a2683641a603f8a8999a1`.

## Git Tracking Boundary

| Path Family | Git Tracking Adjudication |
| --- | --- |
| `replay_packages` | `NOT_TRACKED_DO_NOT_ADD` |
| `logs` | `NOT_TRACKED_DO_NOT_ADD` |
| `run_reports` | `NOT_TRACKED_DO_NOT_ADD` |
| `last_run_report.json` | `NOT_TRACKED_DO_NOT_ADD` |
| `order_state.json` | `ABSENT_NOT_TRACKED_DO_NOT_ADD` |

`git ls-files replay_packages logs run_reports last_run_report.json
order_state.json` returned no tracked files. This packet does not authorize
artifact git-add.

## order_state Adjudication

| Field | Value |
| --- | --- |
| `order_state_json_absence_state` | `ABSENT` |
| `order_state_bound` | `false` |
| `order_state_read_authorized` | `false` |
| `order_state_write_authorized` | `false` |
| `order_state_git_add_authorized` | `false` |

`order_state.json` remains absent and unbound.

## Negative Authority

| Authority | Adjudication |
| --- | --- |
| `artifact_modification_by_this_packet` | `false` |
| `artifact_git_add_performed_by_this_packet` | `false` |
| `replay_package_git_add_performed_by_this_packet` | `false` |
| `package_capture_rerun_by_this_packet` | `false` |
| `produce_read_only_artifacts_rerun_by_this_packet` | `false` |
| `replay_authorized_by_this_packet` | `false` |
| `scoring_authorized_by_this_packet` | `false` |
| `candidate_generation_authorized_by_this_packet` | `false` |
| `broker_action_authorized_by_this_packet` | `false` |
| `tws_action_authorized_by_this_packet` | `false` |
| `runtime_action_authorized_by_this_packet` | `false` |
| `vps_action_authorized_by_this_packet` | `false` |
| `unit_12_action_authorized_by_this_packet` | `false` |
| `order_submission_authorized_by_this_packet` | `false` |
| `order_cancellation_authorized_by_this_packet` | `false` |
| `cleanup_flatten_sell_authorized_by_this_packet` | `false` |
| `scheduler_systemd_action_authorized_by_this_packet` | `false` |
| `credential_mutation_authorized_by_this_packet` | `false` |
| `strategy_risk_execution_behavior_change_authorized_by_this_packet` | `false` |
| `provider_selection_or_broker_behavior_change_authorized_by_this_packet` | `false` |
| `commit_performed_by_this_packet` | `false` |
| `push_performed_by_this_packet` | `false` |

## Adjudication Result

All required artifact adjudication checks passed. The local runtime-only package
manifest exists, the manifest hash matches, source artifact hashes remain stable,
`order_state.json` remains absent, and no generated artifacts are tracked.

The exact next permissible gate is:

`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_LEDGER_RECORD_PACKET`
