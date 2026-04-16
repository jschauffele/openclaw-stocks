from __future__ import annotations

from dataclasses import dataclass

from config import (
    BASE_DIR,
    LOG_FILE,
    STATE_FILE,
    RUN_REPORT_FILE,
    LEGACY_LAST_ORDER_FILE,
    OPENCLAW_ENABLED,
    OPENCLAW_DRY_RUN,
    OPENCLAW_SYMBOL,
    OPENCLAW_QTY,
    OPENCLAW_MAX_POSITION_SIZE,
    OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    ALPACA_BASE_URL,
    ALLOWED_SYMBOLS,
    env_str,
    env_int,
)


@dataclass(frozen=True)
class RuntimeSettings:
    base_dir: str
    log_file: str
    state_file: str
    run_report_file: str
    legacy_last_order_file: str
    openclaw_enabled: bool
    dry_run: bool
    symbol: str
    qty: int
    max_position_size: int
    duplicate_cooldown_seconds: int
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str
    allowed_symbols: tuple[str, ...]
    trigger_source: str
    signal_timeframe: str
    signal_limit: int

    @property
    def mode(self) -> str:
        return "dry_run" if self.dry_run else "paper_submit"


def load_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        base_dir=BASE_DIR,
        log_file=LOG_FILE,
        state_file=STATE_FILE,
        run_report_file=RUN_REPORT_FILE,
        legacy_last_order_file=LEGACY_LAST_ORDER_FILE,
        openclaw_enabled=OPENCLAW_ENABLED,
        dry_run=OPENCLAW_DRY_RUN,
        symbol=OPENCLAW_SYMBOL,
        qty=OPENCLAW_QTY,
        max_position_size=OPENCLAW_MAX_POSITION_SIZE,
        duplicate_cooldown_seconds=OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
        alpaca_api_key=ALPACA_API_KEY,
        alpaca_secret_key=ALPACA_SECRET_KEY,
        alpaca_base_url=ALPACA_BASE_URL,
        allowed_symbols=tuple(ALLOWED_SYMBOLS),
        trigger_source=env_str("OPENCLAW_TRIGGER_SOURCE", "manual_or_systemd"),
        signal_timeframe=env_str("OPENCLAW_SIGNAL_TIMEFRAME", "1Day"),
        signal_limit=env_int("OPENCLAW_SIGNAL_LIMIT", 5),
    )
