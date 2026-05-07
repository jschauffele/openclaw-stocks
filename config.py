import os
from dotenv import load_dotenv

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


def load_config() -> None:
    load_dotenv()
    refresh_config_from_env()


ALLOWED_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "MSTR"]
