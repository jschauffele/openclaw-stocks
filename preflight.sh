#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_DIR="/opt/openclaw-stocks"
ENV_FILE="$PROJECT_DIR/.env"
RUN_BOT="$PROJECT_DIR/run_bot.sh"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="openclaw.service"
TIMER_NAME="openclaw.timer"

FAILURES=0
ACTIVE_MODE=0

pass() {
  printf 'PASS: %s\n' "$1"
}

fail() {
  printf 'FAIL: %s\n' "$1"
  FAILURES=$((FAILURES + 1))
}

section() {
  printf '\n== %s ==\n' "$1"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1
}

get_unit_fragment_path() {
  systemctl show -p FragmentPath --value "$1" 2>/dev/null
}

get_service_user() {
  local user
  user="$(systemctl show -p User --value "$SERVICE_NAME" 2>/dev/null || true)"
  if [[ -z "$user" ]]; then
    printf 'root'
  else
    printf '%s' "$user"
  fi
}

show_status_and_logs() {
  section "Current Service Status"
  if systemctl status "$SERVICE_NAME" --no-pager || true; then
    pass "current service status shown"
  else
    fail "unable to show current service status"
  fi

  section "Recent Journal Output"
  if journalctl -u "$SERVICE_NAME" -n 50 --no-pager; then
    pass "recent journal output shown"
  else
    fail "unable to show recent journal output"
  fi
}

check_env_exists() {
  section "1. .env Exists"
  if [[ -f "$ENV_FILE" ]]; then
    pass "$ENV_FILE exists"
  else
    fail "$ENV_FILE does not exist"
  fi
}

check_env_permissions() {
  section "2. .env Permissions And Ownership"

  if [[ ! -f "$ENV_FILE" ]]; then
    fail "cannot validate permissions because $ENV_FILE is missing"
    return
  fi

  local mode owner group service_user
  mode="$(stat -c '%a' "$ENV_FILE" 2>/dev/null || true)"
  owner="$(stat -c '%U' "$ENV_FILE" 2>/dev/null || true)"
  group="$(stat -c '%G' "$ENV_FILE" 2>/dev/null || true)"
  service_user="$(get_service_user)"

  if [[ -z "$mode" || -z "$owner" || -z "$group" ]]; then
    fail "unable to read ownership or mode for $ENV_FILE"
    return
  fi

  printf 'INFO: %s owner=%s group=%s mode=%s\n' "$ENV_FILE" "$owner" "$group" "$mode"

  local perm_ok=1
  local owner_ok=1
  local group_digit other_digit

  group_digit=$(( (10#$mode / 10) % 10 ))
  other_digit=$(( 10#$mode % 10 ))

  if (( other_digit != 0 )); then
    perm_ok=0
  fi

  if (( group_digit & 2 )); then
    perm_ok=0
  fi

  if [[ "$owner" != "root" && "$owner" != "$service_user" ]]; then
    owner_ok=0
  fi

  if (( perm_ok == 1 && owner_ok == 1 )); then
    pass ".env permissions/ownership are sane"
  else
    fail ".env permissions/ownership are not sane"
  fi
}

check_service_unit() {
  section "3. Service Unit Configuration"

  local service_path service_cat
  service_path="$(get_unit_fragment_path "$SERVICE_NAME")"
  service_cat="$(systemctl cat "$SERVICE_NAME" 2>/dev/null || true)"

  if [[ -z "$service_path" ]]; then
    fail "$SERVICE_NAME does not exist"
    return
  fi

  printf 'INFO: service fragment path: %s\n' "$service_path"

  if grep -Fq "WorkingDirectory=$PROJECT_DIR" <<<"$service_cat"; then
    pass "$SERVICE_NAME contains WorkingDirectory=$PROJECT_DIR"
  else
    fail "$SERVICE_NAME missing WorkingDirectory=$PROJECT_DIR"
  fi

  if grep -Fq "EnvironmentFile=$ENV_FILE" <<<"$service_cat"; then
    pass "$SERVICE_NAME contains EnvironmentFile=$ENV_FILE"
  else
    fail "$SERVICE_NAME missing EnvironmentFile=$ENV_FILE"
  fi
}

check_timer_unit() {
  section "4. Timer Exists And Is Enabled"

  local timer_path
  timer_path="$(get_unit_fragment_path "$TIMER_NAME")"

  if [[ -n "$timer_path" ]]; then
    printf 'INFO: timer fragment path: %s\n' "$timer_path"
    pass "$TIMER_NAME exists"
  else
    fail "$TIMER_NAME does not exist"
  fi

  if systemctl is-enabled --quiet "$TIMER_NAME" 2>/dev/null; then
    pass "$TIMER_NAME is enabled"
  else
    fail "$TIMER_NAME is not enabled"
  fi
}

check_systemd_verify() {
  section "5. systemd-analyze Verify"

  local service_path timer_path
  service_path="$(get_unit_fragment_path "$SERVICE_NAME")"
  timer_path="$(get_unit_fragment_path "$TIMER_NAME")"

  if [[ -z "$service_path" || -z "$timer_path" ]]; then
    fail "cannot run systemd-analyze verify because service or timer path is missing"
    return
  fi

  if systemd-analyze verify "$service_path" "$timer_path" >/tmp/openclaw-preflight-verify.out 2>/tmp/openclaw-preflight-verify.err; then
    pass "systemd-analyze verify passed"
  else
    fail "systemd-analyze verify failed"
    printf 'INFO: verify stderr:\n'
    sed -n '1,200p' /tmp/openclaw-preflight-verify.err
  fi

  rm -f /tmp/openclaw-preflight-verify.out /tmp/openclaw-preflight-verify.err
}

check_run_bot() {
  section "6. run_bot.sh Exists And Is Executable"

  if [[ -f "$RUN_BOT" ]]; then
    pass "$RUN_BOT exists"
  else
    fail "$RUN_BOT does not exist"
  fi

  if [[ -x "$RUN_BOT" ]]; then
    pass "$RUN_BOT is executable"
  else
    fail "$RUN_BOT is not executable"
  fi
}

check_venv() {
  section "7. venv Exists"

  if [[ -d "$VENV_DIR" ]]; then
    pass "$VENV_DIR exists"
  else
    fail "$VENV_DIR does not exist"
  fi
}

check_broker_env_names() {
  section "8. Broker Env Variable Names Present"

  if [[ ! -f "$ENV_FILE" ]]; then
    fail "cannot validate broker env names because $ENV_FILE is missing"
    return
  fi

  mapfile -t found_vars < <(
    grep -E '^[[:space:]]*(APCA_API_KEY_ID|APCA_API_SECRET_KEY|APCA_API_BASE_URL|ALPACA_API_KEY|ALPACA_SECRET_KEY|ALPACA_API_SECRET|ALPACA_BASE_URL)=' "$ENV_FILE" \
      | sed -E 's/^[[:space:]]*([A-Z0-9_]+)=.*/\1=REDACTED/' \
      | sort -u
  )

  if ((${#found_vars[@]} > 0)); then
    printf 'INFO: found broker env names:\n'
    printf '%s\n' "${found_vars[@]}"
  else
    printf 'INFO: found broker env names:\n'
    printf 'none\n'
  fi

  local has_key=0
  local has_secret=0

  if grep -Eq '^[[:space:]]*(APCA_API_KEY_ID|ALPACA_API_KEY)=' "$ENV_FILE"; then
    has_key=1
  fi

  if grep -Eq '^[[:space:]]*(APCA_API_SECRET_KEY|ALPACA_SECRET_KEY|ALPACA_API_SECRET)=' "$ENV_FILE"; then
    has_secret=1
  fi

  if (( has_key == 1 && has_secret == 1 )); then
    pass "required broker env variable names exist in .env"
  else
    fail "required broker env variable names are missing from .env"
  fi
}

check_broker_env_values() {
  section "9. Broker Env Variable Values And Runtime Mode"

  if [[ ! -f "$ENV_FILE" ]]; then
    fail "cannot validate broker env values because $ENV_FILE is missing"
    return
  fi

  local key_name=""
  local secret_name=""
  local base_url_name=""
  local dry_run_name="OPENCLAW_DRY_RUN"

  if grep -Eq '^[[:space:]]*APCA_API_KEY_ID=' "$ENV_FILE"; then
    key_name="APCA_API_KEY_ID"
  elif grep -Eq '^[[:space:]]*ALPACA_API_KEY=' "$ENV_FILE"; then
    key_name="ALPACA_API_KEY"
  fi

  if grep -Eq '^[[:space:]]*APCA_API_SECRET_KEY=' "$ENV_FILE"; then
    secret_name="APCA_API_SECRET_KEY"
  elif grep -Eq '^[[:space:]]*ALPACA_SECRET_KEY=' "$ENV_FILE"; then
    secret_name="ALPACA_SECRET_KEY"
  elif grep -Eq '^[[:space:]]*ALPACA_API_SECRET=' "$ENV_FILE"; then
    secret_name="ALPACA_API_SECRET"
  fi

  if grep -Eq '^[[:space:]]*APCA_API_BASE_URL=' "$ENV_FILE"; then
    base_url_name="APCA_API_BASE_URL"
  elif grep -Eq '^[[:space:]]*ALPACA_BASE_URL=' "$ENV_FILE"; then
    base_url_name="ALPACA_BASE_URL"
  fi

  local key_value=""
  local secret_value=""
  local base_url_value=""
  local dry_run_value=""

  if [[ -n "$key_name" ]]; then
    key_value="$(grep -E "^[[:space:]]*${key_name}=" "$ENV_FILE" | tail -n 1 | sed -E "s/^[[:space:]]*${key_name}=//")"
  fi

  if [[ -n "$secret_name" ]]; then
    secret_value="$(grep -E "^[[:space:]]*${secret_name}=" "$ENV_FILE" | tail -n 1 | sed -E "s/^[[:space:]]*${secret_name}=//")"
  fi

  if [[ -n "$base_url_name" ]]; then
    base_url_value="$(grep -E "^[[:space:]]*${base_url_name}=" "$ENV_FILE" | tail -n 1 | sed -E "s/^[[:space:]]*${base_url_name}=//")"
  fi

  if grep -Eq '^[[:space:]]*OPENCLAW_DRY_RUN=' "$ENV_FILE"; then
    dry_run_value="$(grep -E '^[[:space:]]*OPENCLAW_DRY_RUN=' "$ENV_FILE" | tail -n 1 | sed -E 's/^[[:space:]]*OPENCLAW_DRY_RUN=//')"
  fi

  if [[ -n "$key_name" && -n "$key_value" ]]; then
    pass "$key_name is present and non-empty"
  else
    fail "broker API key variable is missing or empty"
  fi

  if [[ -n "$secret_name" && -n "$secret_value" ]]; then
    pass "$secret_name is present and non-empty"
  else
    fail "broker API secret variable is missing or empty"
  fi

  if [[ -n "$base_url_name" && -n "$base_url_value" ]]; then
    pass "$base_url_name is present and non-empty"
  else
    fail "broker base URL variable is missing or empty"
  fi

  if [[ "$base_url_value" == "https://paper-api.alpaca.markets" ]]; then
    pass "broker base URL points to Alpaca paper endpoint"
  else
    fail "broker base URL is not the Alpaca paper endpoint"
  fi

  if [[ "${dry_run_value,,}" == "true" ]]; then
    pass "OPENCLAW_DRY_RUN is true"
  else
    fail "OPENCLAW_DRY_RUN is not true"
  fi
}

active_validation() {
  section "Active Validation"

  printf 'INFO: --active enabled; running daemon-reload and one manual service start\n'

  if systemctl daemon-reload; then
    pass "systemctl daemon-reload succeeded"
  else
    fail "systemctl daemon-reload failed"
  fi

  if systemctl start "$SERVICE_NAME"; then
    pass "manual start of $SERVICE_NAME succeeded"
  else
    fail "manual start of $SERVICE_NAME failed"
  fi

  show_status_and_logs
}

usage() {
  cat <<'EOF2'
Usage: preflight.sh [--active]

Options:
  --active   Run active validation:
             - systemctl daemon-reload
             - one manual start of openclaw.service
             - show resulting status and logs

Default mode is read-only validation only.
EOF2
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --active)
        ACTIVE_MODE=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        printf 'Unknown argument: %s\n' "$1"
        usage
        exit 2
        ;;
    esac
  done
}

main() {
  parse_args "$@"

  section "OpenClaw VPS Preflight"

  if ! require_cmd systemctl; then
    printf 'FAIL: systemctl not found\n'
    exit 1
  fi

  if ! require_cmd journalctl; then
    printf 'FAIL: journalctl not found\n'
    exit 1
  fi

  if ! require_cmd systemd-analyze; then
    printf 'FAIL: systemd-analyze not found\n'
    exit 1
  fi

  if ! require_cmd stat; then
    printf 'FAIL: stat not found\n'
    exit 1
  fi

  check_env_exists
  check_env_permissions
  check_service_unit
  check_timer_unit
  check_systemd_verify
  check_run_bot
  check_venv
  check_broker_env_names
  check_broker_env_values

  if (( ACTIVE_MODE == 1 )); then
    active_validation
  else
    show_status_and_logs
  fi

  section "Summary"
  if (( FAILURES == 0 )); then
    printf 'SAFE TO PROCEED\n'
    exit 0
  else
    printf 'NOT SAFE TO PROCEED\n'
    exit 1
  fi
}

main "$@"
