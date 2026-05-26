from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tools.evidence.three_close_evidence_scanner import CloseBar

CSV_REQUIRED_FIELDS = frozenset({"symbol", "timestamp", "close"})


@dataclass(frozen=True)
class EvidenceHistoricalCloseRequest:
    symbol: str
    timeframe: str
    start: str
    end: str
    max_bars: int | None = None

    def __post_init__(self) -> None:
        normalized_symbol = _normalize_required_text("symbol", self.symbol)
        normalized_timeframe = _normalize_required_text("timeframe", self.timeframe)
        normalized_start = _normalize_required_text("start", self.start)
        normalized_end = _normalize_required_text("end", self.end)
        if normalized_start >= normalized_end:
            raise ValueError("start must be before end")
        if self.max_bars is not None and self.max_bars <= 0:
            raise ValueError("max_bars must be positive when provided")

        object.__setattr__(self, "symbol", normalized_symbol.upper())
        object.__setattr__(self, "timeframe", normalized_timeframe)
        object.__setattr__(self, "start", normalized_start)
        object.__setattr__(self, "end", normalized_end)


class EvidenceHistoricalCloseProvider(Protocol):
    def get_close_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        max_bars: int | None,
    ) -> tuple[CloseBar, ...]:
        """Return close-only bars for future evidence review.

        This protocol defines only the dependency-injected seam. It is not a real
        provider implementation and does not approve evidence collection.
        """


class CsvStaticHistoricalCloseProvider:
    def __init__(self, input_path: str | Path) -> None:
        path = Path(input_path)
        if str(path).strip() == "":
            raise ValueError("input_path must be provided")
        if not path.exists():
            raise ValueError(f"input_path does not exist: {path}")
        if path.is_dir():
            raise ValueError("input_path must be a CSV file, not a directory")
        self.input_path = path

    def get_close_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        max_bars: int | None,
    ) -> tuple[CloseBar, ...]:
        request = EvidenceHistoricalCloseRequest(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            max_bars=max_bars,
        )
        bars: list[CloseBar] = []

        with self.input_path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            _validate_csv_fields(reader.fieldnames)
            for row_number, row in enumerate(reader, start=2):
                row_symbol = _csv_required_value(row, "symbol", row_number).upper()
                timestamp = _csv_required_value(row, "timestamp", row_number)
                close_raw = _csv_required_value(row, "close", row_number)
                if row_symbol != request.symbol:
                    continue
                if timestamp < request.start or timestamp > request.end:
                    continue

                try:
                    close = float(close_raw)
                except ValueError as exc:
                    raise ValueError(
                        f"CSV row {row_number} has invalid close: {close_raw}"
                    ) from exc

                bars.append(CloseBar(timestamp=timestamp, close=close))
                if request.max_bars is not None and len(bars) >= request.max_bars:
                    break

        return tuple(bars)


class AlpacaEvidenceHistoricalCloseProvider:
    def __init__(self, client: object) -> None:
        if client is None:
            raise ValueError("client must be provided")
        if not hasattr(client, "get_stock_bars"):
            raise ValueError("client must provide get_stock_bars")
        self.client = client

    def get_close_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        max_bars: int | None,
    ) -> tuple[CloseBar, ...]:
        request = EvidenceHistoricalCloseRequest(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            max_bars=max_bars,
        )
        raw_bars = self.client.get_stock_bars(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            limit=request.max_bars,
        )
        bars: list[CloseBar] = []
        for index, raw_bar in enumerate(raw_bars, start=1):
            timestamp = _alpaca_bar_required_value(raw_bar, "timestamp", index)
            close = _alpaca_bar_required_value(raw_bar, "close", index)
            bars.append(CloseBar(timestamp=str(timestamp), close=float(close)))
            if request.max_bars is not None and len(bars) >= request.max_bars:
                break
        return tuple(bars)


def get_close_bars_for_request(
    provider: EvidenceHistoricalCloseProvider,
    request: EvidenceHistoricalCloseRequest,
) -> tuple[CloseBar, ...]:
    bars = provider.get_close_bars(
        request.symbol,
        request.timeframe,
        request.start,
        request.end,
        request.max_bars,
    )
    return _validate_close_bars(bars)


def _validate_close_bars(bars: tuple[CloseBar, ...]) -> tuple[CloseBar, ...]:
    if not isinstance(bars, tuple):
        raise ValueError("provider must return a tuple of CloseBar values")
    for bar in bars:
        if not isinstance(bar, CloseBar):
            raise ValueError("provider must return only CloseBar values")
    return bars


def _validate_csv_fields(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("CSV input must include a header row")
    normalized_fields = {field.strip() for field in fieldnames}
    missing_fields = CSV_REQUIRED_FIELDS - normalized_fields
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"CSV input is missing required fields: {missing}")


def _csv_required_value(row: dict[str, str], field_name: str, row_number: int) -> str:
    raw_value = row.get(field_name, "")
    value = str(raw_value).strip()
    if not value:
        raise ValueError(f"CSV row {row_number} has empty {field_name}")
    return value


def _alpaca_bar_required_value(raw_bar: object, field_name: str, index: int) -> object:
    if not hasattr(raw_bar, field_name):
        raise ValueError(f"Alpaca mock bar {index} is missing {field_name}")
    value = getattr(raw_bar, field_name)
    if value is None or str(value).strip() == "":
        raise ValueError(f"Alpaca mock bar {index} has empty {field_name}")
    return value


def _normalize_required_text(field_name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized
