# D11.41 Next-Session VPS Runtime-Value Update

## Scope and Update Status

D11.41 is a source-controlled next-session runtime-value update only. It
replaces the stale D11.40 proof timestamp `2026-06-24T14:00:00Z` with the next
valid proof-window timestamp `2026-06-25T14:00:00Z`. It does not run the VPS
proof, connect to IBKR/TWS/Gateway, read credentials, or change provider, D11,
Unit 12, package-capture, or runtime status.

| Field | Value |
| --- | --- |
| `update_status` | `NEXT_SESSION_RUNTIME_VALUES_CONFIRMED_PROOF_NOT_RUN` |
| `vps_freshness_proof_run` | `false` |
| `prior_bounded_proof_attempt_run` | `false` |
| `prior_failure_reason` | `ib_insync dependency unavailable` |
| `expected_source_commit` | `c90168d0c655c88183bdac03c4f5de2898387428` |
| `execution_context` | `VPS` |
| `repo_root` | `/opt/openclaw-stocks` |
| `python_path` | `/opt/openclaw-stocks/venv/bin/python` |
| `python_version_ready_after_hours` | `Python 3.12.3` |
| `dependency_readiness_after_hours_verified` | `requirements-diagnostics.txt / ib_insync==0.9.86` |
| `dependency_readiness_is_proof_evidence` | `false` |
| `vps_boundary_validation_after_hours` | `60 passed` |
| `superseded_authorized_regular_session_utc_z` | `2026-06-24T14:00:00Z` |
| `authorized_regular_session_utc_z` | `2026-06-25T14:00:00Z` |
| `authorized_vps_local_endpoint` | `127.0.0.1` |
| `authorized_port` | `7497` |
| `authorized_read_only_client_id` | `9118` |
| `credentials_stored_in_repository` | `false` |
| `credential_values_emitted` | `false` |
| `secrets_captured` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime_before_proof` | `PARKED` |

The authorized next-session regular-session UTC end time is at 7:00 AM Pacific
/ 10:00 AM Eastern on 2026-06-25. Official market open is not the D11
diagnostic target and must not be substituted for this source-controlled
diagnostic time.

The after-hours VPS dependency readiness record only clears the earlier
dependency blocker. It is not market-data proof evidence, does not make the
prior attempt count as run, and does not approve IBKR.

## Bound Future Command

The exact future command is source-controlled for the next valid proof window,
but D11.41 does not execute it:

```text
/opt/openclaw-stocks/venv/bin/python -m tools.ops.ibkr_market_data_vps_read_only_freshness_proof \
  --repo-root /opt/openclaw-stocks \
  --expected-source-commit c90168d0c655c88183bdac03c4f5de2898387428 \
  --execution-context VPS \
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR \
  --timeframe 15Min --requested-end 2026-06-25T14:00:00Z --lookback-minutes 120 \
  --host 127.0.0.1 --port 7497 \
  --client-id 9118 --exchange SMART --currency USD \
  --sec-type STK --timeout-seconds 10 \
  --authorize-vps-ibkr-read-only-freshness-proof
```

The command remains limited to 120 minutes of regular-trading-hours historical
`TRADES` bars for AAPL, MSFT, NVDA, TSLA, and MSTR at `15Min`, SMART/USD/STK,
with a 10-second timeout and the explicit VPS read-only authorization flag.

## Required Proof Record and Closed Boundaries

The later proof output must preserve the D11.36/D11.38 non-secret attestation:

```text
credential_configuration_status=operator_managed_tws_gateway_session_attested
credentials_stored_in_repository=false
credential_values_emitted=false
secrets_captured=false
```

It must capture the confirmed runtime values, command parameters, source
commit/branch before and after, clean pre/post worktree status, dependency
contract `requirements-diagnostics.txt / ib_insync==0.9.86`, observed version,
requested UTC window, per-symbol results, warnings, and full authority boundary.

It must set `vps_runtime=NOT_TOUCHED`, `timer_service=NOT_TOUCHED`,
`package_capture=false`, `replay=false`, `scoring=false`,
`candidate_generation=false`, `broker_api_authority=false`,
`account_query_authority=false`, `order_authority=false`,
`execution_authority=false`, `cleanup_authority=false`,
`flatten_authority=false`, `sell_authority=false`, `cancel_authority=false`,
`live_trading_authority=false`, and `d11_completion_authority=false`.

D11.41 does not approve IBKR, complete D11, unblock Unit 12, open package
capture, or open trading authority. It does not permit account, position,
margin, buying-power, portfolio, order, balance, or execution queries; order
placement, modification, routing, cancellation, flattening, selling, or live
trading; or runtime, timer, service, systemd, strategy, risk, execution,
replay, scoring, or candidate-generation activity.

The next permissible gate is a separate operator terminal step on the VPS, in
the next valid regular-session proof window, that runs exactly the
source-controlled command above and captures its output for source-controlled
adjudication.
