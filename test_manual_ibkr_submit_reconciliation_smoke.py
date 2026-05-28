from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from broker_interface import (
    BrokerExecutionSnapshotState,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
    BrokerReconciliationResult,
    BrokerSubmitReconciliationResult,
)
from broker_factory import SUPPORTED_BROKERS
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from manual_ibkr_submit_reconciliation_smoke import (
    ReconciliationSmokeRecorder,
    RecordingReconciliationBridge,
    RecordingReconciliationClient,
    SmokeRunLock,
    SmokeSafetyRefusal,
    SMOKE_DISCONNECT_TIMEOUT,
    _ibkr_execution_filter_time_now,
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

    def test_callback_evidence_is_preserved_for_submit_and_snapshots(self) -> None:
        registry = IBKRPendingRequestRegistry()
        coordinator = IBKRRequestCoordinator(registry=registry)
        recorder = ReconciliationSmokeRecorder()
        bridge = RecordingReconciliationBridge(
            registry,
            request_coordinator=coordinator,
            recorder=recorder,
        )

        bridge.begin_order_submission(order_id=101)
        bridge.order_status(order_id=101, status="Submitted")
        bridge.begin_open_orders_snapshot(symbol="AAPL")
        bridge.open_order(
            order_id=201,
            symbol="AAPL",
            side="BUY",
            qty=1,
            status="Submitted",
        )
        bridge.open_order_end()
        bridge.begin_position_snapshot(request_id=301, symbol="AAPL")
        bridge.position_multi(request_id=301, symbol="AAPL", qty=0)
        bridge.position_multi_end(request_id=301)
        bridge.begin_execution_snapshot(request_id=401, symbol="AAPL")
        bridge.exec_details(
            request_id=401,
            order_id=101,
            symbol="AAPL",
            side="BOT",
            shares=1,
            exec_id="exec-1",
        )
        bridge.exec_details_end(request_id=401)

        event_types = [event["event_type"] for event in recorder.events]
        self.assertEqual(
            event_types,
            [
                "begin_order_submission",
                "orderStatus",
                "begin_open_orders_snapshot",
                "openOrder",
                "openOrderEnd",
                "begin_position_snapshot",
                "positionMulti",
                "positionMultiEnd",
                "begin_execution_snapshot",
                "execDetails",
                "execDetailsEnd",
            ],
        )
        self.assertEqual(recorder.events[0]["order_id"], 101)
        self.assertTrue(recorder.events[0]["pending"])
        self.assertEqual(
            recorder.events[1]["route_method"],
            "order_status_submit_lifecycle",
        )
        self.assertEqual(recorder.events[3]["symbol"], "AAPL")
        self.assertTrue(recorder.events[3]["routed"])
        self.assertEqual(recorder.events[6]["qty"], 0)
        self.assertTrue(recorder.events[7]["routed"])
        self.assertEqual(recorder.events[9]["exec_id"], "exec-1")
        self.assertTrue(recorder.events[10]["routed"])


class RecordingReconciliationClientTests(unittest.TestCase):
    def test_request_and_place_order_evidence_is_preserved(self) -> None:
        registry = IBKRPendingRequestRegistry()
        coordinator = IBKRRequestCoordinator(registry=registry)
        recorder = ReconciliationSmokeRecorder()
        native_client = FakeRecordingNativeClient()
        client = RecordingReconciliationClient(
            client=native_client,
            request_coordinator=coordinator,
            recorder=recorder,
        )

        coordinator.register_request(101, FakeAggregator("pending-order"))
        client.placeOrder(
            101,
            SimpleNamespace(symbol="AAPL"),
            SimpleNamespace(action="BUY", totalQuantity=1, orderType="LMT"),
        )
        client.reqExecutions(
            401,
            SimpleNamespace(symbol="AAPL", side="BOT", time="20260512-10:01:02"),
        )
        client.reqAllOpenOrders()
        client.reqPositionsMulti(301, "", "")
        client.cancelPositionsMulti(301)

        self.assertEqual(
            [event["event_type"] for event in recorder.events],
            [
                "placeOrder",
                "reqExecutions",
                "reqAllOpenOrders",
                "reqPositionsMulti",
                "cancelPositionsMulti",
            ],
        )
        self.assertEqual(recorder.events[0]["order_id"], 101)
        self.assertEqual(recorder.events[0]["symbol"], "AAPL")
        self.assertEqual(recorder.events[0]["order_type"], "LMT")
        self.assertTrue(recorder.events[0]["pending_before_place_order"])
        self.assertEqual(recorder.events[1]["time"], "20260512-10:01:02")
        self.assertEqual(recorder.events[3]["request_id"], 301)
        self.assertEqual(native_client.calls, [
            "placeOrder",
            "reqExecutions",
            "reqAllOpenOrders",
            "reqPositionsMulti",
            "cancelPositionsMulti",
        ])


class SmokeSafetyControlTests(unittest.TestCase):
    def test_no_production_routing_is_enabled(self) -> None:
        main_source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
        broker_factory_source = Path(__file__).with_name("broker_factory.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("ibkr", SUPPORTED_BROKERS)
        self.assertNotIn("manual_ibkr_submit_reconciliation_smoke", main_source)
        self.assertNotIn("run_localhost_submit_reconciliation_smoke", main_source)
        self.assertIn('SUPPORTED_BROKERS = {"alpaca"}', broker_factory_source)

    def test_submit_reconciliation_smoke_does_not_import_production_paths(self) -> None:
        source = Path(__file__).with_name(
            "manual_ibkr_submit_reconciliation_smoke.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("import main", source)
        self.assertNotIn("from main", source)
        self.assertNotIn("broker_factory", source)
        self.assertNotIn("market_data", source)
        self.assertNotIn("strategy_engine", source)
        self.assertNotIn("risk_engine", source)
        self.assertNotIn("observation_logger", source)
        self.assertNotIn("state_manager", source)

    def test_manual_harness_has_no_order_remediation_controls(self) -> None:
        source = Path(__file__).with_name(
            "manual_ibkr_submit_reconciliation_smoke.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("cancelOrder", source)
        self.assertNotIn("globalCancel", source)
        self.assertNotIn("flatten", source.lower())
        self.assertNotIn("resubmit", source.lower())
        self.assertNotIn("retry_submit", source.lower())
        self.assertNotIn("remediate", source.lower())

    def test_ibkr_execution_filter_time_now_uses_utc_timezone_format(self) -> None:
        self.assertRegex(
            _ibkr_execution_filter_time_now(),
            r"^\d{8}-\d{2}:\d{2}:\d{2}$",
        )

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

    def test_default_run_refuses_unsafe_last_state_before_submit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            write_smoke_last_state(
                state_path,
                {
                    "final_broker_state": "open_orders",
                    "disconnect_joined": True,
                    "disconnect_passed": True,
                },
            )

            with self.assertRaises(SmokeSafetyRefusal):
                run_fake_smoke(
                    lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                    state_path=state_path,
                    open_order_snapshots=[open_orders()],
                    position_snapshots=[flat_position()],
                )

            self.assertEqual(FakeIBKRBrokerAdapter.instances, [])
            self.assertEqual(FakeReconciliationWorkflow.instances, [])

    def test_cleanup_stale_state_only_missing_state_exits_without_native_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"

            with patch(
                "manual_ibkr_submit_reconciliation_smoke.load_ibkr_native_api",
                side_effect=AssertionError("cleanup without state must not connect"),
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    result = run_localhost_submit_reconciliation_smoke(
                        timeout=0.25,
                        lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                        last_state_path=state_path,
                        cleanup_stale_state_only=True,
                    )

            self.assertEqual(result["cleanup_result"], "CLEANUP_NOT_NEEDED")
            self.assertIn("cleanup_result=CLEANUP_NOT_NEEDED", stdout.getvalue())
            self.assertFalse(state_path.exists())

    def test_cleanup_stale_state_only_safe_state_exits_without_native_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            safe_state = {
                "submit_attempted": False,
                "final_broker_state": "clean",
                "disconnect_joined": True,
                "disconnect_passed": True,
            }
            write_smoke_last_state(state_path, safe_state)

            with patch(
                "manual_ibkr_submit_reconciliation_smoke.load_ibkr_native_api",
                side_effect=AssertionError("cleanup safe state must not connect"),
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    result = run_localhost_submit_reconciliation_smoke(
                        timeout=0.25,
                        lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                        last_state_path=state_path,
                        cleanup_stale_state_only=True,
                    )

            self.assertEqual(
                result["cleanup_result"],
                "CLEANUP_NOT_NEEDED_SAFE_STATE",
            )
            self.assertIn(
                "cleanup_result=CLEANUP_NOT_NEEDED_SAFE_STATE",
                stdout.getvalue(),
            )
            self.assertEqual(json.loads(state_path.read_text()), safe_state)

    def test_cleanup_stale_state_only_archives_unsafe_state_when_broker_clean(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            stale_state = {
                "symbol": "AAPL",
                "qty": 1,
                "order_ref": "OPENCLAW_SMOKE_MARKET_20260521125109",
                "order_id": 9,
                "order_status": "submitted",
                "final_broker_state": "open_orders",
                "final_broker_state_reason": "open_orders_exist",
                "disconnect_joined": True,
                "disconnect_passed": True,
            }
            write_smoke_last_state(state_path, stale_state)

            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                timeout=0.25,
                cleanup_stale_state_only=True,
                submitted_at="20260521-13:14:15",
            )

            archive_path = Path(result["archive_path"])
            self.assertEqual(result["cleanup_result"], "STALE_STATE_ARCHIVED")
            self.assertFalse(state_path.exists())
            self.assertTrue(archive_path.exists())
            self.assertEqual(json.loads(archive_path.read_text()), stale_state)
            self.assertEqual(archive_path.parent.name, "archived_ibkr_smoke_states")
            self.assertIn("OPENCLAW_SMOKE_MARKET_20260521125109", archive_path.name)
            self.assertIn("open_orders", archive_path.name)
            self.assertIn("20260521-13_14_15", archive_path.name)
            self.assertEqual(adapter.open_order_calls, [("AAPL", 2.0)])
            self.assertEqual(adapter.position_calls, [("AAPL", 2.0)])
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)
            self.assertEqual(FakeReconciliationWorkflow.instances, [])

    def test_cleanup_stale_state_only_does_not_archive_when_broker_not_clean(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            stale_state = {
                "order_ref": "OPENCLAW_SMOKE_MARKET_20260521125109",
                "final_broker_state": "open_orders",
                "disconnect_joined": True,
                "disconnect_passed": True,
            }
            write_smoke_last_state(state_path, stale_state)

            with self.assertRaisesRegex(SmokeSafetyRefusal, "broker_state=open_orders"):
                run_fake_smoke(
                    lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                    state_path=state_path,
                    open_order_snapshots=[open_orders(qty=1, count=1)],
                    position_snapshots=[flat_position()],
                    timeout=0.25,
                    cleanup_stale_state_only=True,
                )

            self.assertTrue(state_path.exists())
            self.assertEqual(json.loads(state_path.read_text()), stale_state)
            self.assertFalse((Path(tmpdir) / "archived_ibkr_smoke_states").exists())
            adapter = FakeIBKRBrokerAdapter.instances[-1]
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)
            self.assertEqual(FakeReconciliationWorkflow.instances, [])

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
            self.assertTrue(state["submit_attempted"])
            self.assertEqual(state["order_status"], "submitted")
            self.assertEqual(state["final_broker_state"], "open_orders")
            self.assertEqual(state["final_broker_state_reason"], "open_orders_exist")
            self.assertTrue(state["disconnect_joined"])
            self.assertTrue(state["disconnect_passed"])
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
                submitted_at="20260512-10:01:02",
                include_workflow=True,
            )

            self.assertEqual(result.reconciliation_status, "accepted_unfilled")
            intent = workflow.calls[0]["intent"]
            self.assertEqual(intent.submitted_at, "20260512-10:01:02")
            self.assertRegex(intent.submitted_at, r"^\d{8}-\d{2}:\d{2}:\d{2}$")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["submitted_at"], "20260512-10:01:02")
            self.assertRegex(state["submitted_at"], r"^\d{8}-\d{2}:\d{2}:\d{2}$")

    def test_report_only_queries_state_without_submit_and_preserves_last_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            unsafe_state = {
                "manual_review_required": True,
                "submitted_at": "20260512-10:01:02",
            }
            write_smoke_last_state(state_path, unsafe_state)

            result, adapter, _native_api, coordinator = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                report_only=True,
                include_coordinator=True,
            )

            self.assertEqual(result["last_run_state"], unsafe_state)
            self.assertEqual(result["broker_state"].state, "clean")
            self.assertEqual(result["execution_snapshot"].reason, "executions_loaded")
            self.assertEqual(adapter.open_order_calls, [("AAPL", 5.0)])
            self.assertEqual(adapter.position_calls, [("AAPL", 5.0)])
            self.assertEqual(
                adapter.execution_calls,
                [("AAPL", "20260512-10:01:02", 5.0)],
            )
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)
            self.assertEqual(coordinator.disconnect_timeouts, [SMOKE_DISCONNECT_TIMEOUT])
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8")),
                unsafe_state,
            )
            self.assertFalse((Path(tmpdir) / "ibkr_smoke.lock").exists())

    def test_report_only_does_not_imply_submit_or_reconciliation_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"
            previous_state = {
                "submitted_at": "20260512-10:01:02",
                "manual_review_required": False,
            }
            write_smoke_last_state(state_path, previous_state)

            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                report_only=True,
            )

            self.assertEqual(result["broker_state"].state, "clean")
            self.assertEqual(result["execution_snapshot"].reason, "executions_loaded")
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8")),
                previous_state,
            )
            self.assertEqual(FakeReconciliationWorkflow.instances, [])

    def test_preflight_only_state_write_remains_manual_harness_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"

            result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders()],
                position_snapshots=[flat_position()],
                timeout=0.25,
                preflight_only=True,
            )

            self.assertEqual(result.state, "clean")
            self.assertFalse(adapter.build_market_order_called)
            self.assertFalse(adapter.submit_market_order_called)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertFalse(state["submit_attempted"])
            self.assertIsNone(state["order_id"])
            self.assertIsNone(state["order_status"])
            self.assertIsNone(state["reconciliation_status"])
            self.assertFalse(state["manual_review_required"])
            self.assertEqual(state["final_broker_state"], "clean")
            self.assertEqual(FakeReconciliationWorkflow.instances, [])

    def test_submit_reconciliation_evidence_stays_manual_harness_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "ibkr_smoke_last_state.json"

            result, adapter, native_api, workflow = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=state_path,
                open_order_snapshots=[open_orders(), open_orders()],
                position_snapshots=[flat_position(), flat_position()],
                order_status="reconciliation_required",
                order_type="limit",
                limit_price=100.25,
                include_workflow=True,
            )

            self.assertEqual(
                result.submit_state,
                "submit_uncertain_reconciliation_required",
            )
            self.assertEqual(result.reconciliation_status, "accepted_unfilled")
            self.assertTrue(adapter.submit_market_order_called)
            self.assertEqual(native_api.order_count, 1)
            self.assertEqual(len(workflow.calls), 1)
            self.assertIs(workflow.calls[0]["broker"], adapter)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertTrue(state["submit_attempted"])
            self.assertEqual(state["order_id"], "123")
            self.assertEqual(state["order_status"], "reconciliation_required")
            self.assertEqual(state["reconciliation_status"], "accepted_unfilled")
            self.assertFalse(state["manual_review_required"])

    def test_limit_order_builder_sets_smoke_order_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders(), open_orders()],
                position_snapshots=[flat_position(), flat_position()],
                order_type="limit",
                limit_price=100.25,
                submitted_at="20260512-10:01:02",
            )

            self.assertEqual(
                adapter.submitted_order.order.orderRef,
                "OPENCLAW_SMOKE_LIMIT_20260512100102",
            )

    def test_market_order_path_sets_smoke_order_ref_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _result, adapter, _native_api = run_fake_smoke(
                lock_path=Path(tmpdir) / "ibkr_smoke.lock",
                state_path=Path(tmpdir) / "ibkr_smoke_last_state.json",
                open_order_snapshots=[open_orders(), open_orders()],
                position_snapshots=[flat_position(), flat_position()],
                order_type="market",
                submitted_at="20260512-10:01:02",
            )

            self.assertEqual(
                adapter.submitted_order.order.orderRef,
                "OPENCLAW_SMOKE_MARKET_20260512100102",
            )


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
        self.execution_calls: list[tuple[str | None, str | None, float | None]] = []

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

    def get_execution_snapshot(
        self,
        *,
        symbol: str | None = None,
        since: str | None = None,
        timeout_seconds: float | None = None,
        **_kwargs,
    ) -> BrokerExecutionSnapshotState:
        self.execution_calls.append((symbol, since, timeout_seconds))
        return BrokerExecutionSnapshotState(
            broker_name="ibkr",
            passed=True,
            fills=(),
            fill_count=0,
            total_shares=0.0,
            cumulative_qty=None,
            avg_fill_price=None,
            reason="executions_loaded",
        )


class FakeAggregator:
    def __init__(self, result) -> None:
        self._result = result

    def result(self):
        return self._result


class FakeRecordingNativeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def placeOrder(self, order_id, contract, order) -> None:
        self.calls.append("placeOrder")

    def reqExecutions(self, request_id, execution_filter) -> None:
        self.calls.append("reqExecutions")

    def reqAllOpenOrders(self) -> None:
        self.calls.append("reqAllOpenOrders")

    def reqPositionsMulti(self, request_id, account, model_code) -> None:
        self.calls.append("reqPositionsMulti")

    def cancelPositionsMulti(self, request_id) -> None:
        self.calls.append("cancelPositionsMulti")


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
        return FakeMarketOrderPayload()

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
        self.orderRef = None


class FakeMarketOrderPayload:
    def __init__(self) -> None:
        self.order = FakeNativeOrder()


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
    report_only: bool = False,
    cleanup_stale_state_only: bool = False,
    order_type: str = "market",
    limit_price: float | None = None,
    order_status: str = "submitted",
    submitted_at: str = "20260512-10:01:02",
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
                report_only=report_only,
                cleanup_stale_state_only=cleanup_stale_state_only,
                order_type=order_type,
                limit_price=limit_price,
            )
    adapter = (
        FakeIBKRBrokerAdapter.instances[-1]
        if FakeIBKRBrokerAdapter.instances
        else None
    )
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
