from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from broker_client import BrokerClient
from decision_engine import build_action_proposal
from event_logger import generate_run_id, initialize_event_logger, log_event
from execution_engine import get_market_session_status, submit_market_order
from market_data import MarketDataProvider, get_historical_bars
from reporting import persist_report_for_settings
from risk_engine import reconcile_position, risk_check, validate_config
from runtime_settings import RuntimeSettings
from signal_validator import validate_signal_result
from state_manager import duplicate_check_for_settings, write_order_state_for_settings
from strategy_engine import generate_signal_from_closes
from utils import utc_now_iso


class InsufficientMarketDataError(Exception):
    def __init__(self, available_closes: int, required_closes: int):
        super().__init__(
            "Need at least "
            f"{required_closes} closing prices to generate a signal; got {available_closes}"
        )
        self.available_closes = available_closes
        self.required_closes = required_closes


@dataclass
class OpenClawBot:
    settings: RuntimeSettings
    trading_client_factory: Callable[[], BrokerClient]
    market_data_provider_factory: Callable[[], MarketDataProvider]

    def run(self) -> None:
        run_id = generate_run_id()
        initialize_event_logger(run_id)
        side = "buy"
        buying_power = None
        final_event_status = "error"
        final_event_payload = {
            "result": "error",
            "reason": "run_interrupted",
            "order_submitted": False,
            "symbol": self.settings.symbol,
            "qty": self.settings.qty,
        }

        try:
            self._log_run_start(run_id)
            self._safe_log_event(
                event_type="run_started",
                stage="run_lifecycle",
                status="ok",
                payload={
                    "trigger_source": self.settings.trigger_source,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                    "mode": self.settings.mode,
                    "dry_run": self.settings.dry_run,
                },
            )
            self._safe_log_event(
                event_type="config_loaded",
                stage="config",
                status="ok",
                payload={
                    "openclaw_enabled": self.settings.openclaw_enabled,
                    "dry_run": self.settings.dry_run,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                    "max_position_size": self.settings.max_position_size,
                    "duplicate_cooldown_seconds": self.settings.duplicate_cooldown_seconds,
                    "allowed_symbols": list(self.settings.allowed_symbols),
                },
            )

            client = self.trading_client_factory()

            if not self.settings.openclaw_enabled:
                logging.warning("OPENCLAW_ENABLED is false — bot execution disabled")
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": "block_run",
                        "reason": "killswitch_disabled",
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": "killswitch_disabled",
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason="killswitch_disabled",
                    side=side,
                    notes=["OPENCLAW_ENABLED=false"],
                )
                return

            if not validate_config(
                alpaca_api_key=self.settings.alpaca_api_key,
                alpaca_secret_key=self.settings.alpaca_secret_key,
                qty=self.settings.qty,
                max_position_size=self.settings.max_position_size,
                duplicate_cooldown_seconds=self.settings.duplicate_cooldown_seconds,
            ):
                logging.error("Configuration validation failed")
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="error",
                    payload={
                        "final_decision": "block_run",
                        "reason": "config_validation_failed",
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "error"
                final_event_payload = {
                    "result": "error",
                    "reason": "config_validation_failed",
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="error",
                    reason="config_validation_failed",
                    side=side,
                    notes=["Configuration validation failed before market data lookup"],
                )
                return

            try:
                market_status = get_market_session_status(client)
                self._safe_log_event(
                    event_type="market_checked",
                    stage="market_guard",
                    status="ok" if market_status["is_open"] else "blocked",
                    payload={
                        "is_open": market_status.get("is_open"),
                        "reason": market_status.get("reason"),
                        "current_time": market_status.get("current_time"),
                        "session_open": market_status.get("session_open"),
                        "session_close": market_status.get("session_close"),
                        "next_open": market_status.get("next_open"),
                        "next_close": market_status.get("next_close"),
                    },
                )
            except Exception as exc:
                self._safe_log_event(
                    event_type="market_checked",
                    stage="market_guard",
                    status="error",
                    payload={"error": str(exc)},
                )
                raise

            if not market_status["is_open"]:
                logging.warning(f"Market closed — blocking run: {market_status['reason']}")
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": "block_run",
                        "reason": market_status["reason"],
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": market_status["reason"],
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason=market_status["reason"],
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
                return

            try:
                action_proposal, bars_warnings = self._run_strategy_pipeline()
            except InsufficientMarketDataError as exc:
                logging.warning("Strategy skipped due to insufficient market data")
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": "block_run",
                        "reason": "insufficient_market_data",
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": "insufficient_market_data",
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason="insufficient_market_data",
                    side=side,
                    notes=[
                        str(exc),
                        f"required_closes={exc.required_closes}",
                        f"available_closes={exc.available_closes}",
                    ],
                )
                return
            except Exception as exc:
                logging.exception("Strategy pipeline failed")
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="error",
                    payload={
                        "final_decision": "block_run",
                        "reason": "strategy_pipeline_failed",
                        "error": str(exc),
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "error"
                final_event_payload = {
                    "result": "error",
                    "reason": "strategy_pipeline_failed",
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                    "error": str(exc),
                }
                self._persist_report(
                    run_id=run_id,
                    result="error",
                    reason="strategy_pipeline_failed",
                    side=side,
                    notes=[str(exc)],
                )
                return

            for warning in bars_warnings:
                logging.warning(f"Market data warning: {warning}")

            logging.info(
                "Strategy pipeline completed: "
                f"signal={action_proposal['signal']}, "
                f"decision={action_proposal['decision']}, "
                f"action={action_proposal['action']}, "
                f"reason={action_proposal['reason']}"
            )

            if not action_proposal["should_submit"]:
                logging.info(
                    "Strategy proposed no order submission: "
                    f"action={action_proposal['action']}, reason={action_proposal['reason']}"
                )
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": action_proposal["action"],
                        "reason": "strategy_hold",
                        "signal": action_proposal["signal"],
                        "decision": action_proposal["decision"],
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": "strategy_hold",
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason="strategy_hold",
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
                return

            try:
                account = client.get_account()
                buying_power = account.buying_power
                logging.info(f"Account buying power: {buying_power}")
                self._safe_log_event(
                    event_type="account_checked",
                    stage="account",
                    status="ok",
                    payload={"buying_power": buying_power},
                )
            except Exception as exc:
                self._safe_log_event(
                    event_type="account_checked",
                    stage="account",
                    status="error",
                    payload={"error": str(exc)},
                )
                raise

            duplicate_result = duplicate_check_for_settings(
                self.settings,
                self.settings.symbol,
                side,
                self.settings.qty,
            )
            self._safe_log_event(
                event_type="duplicate_checked",
                stage="duplicate",
                status="blocked" if duplicate_result["is_duplicate"] else "ok",
                payload={
                    "is_duplicate": duplicate_result.get("is_duplicate"),
                    "reason": duplicate_result.get("reason"),
                    "age_seconds": duplicate_result.get("age_seconds"),
                },
            )
            if duplicate_result["is_duplicate"]:
                logging.warning(
                    "Duplicate protection blocked current order attempt: "
                    f"symbol={self.settings.symbol}, side={side}, qty={self.settings.qty}"
                )
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": "block_run",
                        "reason": duplicate_result["reason"],
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": duplicate_result["reason"],
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason=duplicate_result["reason"],
                    side=side,
                    buying_power=buying_power,
                    duplicate_age_seconds=duplicate_result["age_seconds"],
                    notes=[
                        "Duplicate protection blocked current order attempt",
                        f"Strategy reason={action_proposal['reason']}",
                    ],
                )
                return

            risk_result = risk_check(
                self.settings.symbol,
                self.settings.qty,
                buying_power,
                max_position_size=self.settings.max_position_size,
                allowed_symbols=self.settings.allowed_symbols,
            )
            self._safe_log_event(
                event_type="risk_checked",
                stage="risk",
                status="ok" if risk_result["passed"] else "blocked",
                payload={
                    "passed": risk_result.get("passed"),
                    "reason": risk_result.get("reason"),
                    "message": risk_result.get("message"),
                    "estimated_cost": risk_result.get("estimated_cost"),
                },
            )
            if not risk_result["passed"]:
                logging.info("REJECTED — no order sent")
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": "block_run",
                        "reason": risk_result["reason"],
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": risk_result["reason"],
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason=risk_result["reason"],
                    side=side,
                    buying_power=buying_power,
                    estimated_cost=risk_result["estimated_cost"],
                    notes=[
                        risk_result["message"],
                        f"Strategy reason={action_proposal['reason']}",
                    ],
                )
                return

            reconciliation_result = reconcile_position(
                client,
                self.settings.symbol,
                self.settings.qty,
                self.settings.max_position_size,
            )
            self._safe_log_event(
                event_type="reconciliation_checked",
                stage="reconciliation",
                status="ok" if reconciliation_result["passed"] else "blocked",
                payload={
                    "passed": reconciliation_result.get("passed"),
                    "reason": reconciliation_result.get("reason"),
                    "message": reconciliation_result.get("message"),
                    "existing_qty": reconciliation_result.get("existing_qty"),
                    "open_buy_order_qty": reconciliation_result.get("open_buy_order_qty"),
                    "projected_qty": reconciliation_result.get("projected_qty"),
                },
            )
            if not reconciliation_result["passed"]:
                logging.warning(
                    "Broker reconciliation blocked current order attempt: "
                    f"symbol={self.settings.symbol}, requested_qty={self.settings.qty}"
                )
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="blocked",
                    payload={
                        "final_decision": "block_run",
                        "reason": reconciliation_result["reason"],
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                    },
                )
                final_event_status = "blocked"
                final_event_payload = {
                    "result": "blocked",
                    "reason": reconciliation_result["reason"],
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                self._persist_report(
                    run_id=run_id,
                    result="blocked",
                    reason=reconciliation_result["reason"],
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
                return

            state_record = self._build_state_record(run_id, side)

            if self.settings.dry_run:
                logging.info("DRY RUN ENABLED — order was NOT submitted")
                logging.info(
                    f"Simulated order: symbol={self.settings.symbol}, qty={self.settings.qty}, "
                    "side=buy, tif=day"
                )
                self._safe_log_event(
                    event_type="decision_made",
                    stage="decision",
                    status="ok",
                    payload={
                        "final_decision": "dry_run_completed",
                        "reason": action_proposal["reason"],
                        "signal": action_proposal["signal"],
                        "decision": action_proposal["decision"],
                        "symbol": self.settings.symbol,
                        "qty": self.settings.qty,
                        "order_submitted": False,
                    },
                )
                final_event_status = "ok"
                final_event_payload = {
                    "result": "success",
                    "reason": "dry_run_completed",
                    "order_submitted": False,
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                }
                write_order_state_for_settings(self.settings, state_record)
                self._persist_report(
                    run_id=run_id,
                    result="success",
                    reason="dry_run_completed",
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
                return

            self._safe_log_event(
                event_type="decision_made",
                stage="decision",
                status="ok",
                payload={
                    "final_decision": "submit_order",
                    "reason": action_proposal["reason"],
                    "signal": action_proposal["signal"],
                    "decision": action_proposal["decision"],
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                    "order_submitted": True,
                },
            )
            response = submit_market_order(
                client,
                symbol=self.settings.symbol,
                qty=self.settings.qty,
                side=side,
            )
            self._safe_log_event(
                event_type="order_submitted",
                stage="execution",
                status="ok",
                payload={
                    "symbol": self.settings.symbol,
                    "qty": self.settings.qty,
                    "side": side,
                    "order_status": str(response.status),
                },
            )
            final_event_status = "ok"
            final_event_payload = {
                "result": "success",
                "reason": "paper_order_submitted",
                "order_submitted": True,
                "symbol": self.settings.symbol,
                "qty": self.settings.qty,
                "order_status": str(response.status),
            }
            write_order_state_for_settings(self.settings, state_record)
            self._persist_report(
                run_id=run_id,
                result="success",
                reason="paper_order_submitted",
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
        finally:
            self._safe_log_event(
                event_type="run_completed",
                stage="run_lifecycle",
                status=final_event_status,
                payload=final_event_payload,
            )
            self._finish_run()

    def _run_strategy_pipeline(self) -> tuple[dict, tuple[str, ...]]:
        provider = self.market_data_provider_factory()
        try:
            bars_result = get_historical_bars(
                provider=provider,
                symbol=self.settings.symbol,
                timeframe=self.settings.signal_timeframe,
                limit=self.settings.signal_limit,
            )
        except Exception as exc:
            self._safe_log_event(
                event_type="data_fetched",
                stage="market_data",
                status="error",
                payload={
                    "symbol": self.settings.symbol,
                    "error": str(exc),
                },
            )
            raise

        closes = [candle.close for candle in bars_result.candles]
        self._safe_log_event(
            event_type="data_fetched",
            stage="market_data",
            status="ok" if len(closes) >= 2 else "blocked",
            payload={
                "symbol": self.settings.symbol,
                "timeframe": self.settings.signal_timeframe,
                "limit": self.settings.signal_limit,
                "close_count": len(closes),
                "previous_close": closes[-2] if len(closes) >= 2 else None,
                "latest_close": closes[-1] if closes else None,
                "warnings": list(bars_result.warnings),
            },
        )
        if len(closes) < 2:
            raise InsufficientMarketDataError(
                available_closes=len(closes),
                required_closes=2,
            )

        try:
            raw_signal_result = generate_signal_from_closes(closes)
            signal_result = validate_signal_result(raw_signal_result)
            action_proposal = build_action_proposal(
                symbol=self.settings.symbol,
                qty=self.settings.qty,
                signal_result=signal_result,
            )
        except Exception as exc:
            self._safe_log_event(
                event_type="strategy_evaluated",
                stage="strategy",
                status="error",
                payload={
                    "symbol": self.settings.symbol,
                    "error": str(exc),
                },
            )
            raise

        self._safe_log_event(
            event_type="strategy_evaluated",
            stage="strategy",
            status="ok" if action_proposal["should_submit"] else "blocked",
            payload={
                "symbol": self.settings.symbol,
                "signal": action_proposal["signal"],
                "decision": action_proposal["decision"],
                "action": action_proposal["action"],
                "reason": action_proposal["reason"],
                "should_submit": action_proposal["should_submit"],
                "previous_close": action_proposal["previous_close"],
                "latest_close": action_proposal["latest_close"],
                "price_delta": action_proposal["price_delta"],
                "percent_change": action_proposal["percent_change"],
            },
        )
        return action_proposal, bars_result.warnings

    def _build_state_record(self, run_id: str, side: str) -> dict:
        return {
            "run_id": run_id,
            "timestamp": utc_now_iso(),
            "symbol": self.settings.symbol,
            "side": side,
            "qty": self.settings.qty,
            "mode": self.settings.mode,
        }

    def _persist_report(
        self,
        run_id: str,
        result: str,
        reason: str,
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
        persist_report_for_settings(
            self.settings,
            run_id=run_id,
            mode=self.settings.mode,
            result=result,
            reason=reason,
            trigger_source=self.settings.trigger_source,
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

    def _safe_log_event(
        self,
        event_type: str,
        stage: str,
        status: str,
        payload: dict,
    ) -> None:
        try:
            log_event(
                event_type=event_type,
                stage=stage,
                status=status,
                payload=payload,
            )
        except Exception:
            pass

    def _log_run_start(self, run_id: str) -> None:
        logging.info("========== OpenClaw run started ==========")
        logging.info(f"run_id={run_id}")
        logging.info(f"Base directory: {self.settings.base_dir}")
        logging.info(f"Log file: {self.settings.log_file}")
        logging.info(f"State file: {self.settings.state_file}")
        logging.info(f"Run report file: {self.settings.run_report_file}")
        logging.info(f"Legacy duplicate file: {self.settings.legacy_last_order_file}")
        logging.info(f"ALPACA_BASE_URL={self.settings.alpaca_base_url}")
        logging.info(f"OPENCLAW_ENABLED={self.settings.openclaw_enabled}")
        logging.info(f"OPENCLAW_DRY_RUN={self.settings.dry_run}")
        logging.info(f"OPENCLAW_SYMBOL={self.settings.symbol}")
        logging.info(f"OPENCLAW_QTY={self.settings.qty}")
        logging.info(f"OPENCLAW_MAX_POSITION_SIZE={self.settings.max_position_size}")
        logging.info(f"OPENCLAW_TRIGGER_SOURCE={self.settings.trigger_source}")
        logging.info(f"OPENCLAW_SIGNAL_TIMEFRAME={self.settings.signal_timeframe}")
        logging.info(f"OPENCLAW_SIGNAL_LIMIT={self.settings.signal_limit}")
        logging.info(
            "OPENCLAW_DUPLICATE_COOLDOWN_SECONDS="
            f"{self.settings.duplicate_cooldown_seconds}"
        )

    @staticmethod
    def _finish_run() -> None:
        logging.info("========== OpenClaw run finished ==========")
