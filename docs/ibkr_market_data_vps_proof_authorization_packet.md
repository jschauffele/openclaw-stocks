# D11.38 Bounded VPS Read-Only Freshness Proof Authorization Packet

## Scope and Authorization Status

This packet authorizes source-controlled preparation for one later bounded VPS
read-only proof only. It does not run the proof, connect to IBKR/TWS/Gateway,
read credentials, or change any provider, D11, Unit 12, package-capture, or
runtime status.

| Field | Value |
| --- | --- |
| `authorization_status` | `prepared_pending_runtime_parameter_addendum` |
| `vps_freshness_proof_run` | `false` |
| `expected_source_commit` | `c175ac79191d6d82291dea27aaa1976c8bb6ca50` |
| `execution_context` | `VPS` |
| `repo_root` | `/opt/openclaw-stocks` |
| `python_path` | `/opt/openclaw-stocks/venv/bin/python` |
| `credential_configuration_recorded` | `false` |
| `credentials_stored_in_repository` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime_before_proof` | `PARKED` |

## Bounded Future Command

The only permitted later proof command is the implemented D11.37 module from
the stated repo root and Python path:

```text
/opt/openclaw-stocks/venv/bin/python -m tools.ops.ibkr_market_data_vps_read_only_freshness_proof \
  --repo-root /opt/openclaw-stocks \
  --expected-source-commit c175ac79191d6d82291dea27aaa1976c8bb6ca50 \
  --execution-context VPS \
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR \
  --timeframe 15Min --requested-end <authorized-regular-session-utc-z> --lookback-minutes 120 \
  --host <authorized-vps-local-endpoint> --port <authorized-port> \
  --client-id <authorized-read-only-client-id> --exchange SMART --currency USD \
  --sec-type STK --timeout-seconds 10 \
  --authorize-vps-ibkr-read-only-freshness-proof
```

The source-controlled D11.36/D11.37 record does not specify the live VPS
endpoint, port, read-only client ID, or future regular-session UTC end time.
They must be supplied in a narrow source-controlled runtime-parameter addendum
before this command is executable. This packet does not authorize substitution
with the local-only smoke command or any other module.

The dependency contract is `requirements-diagnostics.txt / ib_insync==0.9.86`.
The proof is limited to regular-trading-hours historical `TRADES` bars for the
five listed symbols, `15Min`, SMART/USD/STK, and the 120-minute explicit UTC
request window. Any scope change requires a source-controlled doctrine update.

## Required Proof Output and Non-Secret Attestation

The later terminal output must be preserved for source-controlled adjudication
and include: result type, `execution_context=VPS`, repo root, expected/observed
commit before and after, `main` branch before and after, clean pre/post
worktree status, dependency contract and observed version, command parameters,
requested start/end, every result row, warnings, and complete authority
boundary.

It must include exactly these non-secret credential/configuration fields:

```text
credential_configuration_status=operator_managed_tws_gateway_session_attested
credentials_stored_in_repository=false
credential_values_emitted=false
secrets_captured=false
```

For every symbol it must include provider key/name, connection mode,
`read_only=true`, timeframe, UTC latest-candle timestamp, lag minutes,
freshness classification, `d11_countable`, candidate status, primary
eligibility, and failure reason. It must include
`vps_runtime=NOT_TOUCHED`, `timer_service=NOT_TOUCHED`,
`package_capture=false`, `replay=false`, `scoring=false`,
`candidate_generation=false`, `broker_api_authority=false`,
`account_query_authority=false`, `order_authority=false`,
`execution_authority=false`, `cleanup_authority=false`,
`flatten_authority=false`, `sell_authority=false`, `cancel_authority=false`,
`live_trading_authority=false`, and `d11_completion_authority=false`.

## Non-Authorization and Next Gate

The proof is historical-market-data read-only only. It must not query account,
position, margin, buying power, portfolio, order, balance, or execution state;
place, modify, route, cancel, flatten, sell, or otherwise trade; capture
packages; replay; score; generate candidates; mutate runtime, timer, service,
systemd, strategy, risk, or execution behavior; or emit credentials or secrets.

D11.38 does not approve IBKR, complete D11, unblock Unit 12, or open package
capture or trading authority. The next permissible gate is the narrow
source-controlled runtime-parameter addendum naming the live regular-session
UTC end time, VPS-local endpoint, port, and read-only client ID. Only after
that addendum may a separate terminal step run the exact command above.
