from __future__ import annotations

import unittest
from types import SimpleNamespace

from alpaca.common.exceptions import APIError

from alpaca_broker_adapter import AlpacaBrokerAdapter


class FakeClient:
    def __init__(
        self,
        *,
        position=None,
        position_exception: Exception | None = None,
        orders=None,
        orders_exception: Exception | None = None,
    ) -> None:
        self.position = position
        self.position_exception = position_exception
        self.orders = [] if orders is None else orders
        self.orders_exception = orders_exception
        self.order_filter = None

    def get_open_position(self, symbol: str):
        if self.position_exception is not None:
            raise self.position_exception
        return self.position

    def get_orders(self, filter):
        if self.orders_exception is not None:
            raise self.orders_exception
        self.order_filter = filter
        return self.orders


def api_error(message: str, status_code: int | None = None) -> APIError:
    http_error = None
    if status_code is not None:
        http_error = SimpleNamespace(
            response=SimpleNamespace(status_code=status_code),
            request=None,
        )
    return APIError(f'{{"code": 0, "message": "{message}"}}', http_error)


class AlpacaBrokerAdapterTests(unittest.TestCase):
    def test_existing_position_found(self) -> None:
        client = FakeClient(position=SimpleNamespace(qty="3.0"))
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_existing_position("AAPL")

        self.assertEqual(
            result,
            {
                "found": True,
                "qty": 3,
                "raw_qty": "3.0",
                "side": "long",
                "reason": "position_found",
            },
        )

    def test_missing_position(self) -> None:
        client = FakeClient(
            position_exception=api_error("position does not exist", status_code=404)
        )
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_existing_position("AAPL")

        self.assertEqual(
            result,
            {
                "found": False,
                "qty": 0,
                "raw_qty": "0",
                "side": None,
                "reason": "no_position",
            },
        )

    def test_lookup_error(self) -> None:
        error = api_error("broker unavailable", status_code=500)
        client = FakeClient(position_exception=error)
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_existing_position("AAPL")

        self.assertEqual(result["found"], None)
        self.assertEqual(result["qty"], None)
        self.assertEqual(result["raw_qty"], None)
        self.assertEqual(result["side"], None)
        self.assertEqual(result["reason"], "position_lookup_error")
        self.assertEqual(result["error"], str(error))

    def test_open_buy_orders_found(self) -> None:
        client = FakeClient(
            orders=[
                SimpleNamespace(qty="1"),
                SimpleNamespace(qty="2.0"),
            ]
        )
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_open_buy_order_qty("AAPL")

        self.assertEqual(
            result,
            {
                "passed": True,
                "open_buy_order_qty": 3,
                "open_buy_order_count": 2,
                "reason": "open_buy_orders_loaded",
            },
        )

    def test_invalid_qty_handling(self) -> None:
        client = FakeClient(
            orders=[
                SimpleNamespace(id="valid", qty="2"),
                SimpleNamespace(id="invalid", qty="not-a-number"),
                SimpleNamespace(id="none", qty=None),
            ]
        )
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_open_buy_order_qty("AAPL")

        self.assertEqual(
            result,
            {
                "passed": True,
                "open_buy_order_qty": 2,
                "open_buy_order_count": 3,
                "reason": "open_buy_orders_loaded",
            },
        )

    def test_open_order_lookup_failure(self) -> None:
        error = RuntimeError("orders unavailable")
        client = FakeClient(orders_exception=error)
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_open_buy_order_qty("AAPL")

        self.assertEqual(
            result,
            {
                "passed": False,
                "open_buy_order_qty": None,
                "open_buy_order_count": None,
                "reason": "open_buy_order_lookup_failed",
                "error": str(error),
            },
        )


if __name__ == "__main__":
    unittest.main()
