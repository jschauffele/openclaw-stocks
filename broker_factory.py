from alpaca_broker_adapter import AlpacaBrokerAdapter
from client_factory import create_trading_client
import config as default_config
from ibkr_native_imports import IBKRNativeAPI
from ibkr_runtime_assembly import assemble_ibkr_runtime
from ibkr_runtime_config import build_ibkr_runtime_assembly_config


SUPPORTED_BROKERS = {"alpaca"}


def create_broker_adapter(
    broker_name: str,
    *,
    alpaca_api_key: str,
    alpaca_secret_key: str,
    ibkr_config_module: object | None = None,
    ibkr_native_api: IBKRNativeAPI | None = None,
    ibkr_native_api_loader=None,
):
    normalized_broker = broker_name.strip().lower()

    if normalized_broker == "alpaca":
        client = create_trading_client(alpaca_api_key, alpaca_secret_key)
        return AlpacaBrokerAdapter(client)

    if normalized_broker == "ibkr":
        config_module = ibkr_config_module or default_config
        if not hasattr(config_module, "OPENCLAW_IBKR_RUNTIME_ENABLED"):
            config_module.refresh_config_from_env()
        assembly_config = build_ibkr_runtime_assembly_config(config_module)
        if not assembly_config.enabled:
            supported = ", ".join(sorted(SUPPORTED_BROKERS))
            raise ValueError(
                f"Unsupported OPENCLAW_BROKER={broker_name!r}; "
                f"supported brokers: {supported}"
            )
        assembly_kwargs = {"native_api": ibkr_native_api}
        if ibkr_native_api_loader is not None:
            assembly_kwargs["native_api_loader"] = ibkr_native_api_loader
        assembly = assemble_ibkr_runtime(assembly_config, **assembly_kwargs)
        return assembly.adapter

    supported = ", ".join(sorted(SUPPORTED_BROKERS))
    raise ValueError(
        f"Unsupported OPENCLAW_BROKER={broker_name!r}; supported brokers: {supported}"
    )
