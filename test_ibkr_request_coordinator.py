from __future__ import annotations

import threading
import unittest
from types import SimpleNamespace

from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator


class RecordingAggregator:
    def __init__(self, *, label: str = "request") -> None:
        self.label = label
        self.events: list[dict[str, object]] = []

    def on_event(self, event: dict[str, object]) -> None:
        self.events.append(event)

    def result(self):
        return SimpleNamespace(
            label=self.label,
            event_count=len(self.events),
            events=tuple(self.events),
        )


class CountingRegistry(IBKRPendingRequestRegistry):
    def __init__(self) -> None:
        super().__init__()
        self.pop_counts: dict[str, int] = {}

    def pop_request(self, request_id: object):
        request_key = str(request_id)
        self.pop_counts[request_key] = self.pop_counts.get(request_key, 0) + 1
        return super().pop_request(request_id)


class IBKRRequestCoordinatorTests(unittest.TestCase):
    def test_callback_beats_timeout(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())

        self.assertTrue(
            coordinator.route_callback(
                "req-1",
                {"event_type": "value", "request_id": "req-1"},
            )
        )
        self.assertTrue(coordinator.complete_from_callback("req-1"))
        self.assertFalse(coordinator.timeout_request("req-1"))

        result = coordinator.result("req-1")
        self.assertEqual(result.event_count, 1)
        self.assertEqual(coordinator.completed_by("req-1"), "callback")
        self.assertFalse(coordinator.has_pending_request("req-1"))

    def test_timeout_beats_callback(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())

        self.assertTrue(coordinator.timeout_request("req-1"))
        self.assertFalse(
            coordinator.route_callback(
                "req-1",
                {"event_type": "late", "request_id": "req-1"},
            )
        )
        self.assertFalse(coordinator.complete_from_callback("req-1"))

        result = coordinator.result("req-1")
        self.assertEqual(result.event_count, 0)
        self.assertEqual(coordinator.completed_by("req-1"), "timeout")
        self.assertFalse(coordinator.has_pending_request("req-1"))

    def test_duplicate_completion_ignored(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())

        self.assertTrue(coordinator.complete_from_callback("req-1"))
        completed_result = coordinator.result("req-1")

        self.assertFalse(coordinator.complete_from_callback("req-1"))
        self.assertFalse(coordinator.timeout_request("req-1"))
        self.assertIs(coordinator.result("req-1"), completed_result)
        self.assertEqual(coordinator.notification_count, 1)

    def test_late_callback_after_timeout_ignored(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())
        self.assertTrue(coordinator.timeout_request("req-1"))
        completed_result = coordinator.result("req-1")

        self.assertFalse(
            coordinator.route_callback(
                "req-1",
                {"event_type": "late", "request_id": "req-1"},
            )
        )

        self.assertIs(coordinator.result("req-1"), completed_result)
        self.assertEqual(completed_result.event_count, 0)

    def test_callback_and_timeout_race_has_single_terminal_winner(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())
        barrier = threading.Barrier(3)
        outcomes: list[tuple[str, bool]] = []

        def callback() -> None:
            barrier.wait(timeout=1.0)
            coordinator.route_callback(
                "req-1",
                {"event_type": "value", "request_id": "req-1"},
            )
            outcomes.append(("callback", coordinator.complete_from_callback("req-1")))

        def timeout() -> None:
            barrier.wait(timeout=1.0)
            outcomes.append(("timeout", coordinator.timeout_request("req-1")))

        threads = [threading.Thread(target=callback), threading.Thread(target=timeout)]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=1.0)
        for thread in threads:
            thread.join(timeout=1.0)

        self.assertEqual(len(outcomes), 2)
        self.assertEqual(sum(1 for _, won in outcomes if won), 1)
        self.assertIn(coordinator.completed_by("req-1"), {"callback", "timeout"})
        self.assertFalse(coordinator.has_pending_request("req-1"))

    def test_duplicate_callback_race_has_single_terminal_winner(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())
        barrier = threading.Barrier(3)
        outcomes: list[tuple[str, bool]] = []

        def complete(name: str) -> None:
            barrier.wait(timeout=1.0)
            outcomes.append((name, coordinator.complete_from_callback("req-1")))

        threads = [
            threading.Thread(target=complete, args=("a",)),
            threading.Thread(target=complete, args=("b",)),
        ]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=1.0)
        for thread in threads:
            thread.join(timeout=1.0)

        self.assertEqual(len(outcomes), 2)
        self.assertEqual(sum(1 for _, won in outcomes if won), 1)
        self.assertEqual(coordinator.completed_by("req-1"), "callback")
        self.assertEqual(coordinator.notification_count, 1)

    def test_request_popped_exactly_once(self) -> None:
        registry = CountingRegistry()
        coordinator = IBKRRequestCoordinator(registry=registry)
        coordinator.register_request("req-1", RecordingAggregator())

        self.assertTrue(coordinator.timeout_request("req-1"))
        self.assertFalse(coordinator.timeout_request("req-1"))
        self.assertFalse(coordinator.complete_from_callback("req-1"))

        self.assertEqual(registry.pop_counts, {"req-1": 1})

    def test_result_retained_after_request_is_popped(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator(label="snapshot"))
        coordinator.route_callback(
            "req-1",
            {"event_type": "value", "request_id": "req-1"},
        )

        self.assertTrue(coordinator.complete_from_callback("req-1"))

        result = coordinator.result("req-1")
        self.assertEqual(result.label, "snapshot")
        self.assertEqual(result.event_count, 1)
        self.assertFalse(coordinator.has_pending_request("req-1"))

    def test_no_callback_leakage_across_request_ids(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("target", RecordingAggregator(label="target"))
        coordinator.register_request("other", RecordingAggregator(label="other"))

        self.assertTrue(
            coordinator.route_callback(
                "other",
                {"event_type": "value", "request_id": "other"},
            )
        )
        self.assertTrue(coordinator.complete_from_callback("target"))
        self.assertTrue(coordinator.complete_from_callback("other"))

        self.assertEqual(coordinator.result("target").event_count, 0)
        self.assertEqual(coordinator.result("other").event_count, 1)
        self.assertEqual(coordinator.completed_by("target"), "callback")
        self.assertEqual(coordinator.completed_by("other"), "callback")

    def test_wait_for_completion_observes_callback_completion(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())
        waiter_result: list[bool] = []
        waiter_ready = threading.Event()

        def waiter() -> None:
            waiter_ready.set()
            waiter_result.append(
                coordinator.wait_for_completion("req-1", timeout=1.0)
            )

        thread = threading.Thread(target=waiter)
        thread.start()
        self.assertTrue(waiter_ready.wait(timeout=1.0))
        self.assertTrue(coordinator.complete_from_callback("req-1"))
        thread.join(timeout=1.0)

        self.assertEqual(waiter_result, [True])

    def test_wait_for_completion_times_out_without_terminal_result(self) -> None:
        coordinator = IBKRRequestCoordinator()
        coordinator.register_request("req-1", RecordingAggregator())

        self.assertFalse(coordinator.wait_for_completion("req-1", timeout=0.01))
        self.assertIsNone(coordinator.result("req-1"))
        self.assertTrue(coordinator.has_pending_request("req-1"))


if __name__ == "__main__":
    unittest.main()
