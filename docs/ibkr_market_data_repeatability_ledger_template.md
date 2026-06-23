# D11.22 IBKR Market-Data Repeatability Ledger Template

## Scope

This document is the source-controlled template for future local-only IBKR
read-only market-data repeatability diagnostics governed by D11.21.

It is a template and ledger shell with accepted repeatability evidence entries.
It does not authorize a diagnostic run and does not approve IBKR as primary
market-data provider.

## Current Status

| Field | Value |
| --- | --- |
| `ledger_status` | `active_repeatability_ledger` |
| `completed_repeatability_runs` | `2` |
| `invalidated_repeatability_runs` | `0` |
| `ibkr_provider_status` | `ibkr_market_data_candidate` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `replay` | `BLOCKED` |
| `scoring` | `BLOCKED` |
| `candidate_generation` | `BLOCKED` |
| `broker_api_authority` | `false` |
| `order_authority` | `false` |
| `execution_authority` | `false` |
| `vps_runtime` | `PARKED` |

## Planned Protocol

Minimum repeatability evidence before any later provider-approval review:

- at least 3 successful read-only diagnostic runs;
- at least 3 distinct regular-session trading days;
- symbols: AAPL, MSFT, NVDA, TSLA, MSTR;
- timeframe: 15Min;
- optional diagnostics dependency contract:
  `requirements-diagnostics.txt` / `ib_insync==0.9.86`;
- explicit local operator authorization for each run;
- TWS/Gateway manually open before each run;
- no VPS runtime, timer, service, package capture, replay, scoring, or
  candidate-generation activity during the diagnostic window.

## Required Evidence Fields Per Run

Each future diagnostic run record must include:

- run sequence number;
- diagnostic date;
- source commit;
- branch;
- worktree status before the run;
- worktree status after the run;
- local timestamp UTC;
- requested_start;
- requested_end;
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
- dependency_contract;
- dependency_version;
- confirmation that no account, position, margin, buying power, portfolio,
  order, balance, or execution query was performed.

## Completed Evidence Ledger

Run #1 is recorded from accepted D11.23 paste-back evidence only. No rerun was
performed for this ledger entry.

| Run | Date | Source Commit | Symbols | Timeframe | Classification | Countable | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-06-22 | b63d0d2d31b3023b07f7308c84e0ba2e4f38e931 | AAPL, MSFT, NVDA, TSLA, MSTR | 15Min | clean | true | completed |
| 2 | 2026-06-23 | 43057a4b2689da57a1f7a6517159eaf4109f83ca | AAPL, MSFT, NVDA, TSLA, MSTR | 15Min | clean | true | completed |

### Run 1 Ledger Entry

| Field | Value |
| --- | --- |
| `run_sequence_number` | `1` |
| `diagnostic_date` | `2026-06-22` |
| `run_command_timestamp_utc` | `2026-06-22T14:08:04Z` |
| `supplement_timestamp_utc` | `2026-06-22T14:13:54Z` |
| `source` | `LOCAL_MAC` |
| `branch` | `main` |
| `expected_source_commit` | `b63d0d2d31b3023b07f7308c84e0ba2e4f38e931` |
| `observed_head` | `b63d0d2d31b3023b07f7308c84e0ba2e4f38e931` |
| `worktree_status_before_run` | `clean` |
| `worktree_status_after_run` | `clean` |
| `supplement_worktree_status` | `0` |
| `dependency_contract` | `requirements-diagnostics.txt / ib_insync==0.9.86` |
| `observed_dependency` | `ib_insync==0.9.86` |
| `no_rerun_performed` | `true` |
| `vps_runtime` | `NOT_TOUCHED` |
| `timer_service` | `NOT_TOUCHED` |
| `package_capture` | `BLOCKED` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `command_used` | `.venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR --timeframe 15Min --requested-end 2026-06-22T14:00:00Z --lookback-minutes 120 --host 127.0.0.1 --port 7497 --client-id 9117 --exchange SMART --currency USD --sec-type STK --timeout-seconds 10 --authorize-local-ibkr-read-only-smoke` |
| `result_type` | `ibkr_local_read_only_market_data_smoke` |
| `provider_key` | `ibkr_market_data_candidate` |
| `provider_name` | `IBKR read-only market-data diagnostic candidate` |
| `connection_mode` | `local_read_only_smoke` |
| `read_only` | `true` |
| `symbols` | `AAPL, MSFT, NVDA, TSLA, MSTR` |
| `timeframe` | `15Min` |
| `requested_start` | `2026-06-22T12:00:00+00:00` |
| `requested_end` | `2026-06-22T14:00:00+00:00` |
| `latest_candle_timestamp` | `2026-06-22T13:45:00+00:00` |
| `lag_minutes` | `15.0` |
| `freshness_classification` | `clean` |
| `d11_countable` | `true` |
| `d11_primary_candidate_status` | `candidate` |
| `d11_primary_eligible` | `false` |
| `failure_reason` | `` |
| `broker_api_authority` | `false` |
| `order_authority` | `false` |
| `execution_authority` | `false` |
| `d11_completion_authority` | `false` |
| `replay` | `false` |
| `scoring` | `false` |
| `candidate_generation` | `false` |
| `package_capture_authority` | `false` |
| `account_position_margin_buying_power_portfolio_order_balance_execution_query` | `false` |

Run #1 preserves IBKR as candidate only. It does not approve IBKR as primary,
does not complete D11, does not open Unit 12, does not authorize package
capture, replay, scoring, candidate generation, broker/API work, account/
position/margin/buying-power/portfolio/order/balance/execution queries,
orders, execution, dependency installation, VPS mutation, runtime mutation,
systemd mutation, timer/service changes, or credential changes.

### Run 2 Ledger Entry

Run #2 is recorded from accepted D11.27 paste-back evidence adjudicated as
`ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW`. No diagnostic rerun was
performed for this ledger entry. The visually truncated final wrapper line is
not a defect: the accepted diagnostic JSON supplies
`unit_12_status=UNIT_12_BLOCKED`.

| Field | Value |
| --- | --- |
| `run_sequence_number` | `2` |
| `diagnostic_date` | `2026-06-23` |
| `run_command_timestamp_utc` | `2026-06-23T14:11:28Z` |
| `source` | `LOCAL_MAC` |
| `branch` | `main` |
| `expected_source_commit` | `43057a4b2689da57a1f7a6517159eaf4109f83ca` |
| `observed_head` | `43057a4b2689da57a1f7a6517159eaf4109f83ca` |
| `worktree_status_before_run` | `clean` |
| `worktree_status_after_run` | `clean` |
| `dependency_contract` | `requirements-diagnostics.txt / ib_insync==0.9.86` |
| `observed_dependency` | `ib_insync==0.9.86` |
| `no_rerun_performed` | `true` |
| `vps_runtime` | `NOT_TOUCHED` |
| `timer_service` | `NOT_TOUCHED` |
| `package_capture` | `BLOCKED` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `result_type` | `ibkr_local_read_only_market_data_smoke` |
| `provider_key` | `ibkr_market_data_candidate` |
| `provider_name` | `IBKR read-only market-data diagnostic candidate` |
| `connection_mode` | `local_read_only_smoke` |
| `read_only` | `true` |
| `symbols` | `AAPL, MSFT, NVDA, TSLA, MSTR` |
| `timeframe` | `15Min` |
| `requested_start` | `2026-06-23T12:00:00+00:00` |
| `requested_end` | `2026-06-23T14:00:00+00:00` |
| `latest_candle_timestamp` | `2026-06-23T13:45:00+00:00` |
| `lag_minutes` | `15.0` |
| `freshness_classification` | `clean` |
| `d11_countable` | `true` |
| `d11_primary_candidate_status` | `candidate` |
| `d11_primary_eligible` | `false` |
| `failure_reason` | `` |
| `broker_api_authority` | `false` |
| `order_authority` | `false` |
| `execution_authority` | `false` |
| `d11_completion_authority` | `false` |
| `replay` | `false` |
| `scoring` | `false` |
| `candidate_generation` | `false` |
| `package_capture_authority` | `false` |
| `account_position_margin_buying_power_portfolio_order_balance_execution_query` | `false` |

Run #2 preserves IBKR as candidate only. It does not approve IBKR as primary,
does not complete D11, does not open Unit 12, does not authorize package
capture, replay, scoring, candidate generation, broker/API work, account/
position/margin/buying-power/portfolio/order/balance/execution queries,
orders, execution, dependency installation, VPS mutation, runtime mutation,
systemd mutation, timer/service changes, or credential changes. Run #3 remains
future and pending until separately authorized and adjudicated.

## Invalidated Evidence Ledger

No invalidated future repeatability diagnostic runs are recorded here yet.

| Run | Date | Source Commit | Invalidated Reason | Stop Condition |
| --- | --- | --- | --- | --- |
| _none_ | _none_ | _none_ | _none_ | _none_ |

## Stop Conditions

Stop and do not count the run if any condition occurs:

- stale, recency-caveated, quarantined, missing, malformed, or non-UTC latest
  candle timestamp for any target symbol;
- any market-data warning;
- dirty worktree before or after the run;
- wrong branch or wrong source commit;
- missing optional diagnostic dependency or dependency-version mismatch;
- wrong session or missing explicit request window;
- failed focused test suite before the run;
- any account, position, margin, buying power, portfolio, order, balance, or
  execution query;
- any package capture, replay, scoring, candidate generation, Unit 12 opening,
  broker/API authority expansion, order authority, execution authority, VPS
  mutation, runtime mutation, timer/service mutation, or systemd mutation.

## Operator Runbook Template

This runbook is not an authorization to run diagnostics. A future prompt must
explicitly authorize the local read-only diagnostic before use.

Before any future authorized run:

1. Confirm the source-controlled approval prompt names this ledger template.
2. Confirm branch is `main`.
3. Confirm HEAD equals the explicitly authorized source commit.
4. Confirm worktree is clean.
5. Confirm the optional diagnostics dependency environment uses
   `requirements-diagnostics.txt` with `ib_insync==0.9.86`.
6. Confirm TWS/Gateway was manually opened by the operator.
7. Confirm no VPS runtime, timer, service, package capture, replay, scoring, or
   candidate-generation activity is authorized.
8. Confirm no account, position, margin, buying power, portfolio, order,
   balance, or execution query is authorized.

After any future authorized run:

1. Record every required evidence field for each symbol.
2. Confirm worktree remains clean.
3. Mark the run completed only if all symbols are clean and countable.
4. Mark the run invalidated if any stop condition occurs.
5. Do not change `d11_primary_eligible`, D11 status, Unit 12 status, package
   capture authority, replay authority, scoring authority, candidate-generation
   authority, broker authority, order authority, or execution authority.

## Final Provider-Approval Review Template

Provider approval remains a future separate review. The final review must not
start until this ledger contains at least 3 completed successful runs across at
least 3 distinct regular-session trading days.

The final review must explicitly decide whether the repeatability evidence is
sufficient for provider approval. It must remain separate from D11 sufficiency,
package inventory, candidate evidence, baseline-vs-candidate pairing, scoring,
Unit 12, broker/API authority, order authority, and execution authority.

## Non-Authorization

D11.22 does not complete D11, does not make IBKR a primary provider, does not
open Unit 12, and does not authorize package capture, replay, scoring,
candidate generation, broker/API work, account/position/margin/buying-power/
portfolio queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes.
