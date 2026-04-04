import logging
from datetime import datetime, timezone

from alpaca.trading.requests import GetOrdersRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from alpaca.common.exceptions import APIError

from config import (
    client,
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    OPENCLAW_QTY,
    OPENCLAW_MAX_POSITION_SIZE,
    OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
)
from state_manager import load_order_state, legacy_duplicate_match
from utils import parse_iso8601


def validate_config() -> bool:
    if not ALPACA_API_KEY:
        logging.error("Missing required config: ALPACA_API_KEY")
        return False

    if not ALPACA_SECRET_KEY:
        logging.error("Missing required config: ALPACA_SECRET_KEY")
        return False

    if OPENCLAW_QTY <= 0:
        logging.error(f"Invalid OPENCLAW_QTY: {OPENCLAW_QTY}")
        return False

    if OPENCLAW_MAX_POSITION_SIZE <= 0:
        logging.error(
            f"Invalid OPENCLAW_MAX_POSITION_SIZE: {OPENCLAW_MAX_POSITION_SIZE}"
        )
        return False

    if OPENCLAW_DUPLICATE_COOLDOWN_SECONDS < 0:
        logging.error(
            "Invalid OPENCLAW_DUPLICATE_COOLDOWN_SECONDS: "
            f"{OPENCLAW_DUPLICATE_COOLDOWN_SECONDS}"
        )
        return False

    return True


def duplicate_check(symbol: str, side: str, qty: int):
    state = load_order_state()

    if state is None:
        legacy_match = legacy_duplicate_match(symbol)
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

    if age_seconds < OPENCLAW_DUPLICATE_COOLDOWN_SECONDS:
        logging.warning(
            "Duplicate order blocked by cooldown: "
            f"symbol={symbol}, side={side}, qty={qty}, age_seconds={age_seconds}, "
            f"cooldown_seconds={OPENCLAW_DUPLICATE_COOLDOWN_SECONDS}"
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
        f"cooldown_seconds={OPENCLAW_DUPLICATE_COOLDOWN_SECONDS}"
    )
    return {
        "is_duplicate": False,
        "reason": "cooldown_expired",
        "age_seconds": age_seconds,
        "matched_state": state,
    }


def get_market_session_status() -> dict:
    try:
        clock = client.get_clock()
        now = clock.timestamp

        today = now.date()
        calendar_request = GetCalendarRequest(start=today, end=today)
        calendar_days = client.get_calendar(filters=calendar_request)

        if not calendar_days:
            logging.warning("No calendar entry returned for today; treating as market holiday/closed")
            return {
                "is_open": False,
                "reason": "market_holiday_or_closed_day",
                "current_time": str(now),
                "session_open": None,
                "session_close": None,
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        day = calendar_days[0]

        session_open = datetime.combine(today, day.open, tzinfo=now.tzinfo)
        session_close = datetime.combine(today, day.close, tzinfo=now.tzinfo)

        if now < session_open:
            return {
                "is_open": False,
                "reason": "before_regular_session_open",
                "current_time": str(now),
                "session_open": str(session_open),
                "session_close": str(session_close),
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        if now >= session_close:
            return {
                "is_open": False,
                "reason": "after_regular_session_close",
                "current_time": str(now),
                "session_open": str(session_open),
                "session_close": str(session_close),
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        if not clock.is_open:
            return {
                "is_open": False,
                "reason": "broker_clock_closed",
                "current_time": str(now),
                "session_open": str(session_open),
                "session_close": str(session_close),
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
            }

        return {
            "is_open": True,
            "reason": "regular_session_open",
            "current_time": str(now),
            "session_open": str(session_open),
            "session_close": str(session_close),
            "next_open": str(clock.next_open),
            "next_close": str(clock.next_close),
        }

    except Exception as e:
        logging.exception("Market session lookup failed")
        return {
            "is_open": False,
            "reason": "market_session_lookup_failed",
            "error": str(e),
            "current_time": None,
            "session_open": None,
            "session_close": None,
            "next_open": None,
            "next_close": None,
        }


def get_existing_position(symbol: str) -> dict:
    try:
        position = client.get_open_position(symbol)
        qty = int(float(position.qty))
        logging.info(f"Broker position found for {symbol}: qty={qty}")
        return {
            "found": True,
            "qty": qty,
            "raw_qty": str(position.qty),
            "side": "long",
            "reason": "position_found",
        }
    except APIError as e:
        error_text = str(e).lower()
        status_code = getattr(e, "status_code", None)

        if status_code == 404 or "position does not exist" in error_text:
            logging.info(f"No existing broker position for {symbol}")
            return {
                "found": False,
                "qty": 0,
                "raw_qty": "0",
                "side": None,
                "reason": "no_position",
            }

        logging.exception(f"Broker position lookup failed for {symbol}")
        return {
            "found": None,
            "qty": None,
            "raw_qty": None,
            "side": None,
            "reason": "position_lookup_error",
            "error": str(e),
        }


def get_open_buy_order_qty(symbol: str) -> dict:
    try:
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol],
            side=OrderSide.BUY,
        )
        orders = client.get_orders(filter=request)

        total_qty = 0
        for order in orders:
            try:
                total_qty += int(float(order.qty))
            except (TypeError, ValueError):
                logging.warning(
                    f"Could not parse open order qty safely for order id={getattr(order, 'id', 'unknown')}"
                )

        logging.info(
            f"Open buy orders for {symbol}: count={len(orders)}, total_qty={total_qty}"
        )
        return {
            "passed": True,
            "open_buy_order_qty": total_qty,
            "open_buy_order_count": len(orders),
            "reason": "open_buy_orders_loaded",
        }
    except Exception as e:
        logging.exception(f"Open buy order lookup failed for {symbol}")
        return {
            "passed": False,
            "open_buy_order_qty": None,
            "open_buy_order_count": None,
            "reason": "open_buy_order_lookup_failed",
            "error": str(e),
        }


def reconcile_position(symbol: str, requested_qty: int, max_position_size: int) -> dict:
    position_result = get_existing_position(symbol)
    if position_result["found"] is None:
        return {
            "passed": False,
            "reason": "broker_position_lookup_failed",
            "message": position_result.get("error", "Unknown broker position lookup error"),
            "existing_qty": None,
            "open_buy_order_qty": None,
            "projected_qty": None,
        }

    open_order_result = get_open_buy_order_qty(symbol)
    if not open_order_result["passed"]:
        return {
            "passed": False,
            "reason": "broker_open_buy_order_lookup_failed",
            "message": open_order_result.get("error", "Unknown open buy order lookup error"),
            "existing_qty": position_result["qty"],
            "open_buy_order_qty": None,
            "projected_qty": None,
        }

    existing_qty = position_result["qty"]
    open_buy_order_qty = open_order_result["open_buy_order_qty"]
    projected_qty = existing_qty + open_buy_order_qty + requested_qty

    if projected_qty > max_position_size:
        message = (
            f"projected exposure {projected_qty} exceeds max_position_size "
            f"{max_position_size} (existing={existing_qty}, "
            f"open_buy_orders={open_buy_order_qty}, requested={requested_qty})"
        )
        logging.warning(f"Broker reconciliation failed: {message}")
        return {
            "passed": False,
            "reason": "projected_exposure_exceeds_max_position_size",
            "message": message,
            "existing_qty": existing_qty,
            "open_buy_order_qty": open_buy_order_qty,
            "projected_qty": projected_qty,
        }

    logging.info(
        "Broker reconciliation passed: "
        f"existing_qty={existing_qty}, "
        f"open_buy_order_qty={open_buy_order_qty}, "
        f"requested_qty={requested_qty}, "
        f"projected_qty={projected_qty}, "
        f"max_position_size={max_position_size}"
    )
    return {
        "passed": True,
        "reason": "broker_reconciliation_passed",
        "message": "broker_reconciliation_passed",
        "existing_qty": existing_qty,
        "open_buy_order_qty": open_buy_order_qty,
        "projected_qty": projected_qty,
    }


def risk_check(symbol, qty, buying_power, max_position_size=5, allowed_symbols=None):
    if qty <= 0:
        message = f"qty must be > 0 (got {qty})"
        logging.warning(f"Risk check failed: {message}")
        return {
            "passed": False,
            "reason": "qty_non_positive",
            "message": message,
            "estimated_cost": None,
        }

    if qty > max_position_size:
        message = f"qty {qty} exceeds max_position_size {max_position_size}"
        logging.warning(f"Risk check failed: {message}")
        return {
            "passed": False,
            "reason": "qty_exceeds_max_position_size",
            "message": message,
            "estimated_cost": None,
        }

    if allowed_symbols and symbol not in allowed_symbols:
        message = f"symbol {symbol} not in allowed list"
        logging.warning(f"Risk check failed: {message}")
        return {
            "passed": False,
            "reason": "symbol_not_allowed",
            "message": message,
            "estimated_cost": None,
        }

    estimated_cost = qty * 100
    if estimated_cost > buying_power:
        message = (
            f"estimated cost {estimated_cost} exceeds buying power {buying_power}"
        )
        logging.warning(f"Risk check failed: {message}")
        return {
            "passed": False,
            "reason": "insufficient_buying_power_estimate",
            "message": message,
            "estimated_cost": estimated_cost,
        }

    logging.info(
        f"Risk check passed for symbol={symbol}, qty={qty}, estimated_cost={estimated_cost}"
    )
    return {
        "passed": True,
        "reason": "passed",
        "message": "risk_check_passed",
        "estimated_cost": estimated_cost,
    }
