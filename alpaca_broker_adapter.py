import logging

from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from broker_interface import BrokerCapabilities


_TERMINAL_ORDER_STATUSES = {
    "filled",
    "canceled",
    "cancelled",
    "rejected",
    "expired",
}


class AlpacaBrokerAdapter:
    def __init__(self, client) -> None:
        self.client = client

    def connect(self):
        return None

    def health_check(self):
        return True

    def disconnect(self):
        return None

    def get_capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            broker_name="alpaca",
            supports_market_orders=True,
            supports_account_read=True,
            supports_positions_read=True,
            supports_open_orders_read=True,
            supports_paper_trading=True,
            lifecycle_async=False,
        )

    def get_account_buying_power(self) -> float:
        account = self.client.get_account()
        buying_power = float(account.buying_power)
        logging.info(f"Account buying power: {buying_power}")
        return buying_power

    def build_market_order(self, symbol: str, qty: int):
        return MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )

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

    def submit_market_order(self, order):
        logging.info("APPROVED — sending LIVE PAPER order")
        response = self.client.submit_order(order)
        logging.info(f"Order submitted with status: {response.status}")
        return response

    def normalize_order_response(self, response) -> dict:
        broker_status = str(response.status)
        return {
            "broker_name": "alpaca",
            "order_id": str(response.id),
            "order_status": broker_status,
            "broker_status": broker_status,
            "is_terminal": broker_status.lower() in _TERMINAL_ORDER_STATUSES,
            "raw_response": response,
        }
