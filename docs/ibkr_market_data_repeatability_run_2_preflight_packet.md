# D11.27 IBKR Repeatability Run 2 Preflight Packet - Control Prep Only

## Scope

This packet prepares controls and evidence-capture fields for a future D11.27
repeatability run 2. It is preflight/control prep only. It is not the live diagnostic run. It is not authorization to run today.

Run #2 must occur on a distinct U.S. regular-session trading day after Run #1
(2026-06-22). The future run is `LOCAL_MAC` only. TWS/Gateway must be opened
manually by the operator before any separately authorized run. VPS runtime
remains parked. `openclaw.timer` and `openclaw.service` remain off. No VPS
command, runtime start, package capture, replay, scoring, candidate generation,
Unit 12, broker/API/account/order/execution expansion, or dependency
installation is authorized by this packet.

Run #3 remains future and pending. This packet creates no Run #3 ledger entry.

## Control Statements

- This packet is not the live diagnostic run.
- This packet is not authorization to run today.
- Run #2 must occur on a distinct U.S. regular-session trading day after Run #1.
- The future run is `LOCAL_MAC` only.
- TWS/Gateway must be opened manually by the operator.
- VPS runtime remains parked.
- `openclaw.timer` and `openclaw.service` remain off.

## Current Status Preserved

| Field | Value |
| --- | --- |
| `packet_status` | `preflight_control_prep_only` |
| `repeatability_run` | `planned_run_2` |
| `completed_repeatability_runs` | `1` |
| `invalidated_repeatability_runs` | `0` |
| `completed_run_1_only` | `true` |
| `run_2_completed` | `false` |
| `run_2_invalidated` | `false` |
| `ibkr_provider_status` | `ibkr_market_data_candidate` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `vps_runtime` | `PARKED` |

## Planned Run Window

The future run may be performed only during a separately authorized U.S. equity
regular-session window on a distinct trading day after Run #1. The target
diagnostic request must use an explicit UTC request window and must not rely on
implicit current-time defaults.

The operator must stop if the session is not a valid regular-session window for
the target symbols, if the day is not distinct from Run #1, or if the future
authorization does not explicitly approve Run #2.

## Expected Source Control

Before any future separately authorized Run #2:

- branch must be `main`;
- the future Run #2 authorization must supply the exact
  `EXPECTED_SOURCE_COMMIT`; this packet does not supply live-run commit
  authority;
- HEAD must equal that authorization-supplied `EXPECTED_SOURCE_COMMIT`;
- worktree must be clean before the run;
- worktree must remain clean after the run;
- the D11.22 ledger must still show `completed_repeatability_runs=1` and
  `invalidated_repeatability_runs=0`;
- Run #1 must remain the only completed repeatability run;
- Run #2 must not already be recorded as completed or invalidated.

### Historical Packet-Creation Context Only

`02339cba3239b9148ca352e2970cb658bdacc58a` was the source-of-truth commit
when this D11.27 packet was created. It is historical context only, not the
expected source commit for a future Run #2. Later control-only commits must not
make a separately authorized future run stale.

## Dependency Contract

Expected optional diagnostic dependency contract:

- file: `requirements-diagnostics.txt`;
- pin: `ib_insync==0.9.86`;
- no dependency installation is authorized by this packet.

## Focused No-Runtime Validation Before Future Run

Before a future authorized run, the operator should run the focused local test
suite without live broker connections:

```bash
.venv-312/bin/python -m pytest -q test_market_data_provider_boundary.py test_observability_payloads.py tests/test_offline_replay_mapper.py -k "market_data_provider_boundary or market_input_event_payload or d11_inventory_audit or package_capture_ledger"
```

Failure is a stop condition. Do not run the diagnostic after a failed focused
test suite without a separate review.

## Future Local-Only Diagnostic Command Template

This command is a template for a future separately authorized Run #2. Do not run
it from this packet alone.

```bash
.venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke \
  --symbol AAPL \
  --symbol MSFT \
  --symbol NVDA \
  --symbol TSLA \
  --symbol MSTR \
  --timeframe 15Min \
  --requested-end <UTC_REQUESTED_END_FOR_DISTINCT_RUN_2_DAY> \
  --lookback-minutes 120 \
  --host 127.0.0.1 \
  --port 7497 \
  --client-id 9117 \
  --exchange SMART \
  --currency USD \
  --sec-type STK \
  --timeout-seconds 10 \
  --authorize-local-ibkr-read-only-smoke
```

Target symbols: AAPL, MSFT, NVDA, TSLA, MSTR.

Target timeframe: 15Min.

## Future LOCAL_MAC-Only Operator Paste-Back Wrapper

Use this wrapper only after a future authorization explicitly supplies the
exact source commit in `EXPECTED_SOURCE_COMMIT`. Run it in the intended
`LOCAL_MAC` terminal only; do not copy it to a VPS terminal, shell session, or
automation host. It uses no heredoc and prints labeled evidence before and
after one diagnostic invocation. Any failed precheck is a stop condition and
must not be worked around by editing, rerunning, or adding terminal noise.

```bash
set -euo pipefail

EXPECTED_SOURCE_COMMIT='<EXACT_COMMIT_FROM_FUTURE_RUN_2_AUTHORIZATION>'
[[ -n "$EXPECTED_SOURCE_COMMIT" ]] || { echo 'missing authorization-supplied expected source commit' >&2; exit 1; }
[[ "$(git branch --show-current)" == 'main' ]] || { echo 'wrong branch' >&2; exit 1; }
[[ "$(git rev-parse HEAD)" == "$EXPECTED_SOURCE_COMMIT" ]] || { echo 'HEAD does not equal authorization-supplied expected source commit' >&2; exit 1; }
[[ -z "$(git status --porcelain=v1)" ]] || { echo 'dirty worktree before diagnostic' >&2; exit 1; }

DIAGNOSTIC_COMMAND=(
  .venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR
  --timeframe 15Min
  --requested-end '<UTC_REQUESTED_END_FOR_DISTINCT_RUN_2_DAY>'
  --lookback-minutes 120 --host 127.0.0.1 --port 7497 --client-id 9117
  --exchange SMART --currency USD --sec-type STK --timeout-seconds 10
  --authorize-local-ibkr-read-only-smoke
)

printf 'timestamp_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'expected_source_commit=%s\n' "$EXPECTED_SOURCE_COMMIT"
printf 'branch=%s\n' "$(git branch --show-current)"
printf 'head=%s\n' "$(git rev-parse HEAD)"
printf 'worktree_before=CLEAN\n'
printf 'dependency_contract=requirements-diagnostics.txt / ib_insync==0.9.86\n'
printf 'observed_dependency_version=%s\n' "$(.venv-312/bin/python -c 'import ib_insync; print(ib_insync.__version__)')"
printf 'command_used='
printf '%q ' "${DIAGNOSTIC_COMMAND[@]}"
printf '\n'
printf 'diagnostic_command=BEGIN\n'
"${DIAGNOSTIC_COMMAND[@]}"
printf 'diagnostic_command=END\n'
[[ -z "$(git status --porcelain=v1)" ]] || { echo 'dirty worktree after diagnostic' >&2; exit 1; }
printf 'worktree_after=CLEAN\n'
printf 'no_rerun_confirmation=true\n'
printf 'vps_runtime_timer_service_not_touched_confirmation=true\n'
printf 'package_capture=BLOCKED\n'
printf 'unit_12_status=UNIT_12_BLOCKED\n'
```

The diagnostic JSON between `diagnostic_command=BEGIN` and
`diagnostic_command=END`, together with the labeled wrapper output, is the
complete paste-back. It supplies each D11.28 review input, including the
per-symbol result fields, all authority fields, and the required no-query
confirmation from the diagnostic authority boundary. Do not add unrelated
commands, account queries, VPS commands, or a second diagnostic invocation.

## Required Paste-Back Fields

After a future separately authorized Run #2, paste back these fields for
review:

- timestamp UTC;
- expected source commit;
- branch;
- HEAD;
- worktree before;
- worktree after;
- dependency contract;
- observed dependency version;
- command used;
- requested_start;
- requested_end;
- result_type;
- provider_key;
- provider_name;
- connection_mode;
- read_only;
- symbol;
- timeframe;
- latest_candle_timestamp;
- lag_minutes;
- freshness_classification;
- d11_countable;
- d11_primary_candidate_status;
- d11_primary_eligible;
- failure_reason;
- package_capture;
- replay;
- scoring;
- candidate_generation;
- broker_api_authority;
- order_authority;
- execution_authority;
- d11_completion_authority;
- unit_12_status;
- authority_boundary;
- confirmation that no account, position, margin, buying power, portfolio,
  order, balance, or execution query occurred;
- confirmation that VPS runtime was not touched;
- confirmation that timer and service remained off.

## Stop Conditions / Invalidation Criteria

Stop and record an invalidation review, not a rerun-by-impulse, if any condition
occurs:

- stale, recency-caveated, quarantined, missing, malformed, or non-UTC latest
  candle timestamp for any target symbol;
- any warning;
- any missing target symbol;
- wrong branch or wrong head;
- dirty worktree before or after the run;
- missing explicit request window;
- dependency mismatch;
- wrong session or non-distinct trading day relative to Run #1;
- focused no-runtime test failure;
- any account, position, margin, buying power, portfolio, order, balance, or
  execution query;
- any package capture, replay, scoring, candidate generation, Unit 12 opening,
  broker/API authority expansion, order authority, execution authority, VPS
  mutation, runtime mutation, timer/service mutation, or systemd mutation.

## Post-Run Review Routing

If the future Run #2 is clean for every target symbol:

- next step: future Run #2 adjudication/ledger review;
- do not mark IBKR primary approved;
- do not mark D11 sufficient;
- do not open Unit 12;
- do not authorize runtime.

If the future Run #2 fails, is stale, is warning-bearing, or hits any stop
condition:

- next step: invalidated evidence review;
- do not rerun by impulse;
- do not mark IBKR primary approved;
- do not mark D11 sufficient;
- do not open Unit 12;
- do not authorize runtime.

Run #2 acceptance still does not approve IBKR as primary, does not complete D11,
does not open Unit 12, and does not authorize runtime.

## Non-Authorization

D11.27 explicitly preserves these ledger and authority facts:

- It does not record repeatability Run #2 as completed.
- It does not record repeatability Run #2 as invalidated.
- It does not mutate the D11.26 ledger completed or invalidated counts.
- It does not approve IBKR as primary.
- It does not complete D11.
- It does not open Unit 12.
- It does not authorize runtime, order, account, or execution authority.

D11.27 preflight-control prep does not run the diagnostic, does not complete
D11, does not make IBKR a primary provider, does not record repeatability Run #2
as completed, does not record repeatability Run #2 as invalidated, does not
mutate the D11.26 ledger completed or invalidated counts, does not open Unit 12,
and does not authorize package capture, replay, scoring, candidate generation,
broker/API work, account/position/margin/buying-power/portfolio/order/balance/
execution queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes.
