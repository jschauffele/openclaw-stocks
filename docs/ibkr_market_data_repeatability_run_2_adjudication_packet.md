# D11.28 IBKR Repeatability Run 2 Adjudication Packet - Control Prep Only

## Scope

This packet defines post-run adjudication controls for a future D11.28 ledger
recording review after a separately authorized D11.27 repeatability Run #2. It
is adjudication/control prep only. It is not the diagnostic run. It is not
evidence recording. It is not authorization to mutate ledger counts.

Run #2 must have been separately authorized and executed on a distinct U.S.
regular-session trading day after Run #1 (2026-06-22). No completed or
invalidated repeatability evidence is recorded by this packet.

Run #3 remains future and pending. This packet creates no Run #3 ledger entry.

## Control Statements

- This packet is not the diagnostic run.
- This packet is not evidence recording.
- This packet is not authorization to mutate ledger counts.
- No completed or invalidated repeatability evidence is recorded by this packet.
- Run #2 remains planned only.
- Run #2 is not completed.
- Run #2 is not invalidated.
- Run #1 remains the only completed run.
- Run #3 remains future and pending.

## Current Status Preserved

| Field | Value |
| --- | --- |
| `packet_status` | `adjudication_control_prep_only` |
| `repeatability_run` | `planned_run_2` |
| `completed_repeatability_runs` | `1` |
| `invalidated_repeatability_runs` | `0` |
| `completed_run_1_only` | `true` |
| `run_2_completed` | `false` |
| `run_2_invalidated` | `false` |
| `run_3_status` | `future_pending` |
| `ibkr_provider_status` | `ibkr_market_data_candidate` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `vps_runtime` | `PARKED` |

## Review Inputs

A future D11.28 review may adjudicate only a paste-back packet from a separately
authorized D11.27 Run #2. The review input must include every field required by
`docs/ibkr_market_data_repeatability_run_2_preflight_packet.md`.

No reviewer may infer missing evidence from memory, terminal scrollback,
screenshots, broker state, or operator confidence.

## Acceptance Criteria For Run #2 Ledger-Recording Review

All criteria must pass before the future Run #2 may be accepted for D11.28
ledger-recording review:

- exact expected source commit from the future Run #2 authorization is present;
- local timestamp UTC is present;
- branch is `main`;
- HEAD equals the expected source commit;
- worktree was clean before and after the run;
- dependency contract observed as `requirements-diagnostics.txt` /
  `ib_insync==0.9.86`;
- command used is present and matches the Run #2 source-controlled command
  template;
- explicit `requested_start` and `requested_end` are present;
- `result_type` is `ibkr_local_read_only_market_data_smoke`;
- target symbols all present: AAPL, MSFT, NVDA, TSLA, MSTR;
- timeframe is `15Min`;
- `provider_key` and `provider_name` are present;
- `connection_mode` is `local_read_only_smoke`;
- `read_only=true`;
- `latest_candle_timestamp` is valid timezone-aware UTC for every symbol;
- `freshness_classification=clean` for every symbol;
- `d11_countable=true` for every symbol;
- `d11_primary_candidate_status=candidate`;
- `d11_primary_eligible=false`;
- `failure_reason` is empty for every symbol;
- no warnings are present;
- `package_capture=false`;
- `replay=false`;
- `scoring=false`;
- `candidate_generation=false`;
- `broker_api_authority=false`;
- `order_authority=false`;
- `execution_authority=false`;
- `d11_completion_authority=false`;
- `unit_12_status=UNIT_12_BLOCKED`;
- `authority_boundary` is present;
- no account, position, margin, buying power, portfolio, order, balance, or
  execution query occurred;
- VPS runtime was not touched;
- timer and service remained off.

If every criterion passes, the only allowed review outcome is:
`ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW`.

Acceptance still does not approve IBKR as primary, does not complete D11, does
not open Unit 12, and does not authorize runtime.

## Invalidation Criteria

The future Run #2 must be routed to invalidated evidence review if any condition
is present:

- stale, recency-caveated, quarantined, missing, malformed, or non-UTC latest
  candle timestamp;
- any warning;
- any missing target symbol;
- wrong branch or wrong head;
- dirty worktree before or after the run;
- missing explicit request window;
- dependency mismatch;
- non-distinct trading day relative to Run #1;
- account, position, margin, buying power, portfolio, order, balance, or
  execution query;
- package capture, replay, scoring, candidate generation, Unit 12 opening, VPS
  mutation, runtime mutation, timer mutation, service mutation, or systemd
  mutation.

If any invalidation criterion is present, the only allowed review outcome is:
`INVALIDATED_RUN_2_EVIDENCE_REVIEW_REQUIRED`.

Do not rerun by impulse. A failed, stale, warning-bearing, non-distinct, or
invalid Run #2 must be reviewed as invalidated evidence before any separate
future run is authorized.

## Blocked Review Criteria

The future Run #2 must be blocked for source-control or authority review if any
adjudication field is ambiguous, missing, internally contradictory, or outside
the Run #2 authorization scope.

Any adjudication field outside the Run #2 authorization scope blocks review.

The blocked review outcome is:
`BLOCKED_FOR_RUN_2_SOURCE_CONTROL_OR_AUTHORITY_DEFECT`.

## Review Outcomes

Allowed outcomes are exactly:

- `ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW`;
- `INVALIDATED_RUN_2_EVIDENCE_REVIEW_REQUIRED`;
- `BLOCKED_FOR_RUN_2_SOURCE_CONTROL_OR_AUTHORITY_DEFECT`.

No other outcome may be used for D11.28 Run #2 adjudication.

## Non-Authorization

D11.28 explicitly preserves these ledger and authority facts:

- It does not record repeatability Run #2 as completed.
- It does not record repeatability Run #2 as invalidated.
- It does not mutate the D11.26 ledger completed or invalidated counts.
- It does not approve IBKR as primary.
- It does not complete D11.
- It does not open Unit 12.
- It does not authorize runtime, order, account, or execution authority.

D11.28 adjudication-control prep does not run the diagnostic, does not complete
D11, does not make IBKR a primary provider, does not record repeatability Run #2
as completed, does not record repeatability Run #2 as invalidated, does not
mutate the D11.26 ledger completed or invalidated counts, does not open Unit 12,
and does not authorize package capture, replay, scoring, candidate generation,
broker/API work, account/position/margin/buying-power/portfolio/order/balance/
execution queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes.
