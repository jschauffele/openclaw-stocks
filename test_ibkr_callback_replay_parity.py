from __future__ import annotations

import unittest

from broker_interface import BrokerAccountState, BrokerPositionState
from fake_ibkr_callback_aggregator import (
    aggregate_lifecycle,
    aggregate_open_buy_orders,
    aggregate_order_result,
    aggregate_position,
)
from fake_ibkr_callback_state_machine import (
    IBKRAccountSnapshotAggregator,
    IBKRLifecycleAggregator,
    IBKROpenOrdersSnapshotAggregator,
    IBKROrderStatusAggregator,
    IBKRPositionSnapshotAggregator,
    replay,
)


class FakeIBKRCallbackReplayParityTests(unittest.TestCase):
    def test_lifecycle_parity(self) -> None:
        cases = [
            (
                "success",
                [
                    {
                        "event_type": "connect_ready",
                        "message": "api ready",
                        "elapsed_ms": 12,
                    }
                ],
            ),
            (
                "timeout",
                [
                    {
                        "event_type": "timeout",
                        "operation": "connect",
                        "message": "no ready callback",
                        "elapsed_ms": 5000,
                    }
                ],
            ),
        ]

        for name, events in cases:
            with self.subTest(name=name):
                self.assertEqual(
                    aggregate_lifecycle(events),
                    replay(IBKRLifecycleAggregator(), events),
                )

    def test_legacy_position_aggregator_remains_unscoped(self) -> None:
        cases = [
            (
                "position_found",
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
            ),
            (
                "no_position",
                [
                    {"event_type": "position", "symbol": "MSFT", "qty": "2"},
                    {"event_type": "position_end"},
                ],
            ),
            (
                "missing_position_end",
                [{"event_type": "position", "symbol": "MSFT", "qty": "2"}],
            ),
        ]

        for name, events in cases:
            with self.subTest(name=name):
                self.assertIsNotNone(aggregate_position(events, symbol="AAPL"))

    def test_position_multi_strict_replay(self) -> None:
        result = replay(
            IBKRPositionSnapshotAggregator(symbol="AAPL", request_id="target"),
            [
                {
                    "event_type": "position_multi",
                    "request_id": "other",
                    "symbol": "AAPL",
                    "qty": "10",
                },
                {
                    "event_type": "position_multi",
                    "symbol": "AAPL",
                    "qty": "9",
                },
                {
                    "event_type": "position_multi",
                    "request_id": "target",
                    "symbol": "AAPL",
                    "qty": "3",
                    "side": "long",
                },
                {"event_type": "position_multi_end", "request_id": "other"},
                {"event_type": "position_multi_end"},
                {"event_type": "position_multi_end", "request_id": "target"},
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

    def test_legacy_open_order_aggregator_remains_unscoped(self) -> None:
        cases = [
            (
                "open_order_dedupe",
                [
                    {
                        "event_type": "open_order",
                        "order_id": 50,
                        "symbol": "AAPL",
                        "side": "BUY",
                        "qty": "2",
                        "status": "Submitted",
                    },
                    {
                        "event_type": "open_order",
                        "order_id": 50,
                        "symbol": "AAPL",
                        "side": "BUY",
                        "qty": "2",
                        "status": "Submitted",
                    },
                    {
                        "event_type": "open_order",
                        "order_id": 51,
                        "symbol": "AAPL",
                        "side": "BUY",
                        "qty": "1",
                        "status": "PreSubmitted",
                    },
                    {"event_type": "open_order_end"},
                ],
            ),
            (
                "missing_open_order_end",
                [
                    {
                        "event_type": "open_order",
                        "symbol": "AAPL",
                        "side": "BUY",
                        "qty": "2",
                        "status": "Submitted",
                    }
                ],
            ),
        ]

        for name, events in cases:
            with self.subTest(name=name):
                self.assertIsNotNone(aggregate_open_buy_orders(events, symbol="AAPL"))

    def test_open_order_singleton_generation_replay(self) -> None:
        result = replay(
            IBKROpenOrdersSnapshotAggregator(symbol="AAPL", generation=1),
            [
                {
                    "event_type": "open_order",
                    "generation": 2,
                    "order_id": 50,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "9",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "order_id": 51,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "8",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "generation": 1,
                    "order_id": 52,
                    "perm_id": 1001,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "2",
                    "status": "Submitted",
                },
                {
                    "event_type": "open_order",
                    "generation": 1,
                    "order_id": 53,
                    "perm_id": 1001,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "2",
                    "status": "Submitted",
                },
                {"event_type": "open_order_end", "generation": 1},
            ],
        )

        self.assertEqual(result.passed, True)
        self.assertEqual(result.open_buy_order_qty, 2)
        self.assertEqual(result.open_buy_order_count, 1)

    def test_order_result_parity(self) -> None:
        cases = [
            (
                "submitted_order",
                [
                    {"event_type": "next_valid_id", "order_id": 101},
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Submitted",
                    },
                ],
            ),
            (
                "filled_order",
                [
                    {"event_type": "next_valid_id", "order_id": 101},
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Submitted",
                    },
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Filled",
                    },
                ],
            ),
            (
                "rejected_order",
                [
                    {"event_type": "next_valid_id", "order_id": 101},
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Rejected",
                    },
                ],
            ),
            (
                "timeout_after_order_id",
                [
                    {"event_type": "next_valid_id", "order_id": 101},
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Submitted",
                    },
                    {
                        "event_type": "timeout",
                        "operation": "submit_market_order",
                        "message": "no terminal callback",
                    },
                ],
            ),
            (
                "terminal_conflict",
                [
                    {"event_type": "next_valid_id", "order_id": 101},
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Filled",
                    },
                    {
                        "event_type": "order_status",
                        "order_id": 101,
                        "status": "Rejected",
                    },
                ],
            ),
        ]

        for name, events in cases:
            with self.subTest(name=name):
                self.assertEqual(
                    aggregate_order_result(events),
                    replay(IBKROrderStatusAggregator(), events),
                )


class FakeIBKRCallbackRequestIdFilteringTests(unittest.TestCase):
    def test_position_ignores_wrong_request_id(self) -> None:
        result = replay(
            IBKRPositionSnapshotAggregator(symbol="AAPL", request_id="target"),
            [
                {
                    "event_type": "position_multi",
                    "request_id": "other",
                    "symbol": "AAPL",
                    "qty": "10",
                },
                {"event_type": "position_multi_end", "request_id": "target"},
            ],
        )

        self.assertEqual(result.found, False)
        self.assertEqual(result.qty, 0)
        self.assertEqual(result.reason, "no_position")

    def test_open_orders_ignore_wrong_request_id(self) -> None:
        result = replay(
            IBKROpenOrdersSnapshotAggregator(symbol="AAPL", generation=1),
            [
                {
                    "event_type": "open_order",
                    "generation": 2,
                    "order_id": 50,
                    "symbol": "AAPL",
                    "side": "BUY",
                    "qty": "10",
                    "status": "Submitted",
                },
                {"event_type": "open_order_end", "generation": 1},
            ],
        )

        self.assertEqual(result.passed, True)
        self.assertEqual(result.open_buy_order_qty, 0)
        self.assertEqual(result.open_buy_order_count, 0)
        self.assertEqual(result.reason, "open_buy_orders_loaded")

    def test_account_ignores_wrong_request_id(self) -> None:
        account_event = {
            "event_type": "account_summary",
            "request_id": "target",
            "buying_power": "123.45",
        }
        result = replay(
            IBKRAccountSnapshotAggregator(request_id="target"),
            [
                {
                    "event_type": "account_summary",
                    "request_id": "other",
                    "buying_power": "999.99",
                },
                {
                    "event_type": "account_summary",
                    "buying_power": "888.88",
                },
                account_event,
                {"event_type": "account_summary_end", "request_id": "other"},
                {"event_type": "account_summary_end"},
                {"event_type": "account_summary_end", "request_id": "target"},
            ],
        )

        self.assertEqual(
            result,
            BrokerAccountState(
                broker_name="ibkr",
                buying_power=123.45,
                raw_account=account_event,
            ),
        )


if __name__ == "__main__":
    unittest.main()
