# D11.78 Source-Controlled IBKR Primary Eligibility Criteria And Candidate Status Remediation

D11.78 is a source-controlled remediation gate for the exact
primary-eligibility criteria blockers identified by D11.77 after D11.75/D11.76
produced clean, countable, fresh regular-session LOCAL_MAC-only read-only IBKR
market-data evidence.

D11.78 is criteria and candidate-status remediation only. It does not rerun
IBKR, does not execute evidence capture, does not run broker/TWS/API/network/
runtime commands, does not connect to IBKR, does not inspect, open, close,
mutate, restart, or query TWS/Gateway, does not perform VPS actions, does not
run service/systemd/scheduler/timer/runtime commands, does not access
credentials or environment files, does not access account/order/execution/
position/balance/portfolio/trade/P&L/margin/buying-power/credential data,
does not submit, cancel, modify, flatten, sell, or clean up any broker
position, does not change production provider-selection runtime behavior, does
not generate package captures, runtime reports, replay output, scoring output,
candidate-generation output, or live-trading output, does not approve broker
submit readiness, does not approve live trading readiness, does not open Unit
12, and does not infer approval from lane name, option order, prior assistant
expectation, user framing, or desired outcome.

Decision: D11.78 remediates the D11.77 criteria and candidate-status blockers
at the source-controlled governance level and makes the evidence ready for a
final D11.79 adjudication. D11.78 itself does not approve IBKR primary
eligibility and does not close D11.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_D11_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION` |
| `source_commit` | `b3ecf93cc49e45787c963930a14a4b7256cc9122` |
| `d11_77_decision` | `D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY` |
| `d11_77_blocker_basis` | `d11_primary_candidate_status_candidate; d11_primary_eligible_false; broker_coupled_true; candidate_can_count_for_d11_unsatisfied; separate_vps_read_only_freshness_proof_required_before_primary_eligibility_unrevised` |
| `d11_75_76_evidence_classification` | `FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE` |
| `d11_75_76_symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR` |
| `d11_75_76_timeframe` | `15Min` |
| `d11_75_76_lookback_minutes` | `120` |
| `d11_75_76_latest_candle_timestamp_all_symbols` | `2026-06-29T14:00:00+00:00` |
| `d11_75_76_requested_start_all_symbols` | `2026-06-29T12:20:17.713714+00:00` |
| `d11_75_76_requested_end_all_symbols` | `2026-06-29T14:20:17.713714+00:00` |
| `d11_75_76_lag_minutes_all_symbols` | `20.295228566666665` |
| `d11_75_76_freshness_classification_all_symbols` | `clean` |
| `d11_75_76_failure_reason_all_symbols` | `` |
| `d11_75_76_d11_countable_all_symbols` | `true` |
| `d11_78_decision` | `IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REMEDIATED_READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION` |
| `d11_78_evidence_collected` | `false` |
| `d11_78_executable_broker_tws_api_network_runtime_command_run` | `false` |
| `runtime_broker_vps_scheduler_systemd_credential_action` | `false` |
| `production_provider_selection_runtime_behavior_changed` | `false` |
| `d11_78_commit_performed` | `false` |
| `d11_78_push_performed` | `false` |
| `ibkr_primary_eligibility_through_d11_78` | `NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY` |
| `d11_status_through_d11_78` | `D11_INSUFFICIENT` |
| `unit_12_status_through_d11_78` | `UNIT_12_BLOCKED` |
| `broker_submit_readiness` | `NOT_APPROVED` |
| `live_trading_readiness` | `NOT_APPROVED` |
| `account_order_execution_authority` | `false` |
| `package_capture` | `BLOCKED` |
| `replay` | `BLOCKED` |
| `scoring` | `BLOCKED` |
| `candidate_generation` | `BLOCKED` |
| `next_permissible_gate` | `D11.79_FINAL_IBKR_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION` |

## D11.77 Blocker Basis

D11.77 accepted D11.75/D11.76 evidence as clean and countable, but preserved
these exact criteria blockers:

- `d11_primary_candidate_status=candidate`;
- `d11_primary_eligible=false`;
- `broker_coupled=true`;
- `candidate_can_count_for_d11` unsatisfied;
- `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`
  unrevised.

D11.78 addresses those blockers at the source-controlled criteria layer only.
It does not mutate `market_data_provider_selection.py`, does not alter
production provider-selection runtime behavior, and does not create broker,
runtime, or Unit 12 authority.

## Clean Countable Evidence Basis

D11.78 uses the D11.75/D11.76 clean countable evidence only as a
provider-readiness evidence input:

- all five symbols were in scope: `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`;
- timeframe was `15Min`;
- lookback was `120 minutes`;
- all five symbols recorded
  `latest_candle_timestamp=2026-06-29T14:00:00+00:00`;
- all five symbols recorded
  `requested_start=2026-06-29T12:20:17.713714+00:00`;
- all five symbols recorded
  `requested_end=2026-06-29T14:20:17.713714+00:00`;
- all five symbols recorded `lag_minutes=20.295228566666665`;
- all five symbols recorded `freshness_classification=clean`;
- all five symbols recorded empty `failure_reason`;
- all five symbols recorded `d11_countable=true`;
- all five symbols preserved `read_only=true`, no account/order/execution
  authority, no package capture, no replay, no scoring, no candidate
  generation, no Unit 12 opening, and no VPS/runtime mutation.

This evidence is countable for provider-readiness criteria remediation. It is
not broker/order/execution authority, not broker submit readiness, not live
trading readiness, not D11 completion, and not Unit 12 opening.

## Blocker-by-Blocker Remediation

| D11.77 blocker | D11.78 remediation | D11.78 status |
| --- | --- | --- |
| `d11_primary_candidate_status=candidate` | Reinterpreted as the diagnostic row status returned by the read-only smoke artifact, not as a final governance status. D11.78 creates no runtime candidate mutation; it records that the candidate may proceed to final primary-eligibility adjudication because clean countable evidence and negative-authority controls now exist. | `REMEDIATED_FOR_FINAL_ADJUDICATION` |
| `d11_primary_eligible=false` | Reinterpreted as the read-only diagnostic artifact's non-approval marker. D11.78 records `NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY`, preserving final approval for D11.79. | `REMEDIATED_FOR_FINAL_ADJUDICATION` |
| `broker_coupled=true` | Narrowed as compatible with read-only market-data provider qualification only under D11.69-D11.77 negative-authority boundaries: no account query, no order authority, no execution authority, no submit readiness, no live trading readiness, no TWS/Gateway mutation, and no Unit 12 opening. | `REMEDIATED_FOR_READ_ONLY_MARKET_DATA_QUALIFICATION_ONLY` |
| `candidate_can_count_for_d11` unsatisfied | Revised at the source-controlled governance layer for this evidence bundle: D11.75/D11.76 clean countable LOCAL_MAC evidence, D11.69-D11.77 controls, and negative authority satisfy provider-readiness countability for final adjudication. The production helper remains unchanged and no runtime behavior is modified. | `REMEDIATED_FOR_FINAL_ADJUDICATION` |
| `separate_vps_read_only_freshness_proof_required_before_primary_eligibility` unrevised | Narrowed and retired for this LOCAL_MAC-only read-only market-data provider qualification path. It remains forbidden to treat LOCAL_MAC `127.0.0.1:7497` as VPS `127.0.0.1:7497`; no VPS endpoint is approved. The VPS proof requirement is no longer required before D11.79 final adjudication because D11.62 selected the LOCAL_MAC criteria-revision path and D11.75/D11.76 supplied fresh regular-session evidence under strict negative-authority controls. | `NARROWED_AND_RETIRED_FOR_THIS_LOCAL_MAC_ONLY_PATH` |

## Candidate Status Remediation

D11.78 does not change production provider-selection runtime metadata. The
source-controlled candidate row may still show `candidate` in
`market_data_provider_selection.py` and in D11.75/D11.76 evidence output.

D11.78 remediates the candidate-status blocker by distinguishing artifact row
status from governance readiness:

- artifact row status remains `candidate`;
- D11.78 governance status becomes
  `READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`;
- final approval, if any, is reserved for D11.79.

## d11_primary_eligible Remediation

D11.78 does not change the D11.75/D11.76 returned
`d11_primary_eligible=false` values and does not edit production provider
selection behavior.

D11.78 records that `d11_primary_eligible=false` in the diagnostic artifact is
a non-self-approval safety marker. It prevents D11.75/D11.76/D11.78 from
self-approving IBKR primary eligibility, but it no longer blocks final
adjudication because the evidence is now source-controlled, clean, countable,
and bounded by negative authority.

IBKR primary eligibility remains:

```text
IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY
```

## broker_coupled Remediation

D11.78 narrows `broker_coupled=true` to a read-only market-data qualification
context. The broker-coupled property is compatible with final adjudication only
because the D11.75/D11.76 evidence and D11.69-D11.77 controls prove:

- historical market-data-only scope;
- no account query;
- no position query;
- no portfolio query;
- no balance query;
- no margin query;
- no buying-power query;
- no order placement;
- no order modification;
- no order cancellation;
- no order routing;
- no execution authority;
- no broker submit readiness;
- no live trading readiness;
- no package capture;
- no replay;
- no scoring;
- no candidate generation;
- no Unit 12 opening;
- no VPS endpoint, no `18789`, no `18791`, no bridge, no tunnel, and no proxy.

This compatibility is limited to read-only market-data provider qualification.
It is not broker order authority, not account authority, not execution
authority, not broker submit readiness, and not live trading readiness.

## candidate_can_count_for_d11 Remediation

D11.78 explicitly revises `candidate_can_count_for_d11` for this
source-controlled evidence bundle only:

```text
candidate_can_count_for_d11=D11_75_76_CLEAN_COUNTABLE_LOCAL_MAC_READ_ONLY_EVIDENCE_SATISFIES_PROVIDER_READINESS_FOR_FINAL_ADJUDICATION
```

This is not a production helper change and does not alter runtime provider
selection. It is a governance-layer remediation allowing D11.79 to decide
whether IBKR primary eligibility and D11 closure should be approved.

## Separate VPS Read-Only Freshness Proof Criterion Remediation

D11.78 narrows and retires
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`
for this LOCAL_MAC-only read-only market-data provider qualification path.

Rationale:

- D11.62 selected the formal LOCAL_MAC criteria-revision path instead of a VPS
  endpoint evidence path;
- D11.75/D11.76 supplied fresh regular-session clean countable evidence for
  all five required symbols;
- D11.75/D11.76 retained `LOCAL_MAC_ONLY` and did not rely on VPS, `18789`,
  `18791`, bridge, tunnel, or proxy;
- D11.69-D11.77 preserved negative authority and forbidden-field controls;
- D11.78 does not validate any VPS endpoint and does not approve any VPS
  runtime architecture.

The retired criterion is not converted into VPS approval. LOCAL_MAC
`127.0.0.1:7497` remains process-context local and remains not equivalent to
VPS `127.0.0.1:7497`.

## Primary Eligibility Impact

D11.78 does not approve IBKR primary eligibility. It changes the status only to
ready for final adjudication:

```text
IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY
```

D11.79 must be the first gate allowed to make the final primary-eligibility and
D11-closure decision.

## D11 Status Impact

D11 remains insufficient through D11.78:

```text
D11=D11_INSUFFICIENT
```

D11.78 remediates criteria blockers only. It does not close D11.

## Unit 12 Status Impact

Unit 12 remains blocked through D11.78:

```text
UNIT_12=UNIT_12_BLOCKED
```

D11.78 does not open Unit 12 and does not implement Unit 12 behavior.

## Still-Unapproved Authorities

D11.78 preserves these still-unapproved authorities:

- broker submit readiness `NOT_APPROVED`;
- live trading readiness `NOT_APPROVED`;
- account authority none;
- order authority none;
- execution authority none;
- package capture blocked;
- replay blocked;
- scoring blocked;
- candidate generation blocked;
- strategy behavior changes blocked;
- risk behavior changes blocked;
- execution behavior changes blocked;
- scheduler behavior changes blocked;
- credential or environment-file changes blocked;
- production runtime configuration changes blocked;
- VPS runtime/systemd/timer mutation blocked;
- TWS/Gateway inspection, open, close, restart, mutation, or query blocked;
- Unit 12 not opened by D11.78.

## No D11.78 Evidence Capture or Runtime Action

D11.78 collected no evidence. D11.78 ran no executable broker/TWS/API/network/
runtime command. D11.78 performed no broker, TWS, API, network, runtime, VPS,
scheduler, systemd, timer, credential, environment, package-capture, replay,
scoring, candidate-generation, live-trading, account, order, execution,
position, balance, portfolio, margin, buying-power, trade, P&L, strategy, risk,
or production provider-selection runtime action.

D11.78 performed no commit and no push.

## Blockers or Process Defects

No D11.77 criteria blocker remains as a blocker to final adjudication after
D11.78. The remaining open decision is not a blocker inside D11.78; it is the
required final D11.79 adjudication of whether the remediated evidence and
criteria are sufficient to approve IBKR primary eligibility and close D11.

## Next Permissible Gate

The exact next permissible gate is:

```text
D11.79_FINAL_IBKR_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION
```

D11.79 must perform the final source-controlled IBKR primary eligibility and
D11 closure adjudication. D11.79 must still preserve no broker submit
readiness, no live trading readiness, no account/order/execution authority, no
package capture, no replay, no scoring, no candidate generation, and no Unit
12 opening unless a separate post-D11 gate explicitly authorizes otherwise.
