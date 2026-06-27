# D11.71 LOCAL_MAC Read-Only Evidence Capture Execution Packet

D11.71 is the source-controlled execution packet for the future bounded
LOCAL_MAC-only read-only market-data evidence capture authorized by D11.70 and
contracted by D11.69. D11.71 defines the exact future operator instructions
for the next gate only. D11.71 does not execute evidence capture, does not run
broker/TWS/API/network/runtime commands, does not connect to IBKR, does not
inspect or mutate TWS/Gateway, does not perform VPS actions, does not run
service/systemd/scheduler/timer/runtime commands, does not access credentials
or environment files, does not access account/order/execution/position/
balance/portfolio/trade/P&L/margin/buying-power data, does not open Unit 12,
does not approve IBKR primary eligibility, and does not imply broker submit
readiness or live trading readiness.

Decision: execution packet ready for a future D11.72 operator run.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET` |
| `source_commit` | `2f05f254f54f2feb87760820ddc48456e48f0c89` |
| `d11_70_classification` | `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET` |
| `d11_70_decision` | `LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE` |
| `d11_70_authorized_gate_only` | `D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET` |
| `d11_69_decision` | `READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY` |
| `d11_71_decision` | `LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY` |
| `future_execution_source_context` | `LOCAL_MAC_ONLY` |
| `future_execution_operator_surface` | `DIRECT_MAC_TERMINAL` |
| `future_execution_endpoint_candidate` | `127.0.0.1:7497` |
| `future_execution_endpoint_class` | `IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE` |
| `future_execution_symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR` |
| `future_execution_timeframe` | `15Min` |
| `future_execution_lookback_minutes` | `120` |
| `d11_71_evidence_capture_executed` | `false` |
| `d11_71_broker_tws_api_network_runtime_action` | `false` |
| `d11_71_executable_commands_run_by_codex` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `remaining_provider_eligibility_blockers` | `broker_coupled_true; d11_primary_eligible_false; d11_primary_candidate_status_candidate; candidate_can_count_for_d11_unsatisfied` |
| `next_permissible_gate` | `D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN` |

## Source-Controlled Preconditions for Future Execution

D11.72 may proceed only if all of these preconditions are true at the future
operator-run gate:

| Precondition | Required value |
| --- | --- |
| Working directory | `/Users/openclawcontrol/Documents/openclaw-stocks` |
| Branch | `main` |
| Source commit | Must match the source-controlled commit authorized by the future D11.72 packet. |
| Worktree | Clean before the operator run. |
| Source context | `LOCAL_MAC_ONLY` |
| Operator surface | `DIRECT_MAC_TERMINAL` |
| Endpoint candidate | `127.0.0.1:7497` only |
| Endpoint class | IBKR Paper TWS/Gateway local socket candidate |
| TWS/Gateway state | Already manually open by the operator before future capture; D11.72 must not start, stop, restart, inspect, or mutate TWS/Gateway. |
| Python | `.venv-312/bin/python` |
| Scope | Read-only historical market-data-only evidence for provider-readiness adjudication. |

Wrong branch, dirty worktree, HEAD mismatch, wrong directory, wrong endpoint,
wrong source context, wrong operator surface, or TWS/Gateway not already
manually open by the operator before future capture must force fail-closed
handling.

## Exact Operator Context Required Before Future Execution

D11.72 must require the operator to confirm, before any future execution, that:

- the operator is on the LOCAL_MAC host;
- the terminal is a direct Mac terminal, not VPS, bridge, tunnel, proxy, or
  remote shell;
- the repository path is `/Users/openclawcontrol/Documents/openclaw-stocks`;
- TWS/Gateway is already manually open before the future capture;
- D11.72 will not start, stop, restart, inspect, or mutate TWS/Gateway;
- the endpoint candidate is only `127.0.0.1:7497`;
- `18789` and `18791` are not approved market-data endpoints;
- no account/order/execution/position/balance/portfolio/credential access is
  requested, returned, retained, or logged.

## Future Operator Command: Not Run in D11.71

The following command is the exact future D11.72 operator command. It is
source-controlled here for the next gate only.

```bash
# FUTURE D11.72 ONLY - DO NOT RUN IN D11.71
cd /Users/openclawcontrol/Documents/openclaw-stocks
.venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR --timeframe 15Min --lookback-minutes 120 --host 127.0.0.1 --port 7497 --client-id 9117 --exchange SMART --currency USD --sec-type STK --timeout-seconds 10 --authorize-local-ibkr-read-only-smoke
```

This future command is bounded to LOCAL_MAC, direct terminal operation,
endpoint candidate `127.0.0.1:7497`, historical market-data-only scope, symbols
`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`, timeframe `15Min`, and lookback
`120 minutes`. It does not authorize D11.71 execution. Codex did not run this
command in D11.71.

## Expected Artifact Fields

D11.72 must retain only a compact adjudication-ready artifact or terminal
output with these fields:

| Artifact area | Required fields |
| --- | --- |
| Run identity | `artifact_name`, `gate=D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`, `source_commit`, `operator_role`, `created_at_utc`, `local_timezone`. |
| Operator context | `source_context=LOCAL_MAC_ONLY`, `operator_surface=DIRECT_MAC_TERMINAL`, `process_context=LOCAL_MAC`, `endpoint_host=127.0.0.1`, `endpoint_port=7497`, `endpoint_class=IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE`, `vps_used=false`, `bridge_tunnel_proxy_used=false`. |
| Request scope | `symbols=AAPL,MSFT,NVDA,TSLA,MSTR`, `timeframe=15Min`, `lookback_minutes=120`, `historical_market_data_only=true`, `exchange=SMART`, `currency=USD`, `sec_type=STK`. |
| Per-symbol result | `symbol`, `timeframe`, `requested_start`, `requested_end`, `latest_candle_timestamp`, `lag_minutes`, `freshness_classification`, `d11_countable`, `d11_primary_candidate_status=candidate`, `d11_primary_eligible=false`, `failure_reason`. |
| Provider metadata | `provider_key`, `provider_name`, `connection_mode=local_read_only_smoke`, `read_only=true`, `authority_boundary`. |
| Negative authority | `broker_api_authority=false`, `order_authority=false`, `execution_authority=false`, `package_capture=false`, `replay=false`, `scoring=false`, `candidate_generation=false`, `d11_completion_authority=false`, `unit_12_opened=false`. |
| Locality summary | `local_mac_127_0_0_1_7497_not_vps_127_0_0_1_7497=true`, `vps_endpoint_used=false`, `port_18789_used=false`, `port_18791_used=false`. |
| Adjudication summary | PASS/FAIL markers, redaction summary, forbidden-field summary, final `ADJUDICATION_READY_PASS` or `ADJUDICATION_READY_FAIL`. |

## Required PASS/FAIL Markers

D11.72 output must include exactly these PASS/FAIL marker families:

- `LOCAL_MAC_CONTEXT_PASS` or `LOCAL_MAC_CONTEXT_FAIL`;
- `DIRECT_MAC_TERMINAL_PASS` or `DIRECT_MAC_TERMINAL_FAIL`;
- `ENDPOINT_127_0_0_1_7497_SCOPE_PASS` or `ENDPOINT_127_0_0_1_7497_SCOPE_FAIL`;
- `NO_VPS_18789_18791_BRIDGE_TUNNEL_PROXY_PASS` or
  `NO_VPS_18789_18791_BRIDGE_TUNNEL_PROXY_FAIL`;
- `SYMBOL_SCOPE_PASS` or `SYMBOL_SCOPE_FAIL`;
- `TIMEFRAME_15MIN_PASS` or `TIMEFRAME_15MIN_FAIL`;
- `LOOKBACK_120_MINUTES_PASS` or `LOOKBACK_120_MINUTES_FAIL`;
- `HISTORICAL_BARS_SCOPE_PASS` or `HISTORICAL_BARS_SCOPE_FAIL`;
- `FORBIDDEN_FIELDS_ABSENT_PASS` or `FORBIDDEN_FIELDS_ABSENT_FAIL`;
- `NEGATIVE_AUTHORITY_PASS` or `NEGATIVE_AUTHORITY_FAIL`;
- `ADJUDICATION_READY_PASS` or `ADJUDICATION_READY_FAIL`.

Missing, ambiguous, duplicated, or contradictory PASS/FAIL markers force
fail-closed handling.

## Required Redactions

If any accidental account, order, execution, position, balance, portfolio, P&L,
margin, buying power, credential, token, secret, account-identifying, or
person-identifying value appears, D11.72 must redact the value, mark the
artifact `FORBIDDEN_FIELDS_ABSENT_FAIL`, mark `ADJUDICATION_READY_FAIL`, and
exclude the artifact from eligibility approval.

Redaction never converts a forbidden-field violation into a passing artifact.

## Forbidden Fields and Forbidden Contexts

D11.72 must not request, return, retain, or log these fields or contexts:

- account IDs, account aliases, account values, balances, buying power, margin,
  portfolio contents, positions, position quantities, position values, P&L,
  cash, equity, net liquidation, account summary, account ledger;
- open orders, order IDs, order status, executions, fills, trade history,
  commission reports, submit endpoints, cancel endpoints, modify endpoints,
  flatten/sell/cleanup evidence;
- usernames, passwords, tokens, API keys, session secrets, cookies, credential
  file paths, environment variable values, authentication challenge contents;
- VPS, `18789`, `18791`, bridge, tunnel, proxy, guessed endpoints, unapproved
  endpoint substitutions;
- service, systemd, scheduler, timer, runtime, environment, TWS/Gateway,
  openclaw-gateway, VPS, credential, strategy, risk, execution, or
  provider-selection runtime mutation;
- broker submit readiness, live trading readiness, package capture, replay,
  scoring, candidate generation, strategy decisions, risk decisions, execution
  behavior, Unit 12 opening, or IBKR primary eligibility approval.

## Future Run Fail-Closed Conditions

D11.72 must fail closed if any of these occur:

- branch is not `main`;
- worktree is dirty;
- HEAD does not match the D11.72-authorized commit;
- endpoint is not `127.0.0.1:7497`;
- source context is not `LOCAL_MAC_ONLY`;
- operator surface is not `DIRECT_MAC_TERMINAL`;
- TWS/Gateway is not already manually open by the operator before future
  capture;
- request attempts account/order/execution/position/balance/portfolio/
  credential access;
- any forbidden field appears in output;
- any symbol outside `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR` appears;
- any timeframe other than `15Min` appears;
- lookback/request scope is not `120 minutes`;
- VPS, `18789`, `18791`, bridge, tunnel, proxy, service, systemd, scheduler,
  timer, runtime mutation, environment mutation, package capture, replay,
  scoring, candidate generation, strategy/risk/execution mutation, live
  readiness, broker submit readiness, Unit 12 opening, or IBKR primary approval
  appears;
- required artifact fields, required PASS/FAIL markers, required redactions, or
  source-control references are missing.

## Post-Capture Review Requirements for the Next Gate

After any future D11.72 operator run, the next source-controlled review gate
must inspect only the compact D11.72 artifact or terminal output and must:

1. verify every PASS/FAIL marker;
2. verify symbol, timeframe, lookback, endpoint, and LOCAL_MAC-only boundaries;
3. verify forbidden fields did not appear;
4. verify negative-authority markers;
5. verify `IBKR_PRIMARY_ELIGIBILITY` remains `NOT_APPROVED`;
6. verify D11 remains `D11_INSUFFICIENT`;
7. verify Unit 12 remains `UNIT_12_BLOCKED`;
8. preserve provider eligibility blockers unless a later source-controlled
   adjudication explicitly revises them.

## Provider Eligibility and Authority Boundaries

Future evidence capture may support later market-data provider-readiness
adjudication, but it cannot itself approve IBKR primary eligibility.

The provider eligibility blockers remain active:

- `ibkr_market_data_candidate` remains `broker_coupled=true`;
- `ibkr_market_data_candidate` remains `d11_primary_eligible=false`;
- `d11_primary_candidate_status` remains `candidate`;
- `candidate_can_count_for_d11` remains unsatisfied.

`IBKR_PRIMARY_ELIGIBILITY` remains `NOT_APPROVED`. D11 remains
`D11_INSUFFICIENT`. Unit 12 remains `UNIT_12_BLOCKED`. Broker submit readiness
and live trading readiness remain `NOT_APPROVED`.

## Next Gate

The exact next permissible gate is:

```text
D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN
```

D11.72 may be the first gate where the operator actually runs the bounded
LOCAL_MAC-only read-only evidence capture, but only if the run remains inside
the D11.71 execution packet, the D11.70 authorization packet, and the D11.69
contract.

## Status Preserved

```text
d11_71_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY
d11_71_evidence_capture_executed=false
d11_71_broker_tws_api_network_runtime_action=false
d11_71_executable_commands_run_by_codex=false
production_provider_selection_behavior_changed=false
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
broker_submit_readiness=NOT_APPROVED
live_trading_readiness=NOT_APPROVED
remaining_provider_eligibility_blockers=broker_coupled_true; d11_primary_eligible_false; d11_primary_candidate_status_candidate; candidate_can_count_for_d11_unsatisfied
next_permissible_gate=D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN
```

D11.71 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic by Codex, runtime mutation,
timer mutation, service mutation, systemd mutation, TWS mutation, Gateway
mutation, openclaw-gateway mutation, scheduler mutation, credential access,
Unit 12 opening, broker submit readiness, live-trading readiness, evidence
capture in D11.71, executable command execution by Codex, or IBKR primary
eligibility approval.
