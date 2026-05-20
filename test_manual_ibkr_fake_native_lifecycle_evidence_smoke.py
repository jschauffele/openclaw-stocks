from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import manual_ibkr_fake_native_lifecycle_evidence_smoke as smoke
from ibkr_native_imports import IBKRNativeAPI


class RecordingFakeEClient:
    side_effect_calls: list[str] = []
    instances: list["RecordingFakeEClient"] = []

    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = []
        self.run_calls = 0
        self.disconnect_calls = 0
        self.connected = False
        self.__class__.instances.append(self)

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls.append((args, kwargs))
        self.connected = True

    def run(self) -> None:
        self.run_calls += 1

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self.connected = False

    def isConnected(self) -> bool:
        return self.connected

    def placeOrder(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("placeOrder")

    def reqExecutions(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqExecutions")

    def reqAllOpenOrders(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqAllOpenOrders")

    def reqPositionsMulti(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqPositionsMulti")

    def reqAccountSummary(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqAccountSummary")


class FakeEWrapper:
    pass


class FakeContract:
    pass


class FakeOrder:
    pass


class FakeExecutionFilter:
    pass


def recording_fake_native_api() -> IBKRNativeAPI:
    return IBKRNativeAPI(
        e_client=RecordingFakeEClient,
        e_wrapper=FakeEWrapper,
        contract=FakeContract,
        order=FakeOrder,
        execution_filter=FakeExecutionFilter,
    )


class ManualIBKRFakeNativeLifecycleEvidenceSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        RecordingFakeEClient.side_effect_calls = []
        RecordingFakeEClient.instances = []

    def test_smoke_returns_operator_readable_fake_native_evidence(self) -> None:
        report = smoke.run_fake_native_lifecycle_evidence_smoke(
            host="127.0.0.1",
            port=7497,
            client_id=9199,
            next_valid_id=777,
            fake_native_api=recording_fake_native_api(),
        )

        self.assertEqual(report["broker_name"], "ibkr")
        self.assertEqual(report["runtime_mode"], "fake_native_manual_smoke")
        self.assertEqual(report["result"], "blocked")
        self.assertEqual(report["reason"], "ibkr_runtime_submit_not_approved")
        self.assertEqual(report["assembly_enabled"], True)
        self.assertEqual(report["fake_native"], True)
        self.assertEqual(report["connect_attempted"], True)
        self.assertEqual(report["fake_connect_calls"], [(("127.0.0.1", 7497, 9199), {})])
        self.assertEqual(report["connection_completion_source"], "next_valid_id")
        self.assertEqual(report["next_valid_id"], 777)
        self.assertEqual(report["connect_result"]["passed"], True)
        self.assertEqual(report["connect_result"]["reason"], "connect_ready")
        self.assertEqual(report["disconnect_result"]["passed"], True)
        self.assertEqual(
            report["disconnect_result"]["reason"],
            "ibkr_client_disconnected",
        )
        self.assertEqual(report["fake_disconnect_calls"], 1)
        self.assertEqual(report["run_loop_started"], False)
        self.assertEqual(report["run_thread_state"], "not_started")
        self.assertEqual(report["fake_run_calls"], 0)
        self.assertEqual(report["disconnect_joined"], False)
        self.assertEqual(report["shutdown_state"], "no_runtime_thread_started")
        self.assertEqual(report["submit_approved"], False)
        self.assertEqual(report["reconciliation_approved"], False)
        self.assertEqual(report["submit_attempted"], False)
        self.assertEqual(report["reconciliation_attempted"], False)
        self.assertEqual(report["fake_side_effect_calls"], [])
        self.assertEqual(RecordingFakeEClient.side_effect_calls, [])

    def test_smoke_does_not_emit_submit_or_reconciliation_fields(self) -> None:
        report = smoke.run_fake_native_lifecycle_evidence_smoke(
            fake_native_api=recording_fake_native_api(),
        )

        absent_fields = {
            "order_id",
            "order_status",
            "submit_state",
            "submitted_at",
            "reconciliation_status",
            "manual_review_required",
            "filled_qty",
            "working_qty",
            "final_broker_state",
            "open_order_snapshot_summary",
            "position_snapshot_summary",
            "execution_snapshot_summary",
        }
        for field in absent_fields:
            with self.subTest(field=field):
                self.assertNotIn(field, report)

    def test_cli_prints_json_operator_evidence(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            smoke.main()

        report = json.loads(stdout.getvalue())

        self.assertEqual(report["result"], "blocked")
        self.assertEqual(report["reason"], "ibkr_runtime_submit_not_approved")
        self.assertEqual(report["connect_result"]["reason"], "connect_ready")
        self.assertEqual(
            report["disconnect_result"]["reason"],
            "ibkr_client_disconnected",
        )
        self.assertEqual(report["fake_side_effect_calls"], [])

    def test_smoke_stays_detached_from_runtime_orchestration_paths(self) -> None:
        source = Path(__file__).with_name(
            "manual_ibkr_fake_native_lifecycle_evidence_smoke.py"
        ).read_text(encoding="utf-8")

        prohibited_imports = (
            "import main",
            "from main",
            "broker_factory",
            "market_data",
            "strategy_engine",
            "risk_engine",
            "state_manager",
            "observation_logger",
            "ibkr_submit_reconciliation_workflow",
            "load_ibkr_native_api",
        )
        for prohibited_import in prohibited_imports:
            with self.subTest(prohibited_import=prohibited_import):
                self.assertNotIn(prohibited_import, source)


if __name__ == "__main__":
    unittest.main()
