import logging

from broker_interface import BrokerStateReader


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


def reconcile_position(
    broker_state: BrokerStateReader,
    symbol: str,
    requested_qty: int,
    max_position_size: int,
) -> dict:
    position_result = broker_state.get_existing_position(symbol)
    if position_result["found"] is None:
        return {
            "passed": False,
            "reason": "broker_position_lookup_failed",
            "message": position_result.get("error", "Unknown broker position lookup error"),
            "existing_qty": None,
            "open_buy_order_qty": None,
            "projected_qty": None,
        }

    open_order_result = broker_state.get_open_buy_order_qty(symbol)
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


def risk_check(
    symbol,
    qty,
    buying_power,
    latest_close,
    max_position_size=5,
    allowed_symbols=None,
):
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

    estimated_cost = qty * latest_close
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
