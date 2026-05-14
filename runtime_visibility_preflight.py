from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


BLOCKING_BROKER_STATES = frozenset(
    {
        "unknown",
        "open_orders",
        "non_flat_position",
    }
)


@dataclass(frozen=True, slots=True)
class RuntimeVisibilityPreflightReport:
    provider_name: str
    provider_status: str
    enabled: bool
    broker_state: str
    blocking: bool
    reason: str
    raw_diagnostics: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_runtime_visibility_preflight(
    providers: Iterable[object],
) -> list[dict[str, Any]]:
    return [
        build_runtime_visibility_report(provider).to_dict()
        for provider in providers
    ]


def build_runtime_visibility_report(
    provider: object,
    *,
    provider_name: str | None = None,
) -> RuntimeVisibilityPreflightReport:
    resolved_provider_name = provider_name or _provider_name(provider)

    try:
        diagnostics = _read_provider(provider)
    except Exception as exc:
        return RuntimeVisibilityPreflightReport(
            provider_name=resolved_provider_name,
            provider_status="error",
            enabled=True,
            broker_state="unknown",
            blocking=True,
            reason="provider_exception",
            raw_diagnostics={
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
            },
        )

    return _report_from_diagnostics(
        provider_name=resolved_provider_name,
        diagnostics=diagnostics,
    )


def _read_provider(provider: object) -> dict[str, Any]:
    read_broker_state = getattr(provider, "read_broker_state", None)
    if callable(read_broker_state):
        return _ensure_diagnostics(read_broker_state())

    get_runtime_diagnostics = getattr(provider, "get_runtime_diagnostics", None)
    if callable(get_runtime_diagnostics):
        return _ensure_diagnostics(get_runtime_diagnostics())

    raise TypeError(
        "runtime visibility provider must expose read_broker_state "
        "or get_runtime_diagnostics"
    )


def _report_from_diagnostics(
    *,
    provider_name: str,
    diagnostics: dict[str, Any],
) -> RuntimeVisibilityPreflightReport:
    provider_status = str(diagnostics.get("provider_status") or "unknown")
    enabled = bool(diagnostics.get("enabled", provider_status != "disabled"))
    broker_state = str(diagnostics.get("broker_state") or "unknown")
    blocking, reason = _classify_preflight(
        provider_status=provider_status,
        broker_state=broker_state,
    )
    return RuntimeVisibilityPreflightReport(
        provider_name=provider_name,
        provider_status=provider_status,
        enabled=enabled,
        broker_state=broker_state,
        blocking=blocking,
        reason=reason,
        raw_diagnostics=diagnostics,
    )


def _classify_preflight(
    *,
    provider_status: str,
    broker_state: str,
) -> tuple[bool, str]:
    if provider_status == "disabled":
        return False, "provider_disabled"
    if provider_status == "error":
        return True, "provider_error"
    if broker_state == "clean":
        return False, "broker_state_clean"
    if broker_state in BLOCKING_BROKER_STATES:
        return True, f"broker_state_{broker_state}"
    return True, "broker_state_unrecognized"


def _provider_name(provider: object) -> str:
    explicit_name = getattr(provider, "provider_name", None)
    if explicit_name:
        return str(explicit_name)
    return provider.__class__.__name__


def _ensure_diagnostics(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("runtime visibility provider returned non-dict diagnostics")
    return value
