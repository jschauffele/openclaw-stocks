from __future__ import annotations


def build_runtime_visibility_providers(config_module=None) -> list:
    if not _enabled(config_module, "OPENCLAW_RUNTIME_VISIBILITY_ENABLED"):
        return []
    if "fake" not in _provider_names(config_module):
        return []
    return [_TestOnlyRuntimeVisibilityFakeProvider(config_module)]


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


def _truthy(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
