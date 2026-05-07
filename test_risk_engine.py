from __future__ import annotations

import unittest

from broker_interface import BrokerOpenOrderState, BrokerPositionState
from risk_engine import reconcile_position


class FakeBrokerStateReader:
    def __init__(
        self,
        position_result: BrokerPositionState,
        open_order_result: BrokerOpenOrderState,
    ) -> None:
        self.position_result = position_result
        self.open_order_result = open_order_result

    def get_existing_position(self, symbol: str) -> BrokerPositionState:
        return self.position_result

    def get_open_buy_order_qty(self, symbol: str) -> BrokerOpenOrderState:
        return self.open_order_result


class ReconcilePositionTests(unittest.TestCase):
    def test_position_lookup_failure(self) -> None:
        broker_state = FakeBrokerStateReader(
            position_result=BrokerPositionState(
                broker_name="fake",
                found=None,
                qty=None,
                raw_qty=None,
                side=None,
                reason="position_lookup_error",
                error="position lookup failed",
            ),
            open_order_result=BrokerOpenOrderState(
                broker_name="fake",
                passed=True,
                open_buy_order_qty=0,
                open_buy_order_count=0,
                reason="open_buy_orders_loaded",
            ),
        )

        result = reconcile_position(broker_state, "AAPL", 1, 5)

        self.assertEqual(
            result,
            {
                "passed": False,
                "reason": "broker_position_lookup_failed",
                "message": "position lookup failed",
                "existing_qty": None,
                "open_buy_order_qty": None,
                "projected_qty": None,
            },
        )

    def test_open_order_lookup_failure(self) -> None:
        broker_state = FakeBrokerStateReader(
            position_result=BrokerPositionState(
                broker_name="fake",
                found=True,
                qty=2,
                raw_qty="2",
                side="long",
                reason="position_found",
            ),
            open_order_result=BrokerOpenOrderState(
                broker_name="fake",
                passed=False,
                open_buy_order_qty=None,
                open_buy_order_count=None,
                reason="open_buy_order_lookup_failed",
                error="open order lookup failed",
            ),
        )

        result = reconcile_position(broker_state, "AAPL", 1, 5)

        self.assertEqual(
            result,
            {
                "passed": False,
                "reason": "broker_open_buy_order_lookup_failed",
                "message": "open order lookup failed",
                "existing_qty": 2,
                "open_buy_order_qty": None,
                "projected_qty": None,
            },
        )

    def test_projected_exposure_exceeds_max_position_size(self) -> None:
        broker_state = FakeBrokerStateReader(
            position_result=BrokerPositionState(
                broker_name="fake",
                found=True,
                qty=3,
                raw_qty="3",
                side="long",
                reason="position_found",
            ),
            open_order_result=BrokerOpenOrderState(
                broker_name="fake",
                passed=True,
                open_buy_order_qty=2,
                open_buy_order_count=1,
                reason="open_buy_orders_loaded",
            ),
        )

        result = reconcile_position(broker_state, "AAPL", 1, 5)

        self.assertEqual(
            result,
            {
                "passed": False,
                "reason": "projected_exposure_exceeds_max_position_size",
                "message": (
                    "projected exposure 6 exceeds max_position_size 5 "
                    "(existing=3, open_buy_orders=2, requested=1)"
                ),
                "existing_qty": 3,
                "open_buy_order_qty": 2,
                "projected_qty": 6,
            },
        )

    def test_successful_reconciliation(self) -> None:
        broker_state = FakeBrokerStateReader(
            position_result=BrokerPositionState(
                broker_name="fake",
                found=True,
                qty=1,
                raw_qty="1",
                side="long",
                reason="position_found",
            ),
            open_order_result=BrokerOpenOrderState(
                broker_name="fake",
                passed=True,
                open_buy_order_qty=1,
                open_buy_order_count=1,
                reason="open_buy_orders_loaded",
            ),
        )

        result = reconcile_position(broker_state, "AAPL", 1, 5)

        self.assertEqual(
            result,
            {
                "passed": True,
                "reason": "broker_reconciliation_passed",
                "message": "broker_reconciliation_passed",
                "existing_qty": 1,
                "open_buy_order_qty": 1,
                "projected_qty": 3,
            },
        )


if __name__ == "__main__":
    unittest.main()
