# D11.31 IBKR Repeatability Run 3 Preflight Packet - Control Prep Only

## Objective and Scope

This source-controlled packet prepares the controls for the third IBKR
read-only market-data repeatability diagnostic required by D11.21. Run #3 is
planned only. This packet does not run a diagnostic and does not approve one.

Run #3 may occur only on a distinct future U.S. equity regular-session trading
day after Run #2 (2026-06-23), and only after separate explicit authorization.
Market open is not required to prepare this packet; it is required for the
future diagnostic.

## Execution Context

| Activity | Required context |
| --- | --- |
| D11.31 control-packet preparation | `CODEX_LOCAL` |
| Future Run #3 read-only diagnostic | `LOCAL_MAC` only, after separate explicit authorization |
| Post-commit source-controlled validation | `VPS` only if a source-controlled change is committed |

Broker/TWS is not involved in this preparation. It may be involved only for
the future separately authorized `LOCAL_MAC` read-only diagnostic. This packet
does not authorize a broker connection, TWS connection, or IBKR submit smoke.

## Current Status Preserved

| Field | Value |
| --- | --- |
| `packet_status` | `preflight_control_prep_only` |
| `repeatability_run` | `planned_run_3` |
| `completed_repeatability_runs` | `2` |
| `invalidated_repeatability_runs` | `0` |
| `completed_runs` | `1, 2` |
| `run_1_date` | `2026-06-22` |
| `run_2_date` | `2026-06-23` |
| `run_3_completed` | `false` |
| `run_3_invalidated` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `order_authority` | `NONE` |
| `execution_authority` | `NONE` |
| `vps_runtime` | `PARKED` |

D11 remains insufficient until a separately authorized Run #3 is accepted and
recorded. Recording Run #3, if later justified, remains a separate action from
this preparation.

## Authority Boundaries

This packet authorizes source-controlled preparation only. It does not
authorize the future Run #3 diagnostic, live trading, IBKR submit smoke,
cleanup, flattening, selling, cancellation, remediation, broker-factory
activation, account access, position access, margin or buying-power access,
portfolio access, order access, balance access, or execution access.

It does not authorize strategy, risk, or execution behavior changes. It does
not authorize scheduler, systemd, timer, service, runtime, or VPS activation.
It does not approve IBKR as primary, does not complete D11, and does not
unblock Unit 12.

## Future Run #3 Authorization Preconditions

Before the future diagnostic, a separate explicit authorization must identify
the expected source commit and approve only the existing local read-only
historical-market-data diagnostic scope. The operator must confirm:

- branch is `main`, HEAD equals the authorization-supplied source commit, and
  the worktree is clean;
- the ledger still reports `completed_repeatability_runs=2` and
  `invalidated_repeatability_runs=0`;
- Run #1 remains dated 2026-06-22 and Run #2 remains dated 2026-06-23;
- the day is a distinct future U.S. equity regular-session trading day after
  Run #2;
- TWS/Gateway is manually opened by the operator only for that separately
  authorized `LOCAL_MAC` diagnostic; and
- no authority beyond the existing read-only market-data diagnostic is needed.

## Future Run #3 Adjudication Criteria

Run #3 can be considered countable only during a later adjudication if all of
the following are evidenced and aligned with this packet and its separate
authorization:

- the same read-only diagnostic scope is used: AAPL, MSFT, NVDA, TSLA, and
  MSTR at `15Min` with an explicit UTC request window;
- it occurs on a distinct regular-session trading day after Run #2;
- all target results are clean, countable, and free of warnings or failures
  that compromise repeatability evidence;
- no authority expansion, account query, order action, execution action,
  package capture, replay, scoring, candidate generation, Unit 12 activity,
  VPS mutation, or scheduler/systemd/runtime activity occurs; and
- the evidence records the authorization-supplied commit, clean pre/post
  worktree state, dependency contract and version, command used, and all
  diagnostic payload fields required by the repeatability ledger.

## Stop Conditions

Stop and classify the work as blocked for review if any of the following is
true:

- repository branch, HEAD, origin alignment, or expected source commit does
  not match the handoff or separate authorization;
- the working tree is dirty before intended source-controlled changes or the
  future diagnostic;
- the repeatability ledger or a required Run #1/Run #2/D11.27/D11.28/D11.29/
  D11.30 control source is missing, stale, or contradictory;
- the completed-run count is not exactly two, invalidated-run count is not
  zero, or either accepted run date conflicts with the ledger;
- any broker, runtime, VPS, systemd, scheduler, strategy, risk, or execution
  work is needed for this preparation; or
- any order, account, submit, cancel, flatten, sell, cleanup, or remediation
  authority is implied.

Do not bridge a stop condition with a rerun, ad hoc command, terminal change,
or authority expansion.

## Final Classification Choices

- `PASS`: D11.31 preparation is created or updated, its diff is scoped, and
  local source/doc/test validations pass.
- `BLOCKED`: Gate 0 fails, or required source files are missing or
  contradictory.
- `BUG`: existing source-controlled evidence contains a concrete defect.
- `PARKED`: no further action is permissible without user approval.

## Non-Authorization

D11.31 does not perform Run #3, record Run #3 as completed or invalidated,
mutate ledger counts, approve IBKR as primary, complete D11, unblock Unit 12,
or authorize package capture, replay, scoring, candidate generation, broker
work, account/position/margin/buying-power/portfolio/order/balance/execution
queries, orders, execution, dependency installation, VPS mutation, runtime
activation, scheduler/systemd/timer/service changes, or credential changes.
