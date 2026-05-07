import logging

from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest


class AlpacaBrokerAdapter:
    def __init__(self, client) -> None:
        self.client = client

    def get_account_buying_power(self) -> float:
        account = self.client.get_account()
        buying_power = float(account.buying_power)
        logging.info(f"Account buying power: {buying_power}")
        return buying_power

    def get_existing_position(self, symbol: str) -> dict:
        try:
            position = self.client.get_open_position(symbol)
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

    def get_open_buy_order_qty(self, symbol: str) -> dict:
        try:
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                symbols=[symbol],
                side=OrderSide.BUY,
            )
            orders = self.client.get_orders(filter=request)

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
