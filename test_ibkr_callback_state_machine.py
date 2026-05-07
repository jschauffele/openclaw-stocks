from __future__ import annotations

import unittest

from broker_interface import (
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from fake_ibkr_callback_state_machine import (
    IBKRLifecycleAggregator,
    IBKROpenOrdersSnapshotAggregator,
    IBKROrderStatusAggregator,
    IBKRPositionSnapshotAggregator,
    replay,
)


class FakeIBKRCallbackStateMachineTests(unittest.TestCase):
    def test_lifecycle_success_replay(self) -> None:
        result = replay(
            IBKRLifecycleAggregator(),
            [
                {
                    "event_type": "connect_ready",
                    "message": "api ready",
                    "elapsed_ms": 15,
                }
            ],
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
                elapsed_ms=15,
                raw_error=None,
            ),
        )

    def test_position_snapshot_completion_replay(self) -> None:
        result = replay(
            IBKRPositionSnapshotAggregator(symbol="AAPL", request_id="pos-1"),
            [
                {
                    "event_type": "position",
                    "request_id": "other",
                    "symbol": "AAPL",
                    "qty": "9",
                },
                {
                    "event_type": "position",
                    "request_id": "pos-1",
                    "symbol": "MSFT",
                    "qty": "2",
                },
                {
                    "event_type": "position",
                    "request_id": "pos-1",
                    "symbol": "AAPL",
                    "qty": "3",
                    "side": "long",
                },
                {"event_type": "position_end", "request_id": "pos-1"},
            ],
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

    def test_open_order_dedupe_replay(self) -> None:
        result = replay(
            IBKROpenOrdersSnapshotAggregator(symbol="AAPL", request_id="open-1"),
            [
                {
                    "event_type": "open_order",
                    "request_id": "open-1",
                    "order_id": 50,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "2",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "request_id": "open-1",
                    "order_id": 50,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "2",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "request_id": "open-1",
                    "order_id": 51,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "1",
                    "status": "PreSubmitted",
                },
                {"event_type": "open_order_end", "request_id": "open-1"},
            ],
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

    def test_order_status_progression_replay(self) -> None:
        filled_event = {
            "event_type": "order_status",
            "order_id": 101,
            "status": "Filled",
        }

        result = replay(
            IBKROrderStatusAggregator(),
            [
                {"event_type": "next_valid_id", "order_id": 101},
                {"event_type": "order_status", "order_id": 101, "status": "Submitted"},
                filled_event,
            ],
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

    def test_timeout_injection_replay(self) -> None:
        timeout_event = {
            "event_type": "timeout",
            "operation": "submit_market_order",
            "message": "no terminal callback",
        }

        result = replay(
            IBKROrderStatusAggregator(),
            [
                {"event_type": "next_valid_id", "order_id": 101},
                {"event_type": "order_status", "order_id": 101, "status": "Submitted"},
                timeout_event,
            ],
        )

        self.assertEqual(
            result,
            BrokerOrderResult(
                broker_name="ibkr",
                order_id="101",
                order_status="timeout",
                broker_status="Submitted",
                is_terminal=True,
                raw_response=timeout_event,
            ),
        )

    def test_terminal_conflict_handling_replay(self) -> None:
        rejected_event = {
            "event_type": "order_status",
            "order_id": 101,
            "status": "Rejected",
        }

        result = replay(
            IBKROrderStatusAggregator(),
            [
                {"event_type": "next_valid_id", "order_id": 101},
                {"event_type": "order_status", "order_id": 101, "status": "Filled"},
                rejected_event,
            ],
        )

        self.assertEqual(
            result,
            BrokerOrderResult(
                broker_name="ibkr",
                order_id="101",
                order_status="conflicting_terminal_status",
                broker_status="Rejected",
                is_terminal=True,
                raw_response=rejected_event,
            ),
        )


if __name__ == "__main__":
    unittest.main()
