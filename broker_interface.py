from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BrokerAccountState:
    broker_name: str
    buying_power: float
    raw_account: object | None = None


@dataclass(frozen=True, slots=True)
class BrokerPositionState:
    broker_name: str
    found: bool | None
    qty: int | None
    raw_qty: str | None
    side: str | None
    reason: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class BrokerOpenOrderState:
    broker_name: str
    passed: bool
    open_buy_order_qty: int | None
    open_buy_order_count: int | None
    reason: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class BrokerOrderResult:
    broker_name: str
    order_id: str | None
    order_status: str | None
    broker_status: str | None
    is_terminal: bool
    raw_response: object | None = None


@dataclass(frozen=True, slots=True)
class BrokerCapabilities:
    broker_name: str
    supports_market_orders: bool
    supports_account_read: bool
    supports_positions_read: bool
    supports_open_orders_read: bool
    supports_paper_trading: bool
    lifecycle_async: bool


@dataclass(frozen=True, slots=True)
class BrokerError:
    broker_name: str
    reason: str
    message: str
    retryable: bool = False
    raw_error: object | None = None


@dataclass(frozen=True, slots=True)
class BrokerLifecycleResult:
    broker_name: str
    operation: str
    passed: bool
    reason: str
    message: str
    connected: bool
    retryable: bool
    elapsed_ms: int | None = None
    raw_error: object | None = None


class BrokerLifecycle(Protocol):
    def connect(self, timeout_seconds: float | None = None) -> BrokerLifecycleResult:
        ...

    def health_check(
        self, timeout_seconds: float | None = None
    ) -> BrokerLifecycleResult:
        ...

    def disconnect(self, timeout_seconds: float | None = None) -> BrokerLifecycleResult:
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


class BrokerCapabilitiesProvider(Protocol):
    def get_capabilities(self) -> BrokerCapabilities:
        ...
