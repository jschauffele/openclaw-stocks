from __future__ import annotations

import importlib
import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace

import manual_ibkr_localhost_connect_smoke as smoke


class FakeCoordinator:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled
        self.client = None
        self.callback_calls = []
        self.connect_calls = []
        self.timeout_calls = []
        self.error_calls = []
        self.disconnect_calls = []
        self.wait_results = []
        self.connect_state = "disconnected"
        self.shutdown_state = "active"
        self.thread_owner = SimpleNamespace(thread_state="not_started")
        self.result = SimpleNamespace(passed=True, reason="connect_ready")

    def callback_connect_ready(self, **kwargs) -> bool:
        if self.result is not None and self.result.reason == "connect_error":
            return False
        self.callback_calls.append(kwargs)
        self.result = SimpleNamespace(passed=True, reason="connect_ready")
        self.connect_state = "connected"
        return True

    def callback_connect_error(self, **kwargs) -> bool:
        self.error_calls.append(kwargs)
        self.result = SimpleNamespace(passed=False, reason="connect_error")
        self.connect_state = "disconnected"
        return True

    def connect(self, **kwargs) -> None:
        self.connect_calls.append(kwargs)
        self.connect_state = "connecting"
        self.thread_owner.thread_state = "running"

    def wait_for_completion(self, *, timeout) -> bool:
        if self.wait_results:
            return self.wait_results.pop(0)
        return True

    def timeout_connect(self, **kwargs) -> bool:
        self.timeout_calls.append(kwargs)
        self.result = SimpleNamespace(passed=False, reason="connect_timeout")
        return True

    def connect_result(self):
        return self.result

    def disconnect(self, *, timeout) -> bool:
        self.disconnect_calls.append({"timeout": timeout})
        self.connect_state = "disconnected"
        self.shutdown_state = "complete"
        self.thread_owner.thread_state = "stopped"
        return True


class FakeEClient:
    instances = []

    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = []
        self.disconnect_calls = 0
        self.run_calls = 0
        FakeEClient.instances.append(self)

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls.append((args, kwargs))
        raise AssertionError("unit tests must not call real or fake socket connect")

    def disconnect(self) -> None:
        self.disconnect_calls += 1

    def run(self) -> None:
        self.run_calls += 1


class FakeEWrapper:
    def __init__(self) -> None:
        self.native_wrapper_initialized = True


def fake_native_api_loader():
    return SimpleNamespace(e_client=FakeEClient, e_wrapper=FakeEWrapper)


class ManualIBKRLocalhostConnectSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeEClient.instances = []

    def test_wrapper_next_valid_id_routes_to_coordinator(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertTrue(wrapper.nextValidId(101))

        self.assertEqual(coordinator.callback_calls, [{"message": "next_valid_id"}])
        self.assertEqual(coordinator.connect_state, "connected")

    def test_wrapper_error_is_accepted(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertTrue(wrapper.error(-1, 502, "connect failed"))

        self.assertEqual(
            coordinator.error_calls,
            [{"message": "connect failed", "retryable": True}],
        )

    def test_wrapper_error_produces_deterministic_failed_connect_result(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        wrapper.error(-1, 502, "connect failed")
        result = coordinator.connect_result()

        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_error")
        self.assertEqual(coordinator.connect_state, "disconnected")

    def test_wrapper_ignores_nonfatal_farm_status_before_readiness(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        coordinator.result = None
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertFalse(
            wrapper.error(-1, 2104, "Market data farm connection is OK:usfarm")
        )
        self.assertTrue(wrapper.nextValidId(101))

        self.assertEqual(coordinator.error_calls, [])
        self.assertEqual(coordinator.callback_calls, [{"message": "next_valid_id"}])
        self.assertEqual(coordinator.connect_state, "connected")

    def test_wrapper_connect_ack_is_non_terminal(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertFalse(wrapper.connectAck())

        self.assertEqual(coordinator.callback_calls, [])
        self.assertEqual(coordinator.error_calls, [])

    def test_wrapper_connection_closed_is_accepted(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertFalse(wrapper.connectionClosed())

        self.assertEqual(coordinator.callback_calls, [])
        self.assertEqual(coordinator.error_calls, [])

    def test_manual_smoke_bundle_wrapper_subclasses_injected_native_wrapper(
        self,
    ) -> None:
        coordinator = FakeCoordinator(enabled=True)

        bundle = smoke.build_manual_smoke_bundle(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
        )

        self.assertIsInstance(bundle.wrapper, FakeEWrapper)
        self.assertIsInstance(bundle.wrapper, smoke.CoordinatorReadinessWrapper)
        self.assertTrue(bundle.wrapper.native_wrapper_initialized)
        self.assertIs(bundle.wrapper.coordinator, coordinator)
        self.assertIs(FakeEClient.instances[0].wrapper, bundle.wrapper)

    def test_native_wrapper_routes_next_valid_id_to_coordinator(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        bundle = smoke.build_manual_smoke_bundle(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
        )

        self.assertTrue(bundle.wrapper.nextValidId(101))

        self.assertEqual(coordinator.callback_calls, [{"message": "next_valid_id"}])

    def test_native_wrapper_ignores_nonfatal_status_code(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        coordinator.result = None
        bundle = smoke.build_manual_smoke_bundle(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
        )

        self.assertFalse(
            bundle.wrapper.error(-1, 2106, "HMDS data farm connection is OK:ushmds")
        )

        self.assertEqual(coordinator.error_calls, [])
        self.assertIsNone(coordinator.connect_result())

    def test_native_wrapper_routes_fatal_error_to_coordinator(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        bundle = smoke.build_manual_smoke_bundle(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
        )

        self.assertTrue(bundle.wrapper.error(-1, 502, "connect failed"))

        self.assertEqual(
            coordinator.error_calls,
            [{"message": "connect failed", "retryable": True}],
        )

    def test_native_wrapper_connection_closed_and_connect_ack_are_accepted(
        self,
    ) -> None:
        coordinator = FakeCoordinator(enabled=True)
        bundle = smoke.build_manual_smoke_bundle(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
        )

        self.assertFalse(bundle.wrapper.connectionClosed())
        self.assertFalse(bundle.wrapper.connectAck())

        self.assertEqual(coordinator.callback_calls, [])
        self.assertEqual(coordinator.error_calls, [])

    def test_connection_closed_after_error_does_not_replace_failed_result(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        wrapper.error(-1, 502, "connect failed")
        failed_result = coordinator.connect_result()
        self.assertFalse(wrapper.connectionClosed())

        self.assertIs(coordinator.connect_result(), failed_result)
        self.assertEqual(coordinator.connect_result().reason, "connect_error")

    def test_connection_closed_before_readiness_does_not_create_false_success(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        coordinator.result = None
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertFalse(wrapper.connectionClosed())

        self.assertIsNone(coordinator.connect_result())
        self.assertEqual(coordinator.callback_calls, [])
        self.assertEqual(coordinator.error_calls, [])

    def test_late_next_valid_id_after_error_is_ignored(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        self.assertTrue(wrapper.error(-1, 502, "connect failed"))
        self.assertFalse(wrapper.nextValidId(101))

        self.assertEqual(coordinator.callback_calls, [])
        self.assertEqual(coordinator.error_calls[0]["message"], "connect failed")

    def test_timeout_path_calls_coordinator_timeout(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        coordinator.wait_results = [False]

        result = run_smoke_silently(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
            timeout=1.25,
        )

        self.assertEqual(result.reason, "connect_timeout")
        self.assertEqual(
            coordinator.timeout_calls,
            [
                {
                    "message": "manual smoke timed out waiting for nextValidId",
                    "elapsed_ms": 1250,
                }
            ],
        )

    def test_final_cleanup_calls_coordinator_disconnect(self) -> None:
        coordinator = FakeCoordinator(enabled=True)

        run_smoke_silently(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
            timeout=2.0,
        )

        self.assertEqual(coordinator.disconnect_calls, [{"timeout": 2.0}])
        self.assertEqual(coordinator.shutdown_state, "complete")
        self.assertEqual(coordinator.thread_owner.thread_state, "stopped")

    def test_error_path_cleanup_calls_coordinator_disconnect(self) -> None:
        coordinator = FakeCoordinator(enabled=True)
        wrapper = smoke.CoordinatorReadinessWrapper(coordinator)

        wrapper.error(-1, 502, "connect failed")
        run_smoke_silently(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
            timeout=2.0,
        )

        self.assertEqual(coordinator.disconnect_calls, [{"timeout": 2.0}])

    def test_script_import_does_not_execute_smoke(self) -> None:
        module = importlib.reload(smoke)

        self.assertEqual(module.SMOKE_EXECUTIONS, 0)

    def test_no_real_connect_occurs_in_unit_tests(self) -> None:
        coordinator = FakeCoordinator(enabled=True)

        run_smoke_silently(
            native_api_loader=fake_native_api_loader,
            coordinator_factory=lambda enabled: coordinator,
            timeout=1.0,
        )

        self.assertEqual(len(FakeEClient.instances), 1)
        self.assertEqual(FakeEClient.instances[0].connect_calls, [])
        self.assertEqual(coordinator.connect_calls[0]["host"], "127.0.0.1")
        self.assertEqual(coordinator.connect_calls[0]["port"], 7497)


def run_smoke_silently(**kwargs):
    with redirect_stdout(io.StringIO()):
        return smoke.run_localhost_connect_smoke(**kwargs)


if __name__ == "__main__":
    unittest.main()
