#!/bin/bash

set -e

cd /opt/openclaw-stocks

STATE_FILE="/opt/openclaw-stocks/order_state.json"
REPORT_FILE="/opt/openclaw-stocks/last_run_report.json"

case "$1" in
  trigger)
    systemctl start openclaw.service
    ;;
  status)
    systemctl status openclaw.service --no-pager -l
    ;;
  timer-status)
    systemctl status openclaw.timer --no-pager -l
    ;;
  logs)
    journalctl -u openclaw.service -n 30 --no-pager -l
    ;;
  state)
    if [ -f "$STATE_FILE" ]; then
      cat "$STATE_FILE"
    else
      echo "order_state.json not found"
      exit 1
    fi
    ;;
  report)
    if [ -f "$REPORT_FILE" ]; then
      cat "$REPORT_FILE"
    else
      echo "last_run_report.json not found"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 {trigger|status|timer-status|logs|state|report}"
    exit 1
    ;;
esac
