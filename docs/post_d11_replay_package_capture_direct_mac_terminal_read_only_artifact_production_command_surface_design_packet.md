# Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Design Packet

This is the source-controlled design packet for the concrete blocker:

```text
NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED
```

The prior blocker packet recorded that the prior symbolic operator step
`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN` had no exact
executable Direct Mac Terminal command. This packet designs the required command
surface only. It does not implement the command.

Decision: the DIRECT_MAC_TERMINAL read-only artifact production command surface
design is ready for a later implementation gate.

| Field | Value |
| --- | --- |
| `classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET` |
| `source_commit` | `e9a10ff406d46a77417af50800155cb8f057d4b7` |
| `branch` | `main` |
| `local_head` | `e9a10ff406d46a77417af50800155cb8f057d4b7` |
| `origin_main` | `e9a10ff406d46a77417af50800155cb8f057d4b7` |
| `worktree` | `clean` |
| `prior_packet` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET` |
| `prior_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER` |
| `prior_concrete_blocker` | `NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED` |
| `design_decision` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET_READY_FOR_IMPLEMENTATION_GATE` |
| `exact_proposed_command_name` | `produce-read-only-artifacts` |
| `exact_proposed_command_shape` | `.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production` |
| `required_flag_run_id` | `--run-id <run_id>` |
| `required_flag_expected_commit` | `--expected-commit <commit>` |
| `required_flag_authorization` | `--authorize-direct-mac-terminal-read-only-artifact-production` |
| `local_mac_only_boundary` | `REQUIRED` |
| `direct_mac_terminal_boundary` | `REQUIRED` |
| `clean_worktree_required` | `true` |
| `expected_commit_verification_required` | `true` |
| `read_only_no_broker_no_order_no_execution_boundary` | `REQUIRED` |
| `allowed_outputs` | `logs/<run_id>.jsonl; run_reports/<run_id>.json` |
| `prohibited_outputs` | `replay_packages/<run_id>; last_run_report.json unless separately authorized; order_state.json; package capture artifacts; replay output; scoring output; candidate-generation output; Unit 12 output` |
| `implementation_performed_by_this_gate` | `false` |
| `artifact_production_performed_by_this_gate` | `false` |
| `package_capture_executed_by_this_gate` | `false` |
| `replay_executed_by_this_gate` | `false` |
| `scoring_executed_by_this_gate` | `false` |
| `candidate_generation_executed_by_this_gate` | `false` |
| `broker_tws_api_network_runtime_action` | `false` |
| `vps_action` | `false` |
| `unit_12_action` | `false` |
| `production_code_changed` | `false` |
| `command_surface_code_changed` | `false` |
| `commit_performed` | `false` |
| `push_performed` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_authority` | `NONE` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `package_capture_execution` | `NOT_AUTHORIZED` |
| `runtime_artifact_production_execution` | `NOT_AUTHORIZED_BY_THIS_DESIGN_GATE` |
| `replay_execution` | `NOT_AUTHORIZED` |
| `scoring_execution` | `NOT_AUTHORIZED` |
| `candidate_generation_execution` | `NOT_AUTHORIZED` |
| `unit_12_implementation` | `NOT_OPENED` |
| `vps_action_authority` | `NOT_AUTHORIZED` |
| `bounded_vps_execution` | `NOT_AUTHORIZED` |
| `production_code_changes` | `BLOCKED_BY_THIS_GATE` |
| `command_surface_code_changes` | `DESIGNED_ONLY_NOT_IMPLEMENTED` |
| `package_writer_reader_orchestrator_changes` | `BLOCKED` |
| `next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET` |

## Exact Proposed Command Surface

The intended future command shape is:

```text
.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production
```

The command name is:

```text
produce-read-only-artifacts
```

The required flags are:

- `--run-id <run_id>`;
- `--expected-commit <commit>`;
- `--authorize-direct-mac-terminal-read-only-artifact-production`.

The future implementation must not treat `capture-local` as this command.
`capture-local` remains package-capture related and artifact-dependent.

## Expected Commit And Worktree Verification

The future implementation must fail closed unless:

- the branch is `main`;
- LOCAL_MAC HEAD equals `origin/main`;
- `--expected-commit` equals the current LOCAL_MAC HEAD;
- `--expected-commit` equals `origin/main`;
- the worktree is clean;
- the supplied `run_id` is safe and concrete;
- no conflicting artifact target already exists for the same `run_id`.

The future implementation must record the resolved branch, LOCAL_MAC HEAD,
`origin/main`, expected commit, status-short result, and run ID in its evidence.

## LOCAL_MAC And Direct Mac Terminal Boundary

The designed command surface is LOCAL_MAC-only and DIRECT_MAC_TERMINAL-only. It
must not perform VPS action, must not require or accept VPS authorization flags,
must not use endpoint `18789` or `18791`, must not use a bridge, tunnel, or
proxy, and must not delegate to a VPS execution path.

## Read-Only Authority Boundary

The designed command surface is limited to read-only runtime artifact
production. It must not authorize:

- broker submit readiness;
- live trading readiness;
- account authority;
- order authority;
- execution authority;
- position, portfolio, balance, margin, buying-power, trade, P&L, or credential
  access;
- order placement, modification, cancellation, routing, flattening, selling, or
  cleanup;
- package capture;
- replay;
- scoring;
- candidate generation;
- Unit 12.

## Allowed Outputs

The future implementation may be designed to produce only these local runtime
artifact outputs for the supplied `run_id`:

- `logs/<run_id>.jsonl`;
- `run_reports/<run_id>.json`.

Those outputs must contain enough evidence for a later package-capture
preflight to determine run ID alignment, commit alignment, terminal completion,
and read-only authority preservation.

## Prohibited Outputs

The future implementation must not produce:

- `replay_packages/<run_id>`;
- package capture artifacts;
- replay output;
- scoring output;
- candidate-generation output;
- Unit 12 output;
- `order_state.json`;
- broker/account/order/execution artifacts;
- credential or environment files;
- scheduler, service, systemd, timer, or runtime mutation artifacts;
- `last_run_report.json` unless a later source-controlled gate separately
  authorizes that compatibility output.

## Evidence Required From The Later Implementation Gate

The later implementation gate must record:

- the exact command parser entry added or exposed;
- the exact required flags;
- parser behavior proving missing required flags fail closed;
- parser behavior proving package-capture flags are not accepted as authority;
- source checks proving no package capture path is invoked;
- source checks proving no replay, scoring, candidate generation, Unit 12, VPS,
  broker, account, order, or execution path is invoked;
- tests proving expected commit and clean worktree checks are enforced;
- tests proving allowed outputs are constrained to `logs/<run_id>.jsonl` and
  `run_reports/<run_id>.json`;
- tests proving `order_state.json` is not read, written, created, bound,
  validated, inferred, or used.

## Fail-Closed Conditions

The future command must fail closed if:

- branch is not `main`;
- LOCAL_MAC HEAD does not equal `origin/main`;
- `--expected-commit` does not equal LOCAL_MAC HEAD and `origin/main`;
- the worktree is dirty;
- `--run-id` is absent or unsafe;
- `--authorize-direct-mac-terminal-read-only-artifact-production` is absent;
- a package-capture authorization flag is supplied as a substitute;
- any broker, order, execution, account, credential, VPS, replay, scoring,
  candidate-generation, Unit 12, scheduler, service, systemd, timer, or package
  capture authority is required;
- an output target is ambiguous or would overwrite existing governed evidence;
- `order_state.json` would be read, written, created, bound, validated,
  inferred, or used.

## Still-Unapproved Authorities

| Authority | Status |
| --- | --- |
| Broker submit readiness | `NOT_APPROVED` |
| Live trading readiness | `NOT_APPROVED` |
| Account authority | `NONE` |
| Order authority | `NONE` |
| Execution authority | `NONE` |
| Runtime artifact production execution | `NOT_AUTHORIZED_BY_THIS_DESIGN_GATE` |
| Package capture execution | `NOT_AUTHORIZED` |
| Replay execution | `NOT_AUTHORIZED` |
| Scoring execution | `NOT_AUTHORIZED` |
| Candidate generation execution | `NOT_AUTHORIZED` |
| Unit 12 implementation | `NOT_OPENED` |
| VPS action | `NOT_AUTHORIZED` |
| Bounded VPS execution | `NOT_AUTHORIZED` |
| Production code changes | `BLOCKED_BY_THIS_GATE` |
| Command-surface code changes | `DESIGNED_ONLY_NOT_IMPLEMENTED` |
| Package writer/reader/orchestrator changes | `BLOCKED` |

## No Implementation Or Execution

This command-surface design packet performed no implementation, no artifact
production, no package capture, no replay, no scoring, no candidate generation,
no broker/TWS/API/network/runtime action, no VPS action, no Unit 12 action, no
production code change, no command-surface code change, and no package
writer/reader/orchestrator change.

This command-surface design packet performed no commit and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET
```
