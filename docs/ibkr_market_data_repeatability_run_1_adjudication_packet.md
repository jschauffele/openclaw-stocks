# D11.24 IBKR Repeatability Run 1 Adjudication Packet - Control Prep Only

## Scope

This packet defines post-run adjudication controls for a future D11.24 ledger
recording review after a separately authorized D11.23 repeatability run 1. It is adjudication/control prep only. It is not the diagnostic run. It is not evidence recording. It is not authorization to mutate ledger counts.

No completed or invalidated repeatability evidence is recorded by this packet.

## Current Status Preserved

| Field | Value |
| --- | --- |
| `packet_status` | `adjudication_control_prep_only` |
| `repeatability_run` | `planned_run_1` |
| `completed_repeatability_runs` | `0` |
| `invalidated_repeatability_runs` | `0` |
| `ibkr_provider_status` | `ibkr_market_data_candidate` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `vps_runtime` | `PARKED` |

## Review Inputs

A future D11.24 review may adjudicate only a paste-back packet from a separately
authorized D11.23 run 1. The review input must include every field required by
`docs/ibkr_market_data_repeatability_run_1_preflight_packet.md`.

No reviewer may infer missing evidence from memory, terminal scrollback,
screenshots, broker state, or operator confidence.

## Acceptance Criteria For Ledger-Recording Review

All criteria must pass before the future run may be accepted for D11.24 ledger
recording review:

- exact expected source commit from the future authorization is present;
- branch is `main`;
- worktree was clean before and after the run;
- dependency contract observed as `requirements-diagnostics.txt` /
  `ib_insync==0.9.86`;
- explicit `requested_start` and `requested_end` are present;
- target symbols all present: AAPL, MSFT, NVDA, TSLA, MSTR;
- timeframe is `15Min`;
- `provider_key` and `provider_name` are present;
- `connection_mode` is `local_read_only_smoke`;
- `read_only=true`;
- `latest_candle_timestamp` is valid timezone-aware UTC for every symbol;
- `freshness_classification="clean"` for every symbol;
- `d11_countable=true` for every symbol;
- `d11_primary_candidate_status="candidate"`;
- `d11_primary_eligible=false`;
- `failure_reason` is empty for every symbol;
- no warnings are present;
- package capture, replay, scoring, and candidate generation are false;
- no broker/API/account/order/execution authority expansion occurred;
- account, position, margin, buying power, portfolio, order, balance, and
  execution queries did not occur;
- timer, service, VPS, and runtime were untouched.

If every criterion passes, the only allowed review outcome is:
`ACCEPT_FOR_D11_24_LEDGER_RECORDING_REVIEW`.

Acceptance still does not approve IBKR as primary, does not complete D11, does
not open Unit 12, and does not authorize runtime.

## Invalidation Criteria

The future run must be routed to invalidated evidence review if any condition is
present:

- stale, recency-caveated, quarantined, missing, malformed, or non-UTC latest
  candle timestamp;
- any warning;
- any missing target symbol;
- wrong branch or wrong head;
- dirty worktree before or after the run;
- missing explicit request window;
- dependency mismatch;
- account, position, margin, buying power, portfolio, order, balance, or
  execution query;
- package capture, replay, scoring, candidate generation, Unit 12 opening, VPS
  mutation, runtime mutation, timer mutation, service mutation, or systemd
  mutation.

If any invalidation criterion is present, the only allowed review outcome is:
`INVALIDATED_EVIDENCE_REVIEW_REQUIRED`.

Do not rerun by impulse. A failed, stale, warning-bearing, or invalid run must
be reviewed as invalidated evidence before any separate future run is
authorized.

## Blocked Review Criteria

The future run must be blocked for source-control or authority review if any
adjudication packet field is ambiguous, missing, internally contradictory, or
outside the D11.23 authorization scope.

The blocked review outcome is:
`BLOCKED_FOR_SOURCE_CONTROL_OR_AUTHORITY_DEFECT`.

## Review Outcomes

Allowed outcomes are exactly:

- `ACCEPT_FOR_D11_24_LEDGER_RECORDING_REVIEW`;
- `INVALIDATED_EVIDENCE_REVIEW_REQUIRED`;
- `BLOCKED_FOR_SOURCE_CONTROL_OR_AUTHORITY_DEFECT`.

No other outcome may be used for D11.24 run 1 adjudication.

## Non-Authorization

D11.24 adjudication-control prep does not complete D11, does not make IBKR a
primary provider, does not record repeatability run 1 as completed, does not record repeatability run 1 as invalidated, does not mutate the D11.22 ledger counts, does not open Unit 12, and does not authorize package capture, replay,
scoring, candidate generation, broker/API work, account/position/margin/
buying-power/portfolio queries, orders, execution, dependency installation, VPS
mutation, runtime mutation, systemd mutation, timer/service changes, or
credential changes.
