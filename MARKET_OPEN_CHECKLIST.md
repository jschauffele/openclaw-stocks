Market Open Readiness Checklist

Run these checks on the VPS from `/opt/openclaw-stocks`.

1. Fast read-only VPS preflight
```bash
./preflight.sh
```

Expected result:
- Summary ends with `SAFE TO PROCEED`
- `.env` exists and has sane permissions
- `openclaw.service` and `openclaw.timer` exist
- broker base URL points to `https://paper-api.alpaca.markets`
- `OPENCLAW_DRY_RUN` is `true`

2. Python/import precheck
```bash
source venv/bin/activate
python3 preflight_check.py
```

Expected result:
- required files found
- broker env vars found
- imports succeed
- output ends with `PRECHECK RESULT: PASS`

3. Market data smoke test
```bash
python3 test_market_data.py
./smoke_test.sh
```

Expected result:
- historical data fetch succeeds
- smoke test ends with `=== SMOKE TEST PASS ===`

4. Systemd status and recent logs
```bash
systemctl status openclaw.service --no-pager
systemctl status openclaw.timer --no-pager
journalctl -u openclaw.service -n 50 --no-pager
```

Look for:
- no import errors
- no missing env var errors
- no path errors
- no permission errors

5. Optional active validation
```bash
./preflight.sh --active
```

What it does:
- reloads systemd
- starts the service once
- shows resulting status and logs

Use this only when you are ready for one controlled manual run.

6. Runtime artifacts to inspect after a controlled run
- `/opt/openclaw-stocks/openclaw.log`
- `/opt/openclaw-stocks/last_run_report.json`
- `/opt/openclaw-stocks/order_state.json`

Healthy signs:
- a new run appears in the log
- `last_run_report.json` is updated
- if dry run is enabled, the report reason should reflect dry-run completion instead of a submitted order

Decision rule:
- If all checks pass and logs look clean, the VPS is in a strong state for the next market open.
- If any preflight, import, env, or service check fails, fix that first before changing strategy or trading behavior.
