from __future__ import annotations

import logging
from calendar import day_name

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetCalendarRequest, GetOrdersRequest, MarketOrderRequest

from broker_client import BrokerClient
from broker_models import (
    BrokerAccount,
    BrokerOrder,
    BrokerPosition,
    MarketSessionStatus,
    OrderSubmission,
)


def _normalize_order_side(side: str) -> OrderSide:
    normalized = side.lower()
    if normalized == "buy":
        return OrderSide.BUY
    if normalized == "sell":
        return OrderSide.SELL
    raise ValueError(f"Unsupported order side: {side}")


def _normalize_time_in_force(time_in_force: str) -> TimeInForce:
    normalized = time_in_force.lower()
    if normalized == "day":
        return TimeInForce.DAY
    raise ValueError(f"Unsupported time_in_force: {time_in_force}")


class AlpacaBrokerClient(BrokerClient):
    def __init__(self, api_key: str, secret_key: str, *, paper: bool = True):
        self._client = TradingClient(api_key, secret_key, paper=paper)

    @property
    def broker_name(self) -> str:
        return "alpaca"

    def get_account(self) -> BrokerAccount:
        account = self._client.get_account()
        return BrokerAccount(
            account_id=str(getattr(account, "id", "")) or None,
            buying_power=float(account.buying_power),
        )

    def get_market_session_status(self) -> MarketSessionStatus:
        try:
            clock = self._client.get_clock()
            now = clock.timestamp

            today = now.date()
            calendar_request = GetCalendarRequest(start=today, end=today)
            calendar_days = self._client.get_calendar(filters=calendar_request)

            if not calendar_days:
                is_weekend = today.weekday() >= 5
                reason = "weekend_closed_day" if is_weekend else "market_holiday_closed_day"
                closed_day_label = (
                    day_name[today.weekday()] if is_weekend else "weekday holiday/closure"
                )
                logging.warning(
                    "No calendar entry returned for today; treating as closed day: "
                    f"{closed_day_label}"
                )
                return MarketSessionStatus(
                    is_open=False,
                    reason=reason,
                    current_time=str(now),
                    session_open=None,
                    session_close=None,
                    next_open=str(clock.next_open),
                    next_close=str(clock.next_close),
                )

            day = calendar_days[0]
            session_open = day.open.replace(tzinfo=now.tzinfo)
            session_close = day.close.replace(tzinfo=now.tzinfo)

            if now < session_open:
                return MarketSessionStatus(
                    is_open=False,
                    reason="before_regular_session_open",
                    current_time=str(now),
                    session_open=str(session_open),
                    session_close=str(session_close),
                    next_open=str(clock.next_open),
                    next_close=str(clock.next_close),
                )

            if now >= session_close:
                return MarketSessionStatus(
                    is_open=False,
                    reason="after_regular_session_close",
                    current_time=str(now),
                    session_open=str(session_open),
                    session_close=str(session_close),
                    next_open=str(clock.next_open),
                    next_close=str(clock.next_close),
                )

            if not clock.is_open:
                return MarketSessionStatus(
                    is_open=False,
                    reason="broker_clock_closed",
                    current_time=str(now),
                    session_open=str(session_open),
                    session_close=str(session_close),
                    next_open=str(clock.next_open),
                    next_close=str(clock.next_close),
                )

            return MarketSessionStatus(
                is_open=True,
                reason="regular_session_open",
                current_time=str(now),
                session_open=str(session_open),
                session_close=str(session_close),
                next_open=str(clock.next_open),
                next_close=str(clock.next_close),
            )
        except Exception as exc:
            logging.exception("Market session lookup failed")
            return MarketSessionStatus(
                is_open=False,
                reason="market_session_lookup_failed",
                current_time=None,
                session_open=None,
                session_close=None,
                next_open=None,
                next_close=None,
                error=str(exc),
            )

    def get_position(self, symbol: str) -> BrokerPosition | None:
        try:
            position = self._client.get_open_position(symbol)
            qty = int(float(position.qty))
            return BrokerPosition(symbol=symbol, qty=qty, side="long")
        except APIError as exc:
            error_text = str(exc).lower()
            status_code = getattr(exc, "status_code", None)
            if status_code == 404 or "position does not exist" in error_text:
                return None
            raise

    def list_open_orders(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
    ) -> list[BrokerOrder]:
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol] if symbol else None,
            side=_normalize_order_side(side) if side else None,
        )
        orders = self._client.get_orders(filter=request)
        normalized_orders: list[BrokerOrder] = []
        for order in orders:
            try:
                qty = int(float(order.qty))
            except (TypeError, ValueError):
                logging.warning(
                    "Could not parse open order qty safely for order id=%s",
                    getattr(order, "id", "unknown"),
                )
                qty = 0
            normalized_orders.append(
                BrokerOrder(
                    order_id=str(getattr(order, "id", "")) or None,
                    symbol=str(getattr(order, "symbol", symbol or "")),
                    qty=qty,
                    side=str(getattr(order, "side", side or "unknown")).lower(),
                    status=str(getattr(order, "status", "unknown")),
                )
            )
        return normalized_orders

    def submit_market_order(
        self,
        *,
        symbol: str,
        qty: int,
        side: str,
        time_in_force: str = "day",
    ) -> OrderSubmission:
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=_normalize_order_side(side),
            time_in_force=_normalize_time_in_force(time_in_force),
        )
        response = self._client.submit_order(order)
        return OrderSubmission(
            order_id=str(getattr(response, "id", "")) or None,
            status=str(response.status),
        )
