# D11.56 Mac-Local Historical Market-Data Test Preflight

## Scope and Preflight Status

D11.56 is a source-controlled Mac-local historical market-data diagnostic
preflight only. It authorizes the future bounded Mac-local historical
market-data diagnostic for Friday, 2026-06-26 at or after 7:00 AM Pacific /
10:00 AM Eastern if all preflight conditions pass. It does not run endpoint
inspection, does not run the diagnostic during Codex work, does not run VPS
proof, does not start or mutate TWS/Gateway/runtime/services, does not approve
IBKR as primary, does not complete D11, and does not unblock Unit 12.

| Field | Value |
| --- | --- |
| `preflight_status` | `MAC_LOCAL_HISTORICAL_MARKET_DATA_TEST_PREFLIGHT` |
| `source_commit` | `d64ee84942533a4727df66b72c9e4175bb6713c1` |
| `d11_55_vps_validation` | `75 passed in 2.07s` |
| `test_date` | `2026-06-26` |
| `readiness_check_time_pacific` | `06:55` |
| `readiness_check_time_eastern` | `09:55` |
| `diagnostic_not_before_pacific` | `07:00` |
| `diagnostic_not_before_eastern` | `10:00` |
| `selected_mac_local_endpoint` | `127.0.0.1:7497` |
| `selected_endpoint_context` | `LOCAL_MAC` |
| `selected_endpoint_type` | `TWS_PAPER` |
| `selected_endpoint_port` | `7497` |
| `mac_local_market_test_preflight_authorized` | `true` |
| `mac_local_market_test_authorized_for_2026_06_26_after_0700_pacific` | `true` |
| `vps_market_test_authorized` | `false` |
| `proof_rerun_authorized` | `false` |
| `protocol_probe_authorized` | `false` |
| `endpoint_switch_authorized` | `false` |
| `account_order_execution_authority` | `false` |
| `package_capture` | `BLOCKED` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |
| `diagnostic_command_status` | `AUTHORIZED_FROM_EXISTING_LOCAL_READ_ONLY_SMOKE_PATTERN` |

D11.55 is locked as committed, pushed, and VPS-validated with
`75 passed in 2.07s`. It selected
`selected_mac_local_endpoint=127.0.0.1:7497`,
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`, and
`selected_endpoint_port=7497`.

The endpoint is valid only for the `LOCAL_MAC` process context. This preflight
does not validate VPS `127.0.0.1:7497`. The prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

## Timing and Operator Preconditions

The future diagnostic is Mac-local only. VPS is only for source sync and tests,
not IBKR/TWS connectivity. Trader Workstation must be manually open and logged
into paper mode before the diagnostic. Source worktree must be clean before and
after the diagnostic.

The `06:55` Pacific / `09:55` Eastern time is a readiness-check boundary only.
The historical market-data diagnostic must not run before `07:00` Pacific /
`10:00` Eastern. Do not use 6:30 AM Pacific / 9:30 AM Eastern as the diagnostic
time.

## Future Historical-Market-Data-Only Command

This command is derived from the existing accepted LOCAL_MAC repeatability
diagnostic pattern in `docs/ibkr_market_data_repeatability_ledger_template.md`
and the Run #1/Run #2 preflight packets. It uses the existing
`tools.ops.ibkr_market_data_read_only_smoke` module with
`--authorize-local-ibkr-read-only-smoke`.

Do not run this command during Codex work. It is authorized only for LOCAL_MAC on
2026-06-26 at or after 7:00 AM Pacific / 10:00 AM Eastern if all preflight
conditions pass.

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks
set -euo pipefail

EXPECTED_SOURCE_COMMIT='d64ee84942533a4727df66b72c9e4175bb6713c1'
REQUESTED_END_UTC='2026-06-26T14:00:00Z'

[[ "$(git branch --show-current)" == 'main' ]] || { echo 'wrong branch' >&2; exit 1; }
[[ "$(git rev-parse HEAD)" == "$EXPECTED_SOURCE_COMMIT" ]] || { echo 'wrong HEAD' >&2; exit 1; }
[[ -z "$(git status --porcelain=v1)" ]] || { echo 'dirty worktree before diagnostic' >&2; exit 1; }

DIAGNOSTIC_COMMAND=(
  .venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR
  --timeframe 15Min
  --requested-end "$REQUESTED_END_UTC"
  --lookback-minutes 120
  --host 127.0.0.1
  --port 7497
  --client-id 9117
  --exchange SMART
  --currency USD
  --sec-type STK
  --timeout-seconds 10
  --authorize-local-ibkr-read-only-smoke
)

printf 'SUMMARY_START\n'
printf 'timestamp_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'expected_source_commit=%s\n' "$EXPECTED_SOURCE_COMMIT"
printf 'observed_source_commit=%s\n' "$(git rev-parse HEAD)"
printf 'branch=%s\n' "$(git branch --show-current)"
printf 'worktree_before=CLEAN\n'
printf 'dependency_contract=requirements-diagnostics.txt / ib_insync==0.9.86\n'
printf 'observed_dependency_version=%s\n' "$(.venv-312/bin/python -c 'import ib_insync; print(ib_insync.__version__)')"
printf 'endpoint_host=127.0.0.1\n'
printf 'endpoint_port=7497\n'
printf 'instruments=AAPL,MSFT,NVDA,TSLA,MSTR\n'
printf 'requested_end_utc=%s\n' "$REQUESTED_END_UTC"
printf 'command_used='
printf '%q ' "${DIAGNOSTIC_COMMAND[@]}"
printf '\n'
"${DIAGNOSTIC_COMMAND[@]}"
[[ -z "$(git status --porcelain=v1)" ]] || { echo 'dirty worktree after diagnostic' >&2; exit 1; }
printf 'worktree_after=CLEAN\n'
printf 'no_account_order_execution_fields=true\n'
printf 'package_capture=BLOCKED\n'
printf 'unit_12_status=UNIT_12_BLOCKED\n'
printf 'SUMMARY_END\n'
```

The diagnostic is historical-market-data-only. It must not reference or perform
account, position, margin, buying-power, portfolio, balance, order, execution,
cleanup, flatten, sell, cancel, live trading, package capture, replay, scoring,
candidate generation, strategy, risk, or execution behavior.

## Diagnostic Scope and Expected Evidence

Diagnostic instruments:

- `AAPL`
- `MSFT`
- `NVDA`
- `TSLA`
- `MSTR`

Timeframe: `15Min`.

Expected regular-session evidence behavior: the latest returned candle should
be explainable by market-data freshness and 15-minute candle timing.

Compact output must include:

- command used;
- source commit;
- clean pre-worktree;
- clean post-worktree;
- dependency versions;
- endpoint host and port;
- instruments;
- requested UTC window;
- latest candle timestamp per instrument;
- pass/fail classification;
- no account/order/execution fields.

## Closed Authorities

D11.56 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

D11.56 authorizes no account, position, margin, buying-power, portfolio,
balance, order, execution, cleanup, flatten, sell, cancel, or live-trading
authority. It authorizes no package capture, replay, scoring, candidate
generation, strategy, risk, or execution authority.

Closed authority flags remain:

```text
vps_runtime=NOT_TOUCHED
timer_service=NOT_TOUCHED
package_capture=BLOCKED
replay=false
scoring=false
candidate_generation=false
account_query_authority=false
order_authority=false
execution_authority=false
account_order_execution_authority=false
cleanup_authority=false
flatten_authority=false
sell_authority=false
cancel_authority=false
live_trading_authority=false
vps_market_test_authorized=false
proof_rerun_authorized=false
protocol_probe_authorized=false
endpoint_switch_authorized=false
d11_completion_authority=false
unit_12_opening_authority=false
```
