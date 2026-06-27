# D11.72 LOCAL_MAC Read-Only Evidence Capture Operator Run Record

D11.72 source-controls the completed operator-run result from the D11.72
LOCAL_MAC-only read-only market-data evidence capture. The command was run by
the operator, not by Codex. This record does not rerun the capture, does not
create new broker/TWS/API/runtime/network actions, does not fix or reinterpret
the result, does not approve IBKR primary eligibility, does not mark D11
complete, and does not open Unit 12.

Decision: operator run completed and evidence recorded with a recency caveat.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD` |
| `source_commit` | `7479f708c53067980491c31bb37b41c2bcbf4eea` |
| `prior_source_commit` | `7479f708c53067980491c31bb37b41c2bcbf4eea` |
| `d11_71_decision` | `LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY` |
| `d11_72_gate` | `D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN` |
| `d11_72_run_status` | `COMPLETED_BY_OPERATOR` |
| `d11_72_evidence_classification` | `READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT` |
| `tool_run_by` | `OPERATOR_NOT_CODEX` |
| `tool_run` | `.venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke with D11.71-authorized arguments` |
| `source_context` | `LOCAL_MAC_ONLY` |
| `operator_surface` | `DIRECT_MAC_TERMINAL` |
| `endpoint_candidate` | `127.0.0.1:7497` |
| `endpoint_class` | `IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE` |
| `symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR` |
| `timeframe` | `15Min` |
| `lookback_minutes` | `120` |
| `result_type` | `ibkr_local_read_only_market_data_smoke` |
| `all_symbols_read_only` | `true` |
| `all_symbols_provider_key` | `ibkr_market_data_candidate` |
| `all_symbols_connection_mode` | `local_read_only_smoke` |
| `all_symbols_d11_primary_candidate_status` | `candidate` |
| `all_symbols_d11_primary_eligible` | `false` |
| `all_symbols_d11_countable` | `false` |
| `all_symbols_freshness_classification` | `recency_caveated` |
| `all_symbols_failure_reason` | `regular_session_closed_latest_candle_valid_for_last_session` |
| `broker_api_authority` | `false` |
| `order_authority` | `false` |
| `execution_authority` | `false` |
| `package_capture` | `false` |
| `replay` | `false` |
| `scoring` | `false` |
| `candidate_generation` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `d11_72_rerun_authorized` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `next_permissible_gate` | `D11.73_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION` |

## Evidence Classification

The completed operator run is classified as
`READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`.

The evidence is not D11-countable for primary eligibility because all five
symbols returned `d11_countable=false` and
`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`.
The run shows LOCAL_MAC read-only market-data availability with a recency
caveat; it does not satisfy IBKR primary eligibility, does not make the IBKR
candidate countable for D11, and does not approve runtime deployment, broker
submit readiness, live trading readiness, or Unit 12 opening.

## Per-Symbol Operator Result

| Symbol | Read only | Provider key | Provider name | Connection mode | Latest candle timestamp | Requested start | Requested end | Lag minutes | Freshness classification | Failure reason | D11 countable | D11 primary eligible | Candidate status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AAPL` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` |
| `MSFT` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` |
| `NVDA` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` |
| `TSLA` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` |
| `MSTR` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` |

## Negative Authority Confirmation

The operator-supplied terminal output reported no account/order/execution/
position/balance/portfolio/credential fields. D11.72 records these negative
authority markers:

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
- `no_unit_12_opening`
- `no_vps_runtime_systemd_timer_mutation`

The recorded top-level authority booleans are
`broker_api_authority=false`, `order_authority=false`,
`execution_authority=false`, `package_capture=false`, `replay=false`,
`scoring=false`, and `candidate_generation=false`.

## Locality and Forbidden Context Review

D11.72 records the completed capture as LOCAL_MAC-only evidence from
`DIRECT_MAC_TERMINAL` against endpoint candidate `127.0.0.1:7497`. This is
LOCAL_MAC process-context evidence only. It is not VPS localhost evidence and
does not validate VPS `127.0.0.1:7497`.

The operator-supplied result used no VPS path, no `18789`, no `18791`, no
bridge, no tunnel, and no proxy. D11.72 does not approve `18789` or `18791` as
market-data endpoints and does not authorize any VPS rerun or endpoint
substitution.

## Status Preservation

D11.72 preserves:

- `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`
- `D11=D11_INSUFFICIENT`
- `UNIT_12=UNIT_12_BLOCKED`
- `broker_submit_readiness=NOT_APPROVED`
- `live_trading_readiness=NOT_APPROVED`
- `candidate_can_count_for_d11` remains unsatisfied because all recorded
  symbol rows are `d11_countable=false`.

D11.72 does not approve IBKR primary eligibility, does not mark D11 complete,
does not open Unit 12, does not approve broker submit readiness, and does not
approve live trading readiness.

## No Rerun Authorization

D11.72 does not authorize a rerun. It records the completed operator-run result
exactly as evidence and preserves the recency caveat. Any future fresh
regular-session rerun would require a new source-controlled authorization.

## Next Permissible Gate

The exact next permissible gate is
`D11.73_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`.

D11.73 must be a source-controlled adjudication gate that decides whether this
D11.72 capture is sufficient, insufficient due to the recency caveat, or
requires a fresh regular-session rerun under a new authorization. D11.73 must
not infer approval from this D11.72 record; it must adjudicate the recorded
evidence and preserve fail-closed handling unless source-controlled evidence
supports a different result.
