# D11.74 Fresh Regular-Session Read-Only Evidence Capture Authorization Packet

D11.74 is the source-controlled authorization packet for a fresh
regular-session LOCAL_MAC-only read-only evidence capture rerun. It authorizes
only a later operator-run gate. D11.74 does not run IBKR, does not execute
evidence capture, does not create executable evidence-capture commands for
Codex to run, does not perform broker/TWS/API/network/runtime/VPS/scheduler/
systemd/credential work, does not access account/order/execution/position/
balance/portfolio/credential data, does not modify production
provider-selection behavior, does not open Unit 12, does not approve IBKR
primary eligibility, does not mark D11 complete, and does not imply broker
submit readiness or live trading readiness.

Decision: authorize a fresh regular-session LOCAL_MAC-only read-only operator
run for the next gate.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET` |
| `source_commit` | `08bc4cbedd4b465eb6308deadb4a781acc991512` |
| `d11_73_decision` | `D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN` |
| `d11_72_evidence_classification` | `READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT` |
| `d11_72_all_symbols_d11_countable` | `false` |
| `d11_72_all_symbols_d11_primary_eligible` | `false` |
| `d11_72_all_symbols_freshness_classification` | `recency_caveated` |
| `d11_72_all_symbols_failure_reason` | `regular_session_closed_latest_candle_valid_for_last_session` |
| `d11_69_decision` | `READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY` |
| `d11_70_decision` | `LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE` |
| `d11_71_decision` | `LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY` |
| `d11_74_decision` | `FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_OPERATOR_RUN` |
| `authorized_gate_only` | `D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN` |
| `d11_74_evidence_collected` | `false` |
| `d11_74_executable_evidence_capture_command_run` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `remaining_provider_eligibility_blockers` | `broker_coupled_true; d11_primary_eligible_false; d11_primary_candidate_status_candidate; candidate_can_count_for_d11_unsatisfied` |
| `next_permissible_gate` | `D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN` |

## D11.73 Adjudication Basis

D11.73 adjudicated the D11.72 operator-run record as operationally useful but
insufficient for primary-eligibility review:

- D11.72 evidence classification:
  `READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`;
- all five symbols returned `d11_countable=false`;
- all five symbols returned `d11_primary_eligible=false`;
- all five symbols returned `freshness_classification=recency_caveated`;
- all five symbols returned
  `failure_reason=regular_session_closed_latest_candle_valid_for_last_session`;
- all five symbols recorded `latest_candle_timestamp=2026-06-26T19:45:00+00:00`;
- all five symbols recorded `requested_start=2026-06-27T01:40:31.383039+00:00`;
- all five symbols recorded `requested_end=2026-06-27T03:40:31.383039+00:00`;
- all five symbols recorded `lag_minutes=475.52305065`.

D11.73 required a fresh regular-session rerun because the D11.72 run occurred
outside the usable freshness window for countable primary-eligibility
evidence. No source-controlled contradiction was found that blocks a fresh
LOCAL_MAC-only regular-session operator run under the D11.69 contract, D11.70
authorization packet, and D11.71 execution packet.

## Authorized Future Source Context

D11.74 authorizes only this future D11.75 source context:

| Context field | Authorized value |
| --- | --- |
| Source context | `LOCAL_MAC_ONLY` |
| Operator surface | `DIRECT_MAC_TERMINAL` only |
| Process context | LOCAL_MAC process context only |
| Endpoint candidate | `127.0.0.1:7497` |
| Endpoint class | IBKR Paper TWS/Gateway local socket candidate |
| Timing | Fresh regular-session evidence capture only |
| Evidence scope | Market-data/provider-readiness only |
| Purpose | Later adjudication of market-data provider readiness, not provider approval by D11.74. |

The next operator run may use the D11.71 bounded command/procedure only if it
remains inside the D11.69, D11.70, D11.71, D11.73, and D11.74 boundaries.
D11.74 itself does not create executable commands for Codex to run.

## Authorized Future Evidence Target Set

The D11.75 target set authorized by D11.74 is exactly:

| Target ID | Authorized target |
| --- | --- |
| `target_1_local_process_endpoint_identity` | LOCAL_MAC process-context endpoint identity for endpoint candidate `127.0.0.1:7497`. |
| `target_2_read_only_socket_configuration` | Read-only local socket/API mode for the IBKR Paper TWS/Gateway local socket candidate. |
| `target_3_regular_session_historical_bars_availability` | Historical bars availability during a fresh regular-session window for `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`; timeframe `15Min`; lookback/request scope `120 minutes`. |
| `target_4_response_metadata_for_adjudication` | Response metadata needed to adjudicate freshness, countability, provider readiness, and failure reasons. |
| `target_5_negative_authority_evidence` | Negative evidence proving no account/order/execution/submit authority was requested, returned, retained, logged, or used. |

## Regular-Session Timing Boundary

D11.75 is authorized only for a fresh regular-session window where a current or
sufficiently recent `15Min` candle is expected to be available. D11.74
explicitly rejects after-session reruns that are expected to reproduce
`regular_session_closed_latest_candle_valid_for_last_session`.

The future D11.75 operator-run packet or result must record, for every symbol:

- `requested_start`;
- `requested_end`;
- `latest_candle_timestamp`;
- `lag_minutes`;
- `freshness_classification`;
- `failure_reason`;
- `d11_countable`;
- `d11_primary_eligible`.

D11.75 must fail closed if all symbols remain `d11_countable=false` due to the
regular-session-closed recency caveat.

## Allowed Fields

D11.75 may retain only these fields:

| Target ID | Allowed fields |
| --- | --- |
| `target_1_local_process_endpoint_identity` | `source_context`, `operator_surface`, `process_context`, `endpoint_host`, `endpoint_port`, `endpoint_class`, `localhost_process_context_statement`, `vps_equivalence_rejected`, `authorization_gate`, `source_commit`. |
| `target_2_read_only_socket_configuration` | `read_only_socket_scope`, `market_data_only_scope`, `api_connection_mode`, `paper_mode_candidate`, `service_mutation_performed=false`, `systemd_mutation_performed=false`, `scheduler_mutation_performed=false`, `runtime_mutation_performed=false`, `credential_access_performed=false`. |
| `target_3_regular_session_historical_bars_availability` | `symbols`, `timeframe`, `lookback_minutes`, `requested_start`, `requested_end`, `regular_session_window`, `historical_market_data_only=true`, `bar_count`, `latest_candle_timestamp`, `freshness_classification`, `d11_countable`, `d11_primary_eligible`, `d11_primary_candidate_status`, `failure_reason`. |
| `target_4_response_metadata_for_adjudication` | `result_type`, `provider_key`, `provider_name`, `connection_mode`, `exchange`, `currency`, `security_type`, `request_timestamp_utc`, `response_timestamp_utc`, `timezone`, `warnings`, `error_code_class`, `error_message_redacted`, `pass_fail_marker`, `adjudication_ready_summary`. |
| `target_5_negative_authority_evidence` | `broker_api_authority=false`, `order_authority=false`, `execution_authority=false`, `broker_submit_readiness=false`, `live_trading_readiness=false`, `unit_12_opened=false`, `package_capture=false`, `replay=false`, `scoring=false`, `candidate_generation=false`. |

## Forbidden Fields

D11.75 must fail closed if any forbidden field or context is requested,
returned, retained, or logged:

| Category | Forbidden fields or activity |
| --- | --- |
| Account and financial data | Account IDs, account aliases, account values, balances, buying power, margin, portfolio contents, positions, position quantities, position values, P&L, cash, equity, net liquidation, account summary, account ledger. |
| Order and execution data | Open orders, order IDs, order status, executions, fills, trade history, commission reports, submit endpoints, cancel endpoints, modify endpoints, flatten/sell/cleanup evidence, broker submit readiness, live trading readiness. |
| Credential and secret data | Usernames, passwords, tokens, API keys, session secrets, cookies, credential file paths, environment variable values, authentication challenge contents. |
| Endpoint and locality violations | VPS `127.0.0.1:7497`, `18789`, `18791`, bridge, tunnel, proxy, guessed endpoints, unapproved endpoint substitutions, treating LOCAL_MAC `127.0.0.1:7497` as VPS `127.0.0.1:7497`. |
| Runtime and infrastructure mutation | Service changes, scheduler changes, systemd changes, timer changes, runtime configuration changes, environment file changes, TWS/Gateway mutation, openclaw-gateway mutation, VPS runtime mutation, credential mutation. |
| Trading and pipeline activity | Package capture, replay, scoring, candidate generation, strategy mutation, risk mutation, execution mutation, Unit 12 opening, D11 completion, IBKR primary eligibility approval. |

## Redaction Rules

Any accidental account, order, execution, position, balance, portfolio, P&L,
margin, buying power, credential, token, secret, account-identifying, or
person-identifying value must be redacted before retention. The artifact must
then be marked fail-closed with `FORBIDDEN_FIELDS_ABSENT_FAIL` and
`ADJUDICATION_READY_FAIL`. Redaction does not convert a forbidden-field
violation into a passing artifact.

## Required PASS/FAIL Markers

D11.75 output must include these marker families:

- `LOCAL_MAC_CONTEXT_PASS` or `LOCAL_MAC_CONTEXT_FAIL`;
- `DIRECT_MAC_TERMINAL_PASS` or `DIRECT_MAC_TERMINAL_FAIL`;
- `ENDPOINT_127_0_0_1_7497_SCOPE_PASS` or `ENDPOINT_127_0_0_1_7497_SCOPE_FAIL`;
- `REGULAR_SESSION_TIMING_PASS` or `REGULAR_SESSION_TIMING_FAIL`;
- `NO_AFTER_SESSION_STALE_CAPTURE_PASS` or `NO_AFTER_SESSION_STALE_CAPTURE_FAIL`;
- `SYMBOL_SCOPE_PASS` or `SYMBOL_SCOPE_FAIL`;
- `TIMEFRAME_15MIN_PASS` or `TIMEFRAME_15MIN_FAIL`;
- `LOOKBACK_120_MINUTES_PASS` or `LOOKBACK_120_MINUTES_FAIL`;
- `HISTORICAL_BARS_SCOPE_PASS` or `HISTORICAL_BARS_SCOPE_FAIL`;
- `FORBIDDEN_FIELDS_ABSENT_PASS` or `FORBIDDEN_FIELDS_ABSENT_FAIL`;
- `NEGATIVE_AUTHORITY_PASS` or `NEGATIVE_AUTHORITY_FAIL`;
- `ADJUDICATION_READY_PASS` or `ADJUDICATION_READY_FAIL`.

Missing, ambiguous, duplicated, or contradictory markers force fail-closed
treatment.

## Required Artifact Sections

D11.75 must produce only a compact adjudication-ready operator-run packet or
terminal output with these sections:

| Artifact section | Required content |
| --- | --- |
| `artifact_identity` | Artifact name, gate `D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`, D11.74 authorization reference, source commit, operator role, creation timestamp in UTC, local timezone. |
| `operator_context` | `LOCAL_MAC_ONLY`, `DIRECT_MAC_TERMINAL`, LOCAL_MAC process context, endpoint candidate `127.0.0.1:7497`, no VPS, no `18789`, no `18791`, no bridge, no tunnel, no proxy. |
| `regular_session_timing` | Operator-run timing statement, requested window, expected 15-minute candle recency, and explicit not-after-session-stale marker. |
| `request_scope` | Symbols `AAPL,MSFT,NVDA,TSLA,MSTR`, timeframe `15Min`, lookback `120 minutes`, historical-market-data-only scope. |
| `target_results` | One row per symbol with `requested_start`, `requested_end`, `latest_candle_timestamp`, `lag_minutes`, `freshness_classification`, `failure_reason`, `d11_countable`, `d11_primary_eligible`, and candidate status. |
| `negative_authority_attestation` | No account/order/execution/position/balance/portfolio/credential/submit/cancel/modify/flatten/sell/cleanup authority requested, returned, retained, logged, or used. |
| `locality_attestation` | LOCAL_MAC `127.0.0.1:7497` is not VPS `127.0.0.1:7497`; VPS, `18789`, and `18791` were not used. |
| `adjudication_summary` | PASS/FAIL markers, redaction summary, forbidden-field summary, countability summary, provider-readiness summary, and remaining provider-eligibility blockers. |

## Future Run Fail-Closed Conditions

D11.75 must fail closed if any of these occur:

- source context is not `LOCAL_MAC_ONLY`;
- operator surface is not `DIRECT_MAC_TERMINAL`;
- endpoint is not `127.0.0.1:7497`;
- run timing is not a regular-session window where a current or sufficiently
  recent `15Min` candle is expected;
- after-session stale capture is expected to reproduce
  `regular_session_closed_latest_candle_valid_for_last_session`;
- all symbols remain `d11_countable=false` due to the
  regular-session-closed recency caveat;
- any symbol outside `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR` appears;
- any timeframe other than `15Min` appears;
- lookback/request scope is not `120 minutes`;
- account/order/execution/position/balance/portfolio/credential data is
  requested, returned, retained, or logged;
- any forbidden field appears;
- VPS, `18789`, `18791`, bridge, tunnel, proxy, service, scheduler, systemd,
  runtime mutation, credential mutation, package capture, replay, scoring,
  candidate generation, strategy/risk/execution mutation, broker submit
  readiness, live trading readiness, or Unit 12 opening is introduced;
- LOCAL_MAC `127.0.0.1:7497` is treated as VPS `127.0.0.1:7497`;
- required artifact sections, PASS/FAIL markers, timestamps, timezone fields,
  source-control references, or redaction markers are missing.

## Non-Authorized Contexts

D11.74 does not authorize VPS evidence, `18789` evidence, `18791` evidence,
bridge/tunnel/proxy evidence, account evidence, order evidence, execution
evidence, position evidence, balance evidence, portfolio evidence, credential
evidence, broker submit readiness, live trading readiness, Unit 12 opening,
package capture, replay, scoring, candidate generation, runtime mutation,
provider-selection runtime behavior change, production deployment, D11
completion, or IBKR primary eligibility approval.

`127.0.0.1` remains process-context local. LOCAL_MAC `127.0.0.1:7497` is not
equivalent to VPS `127.0.0.1:7497`. D11.74 rejects `18789` and `18791` as
approved market-data endpoints unless a later separate source-controlled
endpoint adjudication approves them.

## Status Preserved

D11.74 preserves:

- `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`;
- `D11=D11_INSUFFICIENT`;
- `UNIT_12=UNIT_12_BLOCKED`;
- `broker_submit_readiness=NOT_APPROVED`;
- `live_trading_readiness=NOT_APPROVED`;
- `ibkr_market_data_candidate` remains `broker_coupled=true`;
- `ibkr_market_data_candidate` remains `d11_primary_eligible=false`;
- `d11_primary_candidate_status` remains `candidate`;
- `candidate_can_count_for_d11` remains unsatisfied.

Future evidence capture may support later adjudication but cannot itself
approve IBKR primary eligibility.

## Next Permissible Gate

The exact next permissible gate is:

```text
D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN
```

D11.75 may be the operator-run gate where the bounded fresh regular-session
LOCAL_MAC-only read-only evidence capture is actually run, but only if it
remains inside the D11.69 contract, D11.70 authorization packet, D11.71
execution packet, D11.73 adjudication, and D11.74 authorization packet.
