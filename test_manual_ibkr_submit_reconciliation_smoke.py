from __future__ import annotations

import unittest

from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from manual_ibkr_submit_reconciliation_smoke import (
    ReconciliationSmokeRecorder,
    RecordingReconciliationBridge,
)


class RecordingReconciliationBridgeTests(unittest.TestCase):
    def test_begin_execution_snapshot_records_generation_without_generation_kwarg(
        self,
    ) -> None:
        registry = IBKRPendingRequestRegistry()
        coordinator = IBKRRequestCoordinator(registry=registry)
        recorder = ReconciliationSmokeRecorder()
        bridge = RecordingReconciliationBridge(
            registry,
            request_coordinator=coordinator,
            recorder=recorder,
        )

        generation = bridge.begin_execution_snapshot(request_id=123, symbol="AAPL")

        self.assertEqual(generation, 123)
        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0]["event_type"], "begin_execution_snapshot")
        self.assertEqual(recorder.events[0]["request_id"], 123)
        self.assertEqual(recorder.events[0]["symbol"], "AAPL")
        self.assertEqual(recorder.events[0]["generation"], 123)


if __name__ == "__main__":
    unittest.main()
