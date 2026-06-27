# D11.73 LOCAL_MAC Read-Only Evidence Capture Adjudication

D11.73 is the source-controlled adjudication gate for the completed D11.72
LOCAL_MAC read-only evidence capture record. It adjudicates only the evidence
already recorded in D11.72. It does not rerun IBKR, does not execute evidence
capture, does not create executable evidence-capture commands, does not perform
broker/TWS/API/network/runtime/VPS/scheduler/systemd/credential work, does not
access account/order/execution/position/balance/portfolio/credential data,
does not modify production provider-selection behavior, does not open Unit 12,
does not approve IBKR primary eligibility, and does not imply broker submit
readiness or live trading readiness.

Decision: the D11.72 evidence is operationally useful but insufficient for
primary-eligibility review because every recorded symbol is non-countable and
recency-caveated.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION` |
| `source_commit` | `7f62130f08a03167975f9187c5a0314f95074568` |
| `d11_72_classification` | `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD` |
| `d11_72_evidence_classification` | `READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT` |
| `d11_72_all_symbols_d11_countable` | `false` |
| `d11_72_all_symbols_d11_primary_eligible` | `false` |
| `d11_72_all_symbols_freshness_classification` | `recency_caveated` |
| `d11_72_all_symbols_failure_reason` | `regular_session_closed_latest_candle_valid_for_last_session` |
| `d11_73_decision` | `D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |
| `d11_73_evidence_collected` | `false` |
| `d11_73_executable_evidence_capture_commands_created` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `next_permissible_gate` | `D11.74_SOURCE_CONTROLLED_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET` |

## D11.72 Evidence Summary

D11.72 recorded a completed operator run from `LOCAL_MAC_ONLY`,
`DIRECT_MAC_TERMINAL`, endpoint candidate `127.0.0.1:7497`, endpoint class
`IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE`, symbols `AAPL`, `MSFT`,
`NVDA`, `TSLA`, `MSTR`, timeframe `15Min`, lookback `120 minutes`, and result
type `ibkr_local_read_only_market_data_smoke`.

The D11.72 record is preserved as operationally useful proof that the LOCAL_MAC
read-only diagnostic path returned historical bar metadata. It is not
countable for D11 primary eligibility because the run occurred outside the
usable freshness window for countable primary-eligibility evidence.
Adjudication result: not countable for D11 primary eligibility.
Source-controlled adjudication marker:
`d11_72_evidence_not_countable_for_d11_primary_eligibility=true`.

## Per-Symbol Adjudication

| Symbol | Read only | Provider key | Connection mode | Latest candle timestamp | Requested start | Requested end | Lag minutes | Freshness classification | Failure reason | D11 countable | D11 primary eligible | Candidate status | D11.73 adjudication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AAPL` | `true` | `ibkr_market_data_candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` | `NON_COUNTABLE_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |
| `MSFT` | `true` | `ibkr_market_data_candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` | `NON_COUNTABLE_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |
| `NVDA` | `true` | `ibkr_market_data_candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` | `NON_COUNTABLE_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |
| `TSLA` | `true` | `ibkr_market_data_candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` | `NON_COUNTABLE_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |
| `MSTR` | `true` | `ibkr_market_data_candidate` | `local_read_only_smoke` | `2026-06-26T19:45:00+00:00` | `2026-06-27T01:40:31.383039+00:00` | `2026-06-27T03:40:31.383039+00:00` | `475.52305065` | `recency_caveated` | `regular_session_closed_latest_candle_valid_for_last_session` | `false` | `false` | `candidate` | `NON_COUNTABLE_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |

## Countability Adjudication

The D11.72 record is non-countable for D11 primary eligibility:

- all five symbols returned `d11_countable=false`;
- all five symbols returned `d11_primary_eligible=false`;
- all five symbols retained `d11_primary_candidate_status=candidate`;
- all five symbols returned
  `failure_reason=regular_session_closed_latest_candle_valid_for_last_session`;
- `candidate_can_count_for_d11` remains unsatisfied because the source
  provider candidate is not `approved_primary`, is not
  `d11_primary_eligible=true`, and remains broker-coupled.

D11.73 therefore cannot approve IBKR primary eligibility from the D11.72
record and cannot mark D11 complete.

## Recency and Freshness Adjudication

All five D11.72 rows have:

- `freshness_classification=recency_caveated`;
- `latest_candle_timestamp=2026-06-26T19:45:00+00:00`;
- `requested_start=2026-06-27T01:40:31.383039+00:00`;
- `requested_end=2026-06-27T03:40:31.383039+00:00`;
- `lag_minutes=475.52305065`.

D11.73 adjudicates that the D11.72 run occurred outside the usable freshness
window for countable primary-eligibility evidence. The appropriate next path is
a fresh regular-session LOCAL_MAC-only read-only evidence capture
authorization packet, not eligibility approval.

## Negative-Authority Adjudication

D11.73 finds no forbidden authority in the D11.72 record. The recorded
negative-authority markers remain accepted for this adjudication:

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

The D11.72 record used no VPS path, no `18789`, no `18791`, no bridge, no
tunnel, and no proxy. LOCAL_MAC `127.0.0.1:7497` remains process-context local
evidence and is not VPS `127.0.0.1:7497` evidence.

## Provider Eligibility Impact

D11.73 preserves:

- `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`;
- `ibkr_market_data_candidate` remains `d11_primary_candidate_status=candidate`;
- `ibkr_market_data_candidate` remains `d11_primary_eligible=false`;
- `candidate_can_count_for_d11` remains unsatisfied;
- broker submit readiness remains `NOT_APPROVED`;
- live trading readiness remains `NOT_APPROVED`.

D11.72 evidence may support a later adjudication of LOCAL_MAC read-only
diagnostic operability, but it does not support primary eligibility review
because it is non-countable due to the recency caveat.

## D11 Status and Unit 12 Impact

D11.73 preserves:

- `D11=D11_INSUFFICIENT`;
- `UNIT_12=UNIT_12_BLOCKED`;
- no Unit 12 opening;
- no D11 completion;
- no broker submit readiness;
- no live trading readiness.

## Required Future Regular-Session Rerun Boundaries

The next gate may authorize only a fresh LOCAL_MAC-only regular-session
read-only evidence capture packet. The future fresh regular-session rerun must
remain within these boundaries:

- `LOCAL_MAC_ONLY`;
- `DIRECT_MAC_TERMINAL`;
- endpoint candidate `127.0.0.1:7497`;
- symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`;
- timeframe `15Min`;
- lookback `120 minutes`;
- market-data/provider-readiness only;
- no account, order, execution, position, balance, portfolio, margin,
  buying-power, trade, P&L, credential, or broker submit authority;
- no VPS, no `18789`, no `18791`, no bridge, no tunnel, no proxy;
- no runtime, service, systemd, scheduler, timer, TWS/Gateway, credential,
  environment, strategy, risk, execution, package capture, replay, scoring, or
  candidate-generation mutation;
- no Unit 12 opening;
- no IBKR primary eligibility approval by the authorization packet itself.

D11.73 does not create executable broker/TWS/API/runtime commands. D11.74 must
be source-controlled authorization only and must not itself perform evidence
capture.

## Next Permissible Gate

The exact next permissible gate is:

```text
D11.74_SOURCE_CONTROLLED_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET
```

D11.74 must be a source-controlled authorization packet for a fresh
LOCAL_MAC-only regular-session read-only evidence capture. It must preserve
the D11.69/D11.70/D11.71 boundaries unless explicitly narrowed, must not
perform evidence capture, and must not approve IBKR primary eligibility.
