from __future__ import annotations

import unittest

import risk_engine


class FakePosition:
    def __init__(self, qty: int, side: str = "long"):
        self.qty = qty
        self.side = side


class FakeOrder:
    def __init__(self, qty: int):
        self.qty = qty


class FakeClient:
    def __init__(self, *, position=None, orders=None, position_error=None, orders_error=None):
        self._position = position
        self._orders = orders or []
        self._position_error = position_error
        self._orders_error = orders_error

    def get_position(self, symbol: str):
        if self._position_error:
            raise self._position_error
        return self._position

    def list_open_orders(self, *, symbol=None, side=None):
        if self._orders_error:
            raise self._orders_error
        return self._orders


class RiskEngineTests(unittest.TestCase):
    def test_get_existing_position_returns_no_position_when_broker_has_none(self):
        result = risk_engine.get_existing_position(FakeClient(position=None), "AAPL")

        self.assertEqual(result["found"], False)
        self.assertEqual(result["qty"], 0)
        self.assertEqual(result["reason"], "no_position")

    def test_get_existing_position_returns_position_details(self):
        result = risk_engine.get_existing_position(
            FakeClient(position=FakePosition(qty=3)),
            "AAPL",
        )

        self.assertEqual(result["found"], True)
        self.assertEqual(result["qty"], 3)
        self.assertEqual(result["reason"], "position_found")

    def test_get_open_buy_order_qty_sums_open_buy_orders(self):
        result = risk_engine.get_open_buy_order_qty(
            FakeClient(orders=[FakeOrder(1), FakeOrder(2)]),
            "AAPL",
        )

        self.assertEqual(result["passed"], True)
        self.assertEqual(result["open_buy_order_qty"], 3)
        self.assertEqual(result["open_buy_order_count"], 2)

    def test_reconcile_position_blocks_when_projected_exposure_exceeds_max(self):
        result = risk_engine.reconcile_position(
            FakeClient(position=FakePosition(qty=3), orders=[FakeOrder(2)]),
            "AAPL",
            requested_qty=1,
            max_position_size=5,
        )

        self.assertEqual(result["passed"], False)
        self.assertEqual(result["reason"], "projected_exposure_exceeds_max_position_size")
        self.assertEqual(result["projected_qty"], 6)

    def test_reconcile_position_passes_when_projected_exposure_is_within_limit(self):
        result = risk_engine.reconcile_position(
            FakeClient(position=FakePosition(qty=3), orders=[FakeOrder(0)]),
            "AAPL",
            requested_qty=1,
            max_position_size=5,
        )

        self.assertEqual(result["passed"], True)
        self.assertEqual(result["reason"], "broker_reconciliation_passed")
        self.assertEqual(result["projected_qty"], 4)

    def test_reconcile_position_reports_position_lookup_failure(self):
        result = risk_engine.reconcile_position(
            FakeClient(position_error=RuntimeError("position lookup failed")),
            "AAPL",
            requested_qty=1,
            max_position_size=5,
        )

        self.assertEqual(result["passed"], False)
        self.assertEqual(result["reason"], "broker_position_lookup_failed")


if __name__ == "__main__":
    unittest.main()
