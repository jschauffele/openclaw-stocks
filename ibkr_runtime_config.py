from __future__ import annotations

from ibkr_runtime_assembly import IBKRRuntimeAssemblyConfig, LOCALHOSTS, PAPER_PORTS


RUNTIME_MODE = "paper_localhost"


def build_ibkr_runtime_assembly_config(
    config_module: object,
) -> IBKRRuntimeAssemblyConfig:
    mode = config_module.OPENCLAW_IBKR_RUNTIME_MODE
    host = config_module.OPENCLAW_IBKR_RUNTIME_HOST
    port = config_module.OPENCLAW_IBKR_RUNTIME_PORT

    if mode != RUNTIME_MODE:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_MODE must be paper_localhost")
    if host not in LOCALHOSTS:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_HOST must be localhost")
    if port not in PAPER_PORTS:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_PORT must be a paper port")

    return IBKRRuntimeAssemblyConfig(
        enabled=config_module.OPENCLAW_IBKR_RUNTIME_ENABLED,
        host=host,
        port=port,
        client_id=config_module.OPENCLAW_IBKR_RUNTIME_CLIENT_ID,
        position_account=config_module.OPENCLAW_IBKR_RUNTIME_ACCOUNT,
        position_model_code=config_module.OPENCLAW_IBKR_RUNTIME_MODEL_CODE,
        order_id_start=config_module.OPENCLAW_IBKR_RUNTIME_ORDER_ID_START,
        connect_timeout_seconds=(
            config_module.OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS
        ),
    )
