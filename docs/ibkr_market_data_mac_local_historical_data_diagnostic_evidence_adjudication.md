# D11.57 Mac-Local Historical Market-Data Diagnostic Evidence Adjudication

## Scope and Adjudication Status

D11.57 is a source-controlled adjudication of the operator-provided D11.56
Mac-local historical market-data-only diagnostic evidence. It does not run
another diagnostic, does not inspect endpoints, does not run VPS proof, does
not connect to IBKR/TWS/Gateway, does not import broker API code, does not
approve IBKR as primary, does not complete D11, and does not unblock Unit 12.

| Field | Value |
| --- | --- |
| `classification` | `MAC_LOCAL_HISTORICAL_MARKET_DATA_DIAGNOSTIC_EVIDENCE_ADJUDICATION` |
| `source_commit` | `5fa8a8e221b79219c86eb3abcd67ad491692de21` |
| `d11_56_vps_validation` | `76 passed in 2.49s` |
| `diagnostic_date` | `2026-06-26` |
| `authorized_utc` | `2026-06-26T14:00:00Z` |
| `observed_run_utc` | `2026-06-26T14:00:26Z` |
| `diagnostic_window_guard` | `PASSED` |
| `selected_mac_local_endpoint` | `127.0.0.1:7497` |
| `selected_endpoint_context` | `LOCAL_MAC` |
| `selected_endpoint_type` | `TWS_PAPER` |
| `selected_endpoint_port` | `7497` |
| `observed_listener` | `TCP *:7497 (LISTEN)` |
| `observed_dependency_python` | `3.12.13` |
| `observed_dependency_ib_insync` | `0.9.86` |
| `symbols` | `AAPL,MSFT,NVDA,TSLA,MSTR` |
| `timeframe` | `15Min` |
| `requested_start_utc` | `2026-06-26T12:00:00+00:00` |
| `requested_end_utc` | `2026-06-26T14:00:00+00:00` |
| `worktree_before` | `CLEAN` |
| `worktree_after` | `CLEAN` |
| `all_symbols_d11_countable` | `true` |
| `all_symbols_freshness_classification` | `clean` |
| `d11_primary_candidate_status` | `candidate` |
| `d11_primary_eligible` | `false` |
| `mac_local_historical_diagnostic_evidence` | `ACCEPTED` |
| `vps_market_test_authorized` | `false` |
| `account_order_execution_authority` | `false` |
| `package_capture` | `BLOCKED` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

## Evidence Timing and Context

The adjudicated diagnostic evidence records
`observed_source_commit=5fa8a8e221b79219c86eb3abcd67ad491692de21` and D11.56
VPS validation `76 passed in 2.49s`. The diagnostic ran at
`2026-06-26T14:00:26Z`, after the authorized
`2026-06-26T14:00:00Z` boundary, and the diagnostic-window guard passed.

The evidence is `LOCAL_MAC` only. The selected endpoint was
`127.0.0.1:7497`, classified as `TWS_PAPER` and valid only for the
`LOCAL_MAC` process context. The observed listener was
`JavaAppli PID 1525 user openclawcontrol` with `TCP *:7497 (LISTEN)`.

This does not validate VPS `127.0.0.1:7497`. The prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

## Diagnostic Command Evidence

The adjudicated operator command was:

```bash
.venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR --timeframe 15Min --requested-end 2026-06-26T14:00:00Z --lookback-minutes 120 --host 127.0.0.1 --port 7497 --client-id 9117 --exchange SMART --currency USD --sec-type STK --timeout-seconds 10 --authorize-local-ibkr-read-only-smoke
```

Requested window:

- `requested_start_utc=2026-06-26T12:00:00+00:00`
- `requested_end_utc=2026-06-26T14:00:00+00:00`

## Per-Symbol Evidence

| Symbol | `d11_countable` | `freshness_classification` | `latest_candle_timestamp` | `lag_minutes` | `d11_primary_candidate_status` | `d11_primary_eligible` | `failure_reason` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AAPL` | `true` | `clean` | `2026-06-26T13:30:00+00:00` | `30.0` | `candidate` | `false` | _empty_ |
| `MSFT` | `true` | `clean` | `2026-06-26T13:30:00+00:00` | `30.0` | `candidate` | `false` | _empty_ |
| `NVDA` | `true` | `clean` | `2026-06-26T13:45:00+00:00` | `15.0` | `candidate` | `false` | _empty_ |
| `TSLA` | `true` | `clean` | `2026-06-26T13:45:00+00:00` | `15.0` | `candidate` | `false` | _empty_ |
| `MSTR` | `true` | `clean` | `2026-06-26T13:45:00+00:00` | `15.0` | `candidate` | `false` | _empty_ |

All five symbols returned `d11_countable=true`. All five symbols returned
`freshness_classification=clean`. All five symbols retained
`d11_primary_candidate_status=candidate`, `d11_primary_eligible=false`, and an
empty `failure_reason`.

## Authority Boundaries Preserved

The adjudicated evidence remained historical-market-data-only and preserved the
following authority boundaries:

- `local_only`
- `explicit_cli_authorization_required`
- `historical_market_data_only`
- `no_credentials_read`
- `no_tws_gateway_start`
- `no_account_query`
- `no_position_query`
- `no_margin_query`
- `no_buying_power_query`
- `no_portfolio_query`
- `no_order_placement`
- `no_order_modification`
- `no_order_cancellation`
- `no_order_routing`
- `no_execution_authority`
- `no_package_capture`
- `no_replay`
- `no_scoring`
- `no_candidate_generation`
- `no_d11_completion`
- `no_unit_12_opening`
- `no_vps_runtime_systemd_timer_mutation`

No account, position, margin, buying-power, portfolio, order, execution, or
credential fields were requested or authorized. No package capture, replay,
scoring, candidate generation, strategy, risk, execution, live-trading, broker
endpoint mutation, gateway mutation, runtime mutation, timer mutation, service
mutation, systemd mutation, TWS start, Gateway start, order placement, order
modification, order cancellation, or order routing authority was created.

## Adjudication Decision

The D11.56 diagnostic evidence is accepted as Mac-local historical diagnostic
evidence:

```text
mac_local_historical_diagnostic_evidence=ACCEPTED
```

This acceptance does not approve IBKR as primary. It does not complete D11. It
does not unblock Unit 12. It does not authorize package capture, VPS market
testing, VPS proof, replay, scoring, candidate generation, strategy, risk,
execution, account/order/execution work, live trading, or broker endpoint
traffic.

D11.57 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

Preserved statuses:

```text
IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED
D11_INSUFFICIENT
UNIT_12_BLOCKED
PACKAGE_CAPTURE=BLOCKED
VPS_RUNTIME=NOT_TOUCHED
```
