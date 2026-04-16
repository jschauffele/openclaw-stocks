from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerAccount:
    account_id: str | None
    buying_power: float


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    qty: int
    side: str | None


@dataclass(frozen=True)
class BrokerOrder:
    order_id: str | None
    symbol: str
    qty: int
    side: str
    status: str


@dataclass(frozen=True)
class MarketSessionStatus:
    is_open: bool
    reason: str
    current_time: str | None
    session_open: str | None
    session_close: str | None
    next_open: str | None
    next_close: str | None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "is_open": self.is_open,
            "reason": self.reason,
            "current_time": self.current_time,
            "session_open": self.session_open,
            "session_close": self.session_close,
            "next_open": self.next_open,
            "next_close": self.next_close,
            "error": self.error,
        }


@dataclass(frozen=True)
class OrderSubmission:
    order_id: str | None
    status: str
