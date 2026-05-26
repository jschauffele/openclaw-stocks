from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tools.evidence.three_close_evidence_scanner import CloseBar


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


def _normalize_required_text(field_name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized
