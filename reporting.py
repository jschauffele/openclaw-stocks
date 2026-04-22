from config import (
    OPENCLAW_SYMBOL,
    OPENCLAW_QTY,
    OPENCLAW_ENABLED,
    OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
    OPENCLAW_MAX_POSITION_SIZE,
    ALLOWED_SYMBOLS,
    ALPACA_BASE_URL,
    RUN_REPORT_FILE,
)
from utils import utc_now_iso
from state_manager import write_run_report


def build_run_report(
    run_id: str,
    mode: str,
    result: str,
    reason: str,
    trigger_source: str,
    side: str,
    buying_power=None,
    estimated_cost=None,
    duplicate_age_seconds=None,
    order_status=None,
    notes=None,
    existing_position_qty=None,
    open_buy_order_qty=None,
    projected_position_qty=None,
) -> dict:
    return {
        "run_id": run_id,
        "timestamp": utc_now_iso(),
        "trigger_source": trigger_source,
        "result": result,
        "reason": reason,
        "symbol": OPENCLAW_SYMBOL,
        "side": side,
        "qty": OPENCLAW_QTY,
        "mode": mode,
        "openclaw_enabled": OPENCLAW_ENABLED,
        "cooldown_seconds": OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
        "max_position_size": OPENCLAW_MAX_POSITION_SIZE,
        "allowed_symbols": ALLOWED_SYMBOLS,
        "alpaca_base_url": ALPACA_BASE_URL,
        "buying_power": buying_power,
        "estimated_cost": estimated_cost,
        "duplicate_age_seconds": duplicate_age_seconds,
        "order_status": order_status,
        "existing_position_qty": existing_position_qty,
        "open_buy_order_qty": open_buy_order_qty,
        "projected_position_qty": projected_position_qty,
        "notes": notes or [],
    }


def persist_report(
    run_id: str,
    mode: str,
    result: str,
    reason: str,
    trigger_source: str,
    side: str,
    buying_power=None,
    estimated_cost=None,
    duplicate_age_seconds=None,
    order_status=None,
    notes=None,
    existing_position_qty=None,
    open_buy_order_qty=None,
    projected_position_qty=None,
) -> None:
    report = build_run_report(
        run_id=run_id,
        mode=mode,
        result=result,
        reason=reason,
        trigger_source=trigger_source,
        side=side,
        buying_power=buying_power,
        estimated_cost=estimated_cost,
        duplicate_age_seconds=duplicate_age_seconds,
        order_status=order_status,
        notes=notes,
        existing_position_qty=existing_position_qty,
        open_buy_order_qty=open_buy_order_qty,
        projected_position_qty=projected_position_qty,
    )
    write_run_report(report, RUN_REPORT_FILE)
