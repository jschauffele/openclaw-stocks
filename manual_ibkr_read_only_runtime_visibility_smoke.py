from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable, Iterable

from runtime_visibility_orchestrator import build_runtime_visibility_summary
from runtime_visibility_provider_composer import build_runtime_visibility_providers


LOCALHOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PAPER_PORTS = frozenset({7497, 4002})
DEFAULT_CLIENT_ID = 9117
DEFAULT_SYMBOL = "AAPL"


@dataclass(frozen=True, slots=True)
class ManualIBKRReadOnlyRuntimeVisibilityConfig:
    OPENCLAW_RUNTIME_VISIBILITY_ENABLED: bool
    OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS: str
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED: bool
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE: str
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST: str
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT: int
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID: int
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT: float
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT: float
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL: str
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS: bool
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE: str | None


ProviderBuilder = Callable[[object], list]
SummaryBuilder = Callable[[Iterable[object]], dict]


def build_manual_ibkr_read_only_runtime_visibility_config(
    *,
    host: str,
    port: int,
    timeout: float,
    disconnect_timeout: float,
    client_id: int = DEFAULT_CLIENT_ID,
    symbol: str = DEFAULT_SYMBOL,
    include_executions: bool = False,
    execution_since: str | None = None,
) -> ManualIBKRReadOnlyRuntimeVisibilityConfig:
    _validate_manual_inputs(
        host=host,
        port=port,
        timeout=timeout,
        disconnect_timeout=disconnect_timeout,
    )
    return ManualIBKRReadOnlyRuntimeVisibilityConfig(
        OPENCLAW_RUNTIME_VISIBILITY_ENABLED=True,
        OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS="ibkr_read_only",
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED=True,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE="paper_localhost",
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST=host,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT=port,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID=client_id,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT=timeout,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT=disconnect_timeout,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL=symbol,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS=include_executions,
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE=execution_since,
    )


def run_manual_ibkr_read_only_runtime_visibility_smoke(
    config: ManualIBKRReadOnlyRuntimeVisibilityConfig,
    *,
    provider_builder: ProviderBuilder = build_runtime_visibility_providers,
    summary_builder: SummaryBuilder = build_runtime_visibility_summary,
) -> dict:
    providers = provider_builder(config)
    summary = summary_builder(providers)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def _validate_manual_inputs(
    *,
    host: str,
    port: int,
    timeout: float,
    disconnect_timeout: float,
) -> None:
    if host not in LOCALHOSTS:
        raise ValueError("manual IBKR visibility smoke requires localhost")
    if port not in PAPER_PORTS:
        raise ValueError("manual IBKR visibility smoke requires a paper port")
    if timeout <= 0:
        raise ValueError("manual IBKR visibility smoke requires timeout > 0")
    if disconnect_timeout <= 0:
        raise ValueError(
            "manual IBKR visibility smoke requires disconnect_timeout > 0"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Manual-only read-only IBKR runtime visibility smoke. "
            "Requires local paper IBKR and prints only runtime_visibility_summary."
        )
    )
    parser.add_argument("--host", required=True, choices=sorted(LOCALHOSTS))
    parser.add_argument("--port", required=True, type=int, choices=sorted(PAPER_PORTS))
    parser.add_argument("--timeout", required=True, type=float)
    parser.add_argument("--disconnect-timeout", required=True, type=float)
    parser.add_argument("--client-id", type=int, default=DEFAULT_CLIENT_ID)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--include-executions", action="store_true")
    parser.add_argument("--execution-since")
    return parser.parse_args()


def main() -> dict:
    args = parse_args()
    config = build_manual_ibkr_read_only_runtime_visibility_config(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        disconnect_timeout=args.disconnect_timeout,
        client_id=args.client_id,
        symbol=args.symbol,
        include_executions=args.include_executions,
        execution_since=args.execution_since,
    )
    return run_manual_ibkr_read_only_runtime_visibility_smoke(config)


if __name__ == "__main__":
    main()
