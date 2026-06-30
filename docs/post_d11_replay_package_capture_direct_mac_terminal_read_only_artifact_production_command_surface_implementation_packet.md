# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Packet

This is the source-controlled implementation packet for the
DIRECT_MAC_TERMINAL read-only artifact production command surface designed by
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET`.

This gate implements the command surface only. It does not run the command,
produce artifacts, execute package capture, replay, scoring, candidate
generation, broker/TWS/API/network/runtime work, VPS work, Unit 12 work,
scheduler/service/systemd/timer work, credential/env work, or
live-trading/account/order/execution work.

Decision: the DIRECT_MAC_TERMINAL read-only artifact production command surface
implementation is ready for local diff review.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET` |
| `source_commit` | `71b2717d53ec71afc4a3bead1938a704b8be58b1` |
| `branch` | `main` |
| `local_head` | `71b2717d53ec71afc4a3bead1938a704b8be58b1` |
| `origin_main` | `71b2717d53ec71afc4a3bead1938a704b8be58b1` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET_READY_FOR_IMPLEMENTATION_GATE` |
| `implementation_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET_READY_FOR_LOCAL_DIFF_REVIEW` |
| `implemented_command_name` | `produce-read-only-artifacts` |
| `implemented_command_surface` | `.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production` |
| `required_flag_run_id` | `--run-id <run_id>` |
| `required_flag_expected_commit` | `--expected-commit <commit>` |
| `required_flag_authorization` | `--authorize-direct-mac-terminal-read-only-artifact-production` |
| `authorization_missing_fails_closed` | `true` |
| `head_expected_commit_check` | `IMPLEMENTED` |
| `local_head_origin_main_alignment_check` | `IMPLEMENTED` |
| `clean_worktree_check` | `IMPLEMENTED` |
| `local_mac_only_boundary` | `IMPLEMENTED` |
| `read_only_no_broker_no_order_no_execution_boundary` | `IMPLEMENTED` |
| `allowed_later_outputs` | `logs/<run_id>.jsonl; run_reports/<run_id>.json; last_run_report.json` |
| `prohibited_outputs` | `replay_packages/; order_state.json; broker/account/order/execution files; scheduler/service/timer/systemd files; credential/env files` |
| `deterministic_terminal_evidence` | `IMPLEMENTED` |
| `artifact_production_run_by_this_gate` | `false` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `vps_action` | `false` |
| `unit_12_action` | `false` |
| `commit_performed` | `false` |
| `push_performed` | `false` |
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
| `vps_action_authority` | `NOT_AUTHORIZED` |
| `bounded_vps_execution` | `NOT_AUTHORIZED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET` |

## Implemented Command Surface

The implemented command surface is:

```text
.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production
```

The command was added to `tools/ops/gate_d_market_session_operator.py` as
`produce-read-only-artifacts`. It requires:

- `--run-id <run_id>`;
- `--expected-commit <commit>`;
- `--authorize-direct-mac-terminal-read-only-artifact-production`.

The command surface does not accept package-capture authority as a substitute.
It does not use `capture-local`, does not delegate to
`package_execution_orchestrator.main`, and does not use `--execution-mode vps`.

## Fail-Closed Preflight

The implementation records and enforces fail-closed checks for:

- branch `main`;
- current LOCAL_MAC HEAD equals `--expected-commit`;
- local `origin/main` equals `--expected-commit`;
- LOCAL_MAC HEAD equals local `origin/main`;
- clean worktree before execution;
- safe concrete `run_id`;
- required authorization flag;
- LOCAL_MAC-only source context;
- DIRECT_MAC_TERMINAL operator surface;
- read-only/no-broker/no-order/no-execution authority boundary;
- absent `logs/<run_id>.jsonl` before write;
- absent `run_reports/<run_id>.json` before write;
- absent `last_run_report.json` before write;
- absent `replay_packages/<run_id>`;
- absent/excluded/not-bound `order_state.json`.

The command fails nonzero and prints
`DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FAILED_CLOSED` if any check
fails.

## Deterministic Terminal Evidence

The implemented command prints deterministic terminal evidence for:

- `RUN_ID`;
- `EXPECTED_COMMIT`;
- `ACTUAL_HEAD`;
- `ORIGIN_MAIN`;
- `ORIGIN_MAIN_ALIGNED`;
- `BRANCH`;
- `WORKTREE_CLEAN`;
- `STATUS_SHORT`;
- `SOURCE_CONTEXT=LOCAL_MAC_ONLY`;
- `OPERATOR_SURFACE=DIRECT_MAC_TERMINAL`;
- `READ_ONLY_AUTHORITY=true`;
- `BROKER_SUBMIT_READINESS=NOT_APPROVED`;
- `LIVE_TRADING_READINESS=NOT_APPROVED`;
- `ACCOUNT_AUTHORITY=NONE`;
- `ORDER_AUTHORITY=NONE`;
- `EXECUTION_AUTHORITY=NONE`;
- `TWS_API_NETWORK_RUNTIME_ACTION=false`;
- `VPS_ACTION=false`;
- `PACKAGE_CAPTURE_EXECUTED=false`;
- `REPLAY_EXECUTED=false`;
- `SCORING_EXECUTED=false`;
- `CANDIDATE_GENERATION_EXECUTED=false`;
- `UNIT_12_ACTION=false`;
- `ORDER_STATE_BOUND=false`;
- produced artifact paths and SHA-256 hashes if a later operator run succeeds.

## Allowed Later Outputs

If a later authorized operator run invokes the implemented command and all
fail-closed checks pass, the command may write only:

- `logs/<run_id>.jsonl`;
- `run_reports/<run_id>.json`;
- `last_run_report.json`.

This implementation gate did not invoke the command and did not create those
outputs.

## Prohibited Outputs And Authorities

The implementation prohibits:

- `replay_packages/`;
- `order_state.json`;
- broker/account/order/execution files;
- scheduler/service/timer/systemd files;
- credential/env files;
- package capture;
- replay;
- scoring;
- candidate generation;
- Unit 12;
- broker/TWS/API/network/runtime action;
- VPS action.

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
| VPS action | `NOT_AUTHORIZED` |
| Bounded VPS execution | `NOT_AUTHORIZED` |

## No Execution In This Gate

This implementation packet performed no artifact production, no package capture,
no replay, no scoring, no candidate generation, no
broker/TWS/API/network/runtime action, no VPS action, no Unit 12 action, no
commit, and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET
```
