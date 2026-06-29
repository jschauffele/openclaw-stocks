# D11.76 Fresh Regular-Session LOCAL_MAC Read-Only Evidence Capture Operator Run Record

D11.76 source-controls the completed D11.75 fresh regular-session
LOCAL_MAC-only read-only market-data evidence capture result. The capture was
run by the operator, not by Codex. This record preserves the operator-supplied
D11.75 evidence exactly for later adjudication. It does not rerun IBKR, does
not execute evidence capture, does not perform broker/TWS/API/network/runtime/
VPS/scheduler/systemd/credential work, does not access account/order/
execution/position/balance/portfolio/trade/P&L/margin/buying-power/credential
data, does not modify production provider-selection behavior, does not
generate package captures, replay output, scoring output, candidate-generation
output, or live-trading output, does not approve IBKR primary eligibility, does
not mark D11 complete, and does not open Unit 12.

Decision: operator run completed and clean countable evidence recorded for
later adjudication only.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD` |
| `source_commit` | `6db5d0b2f1cc47679dd194c846206a0dde36693c` |
| `prior_source_commit` | `6db5d0b2f1cc47679dd194c846206a0dde36693c` |
| `d11_74_decision` | `FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_OPERATOR_RUN` |
| `d11_75_gate` | `D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN` |
| `d11_75_run_status` | `COMPLETED_BY_OPERATOR` |
| `d11_76_evidence_classification` | `FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE` |
| `evidence_record_only_not_provider_approval` | `true` |
| `tool_run_by` | `OPERATOR_NOT_CODEX` |
| `source_context` | `LOCAL_MAC_ONLY` |
| `operator_surface` | `DIRECT_MAC_TERMINAL` |
| `endpoint_candidate` | `127.0.0.1:7497` |
| `endpoint_class` | `IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE` |
| `symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR` |
| `timeframe` | `15Min` |
| `lookback_minutes` | `120` |
| `authority` | `READ_ONLY_MARKET_DATA_ONLY` |
| `result_type` | `ibkr_local_read_only_market_data_smoke` |
| `all_symbols_read_only` | `true` |
| `all_symbols_provider_key` | `ibkr_market_data_candidate` |
| `all_symbols_provider_name` | `IBKR read-only market-data diagnostic candidate` |
| `all_symbols_connection_mode` | `local_read_only_smoke` |
| `all_symbols_latest_candle_timestamp` | `2026-06-29T14:00:00+00:00` |
| `all_symbols_requested_start` | `2026-06-29T12:20:17.713714+00:00` |
| `all_symbols_requested_end` | `2026-06-29T14:20:17.713714+00:00` |
| `all_symbols_lag_minutes` | `20.295228566666665` |
| `all_symbols_freshness_classification` | `clean` |
| `all_symbols_failure_reason` | `` |
| `all_symbols_d11_countable` | `true` |
| `all_symbols_d11_primary_candidate_status` | `candidate` |
| `all_symbols_d11_primary_eligible` | `false` |
| `broker_api_authority` | `false` |
| `order_authority` | `false` |
| `execution_authority` | `false` |
| `package_capture` | `false` |
| `replay` | `false` |
| `scoring` | `false` |
| `candidate_generation` | `false` |
| `d11_completion_authority` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `production_provider_selection_behavior_changed` | `false` |
| `next_permissible_gate` | `D11.77_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION` |

## Evidence Classification

The completed D11.75 operator run is classified as
`FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`.

This is an evidence record only, not provider approval. D11.76 records that all
five symbols returned clean freshness and `d11_countable=true`; it does not
decide whether that evidence is sufficient to approve IBKR primary eligibility
or close D11. D11.77 is the first permissible gate to adjudicate whether the
D11.75/D11.76 clean countable evidence changes IBKR primary eligibility or D11
status.

## Per-Symbol Operator Result

| Symbol | Read only | Provider key | Provider name | Connection mode | Latest candle timestamp | Requested start | Requested end | Lag minutes | Freshness classification | Failure reason | D11 countable | D11 primary eligible | Candidate status | Timeframe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AAPL` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` |
| `MSFT` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` |
| `NVDA` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` |
| `TSLA` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` |
| `MSTR` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` |

## Countability Summary

All five D11.75 rows are recorded as D11-countable evidence:

- all five symbols returned `freshness_classification=clean`;
- all five symbols returned `d11_countable=true`;
- all five symbols returned an empty `failure_reason`;
- all five symbols recorded
  `latest_candle_timestamp=2026-06-29T14:00:00+00:00`;
- all five symbols recorded `lag_minutes=20.295228566666665`.

All five rows also remain non-primary-approved candidate rows:

- all five symbols returned `d11_primary_eligible=false`;
- all five symbols returned `d11_primary_candidate_status=candidate`;
- `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED` remains preserved until a later
  adjudication explicitly changes it.

## Negative Authority Confirmation

D11.76 records no forbidden authority in the D11.75 operator-run evidence:

- `no_account_query`
- `no_position_query`
- `no_portfolio_query`
- `no_balance_query`
- `no_margin_query`
- `no_buying_power_query`
- `no_order_placement`
- `no_order_modification`
- `no_order_cancellation`
- `no_order_routing`
- `no_execution_authority`
- `no_package_capture`
- `no_replay`
- `no_scoring`
- `no_candidate_generation`
- `no_unit_12_opening`
- `no_vps_runtime_systemd_timer_mutation`

The recorded top-level authority booleans are
`broker_api_authority=false`, `order_authority=false`,
`execution_authority=false`, `package_capture=false`, `replay=false`,
`scoring=false`, `candidate_generation=false`, and
`d11_completion_authority=false`.

## Locality and Forbidden Context Review

D11.76 records the completed capture as LOCAL_MAC-only evidence from
`DIRECT_MAC_TERMINAL` against endpoint candidate `127.0.0.1:7497`. This is
LOCAL_MAC process-context evidence only. It is not VPS localhost evidence and
does not validate VPS `127.0.0.1:7497`.

The operator-supplied result used no VPS path, no `18789`, no `18791`, no
bridge, no tunnel, and no proxy. D11.76 does not approve `18789` or `18791` as
market-data endpoints and does not authorize any VPS rerun or endpoint
substitution.

## Status Preservation

D11.76 preserves:

- `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`
- `D11=D11_INSUFFICIENT`
- `UNIT_12=UNIT_12_BLOCKED`
- `broker_submit_readiness=NOT_APPROVED`
- `live_trading_readiness=NOT_APPROVED`

D11.76 does not approve IBKR primary eligibility, does not mark D11 complete,
does not open Unit 12, does not approve broker submit readiness, and does not
approve live trading readiness.

## No Rerun or Runtime Action

D11.76 does not rerun IBKR, does not execute evidence capture, does not run
broker/TWS/API/network/runtime commands, does not connect to IBKR, does not
perform VPS actions, does not run service/systemd/scheduler/timer/runtime
commands, does not access credentials or environment files, and does not
perform package capture, replay, scoring, candidate generation, or
live-trading output generation.

## Next Permissible Gate

The exact next permissible gate is
`D11.77_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`.

D11.77 must adjudicate whether the D11.75/D11.76 clean countable evidence is
sufficient to change IBKR primary eligibility or close D11. D11.76 itself must
not approve IBKR primary eligibility, must not complete D11, and must not open
Unit 12.
