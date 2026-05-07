from __future__ import annotations

from typing import Protocol


class BrokerStateReader(Protocol):
    def get_existing_position(self, symbol: str) -> dict:
        ...

    def get_open_buy_order_qty(self, symbol: str) -> dict:
        ...
