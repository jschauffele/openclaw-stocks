from __future__ import annotations

from broker_interface import BrokerCapabilities


_SKELETON_MESSAGE = "IBKR adapter skeleton only; not runtime-enabled"


class IBKRBrokerAdapter:
    def __init__(self, client=None) -> None:
        self.client = client

    def get_capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            broker_name="ibkr",
            supports_market_orders=False,
            supports_account_read=False,
            supports_positions_read=False,
            supports_open_orders_read=False,
            supports_paper_trading=True,
            lifecycle_async=True,
        )

    def connect(self):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def health_check(self):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def disconnect(self):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def get_account_buying_power(self) -> float:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def get_existing_position(self, symbol: str) -> dict:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def get_open_buy_order_qty(self, symbol: str) -> dict:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def build_market_order(self, symbol: str, qty: int):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def submit_market_order(self, order):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def normalize_order_response(self, response) -> dict:
        raise NotImplementedError(_SKELETON_MESSAGE)
