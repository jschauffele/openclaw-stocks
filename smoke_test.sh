#!/usr/bin/env bash
set -euo pipefail

cd /opt/openclaw-stocks
source venv/bin/activate

STARTED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "=== SMOKE TEST START ==="
echo "started_at=${STARTED_AT}"
echo "project_root=/opt/openclaw-stocks"

python3 preflight_check.py
python3 test_market_data.py

FINISHED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "finished_at=${FINISHED_AT}"
echo "result=PASS"
echo "=== SMOKE TEST PASS ==="
