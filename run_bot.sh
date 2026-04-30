#!/bin/bash

set -e

cd /opt/openclaw-stocks
source venv/bin/activate

SYMBOLS=("AAPL" "MSFT" "NVDA" "TSLA" "MSTR")

for SYMBOL in "${SYMBOLS[@]}"
do
  OPENCLAW_TRIGGER_SOURCE="systemd_timer" OPENCLAW_SYMBOL="$SYMBOL" venv/bin/python main.py
done
