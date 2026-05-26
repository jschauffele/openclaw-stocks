from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tools.evidence.read_only_historical_data_adapter import (
    EvidenceHistoricalCloseRequest,
    get_close_bars_for_request,
)
from tools.evidence.three_close_evidence_scanner import CloseBar


FORBIDDEN_IMPORT_ROOTS = {
    "main",
    "config",
    "alpaca_data_provider",
    "data_engine",
    "broker_factory",
    "broker_interface",
    "risk_engine",
    "execution_engine",
    "state_manager",
    "reporting",
    "observation_logger",
    "event_logger",
    "event_reader",
}


class FakeHistoricalCloseProvider:
    def __init__(self, bars: tuple[CloseBar, ...]) -> None:
        self.bars = bars
        self.calls: list[tuple[str, str, str, str, int | None]] = []

    def get_close_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        max_bars: int | None,
    ) -> tuple[CloseBar, ...]:
        self.calls.append((symbol, timeframe, start, end, max_bars))
        return self.bars


class ReadOnlyHistoricalDataAdapterTests(unittest.TestCase):
    def test_fake_provider_returns_close_bar_tuple(self) -> None:
        bars = (
            CloseBar(timestamp="2026-01-01T00:00:00Z", close=100.0),
            CloseBar(timestamp="2026-01-01T00:15:00Z", close=101.0),
        )
        provider = FakeHistoricalCloseProvider(bars)
        request = EvidenceHistoricalCloseRequest(
            symbol="mstr",
            timeframe="15Min",
            start="2026-01-01T00:00:00Z",
            end="2026-01-02T00:00:00Z",
            max_bars=500,
        )

        result = get_close_bars_for_request(provider, request)

        self.assertEqual(result, bars)
        self.assertEqual(
            provider.calls,
            [
                (
                    "MSTR",
                    "15Min",
                    "2026-01-01T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    500,
                )
            ],
        )

    def test_request_validation_rejects_bad_values(self) -> None:
        invalid_requests = [
            {
                "symbol": "",
                "timeframe": "15Min",
                "start": "2026-01-01",
                "end": "2026-01-02",
                "max_bars": None,
            },
            {
                "symbol": "MSTR",
                "timeframe": "",
                "start": "2026-01-01",
                "end": "2026-01-02",
                "max_bars": None,
            },
            {
                "symbol": "MSTR",
                "timeframe": "15Min",
                "start": "2026-01-02",
                "end": "2026-01-01",
                "max_bars": None,
            },
            {
                "symbol": "MSTR",
                "timeframe": "15Min",
                "start": "2026-01-01",
                "end": "2026-01-02",
                "max_bars": 0,
            },
        ]

        for kwargs in invalid_requests:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    EvidenceHistoricalCloseRequest(**kwargs)

    def test_provider_must_return_close_bar_tuple(self) -> None:
        class ListReturningProvider:
            def get_close_bars(
                self,
                symbol: str,
                timeframe: str,
                start: str,
                end: str,
                max_bars: int | None,
            ) -> list[CloseBar]:
                return [CloseBar(timestamp="2026-01-01T00:00:00Z", close=100.0)]

        request = EvidenceHistoricalCloseRequest(
            symbol="MSTR",
            timeframe="15Min",
            start="2026-01-01",
            end="2026-01-02",
        )

        with self.assertRaises(ValueError):
            get_close_bars_for_request(ListReturningProvider(), request)

    def test_scaffold_performs_no_evidence_collection(self) -> None:
        provider = FakeHistoricalCloseProvider(())
        request = EvidenceHistoricalCloseRequest(
            symbol="MSTR",
            timeframe="15Min",
            start="2026-01-01",
            end="2026-01-02",
        )

        result = get_close_bars_for_request(provider, request)

        self.assertEqual(result, ())
        self.assertEqual(len(provider.calls), 1)

    def test_adapter_does_not_import_forbidden_runtime_modules(self) -> None:
        tree = ast.parse(
            Path("tools/evidence/read_only_historical_data_adapter.py").read_text(
                encoding="utf-8"
            )
        )
        imported_roots = _imported_roots(tree)

        self.assertTrue(FORBIDDEN_IMPORT_ROOTS.isdisjoint(imported_roots))


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


if __name__ == "__main__":
    unittest.main()
