"""Deterministic research signal runner for MSTR OHLCV rules."""

from __future__ import annotations

import ast
import math
from typing import Any

import pandas as pd

from mstr_bot import indicators


ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.UnaryOp,
    ast.BinOp,
    ast.Compare,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


def run_signal_rule(ohlcv: pd.DataFrame, rule_spec: dict[str, Any]) -> dict[str, Any]:
    frame = _prepare_ohlcv(ohlcv)
    enriched = _with_indicators(frame)
    entry_expr = str(rule_spec["entry"])
    exit_expr = str(rule_spec["exit"])
    _validate_expression(entry_expr)
    _validate_expression(exit_expr)

    trades: list[dict[str, Any]] = []
    position: dict[str, Any] | None = None
    equity = 1.0
    equity_curve = [equity]

    for index in range(len(enriched) - 1):
        row = enriched.iloc[index]
        next_row = enriched.iloc[index + 1]
        context = _context(row)
        if position is None:
            context.update({"return_since_entry": 0.0, "bars_held": 0})
            if _eval_rule(entry_expr, context):
                position = {
                    "entry_signal_date": row["date"],
                    "entry_date": next_row["date"],
                    "entry_price": float(next_row["open"]),
                    "entry_index": index + 1,
                }
        else:
            bars_held = index - int(position["entry_index"]) + 1
            return_since_entry = (float(row["close"]) / float(position["entry_price"])) - 1.0
            context.update({"return_since_entry": return_since_entry, "bars_held": bars_held})
            if _eval_rule(exit_expr, context):
                exit_price = float(next_row["open"])
                trade_return = (exit_price / float(position["entry_price"])) - 1.0
                equity *= 1.0 + trade_return
                equity_curve.append(equity)
                trades.append(
                    {
                        "entry_signal_date": _date_string(position["entry_signal_date"]),
                        "entry_date": _date_string(position["entry_date"]),
                        "entry_price": float(position["entry_price"]),
                        "exit_signal_date": _date_string(row["date"]),
                        "exit_date": _date_string(next_row["date"]),
                        "exit_price": exit_price,
                        "bars_held": int((index + 1) - int(position["entry_index"])),
                        "return": trade_return,
                    }
                )
                position = None

    return {
        "trades": trades,
        "summary": _summary(trades, equity_curve),
    }


def _prepare_ohlcv(ohlcv: pd.DataFrame) -> pd.DataFrame:
    required = ("date", "open", "high", "low", "close", "adj_close", "volume")
    missing = [column for column in required if column not in ohlcv.columns]
    if missing:
        raise ValueError(f"missing OHLCV columns: {missing}")
    frame = ohlcv.loc[:, required].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    frame = frame.sort_values("date", kind="mergesort").reset_index(drop=True)
    if frame["date"].duplicated().any():
        raise ValueError("duplicate OHLCV dates")
    for column in ("open", "high", "low", "close", "adj_close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if (frame[["open", "high", "low", "close", "adj_close"]] <= 0).any().any():
        raise ValueError("prices must be positive")
    if (frame["volume"] < 0).any():
        raise ValueError("volume must be non-negative")
    return frame


def _with_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    enriched["rsi_14"] = indicators.rsi(enriched["close"], 14)
    macd_frame = indicators.macd(enriched["close"], 12, 26, 9)
    bollinger_frame = indicators.bollinger(enriched["close"], 20, 2.0)
    enriched = pd.concat([enriched, macd_frame, bollinger_frame], axis=1)
    enriched["atr_14"] = indicators.atr(enriched["high"], enriched["low"], enriched["close"], 14)
    enriched["obv"] = indicators.obv(enriched["close"], enriched["volume"])
    enriched["volume_spike_20_2"] = indicators.volume_spike(enriched["volume"], 20, 2.0)
    enriched["sma_20"] = indicators.sma(enriched["close"], 20)
    enriched["ema_20"] = indicators.ema(enriched["close"], 20)
    enriched["vwap_proxy_20"] = indicators.vwap_proxy(
        enriched["high"],
        enriched["low"],
        enriched["close"],
        enriched["volume"],
        20,
    )
    return enriched


def _context(row: pd.Series) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key, value in row.items():
        if key == "date":
            continue
        if pd.isna(value):
            context[key] = math.nan
        elif isinstance(value, (bool, int, float)):
            context[key] = value
        else:
            context[key] = float(value)
    return context


def _validate_expression(expression: str) -> None:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValueError(f"disallowed rule expression node: {type(node).__name__}")


def _eval_rule(expression: str, context: dict[str, Any]) -> bool:
    tree = ast.parse(expression, mode="eval")
    code = compile(tree, "<rule_spec>", "eval")
    return bool(eval(code, {"__builtins__": {}}, context))  # noqa: S307 - restricted AST and no builtins.


def _summary(trades: list[dict[str, Any]], equity_curve: list[float]) -> dict[str, Any]:
    returns = [float(trade["return"]) for trade in trades]
    return {
        "trade_count": len(trades),
        "win_rate": None if not returns else sum(1 for value in returns if value > 0) / len(returns),
        "mean_return_per_trade": None if not returns else sum(returns) / len(returns),
        "median_return_per_trade": None if not returns else float(pd.Series(returns).median()),
        "total_return": equity_curve[-1] - 1.0,
        "max_drawdown": _max_drawdown(equity_curve),
        "avg_bars_held": None if not trades else sum(int(trade["bars_held"]) for trade in trades) / len(trades),
    }


def _max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        drawdown = (value / peak) - 1.0
        max_drawdown = min(max_drawdown, drawdown)
    return max_drawdown


def _date_string(value: Any) -> str:
    return pd.Timestamp(value).date().isoformat()
