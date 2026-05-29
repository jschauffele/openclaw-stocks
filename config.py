import os
from dotenv import load_dotenv

IBKR_RUNTIME_LOCALHOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
IBKR_RUNTIME_PAPER_PORTS = frozenset({7497, 4002})
IBKR_RUNTIME_MODES = frozenset({"paper_localhost"})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "openclaw.log")
STATE_FILE = os.path.join(BASE_DIR, "order_state.json")
RUN_REPORT_FILE = os.path.join(BASE_DIR, "last_run_report.json")
LEGACY_LAST_ORDER_FILE = os.path.join(BASE_DIR, "last_order.txt")


def env_flag(name: str, default: str = "false") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in ("1", "true", "yes", "on")


def env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def strict_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def strict_env_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def optional_strict_env_int(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def validate_ibkr_runtime_config() -> None:
    if OPENCLAW_IBKR_RUNTIME_MODE not in IBKR_RUNTIME_MODES:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_MODE must be paper_localhost")
    if OPENCLAW_IBKR_RUNTIME_HOST not in IBKR_RUNTIME_LOCALHOSTS:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_HOST must be localhost")
    if OPENCLAW_IBKR_RUNTIME_PORT not in IBKR_RUNTIME_PAPER_PORTS:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_PORT must be a paper port")
    if OPENCLAW_IBKR_RUNTIME_CLIENT_ID <= 0:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_CLIENT_ID must be positive")
    if OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS <= 0:
        raise ValueError(
            "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS must be positive"
        )
    if OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS <= 0:
        raise ValueError(
            "OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS must be positive"
        )
    if OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS <= 0:
        raise ValueError("OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS must be positive")
    if (
        OPENCLAW_IBKR_RUNTIME_ORDER_ID_START is not None
        and OPENCLAW_IBKR_RUNTIME_ORDER_ID_START <= 0
    ):
        raise ValueError("OPENCLAW_IBKR_RUNTIME_ORDER_ID_START must be positive")


def refresh_config_from_env() -> None:
    global OPENCLAW_ENABLED
    global OPENCLAW_DRY_RUN
    global OPENCLAW_SYMBOL
    global OPENCLAW_QTY
    global OPENCLAW_MAX_POSITION_SIZE
    global OPENCLAW_DUPLICATE_COOLDOWN_SECONDS
    global OPENCLAW_BROKER
    global ALPACA_API_KEY
    global ALPACA_SECRET_KEY
    global ALPACA_BASE_URL
    global OPENCLAW_IBKR_RUNTIME_ENABLED
    global OPENCLAW_IBKR_RUNTIME_MODE
    global OPENCLAW_IBKR_RUNTIME_HOST
    global OPENCLAW_IBKR_RUNTIME_PORT
    global OPENCLAW_IBKR_RUNTIME_CLIENT_ID
    global OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS
    global OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS
    global OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS
    global OPENCLAW_IBKR_RUNTIME_ACCOUNT
    global OPENCLAW_IBKR_RUNTIME_MODEL_CODE
    global OPENCLAW_IBKR_RUNTIME_ORDER_ID_START
    global OPENCLAW_RUNTIME_VISIBILITY_ENABLED
    global OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT_SECONDS
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT_SECONDS
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS
    global OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE

    OPENCLAW_ENABLED = env_flag("OPENCLAW_ENABLED", "true")
    OPENCLAW_DRY_RUN = env_flag("OPENCLAW_DRY_RUN", "true")
    OPENCLAW_SYMBOL = env_str("OPENCLAW_SYMBOL", "AAPL").upper()
    OPENCLAW_QTY = env_int("OPENCLAW_QTY", 1)
    OPENCLAW_MAX_POSITION_SIZE = env_int("OPENCLAW_MAX_POSITION_SIZE", 5)
    OPENCLAW_DUPLICATE_COOLDOWN_SECONDS = env_int(
        "OPENCLAW_DUPLICATE_COOLDOWN_SECONDS", 900
    )
    OPENCLAW_BROKER = env_str("OPENCLAW_BROKER", "alpaca").lower()

    ALPACA_API_KEY = env_str("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = env_str("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL = env_str("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    OPENCLAW_IBKR_RUNTIME_ENABLED = env_flag(
        "OPENCLAW_IBKR_RUNTIME_ENABLED", "false"
    )
    OPENCLAW_IBKR_RUNTIME_MODE = env_str(
        "OPENCLAW_IBKR_RUNTIME_MODE", "paper_localhost"
    )
    OPENCLAW_IBKR_RUNTIME_HOST = env_str(
        "OPENCLAW_IBKR_RUNTIME_HOST", "127.0.0.1"
    )
    OPENCLAW_IBKR_RUNTIME_PORT = strict_env_int("OPENCLAW_IBKR_RUNTIME_PORT", 7497)
    OPENCLAW_IBKR_RUNTIME_CLIENT_ID = strict_env_int(
        "OPENCLAW_IBKR_RUNTIME_CLIENT_ID", 9107
    )
    OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS = strict_env_float(
        "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS", 5.0
    )
    OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS = strict_env_float(
        "OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS", 2.0
    )
    OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS = strict_env_float(
        "OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS", 5.0
    )
    OPENCLAW_IBKR_RUNTIME_ACCOUNT = env_str("OPENCLAW_IBKR_RUNTIME_ACCOUNT", "")
    OPENCLAW_IBKR_RUNTIME_MODEL_CODE = env_str(
        "OPENCLAW_IBKR_RUNTIME_MODEL_CODE", ""
    )
    OPENCLAW_IBKR_RUNTIME_ORDER_ID_START = optional_strict_env_int(
        "OPENCLAW_IBKR_RUNTIME_ORDER_ID_START"
    )

    OPENCLAW_RUNTIME_VISIBILITY_ENABLED = env_flag(
        "OPENCLAW_RUNTIME_VISIBILITY_ENABLED", "false"
    )
    OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS = env_str(
        "OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS", ""
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED = env_flag(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED", "false"
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE = env_str(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE", "paper_localhost"
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST = env_str(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST", "127.0.0.1"
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT = strict_env_int(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT", 7497
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID = strict_env_int(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID", 9117
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT_SECONDS = strict_env_float(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT_SECONDS", 5.0
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT = (
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT_SECONDS
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT_SECONDS = strict_env_float(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT_SECONDS", 2.0
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT = (
        OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT_SECONDS
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL = env_str(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL", "AAPL"
    ).upper()
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS = env_flag(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS", "false"
    )
    OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE = env_str(
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE", ""
    )
    validate_ibkr_runtime_config()


def load_config() -> None:
    load_dotenv()
    refresh_config_from_env()


ALLOWED_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "MSTR"]
