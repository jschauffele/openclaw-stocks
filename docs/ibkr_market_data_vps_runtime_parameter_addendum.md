# D11.39 Narrow VPS Runtime-Parameter Addendum

## Scope and Status

D11.39 is a runtime-parameter addendum only. It does not run the VPS proof,
connect to IBKR/TWS/Gateway, read credentials, or change provider, D11, Unit
12, package-capture, or runtime status.

| Field | Value |
| --- | --- |
| `addendum_status` | `PREPARED_PENDING_OPERATOR_RUNTIME_VALUES` |
| `vps_freshness_proof_run` | `false` |
| `expected_source_commit` | `0fb3f459c519b622ed49a6dea580782242b93365` |
| `execution_context` | `VPS` |
| `repo_root` | `/opt/openclaw-stocks` |
| `python_path` | `/opt/openclaw-stocks/venv/bin/python` |
| `authorized_regular_session_utc_z` | `PENDING_OPERATOR_CONFIRMATION` |
| `authorized_vps_local_endpoint` | `PENDING_OPERATOR_CONFIRMATION` |
| `authorized_port` | `PENDING_OPERATOR_CONFIRMATION` |
| `authorized_read_only_client_id` | `PENDING_OPERATOR_CONFIRMATION` |
| `credentials_stored_in_repository` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime_before_proof` | `PARKED` |

The proof command is not executable while any runtime value is pending. D11.39
does not permit an operator to infer, discover, or substitute these values.

## Bound Future Command

After all four runtime values are source-controlled and operator-confirmed, the
only permitted terminal command remains:

```text
/opt/openclaw-stocks/venv/bin/python -m tools.ops.ibkr_market_data_vps_read_only_freshness_proof \
  --repo-root /opt/openclaw-stocks \
  --expected-source-commit 0fb3f459c519b622ed49a6dea580782242b93365 \
  --execution-context VPS \
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR \
  --timeframe 15Min --requested-end <authorized_regular_session_utc_z> --lookback-minutes 120 \
  --host <authorized_vps_local_endpoint> --port <authorized_port> \
  --client-id <authorized_read_only_client_id> --exchange SMART --currency USD \
  --sec-type STK --timeout-seconds 10 \
  --authorize-vps-ibkr-read-only-freshness-proof
```

`authorized_regular_session_utc_z` must be an explicit UTC `Z` timestamp in a
U.S. equity regular session at or after 7:00 AM Pacific / 10:00 AM Eastern.
Official market open is not the D11 diagnostic target; do not use it as the
diagnostic time. The command remains limited to 120 minutes of
regular-trading-hours historical `TRADES` bars for AAPL, MSFT, NVDA, TSLA, and
MSTR at `15Min`, SMART/USD/STK, with a 10-second timeout.

## Required Proof Record and Closed Boundaries

The later output must preserve the D11.36/D11.38 non-secret attestation:

```text
credential_configuration_status=operator_managed_tws_gateway_session_attested
credentials_stored_in_repository=false
credential_values_emitted=false
secrets_captured=false
```

It must capture the four confirmed runtime values, command parameters, source
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

D11.39 does not approve IBKR, complete D11, unblock Unit 12, open package
capture, or open trading authority. It does not permit account, position,
margin, buying-power, portfolio, order, balance, or execution queries; order
placement, modification, routing, cancellation, flattening, selling, or live
trading; or runtime, timer, service, systemd, strategy, risk, execution,
replay, scoring, or candidate-generation activity.

The next permissible gate is a source-controlled update replacing all four
pending runtime values with operator-confirmed values. Only then may a separate
terminal step execute the exact bounded proof command.
