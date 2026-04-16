OpenClaw Stocks

The active runtime path is:

`run_bot.sh -> main.py -> config validation -> market session guard -> strategy/data pipeline -> account lookup -> duplicate check -> risk check -> broker reconciliation -> order build -> dry run or submit -> state/report persistence`

The active execution modules are:

- `main.py`
- `bot_service.py`
- `runtime_settings.py`
- `client_factory.py`
- `execution_engine.py`
- `risk_engine.py`
- `state_manager.py`
- `reporting.py`
- `config.py`

Operator quick checks

Use these commands from `/opt/openclaw-stocks` after activating the venv.

1. VPS preflight
```bash
./preflight.sh
```

Purpose:
Checks `.env`, systemd service/timer wiring, venv presence, paper-trading configuration, and recent logs.

2. Python/import precheck
```bash
python3 preflight_check.py
```

Purpose:
Confirms required files exist, Alpaca env vars are available, imports work, and the provider is prepared to ignore the trading base URL for historical market data.

3. Standalone market data test
```bash
python3 test_market_data.py
```

Purpose:
Verifies the standalone Alpaca market data provider returns a valid `HistoricalBarsResult` for `AAPL`.

4. Full smoke test
```bash
./smoke_test.sh
```

Purpose:
Runs the preflight check and standalone market data test together, with timestamps and a final PASS result when both succeed.

5. Market-open checklist

See `MARKET_OPEN_CHECKLIST.md` for the recommended Day 5 readiness sequence and how to interpret the results.

6. Architecture reference

See `ARCHITECTURE.md` for the current Clean Architecture-style layer map and recommended next refactors.

7. Institutional roadmap

See `ROADMAP.md` for the phased OpenClaw build plan, the execution/research/improvement separation, and the definition of done for each maturity stage.

8. Phase 1-2 blueprint

See `PHASE_1_2_BLUEPRINT.md` for the planning-only backlog covering stabilization and architecture hardening, including future tickets, dependencies, and explicit not-yet boundaries.

9. Full platform blueprint

See `FULL_BLUEPRINT.md` for the end-to-end OpenClaw planning doctrine, constitutional rules, phase map, and planning depth by maturity stage.
