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
    BrokerSubmitReconciliationResult,
    BrokerReconciliationResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from manual_ibkr_submit_reconciliation_smoke import (
    ReconciliationSmokeRecorder,
    RecordingReconciliationBridge,
    SmokeRunLock,
    SmokeSafetyRefusal,
    SMOKE_DISCONNECT_TIMEOUT,
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
                "final_broker_state": "open_orders",
                "disconnect_joined": True,
                "disconnect_passed": True,
            },
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

    def test_limit_mode_without_limit_price_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                order_type="limit",
                limit_price=None,
            )

            self.assertIsNone(result)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)

    def test_limit_mode_with_non_positive_limit_price_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                order_type="limit",
                limit_price=0.0,
            )

            self.assertIsNone(result)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)

    def test_limit_mode_with_negative_qty_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                order_type="limit",
                limit_price=100.0,
                qty=-1,
            )

            self.assertIsNone(result)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)

    def test_market_mode_with_short_timeout_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                order_type="market",
                timeout=0.25,
            )

            self.assertIsNone(result)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)

    def test_clean_limit_mode_builds_limit_order_without_market_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter, native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders(), open_orders()],
                position_snapshots=[flat_position(), flat_position()],
                order_type="limit",
                limit_price=100.25,
            )

            self.assertEqual(result.order_status, "submitted")
            self.assertFalse(adapter.build_market_order_called)
            self.assertTrue(adapter.submit_market_order_called)
            self.assertEqual(native_api.order_count, 1)
            submitted_order = adapter.submitted_order
            self.assertEqual(submitted_order.order.orderType, "LMT")
            self.assertEqual(submitted_order.order.lmtPrice, 100.25)
            self.assertEqual(submitted_order.order.totalQuantity, 1)
            self.assertEqual(submitted_order.order.action, "BUY")
            self.assertEqual(submitted_order.order.tif, "DAY")
            self.assertFalse(submitted_order.order.eTradeOnly)
            self.assertFalse(submitted_order.order.firmQuoteOnly)

    def test_unsafe_broker_state_refuses_before_limit_order_construction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result, adapter, native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders(qty=1, count=1)],
                position_snapshots=[flat_position()],
                order_type="limit",
                limit_price=100.25,
            )

            self.assertIsNone(result)
            self.assertEqual(native_api.order_count, 0)
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)

    def test_final_open_order_state_persists_and_blocks_next_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"

            result, _adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders(), open_orders(qty=1, count=1)],
                position_snapshots=[flat_position(), flat_position()],
                order_type="limit",
                limit_price=100.25,
            )

            self.assertEqual(result.order_status, "submitted")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["final_broker_state"], "open_orders")
            with self.assertRaisesRegex(SmokeSafetyRefusal, "final_broker_state"):
                _refuse_if_last_run_requires_cleanup(state_path)

    def test_short_submit_timeout_uses_disconnect_timeout_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            result, adapter, _native_api, coordinator = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                timeout=0.25,
                preflight_only=True,
                include_coordinator=True,
            )

            self.assertEqual(result.state, "clean")
            self.assertFalse(adapter.submit_market_order_called)
            self.assertEqual(coordinator.disconnect_timeouts, [SMOKE_DISCONNECT_TIMEOUT])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["submit_timeout"], 0.25)
            self.assertEqual(state["disconnect_timeout"], SMOKE_DISCONNECT_TIMEOUT)

    def test_reconciliation_intent_submitted_at_is_populated_and_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            result, _adapter, _native_api, workflow = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders(), open_orders()],
                position_snapshots=[flat_position(), flat_position()],
                order_status="reconciliation_required",
                order_type="limit",
                limit_price=100.25,
                submitted_at="20260512 10:01:02",
                include_workflow=True,
            )

            self.assertEqual(result.reconciliation_status, "accepted_unfilled")
            intent = workflow.calls[0]["intent"]
            self.assertEqual(intent.submitted_at, "20260512 10:01:02")
            self.assertRegex(intent.submitted_at, r"^\d{8} \d{2}:\d{2}:\d{2}$")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["submitted_at"], "20260512 10:01:02")
            self.assertRegex(state["submitted_at"], r"^\d{8} \d{2}:\d{2}:\d{2}$")


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
    open_order_snapshots: list[BrokerOpenOrderState] = []
    position_snapshots: list[BrokerPositionState] = []
    order_status = "submitted"

    def __init__(self, **_kwargs) -> None:
        if not self.open_order_snapshots or not self.position_snapshots:
            raise AssertionError("fake broker snapshots were not configured")
        super().__init__(
            open_order_snapshot=self.open_order_snapshots[0],
            position_snapshot=self.position_snapshots[0],
        )
        self.build_market_order_called = False
        self.submit_market_order_called = False
        self.submitted_order = None
        self.instances.append(self)

    def get_open_buy_order_qty(
        self,
        symbol: str,
        timeout_seconds: float | None = None,
    ) -> BrokerOpenOrderState:
        self.open_order_calls.append((symbol, timeout_seconds))
        if len(self.open_order_snapshots) > 1:
            return self.open_order_snapshots.pop(0)
        return self.open_order_snapshots[0]

    def get_existing_position(
        self,
        symbol: str,
        timeout_seconds: float | None = None,
    ) -> BrokerPositionState:
        self.position_calls.append((symbol, timeout_seconds))
        if len(self.position_snapshots) > 1:
            return self.position_snapshots.pop(0)
        return self.position_snapshots[0]

    def build_market_order(self, symbol: str, qty: int):
        self.build_market_order_called = True
        return object()

    def submit_market_order(self, order, timeout_seconds: float | None = None):
        self.submit_market_order_called = True
        self.submitted_order = order
        return BrokerOrderResult(
            broker_name="ibkr",
            order_id="123",
            order_status=self.order_status,
            broker_status="PreSubmitted",
            is_terminal=False,
        )


class FakeNativeApi:
    def __init__(self) -> None:
        self.order_count = 0

    class e_wrapper:
        pass

    def e_client(self, wrapper):
        return FakeNativeClient()

    def contract(self):
        return FakeNativeContract()

    def order(self):
        self.order_count += 1
        return FakeNativeOrder()


class FakeNativeContract:
    pass


class FakeNativeOrder:
    def __init__(self) -> None:
        self.tif = None
        self.eTradeOnly = None
        self.firmQuoteOnly = None


class FakeNativeClient:
    pass


class FakeCoordinator:
    instances: list["FakeCoordinator"] = []

    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self.client = None
        self.completed_by = "callback"
        self.connect_state = "connected"
        self.shutdown_state = "complete"
        self.thread_owner = FakeThreadOwner()
        self.disconnect_timeouts: list[float] = []
        self.instances.append(self)

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
        self.disconnect_timeouts.append(timeout)
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


class FakeReconciliationWorkflow:
    instances: list["FakeReconciliationWorkflow"] = []

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.instances.append(self)

    def reconcile_if_required(
        self,
        *,
        broker,
        submit_result,
        intent,
        timeout_seconds: float | None = None,
    ) -> BrokerSubmitReconciliationResult:
        self.calls.append(
            {
                "broker": broker,
                "submit_result": submit_result,
                "intent": intent,
                "timeout_seconds": timeout_seconds,
            }
        )
        reconciliation = BrokerReconciliationResult(
            broker_name="ibkr",
            status="accepted_unfilled",
            order_id=intent.order_id,
            perm_id=intent.perm_id,
            symbol=intent.symbol,
            side=intent.side,
            intended_qty=intent.qty,
            filled_qty=0.0,
            working_qty=1.0,
            avg_fill_price=None,
            matched_exec_ids=(),
            reason="open_order_snapshot_shows_working_order",
        )
        return BrokerSubmitReconciliationResult(
            broker_name="ibkr",
            submit_state="submit_uncertain_reconciliation_required",
            reconciliation_status="accepted_unfilled",
            terminal_for_run=True,
            manual_review_required=False,
            order_id=intent.order_id,
            perm_id=intent.perm_id,
            filled_qty=0.0,
            working_qty=1.0,
            reason="open_order_snapshot_shows_working_order",
            ambiguous=False,
            submit_result=submit_result,
            reconciliation_result=reconciliation,
        )


def run_fake_preflight_only(
    *,
    lock_path: Path,
    state_path: Path,
    open_order_snapshot: BrokerOpenOrderState,
    position_snapshot: BrokerPositionState,
):
    result, adapter, _native_api = run_fake_smoke(
        lock_path=lock_path,
        state_path=state_path,
        open_order_snapshots=[open_order_snapshot],
        position_snapshots=[position_snapshot],
        timeout=0.25,
        preflight_only=True,
    )
    return result, adapter


def run_fake_smoke(
    *,
    lock_path: Path,
    state_path: Path,
    open_order_snapshots: list[BrokerOpenOrderState],
    position_snapshots: list[BrokerPositionState],
    timeout: float = 5.0,
    qty: int = 1,
    preflight_only: bool = False,
    order_type: str = "market",
    limit_price: float | None = None,
    order_status: str = "submitted",
    submitted_at: str = "20260512 10:01:02",
    include_coordinator: bool = False,
    include_workflow: bool = False,
):
    FakeIBKRBrokerAdapter.instances = []
    FakeIBKRBrokerAdapter.open_order_snapshots = list(open_order_snapshots)
    FakeIBKRBrokerAdapter.position_snapshots = list(position_snapshots)
    FakeIBKRBrokerAdapter.order_status = order_status
    FakeCoordinator.instances = []
    FakeReconciliationWorkflow.instances = []
    native_api = FakeNativeApi()
    with (
        patch(
            "manual_ibkr_submit_reconciliation_smoke.load_ibkr_native_api",
            return_value=native_api,
        ),
        patch(
            "manual_ibkr_submit_reconciliation_smoke.IBKRRuntimeArbitrationCoordinator",
            FakeCoordinator,
        ),
        patch(
            "manual_ibkr_submit_reconciliation_smoke.IBKRBrokerAdapter",
            FakeIBKRBrokerAdapter,
        ),
        patch(
            "manual_ibkr_submit_reconciliation_smoke.IBKRSubmitReconciliationWorkflow",
            FakeReconciliationWorkflow,
        ),
        patch(
            "manual_ibkr_submit_reconciliation_smoke._ibkr_execution_filter_time_now",
            return_value=submitted_at,
        ),
    ):
        with redirect_stdout(io.StringIO()):
            result = run_localhost_submit_reconciliation_smoke(
                timeout=timeout,
                symbol="AAPL",
                qty=qty,
                lock_path=lock_path,
                last_state_path=state_path,
                preflight_only=preflight_only,
                order_type=order_type,
                limit_price=limit_price,
            )
    adapter = FakeIBKRBrokerAdapter.instances[-1]
    workflow = (
        FakeReconciliationWorkflow.instances[-1]
        if FakeReconciliationWorkflow.instances
        else None
    )
    if include_workflow:
        return result, adapter, native_api, workflow
    if include_coordinator:
        return result, adapter, native_api, FakeCoordinator.instances[-1]
    return result, adapter, native_api


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
