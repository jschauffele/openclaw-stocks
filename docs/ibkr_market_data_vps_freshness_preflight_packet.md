# D11.35 VPS Read-Only Freshness Proof / Credential-Configuration Control Prep

## Scope

This packet is source-controlled control preparation only. It does not run a
VPS proof, connect to IBKR/TWS/Gateway, read credentials, or change any
provider, D11, Unit 12, package-capture, or runtime status.

The existing `tools.ops.ibkr_market_data_read_only_smoke` command is explicitly
local-only and its `--authorize-local-ibkr-read-only-smoke` flag is not
authorization for VPS use. No VPS diagnostic command is currently authorized.

## Execution Context

| Activity | Required context |
| --- | --- |
| D11.35 packet preparation and source validation | `CODEX_LOCAL` |
| Future VPS freshness proof | `VPS` only, after separate explicit authorization and a source-controlled VPS-specific command contract |
| Broker/TWS/Gateway operation | Operator-managed only during the future separately authorized proof |

## Status Preserved

| Field | Value |
| --- | --- |
| `packet_status` | `control_prep_only` |
| `vps_freshness_proof_run` | `false` |
| `credential_configuration_recorded` | `false` |
| `credentials_stored_in_repository` | `false` |
| `completed_repeatability_runs` | `3` |
| `invalidated_repeatability_runs` | `0` |
| `ibkr_provider_status` | `ibkr_market_data_candidate` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `PARKED` |

## Required Future Proof Evidence

The later source-controlled VPS proof record must include all of the following:

- a separate authorization naming the expected source commit, VPS execution
  context, approved command, and permitted read-only historical-market-data
  scope;
- `main` branch, expected and observed commit, and clean worktree before and
  after the proof;
- diagnostic environment attestation for `requirements-diagnostics.txt` and
  `ib_insync==0.9.86`;
- non-secret credential/configuration attestation: the operator-managed
  TWS/Gateway session is configured for diagnostic use, no credential value is
  printed or committed, `credentials_stored_in_repository=false`, and
  `secrets_captured=false`;
- symbols AAPL, MSFT, NVDA, TSLA, and MSTR; `15Min`; an explicit UTC request
  window; provider/feed metadata; UTC latest-candle timestamps; lag; clean
  freshness; countability; warning/failure reason; and the full authority
  boundary; and
- `execution_context=VPS`, `read_only=true`,
  `vps_runtime=NOT_TOUCHED`, `timer_service=NOT_TOUCHED`,
  `package_capture=false`, `replay=false`, `scoring=false`,
  `candidate_generation=false`, `broker_api_authority=false`,
  `order_authority=false`, `execution_authority=false`, and
  `d11_completion_authority=false`.

The future proof may be read-only historical market data only. It must not
query account, position, margin, buying power, portfolio, order, balance, or
execution state, and must not place, modify, route, cancel, flatten, sell, or
otherwise trade.

## Future Command Contract

No exact VPS command exists yet. Before execution, a separately approved,
source-controlled VPS-specific command must use this shape without replacing
the existing local-only smoke command:

```text
<approved-vps-python> -m <approved-vps-read-only-diagnostic-module> \
  --symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR \
  --timeframe 15Min --requested-end <UTC_Z> --lookback-minutes 120 \
  --host <approved-local-vps-endpoint> --port <approved-port> \
  --client-id <approved-read-only-client-id> --exchange SMART --currency USD \
  --sec-type STK --timeout-seconds 10 <approved-vps-read-only-authorization>
```

The command contract must prove that it requests historical market data only,
uses no credentials from source, does not start TWS/Gateway, and emits the
required evidence fields without secrets. Any missing contract, non-UTC
timestamp, warning, stale result, dirty worktree, authority breach, or secret
exposure blocks the proof; do not substitute an ad hoc command or rerun by
impulse.

## Authority Boundaries and Next Gate

D11.35 does not authorize provider approval, D11 completion, Unit 12 opening,
package capture, replay, scoring, candidate generation, broker/API,
account/position/margin/buying-power/portfolio/order/balance/execution query,
runtime, timer, service, systemd, strategy, risk, execution, cleanup, flatten,
sell, cancel, or live-trading authority.

The next permissible gate is separate authorization of the VPS-specific
read-only command contract and the bounded VPS proof. A later adjudication may
consider only a complete, clean, non-secret proof record; it remains separate
from D11 sufficiency and every operational or trading authority.
