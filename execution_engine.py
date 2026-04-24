import logging

from alpaca.common.exceptions import APIError
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.requests import MarketOrderRequest


def get_market_session_status(client) -> dict:
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

        # Ensure timezone consistency
        session_open = day.open.replace(tzinfo=now.tzinfo)
        session_close = day.close.replace(tzinfo=now.tzinfo)

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


def build_market_order(symbol: str, qty: int):
    return MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )


def get_existing_position(client, symbol: str) -> dict:
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


def get_open_buy_order_qty(client, symbol: str) -> dict:
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


def submit_market_order(client, order):
    logging.info("APPROVED — sending LIVE PAPER order")
    response = client.submit_order(order)
    logging.info(f"Order submitted with status: {response.status}")
    return response
