# D11.77 Fresh Regular-Session Read-Only Evidence Capture Adjudication

D11.77 is the source-controlled adjudication gate for the D11.75/D11.76 clean,
countable, fresh regular-session LOCAL_MAC-only read-only IBKR market-data
evidence. It adjudicates only already-recorded source-controlled evidence. It
does not rerun IBKR, does not execute evidence capture, does not run broker/
TWS/API/network/runtime commands, does not connect to IBKR, does not inspect,
open, close, mutate, restart, or query TWS/Gateway, does not perform VPS
actions, does not run service/systemd/scheduler/timer/runtime commands, does
not access credentials or environment files, does not access account/order/
execution/position/balance/portfolio/trade/P&L/margin/buying-power/credential
data, does not change production provider-selection runtime behavior, does not
generate package captures, runtime reports, replay output, scoring output,
candidate-generation output, or live-trading output, does not approve broker
submit readiness, does not approve live trading readiness, does not open Unit
12, and does not infer approval from lane name, option order, prior assistant
expectation, user framing, or desired outcome.

Decision: the D11.75/D11.76 evidence is clean and countable, but insufficient
to approve IBKR primary eligibility or close D11 because source-controlled
primary-eligibility criteria still require candidate-status, primary-eligible,
broker-coupling, and `candidate_can_count_for_d11` resolution.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION` |
| `source_commit` | `1afb04c64275e039d598203dcbcc40b3b2ef9bc2` |
| `d11_76_classification` | `IBKR_D11_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD` |
| `d11_76_evidence_classification` | `FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE` |
| `d11_75_source_commit` | `6db5d0b2f1cc47679dd194c846206a0dde36693c` |
| `d11_75_76_source_context` | `LOCAL_MAC_ONLY` |
| `d11_75_76_operator_surface` | `DIRECT_MAC_TERMINAL` |
| `d11_75_76_endpoint_candidate` | `127.0.0.1:7497` |
| `d11_75_76_symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR` |
| `d11_75_76_timeframe` | `15Min` |
| `d11_75_76_lookback_minutes` | `120` |
| `d11_77_decision` | `D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY` |
| `d11_77_evidence_collected` | `false` |
| `d11_77_executable_broker_tws_api_network_runtime_command_run` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_behavior_changed` | `false` |
| `d11_77_commit_performed` | `false` |
| `d11_77_push_performed` | `false` |
| `d11_75_76_all_symbols_freshness_classification` | `clean` |
| `d11_75_76_all_symbols_d11_countable` | `true` |
| `d11_75_76_all_symbols_failure_reason` | `` |
| `d11_75_76_all_symbols_d11_primary_eligible` | `false` |
| `d11_75_76_all_symbols_d11_primary_candidate_status` | `candidate` |
| `ibkr_primary_eligibility_before_d11_77` | `NOT_APPROVED` |
| `ibkr_primary_eligibility_after_d11_77` | `NOT_APPROVED` |
| `d11_status_before_d11_77` | `D11_INSUFFICIENT` |
| `d11_status_after_d11_77` | `D11_INSUFFICIENT` |
| `unit_12_status_before_d11_77` | `UNIT_12_BLOCKED` |
| `unit_12_status_after_d11_77` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_order_execution_authority` | `false` |
| `package_capture` | `false` |
| `replay` | `false` |
| `scoring` | `false` |
| `candidate_generation` | `false` |
| `primary_blockers_remaining` | `d11_primary_candidate_status_candidate; d11_primary_eligible_false; broker_coupled_true; candidate_can_count_for_d11_unsatisfied; separate_vps_read_only_freshness_proof_required_before_primary_eligibility_unrevised` |
| `next_permissible_gate` | `D11.78_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION` |

## D11.75/D11.76 Evidence Basis

D11.77 accepts the D11.75/D11.76 evidence as clean and countable for D11
market-data evidence review:

- source context was `LOCAL_MAC_ONLY`;
- operator surface was `DIRECT_MAC_TERMINAL`;
- endpoint candidate was `127.0.0.1:7497`;
- symbol scope was `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`;
- timeframe was `15Min`;
- lookback was `120 minutes`;
- authority was `READ_ONLY_MARKET_DATA_ONLY`;
- result type was `ibkr_local_read_only_market_data_smoke`;
- all five symbols returned `freshness_classification=clean`;
- all five symbols returned `d11_countable=true`;
- all five symbols returned an empty `failure_reason`;
- all five symbols recorded
  `latest_candle_timestamp=2026-06-29T14:00:00+00:00`;
- all five symbols recorded
  `requested_start=2026-06-29T12:20:17.713714+00:00`;
- all five symbols recorded
  `requested_end=2026-06-29T14:20:17.713714+00:00`;
- all five symbols recorded `lag_minutes=20.295228566666665`.

This evidence basis is countability evidence. It is not, by itself, provider
approval evidence.

## Per-Symbol Adjudication

| Symbol | Read only | Provider key | Provider name | Connection mode | Latest candle timestamp | Requested start | Requested end | Lag minutes | Freshness classification | Failure reason | D11 countable | D11 primary eligible | Candidate status | Timeframe | D11.77 adjudication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AAPL` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` | `COUNTABLE_BUT_PRIMARY_ELIGIBILITY_NOT_APPROVED` |
| `MSFT` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` | `COUNTABLE_BUT_PRIMARY_ELIGIBILITY_NOT_APPROVED` |
| `NVDA` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` | `COUNTABLE_BUT_PRIMARY_ELIGIBILITY_NOT_APPROVED` |
| `TSLA` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` | `COUNTABLE_BUT_PRIMARY_ELIGIBILITY_NOT_APPROVED` |
| `MSTR` | `true` | `ibkr_market_data_candidate` | `IBKR read-only market-data diagnostic candidate` | `local_read_only_smoke` | `2026-06-29T14:00:00+00:00` | `2026-06-29T12:20:17.713714+00:00` | `2026-06-29T14:20:17.713714+00:00` | `20.295228566666665` | `clean` | `` | `true` | `false` | `candidate` | `15Min` | `COUNTABLE_BUT_PRIMARY_ELIGIBILITY_NOT_APPROVED` |

## Countability Adjudication

D11.77 adjudicates the D11.75/D11.76 evidence as countable D11 market-data
evidence:

```text
d11_75_76_clean_countable_evidence=ACCEPTED
```

This satisfies the narrow freshness/countability problem that blocked D11.72
after D11.73. The earlier recency-caveat blocker is no longer active for the
D11.75/D11.76 evidence.

Countability is not the same as provider approval. A row can be clean and
countable while still reporting `d11_primary_eligible=false` and candidate
status. D11.77 therefore separates the clean evidence result from the
primary-eligibility status result.

## Primary Eligibility Adjudication

D11.77 does not approve IBKR primary eligibility:

```text
IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED
```

The clean countable evidence is insufficient because the inspected
source-controlled criteria still contain unresolved provider-eligibility
requirements:

- all five D11.75/D11.76 symbols still returned
  `d11_primary_eligible=false`;
- all five D11.75/D11.76 symbols still returned
  `d11_primary_candidate_status=candidate`;
- `market_data_provider_selection.py` still records
  `ibkr_market_data_candidate` as `broker_coupled=true`;
- `candidate_can_count_for_d11` still requires
  `d11_primary_candidate_status=approved_primary`,
  `d11_primary_eligible=true`, `order_authority=false`,
  `execution_authority=false`, and `broker_coupled=false`;
- `D11_PRIMARY_PROVIDER_SELECTION_CRITERIA` still includes
  `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`;
- no D11.77 source-controlled criteria revision changes the candidate status,
  primary-eligible flag, broker-coupling compatibility rule, or
  `candidate_can_count_for_d11` criteria.

D11.77 adjudicates the tension directly: the D11.75/D11.76 evidence is clean
and countable, but the same rows explicitly report that the provider remains a
non-primary-approved candidate. The clean evidence supports market-data
availability and freshness; it does not override the candidate-contract and
criteria blockers.

## D11 Status Adjudication

D11 remains insufficient:

```text
D11=D11_INSUFFICIENT
```

D11.77 cannot close D11 while IBKR primary eligibility remains
`NOT_APPROVED` and the provider-candidate blockers remain active.

## Unit 12 Status Adjudication

Unit 12 remains blocked:

```text
UNIT_12=UNIT_12_BLOCKED
```

D11.77 does not open Unit 12. D11.77 defines no Unit 12 implementation, no
strategy execution, no runtime deployment, no broker submit readiness, and no
live trading readiness.

## Negative-Authority Adjudication

D11.77 accepts the D11.75/D11.76 negative-authority evidence and records that
no forbidden authority appeared:

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
- `no_vps_endpoint`
- `no_18789`
- `no_18791`
- `no_bridge`
- `no_tunnel`
- `no_proxy`

The absence of forbidden authority supports the countability of the evidence
for read-only market-data review. It does not create account, order,
execution, broker submit, live trading, package capture, replay, scoring,
candidate-generation, runtime, VPS, or Unit 12 authority.

## Remaining Blockers

The prior D11.72 recency blocker is satisfied for D11.75/D11.76 because the
fresh regular-session evidence is clean and countable.

These blockers remain:

1. `d11_primary_candidate_status=candidate` remains recorded for all five
   rows and in the source-controlled provider candidate.
2. `d11_primary_eligible=false` remains recorded for all five rows and in the
   source-controlled provider candidate.
3. `ibkr_market_data_candidate` remains `broker_coupled=true` in
   `market_data_provider_selection.py`; no source-controlled compatibility
   adjudication in D11.77 makes that compatible with primary eligibility.
4. `candidate_can_count_for_d11` remains unsatisfied because the candidate is
   not `approved_primary`, is not `d11_primary_eligible=true`, and remains
   broker-coupled.
5. `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`
   remains unrevised in `D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`.

Clean `d11_countable=true` evidence is not enough because the active criteria
distinguish market-data evidence countability from provider primary approval.

## Still-Unapproved Authorities

D11.77 leaves these authorities unapproved:

- IBKR primary eligibility;
- D11 completion;
- Unit 12 opening;
- broker submit readiness;
- live trading readiness;
- account query authority;
- position query authority;
- portfolio query authority;
- balance query authority;
- margin query authority;
- buying-power query authority;
- order placement authority;
- order modification authority;
- order cancellation authority;
- order routing authority;
- execution authority;
- package capture;
- runtime reports;
- replay output;
- scoring output;
- candidate generation;
- strategy behavior changes;
- risk behavior changes;
- execution behavior changes;
- scheduler behavior changes;
- credential or environment-file changes;
- VPS runtime/systemd/timer mutation;
- TWS/Gateway inspection, open, close, restart, mutation, or query.

## No D11.77 Evidence Capture or Runtime Action

D11.77 collected no evidence. D11.77 ran no executable broker/TWS/API/network/
runtime command. D11.77 performed no broker, TWS, API, network, runtime, VPS,
scheduler, systemd, timer, credential, environment, package-capture, replay,
scoring, candidate-generation, live-trading, account, order, execution,
position, balance, portfolio, margin, buying-power, trade, P&L, strategy, risk,
or production provider-selection runtime action.

D11.77 performed no commit and no push.

## Next Permissible Gate

The exact next permissible gate is:

```text
D11.78_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION
```

D11.78 must remediate the exact remaining source-controlled blockers before any
future approval attempt: candidate status, `d11_primary_eligible=false`,
broker-coupling compatibility, `candidate_can_count_for_d11`, and the unrevised
separate VPS read-only freshness proof criterion. D11.78 must remain
source-controlled and must not perform evidence capture, broker/TWS/API/
network/runtime/VPS/scheduler/systemd/credential/live-trading work, Unit 12
opening, broker submit readiness approval, live trading readiness approval, or
production provider-selection runtime behavior mutation unless a separately
scoped future authority explicitly permits it.
