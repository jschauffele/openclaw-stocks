# D11.23 IBKR Repeatability Run 1 Preflight Packet - Control Prep Only

## Scope

This packet prepares controls and evidence-capture fields for a future D11.23
repeatability run 1. It is preflight/control prep only. It is not the live diagnostic run. It is not authorization to run immediately, and is not authorization to run outside a valid U.S. regular-session window.

The future run is `LOCAL_MAC` only. TWS/Gateway must be opened manually by the
operator before any separately authorized run. VPS runtime remains parked.
`openclaw.timer` and `openclaw.service` remain off. No VPS command, runtime
start, package capture, replay, scoring, candidate generation, Unit 12,
broker/API/account/order/execution expansion, or dependency installation is
authorized by this packet.

## Current Status Preserved

| Field | Value |
| --- | --- |
| `packet_status` | `preflight_control_prep_only` |
| `repeatability_run` | `planned_run_1` |
| `completed_repeatability_runs` | `0` |
| `invalidated_repeatability_runs` | `0` |
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
regular-session window. The target diagnostic request must use an explicit UTC
request window and must not rely on implicit current-time defaults.

The operator must stop if the session is not a valid regular-session window for
the target symbols.

## Expected Source Control

Before any future separately authorized run:

- branch must be `main`;
- HEAD must equal the source commit authorized by the future run prompt;
- worktree must be clean before the run;
- worktree must remain clean after the run;
- the D11.22 ledger must still show `completed_repeatability_runs=0` and
  `invalidated_repeatability_runs=0` before run 1 is recorded.

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

This command is a template for a future separately authorized run. Do not run it
from this packet alone.

```bash
.venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke \
  --symbol AAPL \
  --symbol MSFT \
  --symbol NVDA \
  --symbol TSLA \
  --symbol MSTR \
  --timeframe 15Min \
  --requested-end <UTC_REQUESTED_END> \
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

## Required Paste-Back Fields

After a future separately authorized run, paste back these fields for review:

- timestamp UTC;
- branch;
- HEAD;
- expected source commit;
- worktree status before run;
- worktree status after run;
- dependency contract and observed dependency version;
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
  order, balance, or execution query was performed;
- confirmation that VPS runtime was not touched;
- confirmation that timer and service remained off.

## Stop Conditions / Invalidation Criteria

Stop and record an invalidation review, not a rerun-by-impulse, if any condition
occurs:

- stale, recency-caveated, quarantined, missing, malformed, or non-UTC latest
  candle timestamp for any target symbol;
- any market-data warning;
- dirty worktree before or after the run;
- wrong branch or wrong source commit;
- missing optional diagnostic dependency or dependency-version mismatch;
- wrong session or missing explicit request window;
- focused no-runtime test failure;
- any account, position, margin, buying power, portfolio, order, balance, or
  execution query;
- any package capture, replay, scoring, candidate generation, Unit 12 opening,
  broker/API authority expansion, order authority, execution authority, VPS
  mutation, runtime mutation, timer/service mutation, or systemd mutation.

## Post-Run Review Routing

If the future run is clean for every target symbol:

- next step: D11.24 ledger recording review;
- do not mark IBKR primary approved;
- do not mark D11 sufficient;
- do not open Unit 12.

If the future run fails, is stale, is warning-bearing, or hits any stop
condition:

- next step: invalidated evidence review;
- do not rerun by impulse;
- do not mark IBKR primary approved;
- do not mark D11 sufficient;
- do not open Unit 12.

## Non-Authorization

D11.23 preflight-control prep does not complete D11, does not make IBKR a
primary provider, does not record repeatability run 1 as completed, does not mutate the D11.22 ledger counts, does not open Unit 12, and does not authorize package capture, replay, scoring, candidate generation, broker/API work,
account/position/margin/buying-power/portfolio queries, orders, execution,
dependency installation, VPS mutation, runtime mutation, systemd mutation,
timer/service changes, or credential changes.
