# D11.22 IBKR Market-Data Repeatability Ledger Template

## Scope

This document is the source-controlled template for future local-only IBKR
read-only market-data repeatability diagnostics governed by D11.21.

It is a template and ledger shell only. It does not record any completed future
diagnostic run, does not authorize a diagnostic run, and does not approve IBKR
as primary market-data provider.

## Current Status

| Field | Value |
| --- | --- |
| `ledger_status` | `template_only` |
| `completed_repeatability_runs` | `0` |
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

No future repeatability diagnostic runs are recorded here yet.

| Run | Date | Source Commit | Symbols | Timeframe | Classification | Countable | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| _none_ | _none_ | _none_ | _none_ | _none_ | _none_ | _none_ | _none_ |

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
