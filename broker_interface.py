from __future__ import annotations

from typing import Protocol


class BrokerLifecycle(Protocol):
    def connect(self):
        ...

    def health_check(self):
        ...

    def disconnect(self):
        ...


class BrokerStateReader(Protocol):
    def get_account_buying_power(self) -> float:
        ...

    def get_existing_position(self, symbol: str) -> dict:
        ...

    def get_open_buy_order_qty(self, symbol: str) -> dict:
        ...


class BrokerOrderExecutor(Protocol):
    def submit_market_order(self, order):
        ...


class BrokerOrderBuilder(Protocol):
    def build_market_order(self, symbol: str, qty: int):
        ...


class BrokerOrderResponseNormalizer(Protocol):
    def normalize_order_response(self, response) -> dict:
        ...
