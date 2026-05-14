from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ibkr_runtime_diagnostics import (
    DEFAULT_CLIENT_ID,
    DEFAULT_DISCONNECT_TIMEOUT,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SYMBOL,
    DEFAULT_TIMEOUT,
    run_ibkr_runtime_diagnostics,
)


DiagnosticsRunner = Callable[..., dict[str, Any]]


@dataclass(frozen=True, slots=True)
class IBKRReadOnlyRuntimeProviderConfig:
    enabled: bool = False
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    client_id: int = DEFAULT_CLIENT_ID
    timeout: float = DEFAULT_TIMEOUT
    disconnect_timeout: float = DEFAULT_DISCONNECT_TIMEOUT
    symbol: str = DEFAULT_SYMBOL
    include_executions: bool = False
    execution_since: str | None = None


class IBKRReadOnlyRuntimeProvider:
    def __init__(
        self,
        config: IBKRReadOnlyRuntimeProviderConfig | None = None,
        *,
        diagnostics_runner: DiagnosticsRunner = run_ibkr_runtime_diagnostics,
    ) -> None:
        self.config = config or IBKRReadOnlyRuntimeProviderConfig()
        self._diagnostics_runner = diagnostics_runner

    def get_runtime_diagnostics(self) -> dict[str, Any]:
        if not self.config.enabled:
            return _provider_state(
                provider_status="disabled",
                enabled=False,
                include_execution_snapshot=self.config.include_executions,
            )

        try:
            diagnostics = self._diagnostics_runner(
                host=self.config.host,
                port=self.config.port,
                client_id=self.config.client_id,
                timeout=self.config.timeout,
                disconnect_timeout=self.config.disconnect_timeout,
                symbol=self.config.symbol,
                include_execution_snapshot=self.config.include_executions,
                execution_since=self.config.execution_since,
                print_output=False,
            )
        except Exception as exc:
            return _provider_state(
                provider_status="error",
                enabled=True,
                include_execution_snapshot=self.config.include_executions,
                error={
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            )

        result = dict(diagnostics)
        result["provider_status"] = "enabled"
        result["enabled"] = True
        result.setdefault("broker_state", "unknown")
        result.setdefault("error", None)
        return result

    def read_broker_state(self) -> dict[str, Any]:
        return self.get_runtime_diagnostics()


def _provider_state(
    *,
    provider_status: str,
    enabled: bool,
    include_execution_snapshot: bool,
    error: dict[str, str] | None = None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "provider_status": provider_status,
        "enabled": enabled,
        "connection_result": None,
        "connection_completion_source": None,
        "next_valid_id": None,
        "open_order_snapshot": None,
        "position_snapshot": None,
        "broker_state": "unknown",
        "disconnect_result": None,
        "connect_state": None,
        "shutdown_state": None,
        "thread_state": None,
        "error": error,
    }
    if include_execution_snapshot:
        state["execution_snapshot"] = None
    return state
