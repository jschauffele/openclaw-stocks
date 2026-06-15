# OpenClaw Stocks Build Status

## Current status
Phase 1 stock paper-trading bot is working.

## Verified components
- VPS project path: /opt/openclaw-stocks
- Python venv working
- main.py working
- .env loading working
- run_bot.sh working
- openclaw.service working as oneshot
- openclaw.timer working every 15 minutes
- openclaw.log working
- order_state.json working
- duplicate cooldown working
- backup created under /opt/backups/openclaw-stocks
- openclaw_control.sh working
- OpenClaw installed and running
- custom skill created: openclaw-stocks-supervisor
- OpenClaw can read logs/state and trigger the stock bot safely

## Current trading mode
- Paper trading endpoint configured
- Dry run enabled
- No live trade execution

## Approved controls
- Allowed symbols are source-controlled in `config.py`; current source lists
  AAPL, MSFT, NVDA, TSLA, and MSTR. Monday observation included those symbols,
  including an MSTR buy signal that reconciliation blocked because existing
  MSTR qty=5 plus requested qty=1 would exceed max_position_size=5.
- Max position size: 5
- Duplicate cooldown: 900 seconds
- Kill switch: OPENCLAW_ENABLED

## Safety boundaries
- OpenClaw does not talk to Alpaca directly
- OpenClaw only uses /opt/openclaw-stocks/openclaw_control.sh
- Crypto bot must remain fully separate

## Monday Runtime Observation — Observational Evidence Only

The Monday scheduled Alpaca paper runtime observation passed operationally under
the existing systemd timer baseline. VPS scheduled paper runtime ran under
`openclaw.timer`; `openclaw.service` completed cycles successfully and returned
inactive/dead between runs; `openclaw.timer` remained active/enabled.

Observed pre-open cycles blocked as `before_regular_session_open`. The
market-open 13:30 UTC cycle produced mostly hold/no-order decisions. MSTR
generated a buy signal at 13:30 UTC, but reconciliation blocked the order
because existing MSTR qty=5 plus requested qty=1 would exceed
`max_position_size=5`. Later observed cycles produced hold/no-order behavior.
The end-of-session corrected check showed final passive state clean.

No traceback, failed unit, restart loop, unauthorized order submission, manual
start/restart, VPS repo edit, replay, scoring, package capture, or candidate
generation was authorized or observed. This observation does not mark Gate D
complete, does not mark D11 sufficient, does not open Unit 12, does not prove
D13 operational package-capture behavior, does not populate D14, does not
produce D15 candidate evidence, and does not authorize live trading, IBKR
execution, replay/scoring, package capture, candidate generation, strategy
changes, risk changes, config changes, or broker/API expansion.

## Next recommended work
1. Add structured run reports
2. Add market-hours guard
3. Add broker reconciliation checks
4. Split main.py into modules
5. Then build separate crypto bot
