# OpenClaw Stocks Build Status

## Current status
Phase 1 stock paper-trading bot is working and already includes the core Day 5-style safety flow in the active runtime path.

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
- structured run reports working
- market-hours guard working
- broker reconciliation working
- modular runtime path active through dedicated execution/risk/state/reporting modules
- automated tests now cover the validated runtime path, risk/reconciliation cases, and market-data retry behavior
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

## Active runtime path
run_bot.sh -> main.py -> config validation -> market session guard -> strategy/data pipeline -> account lookup -> duplicate check -> risk check -> broker reconciliation -> order build -> dry run or submit -> state/report persistence

## Active execution modules
- main.py
- bot_service.py
- runtime_settings.py
- client_factory.py
- execution_engine.py
- risk_engine.py
- state_manager.py
- reporting.py
- config.py

## Current stabilization checkpoint
- `guards.py` is now explicitly marked as legacy/deprecated and is not the active runtime path
- `test_bot_service.py` protects the validated runtime flow with fakes/stubs
- `test_risk_engine.py` protects the validated risk and reconciliation logic
- `test_market_data.py` covers the insufficient-bars retry and no-data fallback behavior without live Alpaca dependencies
- 15 focused tests are currently passing

## Current focus
1. Verify VPS readiness before market open using preflight.sh, preflight_check.py, and smoke_test.sh
2. Keep dry-run enabled until market-open checks pass cleanly on the VPS
3. Confirm the systemd service/timer, .env loading, and recent logs on the VPS
4. Continue only low-risk local cleanup that preserves the validated runtime path
5. Build the separate crypto bot later, without changing the stock bot safety boundaries

## Institutional direction
- The live bot remains the execution brain and must not experiment on itself in production
- Research and improvement capabilities will be added as separate layers, not mixed into the live runtime path
- See `ROADMAP.md` for the phased build plan and promotion-gate model
