from __future__ import annotations


LOCALHOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PAPER_PORTS = frozenset({7497, 4002})


def build_runtime_visibility_providers(
    config_module=None,
    *,
    ibkr_provider_factory=None,
) -> list:
    if not _enabled(config_module, "OPENCLAW_RUNTIME_VISIBILITY_ENABLED"):
        return []
    providers = []
    provider_names = _provider_names(config_module)
    if "fake" in provider_names:
        providers.append(_TestOnlyRuntimeVisibilityFakeProvider(config_module))
    if "ibkr_read_only" in provider_names:
        ibkr_provider = _build_ibkr_read_only_provider(
            config_module,
            ibkr_provider_factory=ibkr_provider_factory,
        )
        if ibkr_provider is not None:
            providers.append(ibkr_provider)
    return providers


class _TestOnlyRuntimeVisibilityFakeProvider:
    provider_name = "fake"

    def __init__(self, config_module=None) -> None:
        self.config_module = config_module

    def read_broker_state(self) -> dict:
        return {
            "provider_status": _config_value(
                self.config_module,
                "OPENCLAW_RUNTIME_VISIBILITY_FAKE_PROVIDER_STATUS",
                "enabled",
            ),
            "enabled": True,
            "broker_state": _config_value(
                self.config_module,
                "OPENCLAW_RUNTIME_VISIBILITY_FAKE_BROKER_STATE",
                "clean",
            ),
        }


def _enabled(config_module, name: str) -> bool:
    return _truthy(_config_value(config_module, name, False))


def _build_ibkr_read_only_provider(config_module, *, ibkr_provider_factory=None):
    if not _enabled(config_module, "OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED"):
        return None
    if (
        _config_value(
            config_module,
            "OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE",
            "",
        )
        != "paper_localhost"
    ):
        return None

    config_kwargs = _ibkr_config_kwargs(config_module)
    if config_kwargs is None:
        return None

    if ibkr_provider_factory is not None:
        return ibkr_provider_factory(**config_kwargs)

    from ibkr_read_only_runtime_provider import (
        IBKRReadOnlyRuntimeProvider,
        IBKRReadOnlyRuntimeProviderConfig,
    )

    return IBKRReadOnlyRuntimeProvider(
        IBKRReadOnlyRuntimeProviderConfig(**config_kwargs)
    )


def _ibkr_config_kwargs(config_module) -> dict | None:
    host = _config_value(
        config_module,
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST",
        "127.0.0.1",
    )
    port = _int_value(
        _config_value(config_module, "OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT", 7497)
    )
    timeout = _float_value(
        _config_value(config_module, "OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT", 5.0)
    )
    disconnect_timeout = _float_value(
        _config_value(
            config_module,
            "OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT",
            1.0,
        )
    )
    if host not in LOCALHOSTS:
        return None
    if port not in PAPER_PORTS:
        return None
    if timeout is None or timeout <= 0:
        return None
    if disconnect_timeout is None or disconnect_timeout <= 0:
        return None
    return {
        "enabled": True,
        "host": host,
        "port": port,
        "client_id": _int_value(
            _config_value(
                config_module,
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID",
                9117,
            )
        ),
        "timeout": timeout,
        "disconnect_timeout": disconnect_timeout,
        "symbol": _config_value(
            config_module,
            "OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL",
            "AAPL",
        ),
        "include_executions": _truthy(
            _config_value(
                config_module,
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS",
                False,
            )
        ),
        "execution_since": _config_value(
            config_module,
            "OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE",
            None,
        ),
    }


def _provider_names(config_module) -> set[str]:
    raw_providers = _config_value(
        config_module,
        "OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS",
        "",
    )
    if isinstance(raw_providers, str):
        return {
            provider.strip().lower()
            for provider in raw_providers.split(",")
            if provider.strip()
        }
    try:
        return {str(provider).strip().lower() for provider in raw_providers}
    except TypeError:
        return set()


def _config_value(config_module, name: str, default):
    if config_module is None:
        return default
    return getattr(config_module, name, default)


def _int_value(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_value(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
