from __future__ import annotations

from ibkr_lifecycle_connect_evidence import (
    record_fake_native_lifecycle_connect_evidence,
)
from ibkr_native_imports import IBKRNativeAPI
from ibkr_runtime_assembly import IBKRRuntimeAssemblyConfig, assemble_ibkr_runtime


def build_fake_native_lifecycle_connect_report_fields(
    config: IBKRRuntimeAssemblyConfig,
    *,
    fake_native_api: IBKRNativeAPI,
    next_valid_id: int | None = None,
) -> dict:
    if fake_native_api is None:
        raise ValueError("fake-native lifecycle evidence requires injected native API")

    assembly = assemble_ibkr_runtime(
        config,
        native_api=fake_native_api,
        native_api_loader=_reject_native_api_load,
    )
    evidence = record_fake_native_lifecycle_connect_evidence(
        assembly,
        next_valid_id=next_valid_id,
    )

    return {
        "assembly_enabled": True,
        "fake_native": True,
        "connect_attempted": True,
        "run_loop_started": False,
        **evidence.as_report_fields(),
    }


def _reject_native_api_load() -> IBKRNativeAPI:
    raise RuntimeError("fake-native lifecycle boundary cannot load real IBKR API")
