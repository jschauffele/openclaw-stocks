import logging

from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from alpaca.common.exceptions import APIError


def validate_config(
    alpaca_api_key: str,
    alpaca_secret_key: str,
    qty: int,
    max_position_size: int,
    duplicate_cooldown_seconds: int,
) -> bool:
    if not alpaca_api_key:
        logging.error("Missing required config: ALPACA_API_KEY")
        return False

    if not alpaca_secret_key:
        logging.error("Missing required config: ALPACA_SECRET_KEY")
        return False

    if qty <= 0:
        logging.error(f"Invalid OPENCLAW_QTY: {qty}")
        return False

    if max_position_size <= 0:
        logging.error(f"Invalid OPENCLAW_MAX_POSITION_SIZE: {max_position_size}")
        return False

    if duplicate_cooldown_seconds < 0:
        logging.error(
            "Invalid OPENCLAW_DUPLICATE_COOLDOWN_SECONDS: "
            f"{duplicate_cooldown_seconds}"
        )
        return False

    return True


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


def reconcile_position(client, symbol: str, requested_qty: int, max_position_size: int) -> dict:
    position_result = get_existing_position(client, symbol)
    if position_result["found"] is None:
        return {
            "passed": False,
            "reason": "broker_position_lookup_failed",
            "message": position_result.get("error", "Unknown broker position lookup error"),
            "existing_qty": None,
            "open_buy_order_qty": None,
            "projected_qty": None,
        }

    open_order_result = get_open_buy_order_qty(client, symbol)
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
