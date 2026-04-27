from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import config


OBSERVATION_LOG_FILE = (
    Path(config.BASE_DIR) / "observations" / "observation_log.jsonl"
)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _float_value(row: dict, field: str) -> float | None:
    value = row.get(field)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def summarize_observations(rows: list[dict]) -> dict:
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
            "by_symbol": {
                symbol: {
                    "count": buy_counts_by_symbol[symbol],
                    "percent_change": _average(
                        buy_percent_changes_by_symbol[symbol]
                    ),
                    "three_close_percent_change": _average(
                        buy_three_close_percent_changes_by_symbol[symbol]
                    ),
                }
                for symbol in buy_symbols
            },
        },
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
            "BUY-Only By Symbol:",
        ]
    )

    for symbol in sorted(buy_only["by_symbol"]):
        metrics = buy_only["by_symbol"][symbol]
        lines.append(
            f"{symbol}: count={metrics['count']}, "
            f"percent_change={metrics['percent_change']:.4f}, "
            "three_close_percent_change="
            f"{metrics['three_close_percent_change']:.4f}"
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
