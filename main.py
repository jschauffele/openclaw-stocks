from event_logger import initialize_event_logger, generate_run_id, log_event
import logging

from alpaca.trading.enums import OrderSide, TimeInForce

from alpaca_data_provider import AlpacaMarketDataProvider
import config
from decision_engine import build_action_proposal
from execution_engine import (
    get_market_session_status,
    build_market_order,
    submit_market_order,
)
from market_data import get_historical_bars
from risk_engine import validate_config, risk_check, reconcile_position
from signal_validator import validate_signal_result
from strategy_engine import generate_signal_from_closes
from utils import setup_logging, utc_now_iso


class InsufficientMarketDataError(Exception):
    def __init__(self, available_closes: int, required_closes: int):
        super().__init__(
            "Need at least "
            f"{required_closes} closing prices to generate a signal; got {available_closes}"
        )
        self.available_closes = available_closes
        self.required_closes = required_closes


def main():
    config.load_config()

    from client_factory import create_trading_client
    from reporting import persist_report
    from state_manager import duplicate_check, write_order_state

    BASE_DIR = config.BASE_DIR
    LOG_FILE = config.LOG_FILE
    STATE_FILE = config.STATE_FILE
    RUN_REPORT_FILE = config.RUN_REPORT_FILE
    LEGACY_LAST_ORDER_FILE = config.LEGACY_LAST_ORDER_FILE
    OPENCLAW_ENABLED = config.OPENCLAW_ENABLED
    OPENCLAW_DRY_RUN = config.OPENCLAW_DRY_RUN
    OPENCLAW_SYMBOL = config.OPENCLAW_SYMBOL
    OPENCLAW_QTY = config.OPENCLAW_QTY
    OPENCLAW_MAX_POSITION_SIZE = config.OPENCLAW_MAX_POSITION_SIZE
    OPENCLAW_DUPLICATE_COOLDOWN_SECONDS = config.OPENCLAW_DUPLICATE_COOLDOWN_SECONDS
    ALPACA_API_KEY = config.ALPACA_API_KEY
    ALPACA_SECRET_KEY = config.ALPACA_SECRET_KEY
    ALPACA_BASE_URL = config.ALPACA_BASE_URL
    ALLOWED_SYMBOLS = config.ALLOWED_SYMBOLS
    env_str = config.env_str
    env_int = config.env_int

    setup_logging(LOG_FILE)
    client = create_trading_client(ALPACA_API_KEY, ALPACA_SECRET_KEY)

    run_id = generate_run_id()
    initialize_event_logger(run_id)
    log_event("system", "startup", "ok", {"message": "run_started"})
    side = OrderSide.BUY.value
    mode = "dry_run" if OPENCLAW_DRY_RUN else "paper_submit"
    trigger_source = env_str("OPENCLAW_TRIGGER_SOURCE", "manual_or_systemd")
    signal_timeframe = env_str("OPENCLAW_SIGNAL_TIMEFRAME", "1Day")
    signal_limit = env_int("OPENCLAW_SIGNAL_LIMIT", 5)

    logging.info("========== OpenClaw run started ==========")
    logging.info(f"run_id={run_id}")
    logging.info(f"Base directory: {BASE_DIR}")
    logging.info(f"Log file: {LOG_FILE}")
    logging.info(f"State file: {STATE_FILE}")
    logging.info(f"Run report file: {RUN_REPORT_FILE}")
    logging.info(f"Legacy duplicate file: {LEGACY_LAST_ORDER_FILE}")
    logging.info(f"ALPACA_BASE_URL={ALPACA_BASE_URL}")
    logging.info(f"OPENCLAW_ENABLED={OPENCLAW_ENABLED}")
    logging.info(f"OPENCLAW_DRY_RUN={OPENCLAW_DRY_RUN}")
    logging.info(f"OPENCLAW_SYMBOL={OPENCLAW_SYMBOL}")
    logging.info(f"OPENCLAW_QTY={OPENCLAW_QTY}")
    logging.info(f"OPENCLAW_MAX_POSITION_SIZE={OPENCLAW_MAX_POSITION_SIZE}")
    logging.info(f"OPENCLAW_TRIGGER_SOURCE={trigger_source}")
    logging.info(f"OPENCLAW_SIGNAL_TIMEFRAME={signal_timeframe}")
    logging.info(f"OPENCLAW_SIGNAL_LIMIT={signal_limit}")
    logging.info(
        "OPENCLAW_DUPLICATE_COOLDOWN_SECONDS="
        f"{OPENCLAW_DUPLICATE_COOLDOWN_SECONDS}"
    )

    if not OPENCLAW_ENABLED:
        logging.warning("OPENCLAW_ENABLED is false — bot execution disabled")
        log_event("system", "killswitch", "blocked", {"openclaw_enabled": False})
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason="killswitch_disabled",
            trigger_source=trigger_source,
            side=side,
            notes=["OPENCLAW_ENABLED=false"],
        )
        log_event("system", "completion", "blocked", {"reason": "killswitch_disabled"})
        logging.info("========== OpenClaw run finished ==========")
        return

    if not validate_config(
        alpaca_api_key=ALPACA_API_KEY,
        alpaca_secret_key=ALPACA_SECRET_KEY,
        qty=OPENCLAW_QTY,
        max_position_size=OPENCLAW_MAX_POSITION_SIZE,
        duplicate_cooldown_seconds=OPENCLAW_DUPLICATE_COOLDOWN_SECONDS,
    ):
        logging.error("Configuration validation failed")
        log_event("system", "config", "invalid", {"reason": "config_validation_failed"})
        persist_report(
            run_id=run_id,
            mode=mode,
            result="error",
            reason="config_validation_failed",
            trigger_source=trigger_source,
            side=side,
            notes=["Configuration validation failed before market data lookup"],
        )
        log_event("system", "completion", "error", {"reason": "config_validation_failed"})
        logging.info("========== OpenClaw run finished ==========")
        return

    log_event("system", "config", "ok", {"message": "config_validation_passed"})

    market_status = get_market_session_status(client)
    if not market_status["is_open"]:
        logging.warning(f"Market closed — blocking run: {market_status['reason']}")
        log_event(
            "system",
            "market_session",
            "blocked",
            {
                "reason": market_status["reason"],
                "current_time": market_status.get("current_time"),
                "session_open": market_status.get("session_open"),
                "session_close": market_status.get("session_close"),
                "next_open": market_status.get("next_open"),
                "next_close": market_status.get("next_close"),
            },
        )
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason=market_status["reason"],
            trigger_source=trigger_source,
            side=side,
            notes=[
                f"Blocked due to market session status: {market_status['reason']}",
                f"current_time={market_status.get('current_time')}",
                f"session_open={market_status.get('session_open')}",
                f"session_close={market_status.get('session_close')}",
                f"next_open={market_status.get('next_open')}",
                f"next_close={market_status.get('next_close')}",
            ],
        )
        log_event("system", "completion", "blocked", {"reason": market_status["reason"]})
        logging.info("========== OpenClaw run finished ==========")
        return

    log_event("system", "market_session", "open", {"reason": market_status.get("reason")})

    try:
        provider = AlpacaMarketDataProvider()
        bars_result = get_historical_bars(
            provider=provider,
            symbol=OPENCLAW_SYMBOL,
            timeframe=signal_timeframe,
            limit=signal_limit,
        )
        closes = [candle.close for candle in bars_result.candles]
        if len(closes) < 2:
            raise InsufficientMarketDataError(
                available_closes=len(closes),
                required_closes=2,
            )
        raw_signal_result = generate_signal_from_closes(closes)
        signal_result = validate_signal_result(raw_signal_result)
        action_proposal = build_action_proposal(
            symbol=OPENCLAW_SYMBOL,
            qty=OPENCLAW_QTY,
            signal_result=signal_result,
        )
    except InsufficientMarketDataError as exc:
        logging.warning("Strategy skipped due to insufficient market data")
        log_event("data", "fetch", "insufficient", {"symbol": OPENCLAW_SYMBOL, "error": str(exc)})
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason="insufficient_market_data",
            trigger_source=trigger_source,
            side=side,
            notes=[
                str(exc),
                f"required_closes={exc.required_closes}",
                f"available_closes={exc.available_closes}",
            ],
        )
        log_event("system", "completion", "blocked", {"reason": "insufficient_market_data"})
        logging.info("========== OpenClaw run finished ==========")
        return
    except Exception as exc:
        logging.exception("Strategy pipeline failed")
        log_event("data", "fetch", "error", {"symbol": OPENCLAW_SYMBOL, "error": str(exc)})
        persist_report(
            run_id=run_id,
            mode=mode,
            result="error",
            reason="strategy_pipeline_failed",
            trigger_source=trigger_source,
            side=side,
            notes=[str(exc)],
        )
        log_event("system", "completion", "error", {"reason": "strategy_pipeline_failed"})
        logging.info("========== OpenClaw run finished ==========")
        return

    if bars_result.warnings:
        for warning in bars_result.warnings:
            logging.warning(f"Market data warning: {warning}")

    log_event(
        "data",
        "fetch",
        "ok",
        {
            "symbol": OPENCLAW_SYMBOL,
            "candles": len(bars_result.candles),
        },
    )
    logging.info(
        "Strategy pipeline completed: "
        f"signal={action_proposal['signal']}, "
        f"decision={action_proposal['decision']}, "
        f"action={action_proposal['action']}, "
        f"reason={action_proposal['reason']}"
    )
    log_event(
        "strategy",
        "signal_evaluation",
        "ok",
        {
            "signal": action_proposal.get("signal"),
            "decision": action_proposal.get("decision"),
            "action": action_proposal.get("action"),
            "reason": action_proposal.get("reason"),
        },
    )

    if not action_proposal["should_submit"]:
        logging.info(
            "Strategy proposed no order submission: "
            f"action={action_proposal['action']}, reason={action_proposal['reason']}"
        )
        log_event(
            "strategy",
            "signal_evaluation",
            "blocked",
            {
                "action": action_proposal.get("action"),
                "reason": action_proposal.get("reason"),
            },
        )
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason="strategy_hold",
            trigger_source=trigger_source,
            side=side,
            notes=[
                f"Strategy action={action_proposal['action']}",
                f"Strategy reason={action_proposal['reason']}",
                f"previous_close={action_proposal['previous_close']}",
                f"latest_close={action_proposal['latest_close']}",
                f"price_delta={action_proposal['price_delta']}",
                f"percent_change={action_proposal['percent_change']}",
            ],
        )
        log_event("system", "completion", "blocked", {"reason": "strategy_hold"})
        logging.info("========== OpenClaw run finished ==========")
        return

    account = client.get_account()
    buying_power = float(account.buying_power)
    logging.info(f"Account buying power: {buying_power}")

    duplicate_result = duplicate_check(OPENCLAW_SYMBOL, side, OPENCLAW_QTY)
    if duplicate_result["is_duplicate"]:
        logging.warning(
            "Duplicate protection blocked current order attempt: "
            f"symbol={OPENCLAW_SYMBOL}, side={side}, qty={OPENCLAW_QTY}"
        )
        log_event("order", "duplicate_check", "blocked", {"symbol": OPENCLAW_SYMBOL, "reason": duplicate_result["reason"]})
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason=duplicate_result["reason"],
            trigger_source=trigger_source,
            side=side,
            buying_power=buying_power,
            duplicate_age_seconds=duplicate_result["age_seconds"],
            notes=[
                "Duplicate protection blocked current order attempt",
                f"Strategy reason={action_proposal['reason']}",
            ],
        )
        log_event("system", "completion", "blocked", {"reason": duplicate_result["reason"]})
        logging.info("========== OpenClaw run finished ==========")
        return

    log_event("order", "duplicate_check", "clear", {"symbol": OPENCLAW_SYMBOL})

    risk_result = risk_check(
        OPENCLAW_SYMBOL,
        OPENCLAW_QTY,
        buying_power,
        action_proposal["latest_close"],
        max_position_size=OPENCLAW_MAX_POSITION_SIZE,
        allowed_symbols=ALLOWED_SYMBOLS,
    )
    log_event(
        "risk",
        "risk_check",
        "ok" if risk_result.get("passed") else "blocked",
        {
            "passed": risk_result.get("passed"),
            "reason": risk_result.get("reason"),
            "symbol": OPENCLAW_SYMBOL,
            "qty": OPENCLAW_QTY,
        },
    )
    if not risk_result["passed"]:
        logging.info("REJECTED — no order sent")
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason=risk_result["reason"],
            trigger_source=trigger_source,
            side=side,
            buying_power=buying_power,
            estimated_cost=risk_result["estimated_cost"],
            notes=[
                risk_result["message"],
                f"Strategy reason={action_proposal['reason']}",
            ],
        )
        log_event("system", "completion", "blocked", {"reason": risk_result["reason"]})
        logging.info("========== OpenClaw run finished ==========")
        return

    reconciliation_result = reconcile_position(
        client,
        OPENCLAW_SYMBOL,
        OPENCLAW_QTY,
        OPENCLAW_MAX_POSITION_SIZE,
    )
    if not reconciliation_result["passed"]:
        logging.warning(
            "Broker reconciliation blocked current order attempt: "
            f"symbol={OPENCLAW_SYMBOL}, requested_qty={OPENCLAW_QTY}"
        )
        log_event("position", "reconcile", "mismatch", {
            "symbol": OPENCLAW_SYMBOL,
            "broker_qty": reconciliation_result["existing_qty"],
            "open_buy_order_qty": reconciliation_result["open_buy_order_qty"],
            "projected_qty": reconciliation_result["projected_qty"],
            "reason": reconciliation_result["reason"],
        })
        persist_report(
            run_id=run_id,
            mode=mode,
            result="blocked",
            reason=reconciliation_result["reason"],
            trigger_source=trigger_source,
            side=side,
            buying_power=buying_power,
            estimated_cost=risk_result["estimated_cost"],
            existing_position_qty=reconciliation_result["existing_qty"],
            open_buy_order_qty=reconciliation_result["open_buy_order_qty"],
            projected_position_qty=reconciliation_result["projected_qty"],
            notes=[
                reconciliation_result["message"],
                f"Strategy reason={action_proposal['reason']}",
            ],
        )
        log_event("system", "completion", "blocked", {"reason": reconciliation_result["reason"]})
        logging.info("========== OpenClaw run finished ==========")
        return

    log_event("position", "reconcile", "ok", {
        "symbol": OPENCLAW_SYMBOL,
        "broker_qty": reconciliation_result["existing_qty"],
        "open_buy_order_qty": reconciliation_result["open_buy_order_qty"],
        "projected_qty": reconciliation_result["projected_qty"],
    })

    order = build_market_order(OPENCLAW_SYMBOL, OPENCLAW_QTY)

    state_record = {
        "run_id": run_id,
        "timestamp": utc_now_iso(),
        "symbol": OPENCLAW_SYMBOL,
        "side": side,
        "qty": OPENCLAW_QTY,
        "mode": mode,
    }

    if OPENCLAW_DRY_RUN:
        logging.info("DRY RUN ENABLED — order was NOT submitted")
        logging.info(
            f"Simulated order: symbol={OPENCLAW_SYMBOL}, qty={OPENCLAW_QTY}, "
            f"side={OrderSide.BUY}, tif={TimeInForce.DAY}"
        )
        log_event("order", "submission", "dry_run", {
            "symbol": OPENCLAW_SYMBOL,
            "qty": OPENCLAW_QTY,
            "side": side,
            "mode": "dry_run",
        })
        write_order_state(state_record)
        persist_report(
            run_id=run_id,
            mode=mode,
            result="success",
            reason="dry_run_completed",
            trigger_source=trigger_source,
            side=side,
            buying_power=buying_power,
            estimated_cost=risk_result["estimated_cost"],
            existing_position_qty=reconciliation_result["existing_qty"],
            open_buy_order_qty=reconciliation_result["open_buy_order_qty"],
            projected_position_qty=reconciliation_result["projected_qty"],
            notes=[
                "Dry run completed successfully; no live paper order submitted",
                f"Strategy reason={action_proposal['reason']}",
                f"signal={action_proposal['signal']}",
                f"decision={action_proposal['decision']}",
            ],
        )
        log_event("system", "completion", "ok", {"reason": "dry_run_completed"})
        logging.info("========== OpenClaw run finished ==========")
        return

    try:
        response = submit_market_order(client, order)
    except Exception as exc:
        log_event("order", "submission", "error", {
            "symbol": OPENCLAW_SYMBOL,
            "qty": OPENCLAW_QTY,
            "error": str(exc),
        })
        logging.exception("Order submission failed")
        log_event("system", "completion", "error", {"reason": "order_submission_failed"})
        logging.info("========== OpenClaw run finished ==========")
        return

    log_event("order", "submission", "paper_submitted", {
        "symbol": OPENCLAW_SYMBOL,
        "qty": OPENCLAW_QTY,
        "side": side,
        "order_id": str(response.id),
        "mode": "paper_submit",
    })
    write_order_state(state_record)
    persist_report(
        run_id=run_id,
        mode=mode,
        result="success",
        reason="paper_order_submitted",
        trigger_source=trigger_source,
        side=side,
        buying_power=buying_power,
        estimated_cost=risk_result["estimated_cost"],
        order_status=str(response.status),
        existing_position_qty=reconciliation_result["existing_qty"],
        open_buy_order_qty=reconciliation_result["open_buy_order_qty"],
        projected_position_qty=reconciliation_result["projected_qty"],
        notes=[
            "Live paper order submitted successfully",
            f"Strategy reason={action_proposal['reason']}",
            f"signal={action_proposal['signal']}",
            f"decision={action_proposal['decision']}",
        ],
    )
    log_event("system", "completion", "ok", {"reason": "paper_order_submitted"})
    logging.info("========== OpenClaw run finished ==========")


if __name__ == "__main__":
    main()
