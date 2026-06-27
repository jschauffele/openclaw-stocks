# D11.70 LOCAL_MAC Read-Only Evidence Capture Authorization Packet

D11.70 is the source-controlled authorization packet for a later bounded
LOCAL_MAC-only read-only evidence capture under the D11.69 contract. D11.70
does not perform evidence capture, does not create executable evidence-capture
commands, does not perform broker/TWS/API/runtime/network/service/scheduler/
systemd/credential/VPS actions, does not access account/order/execution/
portfolio/position/P&L/margin/buying-power/credential data, does not modify
production provider-selection behavior, does not open Unit 12, does not
approve IBKR primary eligibility, and does not imply broker submit readiness or
live trading readiness.

Decision: authorize only a future D11.71 LOCAL_MAC-only read-only evidence
capture execution packet.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET` |
| `source_commit` | `36342c53ef9ae0fc026c8588511d4a9c8d05f90f` |
| `d11_69_classification` | `IBKR_D11_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION` |
| `d11_69_decision` | `READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY` |
| `d11_69_selected_future_source_context` | `LOCAL_MAC_ONLY / DIRECT_MAC_TERMINAL / IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE / 127.0.0.1:7497` |
| `d11_70_decision` | `LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE` |
| `authorized_gate_only` | `D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET` |
| `d11_70_evidence_collected` | `false` |
| `d11_70_executable_evidence_capture_commands_created` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |
| `account_order_execution_authority` | `false` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `remaining_provider_eligibility_blockers` | `broker_coupled_candidate_unresolved; d11_primary_eligible_false; d11_primary_candidate_status_candidate; candidate_can_count_for_d11_unsatisfied` |
| `next_permissible_gate` | `D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET` |

## Source-Controlled Preconditions

D11.70 authorizes the next gate because these source-controlled preconditions
are satisfied:

| Precondition | Source-controlled result |
| --- | --- |
| D11.68 forced a concrete blocker review | `READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER` was recorded. |
| D11.69 remediated capture-contract blockers | `READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY` was recorded. |
| Exact future source context exists | `LOCAL_MAC_ONLY / DIRECT_MAC_TERMINAL / IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE / 127.0.0.1:7497`. |
| Exact future target set exists | LOCAL_MAC endpoint identity, read-only socket configuration, API connection mode, historical bars availability, response metadata, and negative authority evidence. |
| Allowed and forbidden field boundaries exist | D11.69 defines allowed fields, forbidden fields, redaction rules, PASS/FAIL markers, and fail-closed artifact rules. |
| Provider eligibility remains closed | IBKR primary eligibility remains `NOT_APPROVED`; D11 remains `D11_INSUFFICIENT`; Unit 12 remains `UNIT_12_BLOCKED`. |

No source-controlled contradiction was found that blocks a later D11.71
LOCAL_MAC-only read-only evidence capture execution packet.

## Authorized Future Source Context

D11.70 authorizes only the following future source context for D11.71:

| Context field | Authorized value |
| --- | --- |
| Source context | `LOCAL_MAC_ONLY` |
| Operator surface | `DIRECT_MAC_TERMINAL` only |
| Process context | LOCAL_MAC process context only |
| Endpoint candidate | `127.0.0.1:7497` |
| Endpoint class | IBKR Paper TWS/Gateway local socket candidate |
| Evidence scope | Market-data/provider-readiness only |
| VPS reliance | Forbidden |
| `18789`/`18791` reliance | Forbidden |
| Bridge/tunnel/proxy reliance | Forbidden |
| Runtime mutation | Forbidden |
| Account/order/execution authority | Forbidden |

D11.70 authorizes only D11.71 to contain bounded execution instructions. D11.70
itself contains no executable evidence-capture commands.

## Authorized Future Evidence Target Set

The D11.71 target set authorized by D11.70 is exactly:

| Target ID | Authorized target |
| --- | --- |
| `target_1_local_process_endpoint_identity` | LOCAL_MAC process-context endpoint identity for endpoint candidate `127.0.0.1:7497`. |
| `target_2_read_only_socket_configuration` | Read-only local socket configuration evidence for the IBKR Paper TWS/Gateway local socket candidate. |
| `target_3_api_connection_mode` | API connection mode evidence limited to local paper market-data provider readiness. |
| `target_4_historical_bars_availability` | Historical bars availability for `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`; timeframe `15Min`; lookback/request scope `120 minutes`. |
| `target_5_response_metadata_for_adjudication` | Response metadata needed to adjudicate market-data provider readiness. |
| `target_6_negative_authority_evidence` | Negative evidence proving no account/order/execution/submit authority was requested, returned, retained, logged, or used. |

The purpose of this target set is later adjudication of market-data provider
readiness. It is not provider approval by D11.70 and cannot itself approve IBKR
primary eligibility.

## Allowed Fields

D11.71 may authorize collection only of these fields:

| Target ID | Allowed fields |
| --- | --- |
| `target_1_local_process_endpoint_identity` | `source_context`, `operator_surface`, `process_context`, `endpoint_host`, `endpoint_port`, `endpoint_class`, `localhost_process_context_statement`, `vps_equivalence_rejected`, `capture_authorization_gate`, `source_commit`. |
| `target_2_read_only_socket_configuration` | `read_only_socket_scope`, `market_data_only_scope`, `manual_tws_gateway_state_observed_only`, `service_mutation_performed=false`, `systemd_mutation_performed=false`, `scheduler_mutation_performed=false`, `runtime_mutation_performed=false`, `credential_access_performed=false`. |
| `target_3_api_connection_mode` | `api_connection_mode`, `paper_mode_candidate`, `market_data_request_scope`, `account_data_requested=false`, `position_data_requested=false`, `order_data_requested=false`, `execution_data_requested=false`, `submit_cancel_modify_requested=false`. |
| `target_4_historical_bars_availability` | `symbols`, `timeframe`, `lookback_minutes`, `requested_start_utc`, `requested_end_utc`, `regular_session_window`, `historical_market_data_only=true`, `bar_count`, `latest_candle_timestamp_utc`, `freshness_classification`, `d11_countable_candidate`, `failure_reason`. |
| `target_5_response_metadata_for_adjudication` | `provider_key`, `provider_name`, `feed_name`, `exchange`, `currency`, `security_type`, `request_timestamp_utc`, `response_timestamp_utc`, `timezone`, `warnings`, `error_code_class`, `error_message_redacted`, `pass_fail_marker`, `adjudication_ready_summary`. |
| `target_6_negative_authority_evidence` | `account_order_execution_authority=false`, `broker_submit_readiness=false`, `live_trading_readiness=false`, `unit_12_opened=false`, `package_capture_performed=false`, `replay_performed=false`, `scoring_performed=false`, `candidate_generation_performed=false`. |

## Forbidden Fields

D11.71 must fail closed if any forbidden field is requested, returned,
retained, or logged:

| Category | Forbidden fields or activity |
| --- | --- |
| Account and financial data | Account IDs, account aliases, account values, balances, buying power, margin, portfolio contents, positions, position quantities, position values, P&L, cash, equity, net liquidation, account summary, account ledger. |
| Order and execution data | Open orders, order IDs, order status, executions, fills, trade history, commission reports, submit endpoints, cancel endpoints, modify endpoints, flatten/sell/cleanup evidence. |
| Credential and secret data | Usernames, passwords, tokens, API keys, session secrets, cookies, credential file paths, environment variable values, authentication challenge contents. |
| Runtime and infrastructure mutation | Service changes, systemd changes, scheduler changes, timer changes, runtime configuration changes, environment file changes, TWS/Gateway mutation, openclaw-gateway mutation, VPS runtime mutation, bridge/tunnel/proxy setup. |
| Out-of-scope endpoint evidence | VPS `127.0.0.1:7497`, `18789`, `18791`, bridge/tunnel/proxy endpoints, guessed endpoints, unapproved endpoint substitutions. |
| Trading and pipeline activity | Broker submit readiness, live trading readiness, package capture, replay, scoring, candidate generation, strategy decisions, risk decisions, execution behavior, Unit 12 opening. |

## Redaction Rules

D11.71 must require redaction before retention of any accidental account,
order, execution, credential, token, secret, account-identifying, or
person-identifying content. If redaction is not possible, the artifact must be
marked fail-closed and excluded from eligibility adjudication.

Redaction markers must preserve enough context to show the prohibited field
class without retaining the prohibited value. A redacted prohibited field still
forces fail-closed capture adjudication because the field appeared.

## Required PASS/FAIL Markers

D11.71 must require these markers:

- `LOCAL_MAC_CONTEXT_PASS` or `LOCAL_MAC_CONTEXT_FAIL`;
- `ENDPOINT_CANDIDATE_SCOPE_PASS` or `ENDPOINT_CANDIDATE_SCOPE_FAIL`;
- `READ_ONLY_SOCKET_SCOPE_PASS` or `READ_ONLY_SOCKET_SCOPE_FAIL`;
- `API_CONNECTION_MODE_PASS` or `API_CONNECTION_MODE_FAIL`;
- `HISTORICAL_BARS_SCOPE_PASS` or `HISTORICAL_BARS_SCOPE_FAIL`;
- `FORBIDDEN_FIELDS_ABSENT_PASS` or `FORBIDDEN_FIELDS_ABSENT_FAIL`;
- `NEGATIVE_AUTHORITY_PASS` or `NEGATIVE_AUTHORITY_FAIL`;
- `ADJUDICATION_READY_PASS` or `ADJUDICATION_READY_FAIL`.

Missing, ambiguous, or contradictory markers force fail-closed adjudication.

## Required Artifact Sections

D11.71 must require a non-executable artifact with these sections:

| Artifact section | Required content |
| --- | --- |
| `artifact_identity` | Artifact name, D11 gate, D11.70 authorization reference, source commit, operator role label, creation timestamp in UTC, local timezone name. |
| `operator_context` | `LOCAL_MAC_ONLY`, `DIRECT_MAC_TERMINAL`, LOCAL_MAC process context, endpoint candidate `127.0.0.1:7497`, no VPS, no bridge, no tunnel, no proxy. |
| `source_control_references` | D11.57 accepted evidence reference, D11.69 contract reference, D11.70 authorization reference, and D11.71 execution packet reference. |
| `target_results` | One PASS/FAIL/NOT_COLLECTED marker per target ID, required timestamps, timezone fields, and adjudication-ready summary. |
| `redactions` | Required redaction markers for any accidental prohibited content. |
| `prohibited_fields_attestation` | Statement that forbidden fields were not requested, returned, retained, or logged; any violation must be marked FAIL. |
| `negative_authority_attestation` | Statement that no account/order/execution/position/balance/portfolio/credential/submit/cancel/modify/flatten/sell/cleanup authority was requested or used. |
| `locality_attestation` | Statement that LOCAL_MAC `127.0.0.1:7497` is not VPS `127.0.0.1:7497`; VPS and `18789`/`18791` were not used. |
| `adjudication_summary` | Historical data availability, endpoint locality, read-only socket scope, API connection mode, provider-readiness metadata, negative authority evidence, unresolved provider-eligibility blockers, and final PASS/FAIL marker. |

## Future Capture Fail-Closed Conditions

D11.71 must fail closed before or during capture if any of these occur:

- the source context is not `LOCAL_MAC_ONLY`;
- the operator surface is not `DIRECT_MAC_TERMINAL`;
- the endpoint candidate is not `127.0.0.1:7497`;
- LOCAL_MAC `127.0.0.1:7497` is treated as VPS `127.0.0.1:7497`;
- VPS, `18789`, `18791`, bridge, tunnel, proxy, guessed endpoint, or
  unapproved endpoint substitution is introduced;
- account, order, execution, position, balance, portfolio, P&L, margin, buying
  power, trade, credential, token, or session-secret data is requested,
  returned, retained, or logged;
- submit, cancel, modify, flatten, sell, cleanup, broker submit readiness, live
  trading readiness, or Unit 12 opening is introduced;
- service, scheduler, systemd, timer, runtime, environment, TWS/Gateway,
  openclaw-gateway, VPS, credential, strategy, risk, execution, package
  capture, replay, scoring, or candidate-generation mutation is introduced;
- required artifact sections, required redactions, timestamps/timezone fields,
  PASS/FAIL markers, source-control references, or adjudication summary fields
  are missing;
- executable instructions exceed the D11.70 authorization boundary or conflict
  with the D11.69 contract.

## Non-Authorized Contexts

D11.70 does not authorize VPS evidence, `18789` evidence, `18791` evidence,
bridge/tunnel/proxy evidence, broker account evidence, order evidence,
execution evidence, position evidence, balance evidence, portfolio evidence,
credential evidence, broker submit readiness, live trading readiness, Unit 12
opening, package capture, replay, scoring, candidate generation, runtime
mutation, provider-selection runtime behavior change, or production deployment.

## Localhost and Endpoint Boundaries

`127.0.0.1` is process-context local. LOCAL_MAC `127.0.0.1:7497` is not
equivalent to VPS `127.0.0.1:7497`.

D11.70 rejects treating LOCAL_MAC `127.0.0.1:7497` as VPS
`127.0.0.1:7497`. D11.70 rejects `18789` and `18791` as approved market-data
endpoints. Any future use of VPS `127.0.0.1:7497`, `18789`, or `18791` requires
a separate source-controlled endpoint adjudication and is outside D11.70.

## Provider Eligibility Boundaries

Future evidence capture may support later market-data provider-readiness
adjudication, but it cannot itself approve IBKR primary eligibility.

The provider eligibility blockers remain active:

- `ibkr_market_data_candidate` remains `broker_coupled=true`;
- `ibkr_market_data_candidate` remains `d11_primary_eligible=false`;
- `d11_primary_candidate_status` remains `candidate`;
- `candidate_can_count_for_d11` remains unsatisfied.

`IBKR_PRIMARY_ELIGIBILITY` remains `NOT_APPROVED`. D11 remains
`D11_INSUFFICIENT`. Unit 12 remains `UNIT_12_BLOCKED`. Broker submit readiness
and live trading readiness remain unapproved.

## Next Gate

The exact next permissible gate is:

```text
D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET
```

D11.71 may be the first gate allowed to contain exact bounded execution
instructions for LOCAL_MAC-only read-only market-data evidence capture, but
only if it remains inside the D11.70 authorization packet and the D11.69
contract. D11.70 itself does not collect evidence and does not create executable
evidence-capture commands.

## Status Preserved

```text
d11_70_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE
authorized_gate_only=D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET
d11_70_evidence_collected=false
d11_70_executable_evidence_capture_commands_created=false
runtime_broker_vps_scheduler_systemd_credential_action=false
production_provider_selection_behavior_changed=false
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
package_capture=BLOCKED
vps_runtime=NOT_TOUCHED
account_order_execution_authority=false
broker_submit_readiness=NOT_APPROVED
live_trading_readiness=NOT_APPROVED
next_permissible_gate=D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET
```

D11.70 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, evidence collection
in D11.70, executable evidence-capture commands in D11.70, or IBKR primary
eligibility approval.
