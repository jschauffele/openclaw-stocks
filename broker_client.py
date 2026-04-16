from __future__ import annotations

from typing import Protocol

from broker_models import (
    BrokerAccount,
    BrokerOrder,
    BrokerPosition,
    MarketSessionStatus,
    OrderSubmission,
)


class BrokerClient(Protocol):
    @property
    def broker_name(self) -> str:
        ...

    def get_account(self) -> BrokerAccount:
        ...

    def get_market_session_status(self) -> MarketSessionStatus:
        ...

    def get_position(self, symbol: str) -> BrokerPosition | None:
        ...

    def list_open_orders(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
    ) -> list[BrokerOrder]:
        ...

    def submit_market_order(
        self,
        *,
        symbol: str,
        qty: int,
        side: str,
        time_in_force: str = "day",
    ) -> OrderSubmission:
        ...
