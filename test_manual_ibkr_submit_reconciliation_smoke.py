from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from broker_interface import (
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerPositionState,
)
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from manual_ibkr_submit_reconciliation_smoke import (
    ReconciliationSmokeRecorder,
    RecordingReconciliationBridge,
    SmokeRunLock,
    SmokeSafetyRefusal,
    _refuse_if_last_run_requires_cleanup,
    classify_smoke_broker_state,
    query_smoke_broker_state,
    run_localhost_submit_reconciliation_smoke,
    write_smoke_last_state,
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


class SmokeSafetyControlTests(unittest.TestCase):
    def test_refuse_when_open_orders_exist(self) -> None:
        state = classify_smoke_broker_state(
            open_order_snapshot=open_orders(qty=1, count=1),
            position_snapshot=flat_position(),
        )

        self.assertEqual(state.state, "open_orders")
        self.assertEqual(state.reason, "open_orders_exist")

    def test_refuse_when_non_flat_position_exists(self) -> None:
        state = classify_smoke_broker_state(
            open_order_snapshot=open_orders(),
            position_snapshot=position(qty=-3, found=True),
        )

        self.assertEqual(state.state, "non_flat_position")
        self.assertEqual(state.reason, "position_is_non_flat")

    def test_refuse_when_lock_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "ibkr_smoke.lock"
            first_lock = SmokeRunLock(lock_path)
            second_lock = SmokeRunLock(lock_path)

            first_lock.acquire()
            try:
                with self.assertRaisesRegex(SmokeSafetyRefusal, "already in flight"):
                    second_lock.acquire()
            finally:
                first_lock.release()

    def test_refuse_when_last_run_state_requires_cleanup(self) -> None:
        unsafe_states = (
            {"manual_review_required": True},
            {"reconciliation_status": "unresolved"},
            {"reconciliation_status": "partially_filled_unresolved"},
            {"disconnect_joined": False, "disconnect_passed": False},
            {
                "submit_attempted": True,
                "final_broker_state": "unknown",
                "disconnect_joined": True,
                "disconnect_passed": True,
            },
        )

        for unsafe_state in unsafe_states:
            with self.subTest(unsafe_state=unsafe_state):
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
                    write_smoke_last_state(state_path, unsafe_state)

                    with self.assertRaises(SmokeSafetyRefusal):
                        _refuse_if_last_run_requires_cleanup(state_path)

    def test_lock_releases_on_normal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "ibkr_smoke.lock"
            lock = SmokeRunLock(lock_path)

            lock.acquire()
            lock.release()

            self.assertFalse(lock_path.exists())
            SmokeRunLock(lock_path).acquire()

    def test_clean_broker_state_allows_submit_path_to_continue(self) -> None:
        adapter = FakeSafetyAdapter(
            open_order_snapshot=open_orders(),
            position_snapshot=flat_position(),
        )

        state = query_smoke_broker_state(adapter, symbol="AAPL", timeout=2.0)

        self.assertEqual(state.state, "clean")
        self.assertEqual(state.reason, "no_open_orders_or_position")
        self.assertEqual(adapter.open_order_calls, [("AAPL", 2.0)])
        self.assertEqual(adapter.position_calls, [("AAPL", 2.0)])

    def test_preflight_only_clean_state_queries_state_and_skips_submit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "ibkr_smoke.lock"
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"

            result, adapter = run_fake_preflight_only(
                lock_path=lock_path,
                state_path=state_path,
                open_order_snapshot=open_orders(),
                position_snapshot=flat_position(),
            )

            self.assertEqual(result.state, "clean")
            self.assertEqual(adapter.open_order_calls, [("AAPL", 2.0)])
            self.assertEqual(adapter.position_calls, [("AAPL", 2.0)])
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)
            self.assertFalse(lock_path.exists())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertFalse(state["submit_attempted"])
            self.assertEqual(state["final_broker_state"], "clean")

    def test_preflight_only_refuses_on_open_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter = run_fake_preflight_only(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshot=open_orders(qty=1, count=1),
                position_snapshot=flat_position(),
            )

            self.assertIsNone(result)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)

    def test_preflight_only_refuses_on_non_flat_position(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter = run_fake_preflight_only(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshot=open_orders(),
                position_snapshot=position(qty=2, found=True),
            )

            self.assertIsNone(result)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)


class FakeSafetyAdapter:
    def __init__(
        self,
        *,
        open_order_snapshot: BrokerOpenOrderState,
        position_snapshot: BrokerPositionState,
    ) -> None:
        self.open_order_snapshot = open_order_snapshot
        self.position_snapshot = position_snapshot
        self.open_order_calls: list[tuple[str, float | None]] = []
        self.position_calls: list[tuple[str, float | None]] = []

    def get_open_buy_order_qty(
        self,
        symbol: str,
        timeout_seconds: float | None = None,
    ) -> BrokerOpenOrderState:
        self.open_order_calls.append((symbol, timeout_seconds))
        return self.open_order_snapshot

    def get_existing_position(
        self,
        symbol: str,
        timeout_seconds: float | None = None,
    ) -> BrokerPositionState:
        self.position_calls.append((symbol, timeout_seconds))
        return self.position_snapshot


class FakeIBKRBrokerAdapter(FakeSafetyAdapter):
    instances: list["FakeIBKRBrokerAdapter"] = []
    open_order_snapshot: BrokerOpenOrderState | None = None
    position_snapshot: BrokerPositionState | None = None

    def __init__(self, **_kwargs) -> None:
        if self.open_order_snapshot is None or self.position_snapshot is None:
            raise AssertionError("fake broker snapshots were not configured")
        super().__init__(
            open_order_snapshot=self.open_order_snapshot,
            position_snapshot=self.position_snapshot,
        )
        self.build_market_order_called = False
        self.submit_market_order_called = False
        self.instances.append(self)

    def build_market_order(self, symbol: str, qty: int):
        self.build_market_order_called = True
        raise AssertionError("preflight-only must not build an order")

    def submit_market_order(self, order, timeout_seconds: float | None = None):
        self.submit_market_order_called = True
        raise AssertionError("preflight-only must not submit an order")


class FakeNativeApi:
    class e_wrapper:
        pass

    def e_client(self, wrapper):
        return FakeNativeClient()


class FakeNativeClient:
    pass


class FakeCoordinator:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self.client = None
        self.completed_by = "callback"
        self.connect_state = "connected"
        self.shutdown_state = "complete"
        self.thread_owner = FakeThreadOwner()

    def connect(self, *, host: str, port: int, client_id: int, timeout: float) -> None:
        return None

    def wait_for_completion(self, timeout: float) -> bool:
        return True

    def timeout_connect(self, *, message: str, elapsed_ms: int) -> None:
        raise AssertionError("fake connect should not time out")

    def connect_result(self) -> BrokerLifecycleResult:
        return BrokerLifecycleResult(
            broker_name="ibkr",
            operation="connect",
            passed=True,
            reason="connect_ready",
            message="next_valid_id",
            connected=True,
            retryable=False,
        )

    def disconnect(self, *, timeout: float) -> bool:
        self.connect_state = "disconnected"
        return True

    def disconnect_result(self) -> BrokerLifecycleResult:
        return BrokerLifecycleResult(
            broker_name="ibkr",
            operation="disconnect",
            passed=True,
            reason="disconnect_complete",
            message="IBKR runtime disconnected",
            connected=False,
            retryable=False,
        )


class FakeThreadOwner:
    thread_state = "running"


def run_fake_preflight_only(
    *,
    lock_path: Path,
    state_path: Path,
    open_order_snapshot: BrokerOpenOrderState,
    position_snapshot: BrokerPositionState,
):
    FakeIBKRBrokerAdapter.instances = []
    FakeIBKRBrokerAdapter.open_order_snapshot = open_order_snapshot
    FakeIBKRBrokerAdapter.position_snapshot = position_snapshot
    with (
        patch(
            "manual_ibkr_submit_reconciliation_smoke.load_ibkr_native_api",
            return_value=FakeNativeApi(),
        ),
        patch(
            "manual_ibkr_submit_reconciliation_smoke.IBKRRuntimeArbitrationCoordinator",
            FakeCoordinator,
        ),
        patch(
            "manual_ibkr_submit_reconciliation_smoke.IBKRBrokerAdapter",
            FakeIBKRBrokerAdapter,
        ),
    ):
        with redirect_stdout(io.StringIO()):
            result = run_localhost_submit_reconciliation_smoke(
                timeout=0.25,
                symbol="AAPL",
                qty=1,
                lock_path=lock_path,
                last_state_path=state_path,
                preflight_only=True,
            )
    return result, FakeIBKRBrokerAdapter.instances[-1]


def open_orders(qty: int = 0, count: int = 0) -> BrokerOpenOrderState:
    return BrokerOpenOrderState(
        broker_name="ibkr",
        passed=True,
        open_buy_order_qty=qty,
        open_buy_order_count=count,
        reason="open_buy_orders_loaded",
    )


def flat_position() -> BrokerPositionState:
    return position(qty=0, found=False)


def position(*, qty: int, found: bool) -> BrokerPositionState:
    return BrokerPositionState(
        broker_name="ibkr",
        found=found,
        qty=qty,
        raw_qty=str(qty),
        side="long" if qty >= 0 else "short",
        reason="position_loaded" if found else "no_position",
    )


if __name__ == "__main__":
    unittest.main()
