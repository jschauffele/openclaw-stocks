# D11.42 VPS Read-Only Freshness Proof Connection-Refused Adjudication

## Scope and Adjudication Status

D11.42 is the source-controlled adjudication record for the bounded VPS
read-only market-data freshness proof attempt that ran during the authorized
regular-session proof window but produced zero countable market-data evidence.
The attempt is classified as proof-run-but-non-countable because the authorized
endpoint `127.0.0.1:7497` was not listening from the VPS process context.
Later VPS audit showed `openclaw-gateway` present on `127.0.0.1:18789` and
`127.0.0.1:18791`; existing documentation states `127.0.0.1` means loopback of
the current process context. The proven blocker is therefore endpoint/context
mismatch, not a proven desktop or broker gateway product failure.

| Field | Value |
| --- | --- |
| `adjudication_status` | `PROOF_RUN_BUT_NON_COUNTABLE` |
| `vps_freshness_proof_run` | `true` |
| `d11_countable_evidence_produced` | `false` |
| `provider_approval_evidence` | `false` |
| `root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH` |
| `authorized_endpoint_status` | `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `observed_gateway_context` | `OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791` |
| `desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE` |
| `broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE` |
| `top_level_failure_reason` | `empty` |
| `execution_context` | `VPS` |
| `authorized_pacific` | `2026-06-25 07:00:00 PDT` |
| `authorized_utc` | `2026-06-25 14:00:00 UTC` |
| `observed_current_utc_examples` | `2026-06-25 14:12:49 UTC; 2026-06-25 14:13:35 UTC` |
| `expected_source_commit` | `04e856c8a8d3387ccf2b0af5e55b493ea853a401` |
| `observed_head` | `04e856c8a8d3387ccf2b0af5e55b493ea853a401` |
| `branch` | `main` |
| `repo_root` | `/opt/openclaw-stocks` |
| `worktree_status_before_run` | `clean` |
| `worktree_status_after_run` | `clean` |
| `dependency_contract` | `requirements-diagnostics.txt / ib_insync==0.9.86` |
| `observed_dependency` | `ib_insync==0.9.86` |
| `requested_start` | `2026-06-25T12:00:00+00:00` |
| `requested_end` | `2026-06-25T14:00:00+00:00` |
| `symbols` | `AAPL, MSFT, NVDA, TSLA, MSTR` |
| `timeframe` | `15Min` |
| `host` | `127.0.0.1` |
| `port` | `7497` |
| `read_only` | `true` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |

Terminal output repeatedly included:

```text
API connection failed: ConnectionRefusedError(111, "Connect call failed ('127.0.0.1', 7497)")
```

The dependency contract was satisfied and the source/worktree state matched the
authorized commit. The failure is not a dependency failure and not proof
evidence supporting provider approval. D11.42 does not adjudicate the refusal
as a proven desktop terminal issue or a proven broker gateway product issue.

## Per-Symbol Adjudication

Each requested symbol failed the historical read-only request in the same way:

| Symbol | `freshness_classification` | `d11_countable` | `d11_primary_eligible` | `latest_candle_timestamp` | `lag_minutes` | `failure_reason` |
| --- | --- | --- | --- | --- | --- | --- |
| `AAPL` | `unavailable` | `false` | `false` | `null` | `null` | `historical read-only request failed: ConnectionRefusedError` |
| `MSFT` | `unavailable` | `false` | `false` | `null` | `null` | `historical read-only request failed: ConnectionRefusedError` |
| `NVDA` | `unavailable` | `false` | `false` | `null` | `null` | `historical read-only request failed: ConnectionRefusedError` |
| `TSLA` | `unavailable` | `false` | `false` | `null` | `null` | `historical read-only request failed: ConnectionRefusedError` |
| `MSTR` | `unavailable` | `false` | `false` | `null` | `null` | `historical read-only request failed: ConnectionRefusedError` |

Because all five results are unavailable and non-countable, D11.42 does not
complete D11, does not approve IBKR, does not unblock Unit 12, does not open
package capture, and does not open any trading or runtime authority.

## Read-Only Boundary and Next Gate

D11.42 preserves the historical-market-data-only boundary. The attempt did not
authorize account, position, margin, buying-power, portfolio, order, balance,
or execution queries; order placement, modification, routing, cancellation,
flattening, selling, or live trading; package capture; replay; scoring;
candidate generation; timer, service, systemd, or runtime mutation; or
strategy, risk, or execution changes.

Closed authority flags remain:

```text
vps_runtime=NOT_TOUCHED
timer_service=NOT_TOUCHED
package_capture=false
replay=false
scoring=false
candidate_generation=false
broker_api_authority=false
account_query_authority=false
order_authority=false
execution_authority=false
cleanup_authority=false
flatten_authority=false
sell_authority=false
cancel_authority=false
live_trading_authority=false
d11_completion_authority=false
```

The next permissible gate is operator-managed VPS endpoint/context readiness
confirmation for the authorized read-only localhost target before any
separately authorized bounded VPS read-only proof retry. This next gate is
readiness confirmation only; it is not authorization for the bot to start or
mutate gateway, runtime, timer, service, systemd, package capture, replay,
scoring, candidate generation, account/order queries, execution, or live
trading.
