# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Authorization Correction Packet

This is the source-controlled correction packet for the expected-commit blocker:

```text
AUTHORIZED_EXPECTED_COMMIT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD
```

The prior expected-commit adjudication packet blocked the operator run because
the authorized command used expected commit
`dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`, while the then-current
source-of-truth HEAD was `44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`.

This correction packet does not hardcode the current pre-correction commit as
the final operator-run expected commit. The later operator run must resolve its
expected commit only after this correction packet is committed, pushed, and
VPS-validated. That resolved commit must be the final validated source-of-truth
HEAD after this correction packet.

This packet is authorization-correction only. It does not run
`produce-read-only-artifacts`, does not produce artifacts, does not execute
package capture, replay, scoring, candidate generation, broker/TWS/API/network/
runtime work, VPS work, Unit 12 work, scheduler/service/systemd/timer work,
credential/env work, or live-trading/account/order/execution work.

Decision: ready for final operator command resolution.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET` |
| `source_commit` | `6894dcfd62bbfc25a1627e8f7c27089d28fba5a6` |
| `branch` | `main` |
| `local_head` | `6894dcfd62bbfc25a1627e8f7c27089d28fba5a6` |
| `origin_main` | `6894dcfd62bbfc25a1627e8f7c27089d28fba5a6` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET_BLOCKED_PENDING_CORRECTED_OPERATOR_RUN_AUTHORIZATION` |
| `prior_concrete_blocker` | `AUTHORIZED_EXPECTED_COMMIT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_6894dcf` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `123 tests passed` |
| `authorization_correction_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET_READY_FOR_FINAL_OPERATOR_COMMAND_RESOLUTION` |
| `authorized_future_attempt_count` | `1` |
| `authorized_source_context` | `LOCAL_MAC_ONLY` |
| `authorized_operator_surface` | `DIRECT_MAC_TERMINAL` |
| `authorized_run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `corrected_expected_commit_binding` | `FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET` |
| `pre_correction_commit_not_final_expected_commit` | `true` |
| `corrected_command_shape` | `.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit <FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET> --authorize-direct-mac-terminal-read-only-artifact-production` |
| `expected_commit_must_equal_local_head_at_operator_run` | `true` |
| `expected_commit_must_equal_origin_main_at_operator_run` | `true` |
| `clean_worktree_required_before_operator_run` | `true` |
| `allowed_later_output_log` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` |
| `allowed_later_output_run_report` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json` |
| `allowed_later_output_last_run_report` | `last_run_report.json` |
| `prohibited_outputs` | `replay_packages/; order_state.json; broker/account/order/execution files; scheduler/service/timer/systemd files; credential/env files` |
| `produce_read_only_artifacts_run_by_this_gate` | `false` |
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
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET` |

## Corrected Command Shape

The corrected command shape is:

```text
.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit <FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET> --authorize-direct-mac-terminal-read-only-artifact-production
```

The placeholder must be resolved only after this correction packet is committed,
pushed, and VPS-validated. The final operator command resolution packet must
replace the placeholder with the final validated source-of-truth HEAD after this
correction packet.

## Corrected Authorization Boundaries

The later operator run remains limited to exactly one attempt and must preserve:

- LOCAL_MAC only;
- DIRECT_MAC_TERMINAL only;
- expected commit equals LOCAL_MAC HEAD at the time of the operator run;
- expected commit equals `origin/main` at the time of the operator run;
- clean worktree before the operator run;
- read-only boundary relative to broker/account/order/execution authority;
- no broker submit readiness;
- no live trading readiness;
- no account authority;
- no order authority;
- no execution authority;
- no TWS/API/network runtime action;
- no VPS runtime action;
- no scheduler/systemd/timer/service mutation;
- no credential/env mutation;
- no production provider-selection changes;
- no production broker behavior changes;
- no strategy/risk/execution changes;
- no package capture;
- no replay;
- no scoring;
- no candidate generation;
- no Unit 12.

## Allowed Later Outputs

Only the later operator run may create:

- `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`;
- `run_reports/post_d11_direct_mac_read_only_artifacts_001.json`;
- `last_run_report.json`.

This correction packet did not create those outputs.

## Prohibited Outputs

The later operator run must not create:

- `replay_packages/`;
- `order_state.json`;
- broker/account/order/execution files;
- scheduler/service/timer/systemd files;
- credential/env files.

## No Execution In This Gate

This correction packet performed no `produce-read-only-artifacts` run, no
artifact production, no package capture, no replay, no scoring, no candidate
generation, no broker/TWS/API/network/runtime action, no VPS action, no Unit 12
action, no commit, and no push.

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
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET
```
