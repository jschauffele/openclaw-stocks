# D11.36 VPS Read-Only Market-Data Freshness Command Contract

## Scope and Status

This is a source-controlled command contract only. It does not implement the
named module, run a VPS proof, connect to IBKR/TWS/Gateway, read credentials,
or change provider, D11, Unit 12, package-capture, or runtime status.

| Field | Value |
| --- | --- |
| `packet_status` | `command_contract_prep_only` |
| `vps_freshness_proof_run` | `false` |
| `credential_configuration_recorded` | `false` |
| `credentials_stored_in_repository` | `false` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `PARKED` |

The local-only `tools.ops.ibkr_market_data_read_only_smoke` module and its
`--authorize-local-ibkr-read-only-smoke` flag are explicitly prohibited from
this VPS contract.

## Future Authorized Command Shape

Only after separate explicit authorization, from repo root
`/opt/openclaw-stocks`, the future VPS-specific diagnostic must use this exact
module and authorization-flag shape:

```text
/opt/openclaw-stocks/venv/bin/python -m tools.ops.ibkr_market_data_vps_read_only_freshness_proof \
  --repo-root /opt/openclaw-stocks \
  --expected-source-commit <authorized-40-hex-commit> \
  --execution-context VPS \
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR \
  --timeframe 15Min --requested-end <authorized-utc-z> --lookback-minutes 120 \
  --host <authorized-vps-local-endpoint> --port <authorized-port> \
  --client-id <authorized-read-only-client-id> --exchange SMART --currency USD \
  --sec-type STK --timeout-seconds 10 \
  --authorize-vps-ibkr-read-only-freshness-proof
```

`tools.ops.ibkr_market_data_vps_read_only_freshness_proof` and its
authorization flag are contract identifiers only; neither is implemented or
authorized by D11.36. The authorization must supply the actual 40-character
commit, UTC end time, endpoint, port, and read-only client id. It must confirm
`main`, a clean worktree before and after, and the pinned
`requirements-diagnostics.txt` / `ib_insync==0.9.86` environment.

The command must request regular-trading-hours historical bars only. The symbol,
timeframe, request-window, exchange, currency, and security-type scope above
matches the accepted repeatability evidence and may change only through a later
source-controlled doctrine update.

## Required Non-Secret Output Record

The later command output must include:

- `result_type=ibkr_vps_read_only_market_data_freshness_proof`,
  `execution_context=VPS`, `repo_root=/opt/openclaw-stocks`, branch, expected
  and observed commit, and pre/post worktree status;
- `dependency_contract=requirements-diagnostics.txt / ib_insync==0.9.86` and
  observed dependency version;
- `credential_configuration_status=operator_managed_tws_gateway_session_attested`,
  `credentials_stored_in_repository=false`, `credential_values_emitted=false`,
  and `secrets_captured=false`; and
- provider key/name, `connection_mode=vps_read_only_historical_market_data`,
  `read_only=true`, every requested symbol, timeframe, UTC requested start/end,
  UTC latest candle timestamp, lag, freshness classification, countability,
  candidate status, primary eligibility, failure reason, warnings, and the
  complete authority boundary.

The later output must also set `vps_runtime=NOT_TOUCHED`,
`timer_service=NOT_TOUCHED`, `package_capture=false`, `replay=false`,
`scoring=false`, `candidate_generation=false`, `broker_api_authority=false`,
`account_query_authority=false`, `order_authority=false`,
`execution_authority=false`, `cleanup_authority=false`,
`flatten_authority=false`, `sell_authority=false`, `cancel_authority=false`,
`live_trading_authority=false`, and `d11_completion_authority=false`.

## Prohibitions and Next Gate

The future command is historical market-data read-only only. It must not read
or print secrets; query account, position, margin, buying power, portfolio,
order, balance, or execution state; place, modify, route, cancel, flatten,
sell, or otherwise trade; or capture packages, replay, score, generate
candidates, mutate timer/service/systemd/runtime state, or change strategy,
risk, or execution behavior.

D11.36 does not approve IBKR, complete D11, or open Unit 12. The next
permissible gate is separate authorization to implement or otherwise approve
this VPS-specific command contract and execute one bounded VPS proof. That
future gate remains separate from provider approval, D11 sufficiency, Unit 12,
and all operational or trading authority.
