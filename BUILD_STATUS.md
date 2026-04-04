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
- Allowed symbols: AAPL, MSFT, GOOG
- Max position size: 5
- Duplicate cooldown: 900 seconds
- Kill switch: OPENCLAW_ENABLED

## Safety boundaries
- OpenClaw does not talk to Alpaca directly
- OpenClaw only uses /opt/openclaw-stocks/openclaw_control.sh
- Crypto bot must remain fully separate

## Next recommended work
1. Add structured run reports
2. Add market-hours guard
3. Add broker reconciliation checks
4. Split main.py into modules
5. Then build separate crypto bot
