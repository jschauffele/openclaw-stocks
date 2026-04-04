Operator Quick Checks

Use these commands from /opt/openclaw-stocks after activating the venv.

1. Preflight check
python3 preflight_check.py

Purpose:
Confirms required files exist, Alpaca env vars are available, imports work, and the provider is prepared to ignore the trading base URL for historical market data.

2. Standalone market data test
python3 test_market_data.py

Purpose:
Verifies the standalone Alpaca market data provider returns a valid HistoricalBarsResult for AAPL.

3. Full smoke test
./smoke_test.sh

Purpose:
Runs the preflight check and standalone market data test together, with timestamps and a final PASS result when both succeed.
