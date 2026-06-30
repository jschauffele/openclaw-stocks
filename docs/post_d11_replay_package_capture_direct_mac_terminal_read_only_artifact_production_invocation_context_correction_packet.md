# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Invocation Context Correction Packet

This is the source-controlled invocation-context correction packet for the
failed DIRECT_MAC_TERMINAL / LOCAL_MAC bounded read-only artifact-production
operator run.

The prior operator attempt failed before artifact production because direct
script invocation did not resolve the repo root `tools` package import. This
packet corrects only the future invocation shape by requiring module execution
from the repository root.

This packet is correction-only. It does not rerun `produce-read-only-artifacts`,
does not produce artifacts, does not authorize package capture, does not execute
replay, scoring, candidate generation, broker/TWS/API/network/runtime work, VPS
work, Unit 12 work, scheduler/service/systemd/timer work, credential/env work,
or live-trading/account/order/execution work.

Decision: ready for corrected operator command resolution.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET` |
| `source_commit` | `47968d8ad0bcc785f1cebb0653696883db2f4885` |
| `branch` | `main` |
| `local_head` | `47968d8ad0bcc785f1cebb0653696883db2f4885` |
| `origin_main` | `47968d8ad0bcc785f1cebb0653696883db2f4885` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET_FAILED_BEFORE_ARTIFACT_PRODUCTION_WITH_CONCRETE_BLOCKER` |
| `prior_concrete_blocker` | `DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT` |
| `vps_validation_head_matches_expected` | `PASS_head_matches_expected_47968d8` |
| `vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned` |
| `vps_validation_pytest` | `126 tests passed` |
| `invocation_context_correction_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET_READY_FOR_CORRECTED_OPERATOR_COMMAND_RESOLUTION` |
| `failed_invocation_shape` | `.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production` |
| `corrected_invocation_shape` | `.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production` |
| `authorized_run_id` | `post_d11_direct_mac_read_only_artifacts_001` |
| `expected_commit_resolution` | `EXPECTED_COMMIT="$(git rev-parse HEAD)"` |
| `final_command_block_requires_git_fetch_origin_main` | `true` |
| `final_command_block_requires_branch_main` | `true` |
| `final_command_block_requires_clean_worktree` | `true` |
| `final_command_block_requires_head_origin_alignment` | `true` |
| `produce_read_only_artifacts_rerun_by_this_gate` | `false` |
| `artifact_production_performed_by_this_gate` | `false` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `vps_action_by_this_gate` | `false` |
| `unit_12_action` | `false` |
| `production_code_changed_by_this_gate` | `false` |
| `command_surface_code_changed_by_this_gate` | `false` |
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
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET` |

## Correction Adjudication

The prior direct script invocation:

```text
.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production
```

failed before artifact production with:

```text
ModuleNotFoundError: No module named 'tools'
```

The corrected invocation shape is module execution from the repository root:

```text
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production
```

This correction does not authorize a rerun. It defines the command shape that a
later corrected operator command resolution packet may use.

## Required Final Command Block Shape

The later corrected command-resolution packet must preserve this fail-closed
command block shape:

```sh
git fetch origin main
test "$(git rev-parse --abbrev-ref HEAD)" = "main"
test -z "$(git status --short)"
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
EXPECTED_COMMIT="$(git rev-parse HEAD)"
test "$EXPECTED_COMMIT" = "$(git rev-parse origin/main)"
.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production
```

## Preserved Boundaries

This packet preserves:

- no `produce-read-only-artifacts` rerun;
- no runtime artifact production;
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
- no broker/TWS/API/network/runtime action;
- no VPS action or bounded VPS execution;
- no scheduler/service/systemd/timer mutation;
- no credential/env mutation;
- no strategy/risk/execution behavior change;
- no provider-selection or broker behavior change;
- no production code change;
- no command-surface code change.

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

## No Rerun Or Execution In This Gate

This invocation-context correction packet performed no rerun, no
`produce-read-only-artifacts` run, no artifact production, no package capture,
no replay, no scoring, no candidate generation, no broker/TWS/API/network/
runtime action, no VPS action, no Unit 12 action, no production code change, no
command-surface code change, no commit, and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET
```
