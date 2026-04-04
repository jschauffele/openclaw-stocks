#!/bin/bash

set -e

cd /opt/openclaw-stocks
source venv/bin/activate
OPENCLAW_TRIGGER_SOURCE=systemd_timer python3 main.py
