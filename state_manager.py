import json
import logging
import os
from datetime import datetime, timezone

from utils import parse_iso8601, write_json_atomic


def load_order_state_from_path(state_file: str):
    if not os.path.exists(state_file):
        logging.info(f"No state file yet: {state_file}")
        return None

    try:
        with open(state_file, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logging.warning("State file exists but does not contain a JSON object")
            return None

        logging.info(
            "Loaded state file: "
            f"symbol={data.get('symbol')}, "
            f"side={data.get('side')}, "
            f"qty={data.get('qty')}, "
            f"timestamp={data.get('timestamp')}, "
            f"mode={data.get('mode')}"
        )
        return data

    except json.JSONDecodeError:
        logging.warning("State file is invalid JSON; ignoring it safely")
        return None
    except OSError as e:
        logging.warning(f"Could not read state file: {e}")
        return None


def write_order_state_for_settings(settings, state: dict) -> None:
    write_json_atomic(settings.state_file, state)
    logging.info(f"Order state written to {settings.state_file}")


def write_run_report_for_settings(settings, report: dict) -> None:
    write_json_atomic(settings.run_report_file, report)
    logging.info(f"Run report written to {settings.run_report_file}")


def legacy_duplicate_match_for_settings(settings, symbol: str) -> bool:
    if not os.path.exists(settings.legacy_last_order_file):
        return False

    try:
        with open(settings.legacy_last_order_file, "r") as f:
            last = f.read().strip()
        if last:
            logging.info(f"Legacy last_order.txt contains: {last}")
        return last == symbol
    except OSError as e:
        logging.warning(f"Could not read legacy duplicate file: {e}")
        return False


def duplicate_check_for_settings(settings, symbol: str, side: str, qty: int):
    state = load_order_state_from_path(settings.state_file)

    if state is None:
        legacy_match = legacy_duplicate_match_for_settings(settings, symbol)
        if legacy_match:
            logging.warning(
                "Legacy duplicate guard matched current symbol; blocking safely"
            )
            return {
                "is_duplicate": True,
                "reason": "legacy_duplicate_match",
                "age_seconds": None,
                "matched_state": None,
            }

        return {
            "is_duplicate": False,
            "reason": "no_matching_state",
            "age_seconds": None,
            "matched_state": None,
        }

    state_symbol = state.get("symbol")
    state_side = state.get("side")
    state_qty = state.get("qty")
    state_timestamp = state.get("timestamp")

    if state_symbol != symbol or state_side != side or state_qty != qty:
        logging.info("State file does not match current order signature")
        return {
            "is_duplicate": False,
            "reason": "state_signature_mismatch",
            "age_seconds": None,
            "matched_state": state,
        }

    recorded_at = parse_iso8601(state_timestamp)
    if recorded_at is None:
        logging.warning("State timestamp is invalid; blocking safely")
        return {
            "is_duplicate": True,
            "reason": "invalid_state_timestamp",
            "age_seconds": None,
            "matched_state": state,
        }

    now = datetime.now(timezone.utc)
    age_seconds = int((now - recorded_at).total_seconds())

    if age_seconds < 0:
        logging.warning("State timestamp is in the future; blocking safely")
        return {
            "is_duplicate": True,
            "reason": "future_state_timestamp",
            "age_seconds": age_seconds,
            "matched_state": state,
        }

    if age_seconds < settings.duplicate_cooldown_seconds:
        logging.warning(
            "Duplicate order blocked by cooldown: "
            f"symbol={symbol}, side={side}, qty={qty}, age_seconds={age_seconds}, "
            f"cooldown_seconds={settings.duplicate_cooldown_seconds}"
        )
        return {
            "is_duplicate": True,
            "reason": "cooldown_active",
            "age_seconds": age_seconds,
            "matched_state": state,
        }

    logging.info(
        "Previous matching order is outside cooldown window: "
        f"age_seconds={age_seconds}, "
        f"cooldown_seconds={settings.duplicate_cooldown_seconds}"
    )
    return {
        "is_duplicate": False,
        "reason": "cooldown_expired",
        "age_seconds": age_seconds,
        "matched_state": state,
    }


def load_order_state():
    from config import STATE_FILE

    return load_order_state_from_path(STATE_FILE)


def write_order_state(state: dict) -> None:
    from config import STATE_FILE

    write_json_atomic(STATE_FILE, state)
    logging.info(f"Order state written to {STATE_FILE}")


def write_run_report(report: dict) -> None:
    from config import RUN_REPORT_FILE

    write_json_atomic(RUN_REPORT_FILE, report)
    logging.info(f"Run report written to {RUN_REPORT_FILE}")


def legacy_duplicate_match(symbol: str) -> bool:
    from config import LEGACY_LAST_ORDER_FILE

    class _LegacySettings:
        legacy_last_order_file = LEGACY_LAST_ORDER_FILE

    return legacy_duplicate_match_for_settings(_LegacySettings(), symbol)


def duplicate_check(symbol: str, side: str, qty: int):
    from config import (
        STATE_FILE,
        LEGACY_LAST_ORDER_FILE,
        OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
    )

    class _ConfigBackedSettings:
        state_file = STATE_FILE
        legacy_last_order_file = LEGACY_LAST_ORDER_FILE
        duplicate_cooldown_seconds = OPENCLAW_DUPLICATE_COOLDOWN_SECONDS

    return duplicate_check_for_settings(_ConfigBackedSettings(), symbol, side, qty)
