from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import config


OBSERVATION_LOG_FILE = (
    Path(config.BASE_DIR) / "observations" / "observation_log.jsonl"
)
STALE_OBSERVATION_REPEAT_THRESHOLD = 3


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _minimum(values: list[float]) -> float:
    if not values:
        return 0.0
    return min(values)


def _maximum(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values)


def _float_value(row: dict, field: str) -> float | None:
    value = row.get(field)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stale_observation_warnings(
    rows: list[dict],
    repeat_threshold: int = STALE_OBSERVATION_REPEAT_THRESHOLD,
) -> list[dict]:
    repeated_metrics_by_symbol = defaultdict(Counter)
    for row in rows:
        symbol = str(row.get("symbol", "")).strip().upper()
        if not symbol:
            continue

        percent_change = _float_value(row, "percent_change")
        three_close_percent_change = _float_value(
            row,
            "three_close_percent_change",
        )
        if percent_change is None or three_close_percent_change is None:
            continue

        repeated_metrics_by_symbol[symbol][
            (percent_change, three_close_percent_change)
        ] += 1

    warnings = []
    for symbol in sorted(repeated_metrics_by_symbol):
        for metrics, count in repeated_metrics_by_symbol[symbol].items():
            if count >= repeat_threshold:
                warnings.append(
                    {
                        "warning": "POSSIBLE_STALE_DATA",
                        "symbol": symbol,
                        "count": count,
                        "percent_change": metrics[0],
                        "three_close_percent_change": metrics[1],
                    }
                )
    return warnings


def load_observations(log_file: str | Path = OBSERVATION_LOG_FILE) -> list[dict]:
    path = Path(log_file)
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def clean_observations(
    rows: list[dict],
    allowed_symbols: list[str] | tuple[str, ...] | None = None,
) -> list[dict]:
    symbol_source = (
        config.ALLOWED_SYMBOLS if allowed_symbols is None else allowed_symbols
    )
    allowed = {
        symbol.strip().upper()
        for symbol in symbol_source
        if symbol.strip()
    }
    seen_market_snapshots = set()
    cleaned_rows = []

    for row in rows:
        symbol = str(row.get("symbol", "")).strip().upper()
        if not symbol or symbol not in allowed:
            continue

        latest_candle_timestamp = row.get("latest_candle_timestamp")
        if latest_candle_timestamp:
            snapshot_key = (symbol, str(latest_candle_timestamp).strip())
            if snapshot_key in seen_market_snapshots:
                continue
            seen_market_snapshots.add(snapshot_key)

        cleaned_rows.append(row)

    return cleaned_rows


def summarize_observations(rows: list[dict]) -> dict:
    rows = clean_observations(rows)
    by_symbol = Counter()
    signals = Counter()
    percent_changes = []
    three_close_percent_changes = []
    percent_changes_by_symbol = defaultdict(list)
    three_close_percent_changes_by_symbol = defaultdict(list)
    buy_percent_changes = []
    buy_three_close_percent_changes = []
    buy_counts_by_symbol = Counter()
    buy_percent_changes_by_symbol = defaultdict(list)
    buy_three_close_percent_changes_by_symbol = defaultdict(list)
    stale_observation_warnings = _stale_observation_warnings(rows)

    for row in rows:
        symbol = str(row.get("symbol", "")).strip().upper()
        if symbol:
            by_symbol[symbol] += 1

        signal = str(row.get("signal", "")).strip().upper()
        if signal in ("BUY", "HOLD"):
            signals[signal] += 1
        is_buy = signal == "BUY"
        if is_buy and symbol:
            buy_counts_by_symbol[symbol] += 1

        percent_change = _float_value(row, "percent_change")
        if percent_change is not None:
            percent_changes.append(percent_change)
            if symbol:
                percent_changes_by_symbol[symbol].append(percent_change)
            if is_buy:
                buy_percent_changes.append(percent_change)
                if symbol:
                    buy_percent_changes_by_symbol[symbol].append(
                        percent_change
                    )

        three_close_percent_change = _float_value(
            row,
            "three_close_percent_change",
        )
        if three_close_percent_change is not None:
            three_close_percent_changes.append(three_close_percent_change)
            if symbol:
                three_close_percent_changes_by_symbol[symbol].append(
                    three_close_percent_change
                )
            if is_buy:
                buy_three_close_percent_changes.append(
                    three_close_percent_change
                )
                if symbol:
                    buy_three_close_percent_changes_by_symbol[symbol].append(
                        three_close_percent_change
                    )

    symbols = sorted(by_symbol)
    buy_symbols = sorted(buy_counts_by_symbol)
    return {
        "total": len(rows),
        "by_symbol": by_symbol,
        "signals": signals,
        "averages": {
            "percent_change": _average(percent_changes),
            "three_close_percent_change": _average(
                three_close_percent_changes
            ),
        },
        "distribution": {
            "percent_change": {
                "min": _minimum(percent_changes),
                "max": _maximum(percent_changes),
            },
            "three_close_percent_change": {
                "min": _minimum(three_close_percent_changes),
                "max": _maximum(three_close_percent_changes),
            },
        },
        "averages_by_symbol": {
            symbol: {
                "percent_change": _average(percent_changes_by_symbol[symbol]),
                "three_close_percent_change": _average(
                    three_close_percent_changes_by_symbol[symbol]
                ),
            }
            for symbol in symbols
        },
        "buy_only": {
            "count": signals.get("BUY", 0),
            "averages": {
                "percent_change": _average(buy_percent_changes),
                "three_close_percent_change": _average(
                    buy_three_close_percent_changes
                ),
            },
            "distribution": {
                "percent_change": {
                    "min": _minimum(buy_percent_changes),
                    "max": _maximum(buy_percent_changes),
                },
                "three_close_percent_change": {
                    "min": _minimum(buy_three_close_percent_changes),
                    "max": _maximum(buy_three_close_percent_changes),
                },
            },
            "by_symbol": {
                symbol: {
                    "count": buy_counts_by_symbol[symbol],
                    "percent_change": {
                        "avg": _average(
                            buy_percent_changes_by_symbol[symbol]
                        ),
                        "min": _minimum(
                            buy_percent_changes_by_symbol[symbol]
                        ),
                        "max": _maximum(
                            buy_percent_changes_by_symbol[symbol]
                        ),
                    },
                    "three_close_percent_change": {
                        "avg": _average(
                            buy_three_close_percent_changes_by_symbol[symbol]
                        ),
                        "min": _minimum(
                            buy_three_close_percent_changes_by_symbol[symbol]
                        ),
                        "max": _maximum(
                            buy_three_close_percent_changes_by_symbol[symbol]
                        ),
                    },
                }
                for symbol in buy_symbols
            },
        },
        "warnings": stale_observation_warnings,
    }


def format_summary(summary: dict) -> str:
    lines = [
        f"Total Observations: {summary['total']}",
        "",
        "By Symbol:",
    ]

    for symbol in sorted(summary["by_symbol"]):
        lines.append(f"{symbol}: {summary['by_symbol'][symbol]}")

    lines.extend(
        [
            "",
            "Signals:",
            f"BUY: {summary['signals'].get('BUY', 0)}",
            f"HOLD: {summary['signals'].get('HOLD', 0)}",
            "",
            "Averages:",
            "percent_change: "
            f"{summary['averages']['percent_change']:.4f}",
            "three_close_percent_change: "
            f"{summary['averages']['three_close_percent_change']:.4f}",
            "",
            "Distribution:",
            "percent_change: "
            f"min={summary['distribution']['percent_change']['min']:.4f}, "
            f"max={summary['distribution']['percent_change']['max']:.4f}",
            "three_close_percent_change: "
            "min="
            f"{summary['distribution']['three_close_percent_change']['min']:.4f}, "
            "max="
            f"{summary['distribution']['three_close_percent_change']['max']:.4f}",
        ]
    )

    averages_by_symbol = summary["averages_by_symbol"]
    if averages_by_symbol:
        lines.extend(["", "Averages By Symbol:"])
        for symbol in sorted(averages_by_symbol):
            averages = averages_by_symbol[symbol]
            lines.append(
                f"{symbol}: percent_change={averages['percent_change']:.4f}, "
                "three_close_percent_change="
                f"{averages['three_close_percent_change']:.4f}"
            )

    buy_only = summary["buy_only"]
    lines.extend(
        [
            "",
            "BUY-Only Metrics:",
            f"BUY Count: {buy_only['count']}",
            "Avg BUY percent_change: "
            f"{buy_only['averages']['percent_change']:.4f}",
            "Avg BUY three_close_percent_change: "
            f"{buy_only['averages']['three_close_percent_change']:.4f}",
            "",
            "BUY Distribution:",
            "percent_change: "
            f"min={buy_only['distribution']['percent_change']['min']:.4f}, "
            f"max={buy_only['distribution']['percent_change']['max']:.4f}",
            "three_close_percent_change: "
            "min="
            f"{buy_only['distribution']['three_close_percent_change']['min']:.4f}, "
            "max="
            f"{buy_only['distribution']['three_close_percent_change']['max']:.4f}",
            "",
            "BUY-Only By Symbol:",
        ]
    )

    for symbol in sorted(buy_only["by_symbol"]):
        metrics = buy_only["by_symbol"][symbol]
        lines.append(
            f"{symbol}: count={metrics['count']}, "
            "percent_change "
            f"avg={metrics['percent_change']['avg']:.4f} "
            f"min={metrics['percent_change']['min']:.4f} "
            f"max={metrics['percent_change']['max']:.4f}, "
            "three_close_percent_change "
            f"avg={metrics['three_close_percent_change']['avg']:.4f} "
            f"min={metrics['three_close_percent_change']['min']:.4f} "
            f"max={metrics['three_close_percent_change']['max']:.4f}"
        )

    if summary["warnings"]:
        lines.extend(["", "Warnings:"])
        for warning in summary["warnings"]:
            lines.append(
                f"{warning['warning']}: symbol={warning['symbol']} "
                f"count={warning['count']} "
                f"percent_change={warning['percent_change']:.4f} "
                "three_close_percent_change="
                f"{warning['three_close_percent_change']:.4f}"
            )

    return "\n".join(lines)


def main() -> None:
    rows = load_observations()
    if not rows:
        print("no observations yet")
        return

    print(format_summary(summarize_observations(rows)))


if __name__ == "__main__":
    main()
