from __future__ import annotations

import unittest

from broker_interface import (
    BrokerAccountState,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from fake_ibkr_callback_aggregator import (
    aggregate_account,
    aggregate_lifecycle,
    aggregate_open_buy_orders,
    aggregate_order_result,
    aggregate_position,
)


class FakeIBKRCallbackAggregatorTests(unittest.TestCase):
    def test_connect_success(self) -> None:
        result = aggregate_lifecycle(
            [
                {
                    "event_type": "connect_ready",
                    "message": "api ready",
                    "elapsed_ms": 12,
                }
            ]
        )

        self.assertEqual(
            result,
            BrokerLifecycleResult(
                broker_name="ibkr",
                operation="connect",
                passed=True,
                reason="connect_ready",
                message="api ready",
                connected=True,
                retryable=False,
                elapsed_ms=12,
                raw_error=None,
            ),
        )

    def test_connect_timeout(self) -> None:
        timeout_event = {
            "event_type": "timeout",
            "operation": "connect",
            "message": "no ready callback",
            "elapsed_ms": 5000,
        }

        result = aggregate_lifecycle([timeout_event])

        self.assertEqual(
            result,
            BrokerLifecycleResult(
                broker_name="ibkr",
                operation="connect",
                passed=False,
                reason="connect_timeout",
                message="no ready callback",
                connected=False,
                retryable=True,
                elapsed_ms=5000,
                raw_error=timeout_event,
            ),
        )

    def test_account_snapshot_success(self) -> None:
        account_event = {"event_type": "account_value", "buying_power": "12345.67"}

        result = aggregate_account([account_event])

        self.assertEqual(
            result,
            BrokerAccountState(
                broker_name="ibkr",
                buying_power=12345.67,
                raw_account=account_event,
            ),
        )

    def test_position_found(self) -> None:
        result = aggregate_position(
            [
                {"event_type": "position", "symbol": "MSFT", "qty": "2"},
                {
                    "event_type": "position",
                    "symbol": "AAPL",
                    "qty": "3",
                    "side": "long",
                },
                {"event_type": "position_end"},
            ],
            symbol="AAPL",
        )

        self.assertEqual(
            result,
            BrokerPositionState(
                broker_name="ibkr",
                found=True,
                qty=3,
                raw_qty="3",
                side="long",
                reason="position_found",
            ),
        )

    def test_no_position(self) -> None:
        result = aggregate_position(
            [
                {"event_type": "position", "symbol": "MSFT", "qty": "2"},
                {"event_type": "position_end"},
            ],
            symbol="AAPL",
        )

        self.assertEqual(
            result,
            BrokerPositionState(
                broker_name="ibkr",
                found=False,
                qty=0,
                raw_qty="0",
                side=None,
                reason="no_position",
            ),
        )

    def test_open_buy_order_aggregation(self) -> None:
        result = aggregate_open_buy_orders(
            [
                {
                    "event_type": "open_order",
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "2",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "symbol": "AAPL",
                    "side": "SELL",
                    "qty": "7",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "1",
                    "status": "PreSubmitted",
                },
                {
                    "event_type": "open_order",
                    "symbol": "MSFT",
                    "side": "BUY",
                    "qty": "9",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "4",
                    "status": "Filled",
                },
                {"event_type": "open_order_end"},
            ],
            symbol="AAPL",
        )

        self.assertEqual(
            result,
            BrokerOpenOrderState(
                broker_name="ibkr",
                passed=True,
                open_buy_order_qty=3,
                open_buy_order_count=2,
                reason="open_buy_orders_loaded",
            ),
        )

    def test_submitted_order(self) -> None:
        submitted_event = {
            "event_type": "order_status",
            "order_id": 101,
            "status": "Submitted",
        }

        result = aggregate_order_result(
            [
                {"event_type": "next_valid_id", "order_id": 101},
                submitted_event,
            ]
        )

        self.assertEqual(
            result,
            BrokerOrderResult(
                broker_name="ibkr",
                order_id="101",
                order_status="submitted",
                broker_status="Submitted",
                is_terminal=False,
                raw_response=submitted_event,
            ),
        )

    def test_filled_order(self) -> None:
        filled_event = {
            "event_type": "order_status",
            "order_id": 101,
            "status": "Filled",
        }

        result = aggregate_order_result(
            [
                {"event_type": "next_valid_id", "order_id": 101},
                {"event_type": "order_status", "order_id": 101, "status": "Submitted"},
                filled_event,
            ]
        )

        self.assertEqual(
            result,
            BrokerOrderResult(
                broker_name="ibkr",
                order_id="101",
                order_status="filled",
                broker_status="Filled",
                is_terminal=True,
                raw_response=filled_event,
            ),
        )

    def test_rejected_order(self) -> None:
        rejected_event = {
            "event_type": "order_status",
            "order_id": 101,
            "status": "Rejected",
        }

        result = aggregate_order_result(
            [
                {"event_type": "next_valid_id", "order_id": 101},
                rejected_event,
            ]
        )

        self.assertEqual(
            result,
            BrokerOrderResult(
                broker_name="ibkr",
                order_id="101",
                order_status="rejected",
                broker_status="Rejected",
                is_terminal=True,
                raw_response=rejected_event,
            ),
        )

    def test_no_order_id_timeout(self) -> None:
        timeout_event = {
            "event_type": "timeout",
            "operation": "submit_market_order",
            "message": "no order id callback",
        }

        result = aggregate_order_result([timeout_event])

        self.assertEqual(
            result,
            BrokerOrderResult(
                broker_name="ibkr",
                order_id=None,
                order_status="timeout",
                broker_status=None,
                is_terminal=True,
                raw_response=timeout_event,
            ),
        )


if __name__ == "__main__":
    unittest.main()
