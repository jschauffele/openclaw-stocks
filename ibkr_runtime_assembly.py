from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable

from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import IBKRNativeAPI, load_ibkr_native_api
from ibkr_native_lifecycle import (
    IBKRNativeClientBundle,
    build_ibkr_native_client_bundle,
)
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator
from ibkr_timeout_injector import IBKRTimeoutInjector


LOCALHOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PAPER_PORTS = frozenset({7497, 4002})


NativeApiLoader = Callable[[], IBKRNativeAPI]


@dataclass(frozen=True, slots=True)
class IBKRRuntimeAssemblyConfig:
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 9107
    account_summary_group: str = "All"
    account_summary_tags: str = "BuyingPower"
    account_summary_request_id_start: int = 1
    position_account: str = ""
    position_model_code: str = ""
    position_request_id_start: int = 10001
    execution_request_id_start: int = 20001
    order_id_start: int | None = None
    connect_timeout_seconds: float = 5.0


@dataclass(frozen=True, slots=True)
class IBKRRuntimeAssembly:
    config: IBKRRuntimeAssemblyConfig
    adapter: IBKRBrokerAdapter
    registry: IBKRPendingRequestRegistry
    request_coordinator: IBKRRequestCoordinator
    bridge: IBKRCallbackBridge
    timeout_injector: IBKRTimeoutInjector
    runtime_coordinator: IBKRRuntimeArbitrationCoordinator | None
    native_bundle: IBKRNativeClientBundle | None
    native_api: IBKRNativeAPI | None

    @property
    def enabled(self) -> bool:
        return self.config.enabled


def assemble_ibkr_runtime(
    config: IBKRRuntimeAssemblyConfig | None = None,
    *,
    native_api: IBKRNativeAPI | None = None,
    native_api_loader: NativeApiLoader = load_ibkr_native_api,
) -> IBKRRuntimeAssembly:
    assembly_config = config or IBKRRuntimeAssemblyConfig()
    _validate_config(assembly_config)

    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = IBKRCallbackBridge(
        registry,
        request_coordinator=request_coordinator,
    )
    timeout_injector = IBKRTimeoutInjector(registry)

    resolved_native_api = native_api
    native_bundle = None
    runtime_coordinator = None
    client = None

    if assembly_config.enabled:
        if resolved_native_api is None:
            resolved_native_api = native_api_loader()
        native_bundle = build_ibkr_native_client_bundle(
            native_api=resolved_native_api,
            bridge=bridge,
        )
        client = native_bundle.client
        runtime_coordinator = IBKRRuntimeArbitrationCoordinator(
            client=client,
            enabled=True,
            registry=registry,
            bridge=bridge,
            timeout_injector=timeout_injector,
        )

    adapter = IBKRBrokerAdapter(
        client=client,
        native_api=resolved_native_api,
        bridge=bridge,
        registry=registry,
        timeout_injector=timeout_injector,
        request_coordinator=request_coordinator,
        coordinator=runtime_coordinator,
        host=assembly_config.host,
        port=assembly_config.port,
        client_id=assembly_config.client_id,
        enabled=assembly_config.enabled,
        account_summary_group=assembly_config.account_summary_group,
        account_summary_tags=assembly_config.account_summary_tags,
        account_summary_request_id_start=(
            assembly_config.account_summary_request_id_start
        ),
        position_account=assembly_config.position_account,
        position_model_code=assembly_config.position_model_code,
        position_request_id_start=assembly_config.position_request_id_start,
        execution_request_id_start=assembly_config.execution_request_id_start,
        order_id_start=assembly_config.order_id_start,
    )

    return IBKRRuntimeAssembly(
        config=assembly_config,
        adapter=adapter,
        registry=registry,
        request_coordinator=request_coordinator,
        bridge=bridge,
        timeout_injector=timeout_injector,
        runtime_coordinator=runtime_coordinator,
        native_bundle=native_bundle,
        native_api=resolved_native_api,
    )


def _validate_config(config: IBKRRuntimeAssemblyConfig) -> None:
    if config.host not in LOCALHOSTS:
        raise ValueError("IBKR runtime assembly is restricted to localhost")
    if config.port not in PAPER_PORTS:
        raise ValueError("IBKR runtime assembly is restricted to paper ports")
    if (
        not isfinite(config.connect_timeout_seconds)
        or config.connect_timeout_seconds <= 0
    ):
        raise ValueError("IBKR runtime assembly requires a finite positive timeout")
