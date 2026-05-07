from __future__ import annotations

import unittest
from types import SimpleNamespace

from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, TimeInForce

from alpaca_broker_adapter import AlpacaBrokerAdapter


class FakeClient:
    def __init__(
        self,
        *,
        position=None,
        position_exception: Exception | None = None,
        orders=None,
        orders_exception: Exception | None = None,
        submit_exception: Exception | None = None,
    ) -> None:
        self.position = position
        self.position_exception = position_exception
        self.orders = [] if orders is None else orders
        self.orders_exception = orders_exception
        self.submit_exception = submit_exception
        self.order_filter = None
        self.submitted_order = None

    def get_account(self):
        return SimpleNamespace(buying_power=self.buying_power)

    def get_open_position(self, symbol: str):
        if self.position_exception is not None:
            raise self.position_exception
        return self.position

    def get_orders(self, filter):
        if self.orders_exception is not None:
            raise self.orders_exception
        self.order_filter = filter
        return self.orders

    def submit_order(self, order):
        if self.submit_exception is not None:
            raise self.submit_exception
        self.submitted_order = order
        return self.submit_response


def api_error(message: str, status_code: int | None = None) -> APIError:
    http_error = None
    if status_code is not None:
        http_error = SimpleNamespace(
            response=SimpleNamespace(status_code=status_code),
            request=None,
        )
    return APIError(f'{{"code": 0, "message": "{message}"}}', http_error)


class AlpacaBrokerAdapterTests(unittest.TestCase):
    def test_lifecycle_methods_are_noops_for_alpaca(self) -> None:
        adapter = AlpacaBrokerAdapter(FakeClient())

        self.assertIsNone(adapter.connect())
        self.assertTrue(adapter.health_check())
        self.assertIsNone(adapter.disconnect())

    def test_build_market_order_preserves_current_alpaca_request(self) -> None:
        adapter = AlpacaBrokerAdapter(None)

        order = adapter.build_market_order("AAPL", 1)

        self.assertEqual(order.symbol, "AAPL")
        self.assertEqual(order.qty, 1)
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.time_in_force, TimeInForce.DAY)

    def test_string_buying_power_returns_float(self) -> None:
        client = FakeClient()
        client.buying_power = "123.45"
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_account_buying_power()

        self.assertEqual(result, 123.45)
        self.assertIsInstance(result, float)

    def test_numeric_buying_power_returns_float_compatible_value(self) -> None:
        client = FakeClient()
        client.buying_power = 123.45
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.get_account_buying_power()

        self.assertEqual(result, 123.45)
        self.assertIsInstance(result, float)

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

    def test_submit_market_order_returns_raw_response(self) -> None:
        order = object()
        response = SimpleNamespace(id="order-1", status="accepted")
        client = FakeClient()
        client.submit_response = response
        adapter = AlpacaBrokerAdapter(client)

        result = adapter.submit_market_order(order)

        self.assertIs(result, response)
        self.assertIs(client.submitted_order, order)
        self.assertEqual(result.status, "accepted")

    def test_normalize_order_response_preserves_raw_response(self) -> None:
        response = SimpleNamespace(id=123, status="accepted")
        adapter = AlpacaBrokerAdapter(FakeClient())

        result = adapter.normalize_order_response(response)

        self.assertEqual(
            result,
            {
                "order_id": "123",
                "order_status": "accepted",
                "raw_response": response,
            },
        )
        self.assertIs(result["raw_response"], response)

    def test_submit_market_order_failure_propagates(self) -> None:
        error = RuntimeError("submit failed")
        client = FakeClient(submit_exception=error)
        adapter = AlpacaBrokerAdapter(client)

        with self.assertRaises(RuntimeError) as context:
            adapter.submit_market_order(object())

        self.assertIs(context.exception, error)


if __name__ == "__main__":
    unittest.main()
