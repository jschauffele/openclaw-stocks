from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.evidence.collect_3_close_evidence import FAIL_CLOSED_MESSAGE, main
from tools.evidence.read_only_historical_data_adapter import (
    AlpacaEvidenceHistoricalCloseProvider,
    CsvStaticHistoricalCloseProvider,
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


class FakeAlpacaBar:
    def __init__(self, timestamp: str, close: float) -> None:
        self.timestamp = timestamp
        self.close = close


class FakeAlpacaClient:
    def __init__(self, bars: tuple[object, ...]) -> None:
        self.bars = bars
        self.calls: list[dict[str, object]] = []

    def get_stock_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        limit: int | None,
    ) -> tuple[object, ...]:
        self.calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "start": start,
                "end": end,
                "limit": limit,
            }
        )
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
        for relative_path in [
            "tools/evidence/read_only_historical_data_adapter.py",
            "tools/evidence/collect_3_close_evidence.py",
        ]:
            with self.subTest(path=relative_path):
                tree = ast.parse(Path(relative_path).read_text(encoding="utf-8"))
                imported_roots = _imported_roots(tree)
                self.assertTrue(FORBIDDEN_IMPORT_ROOTS.isdisjoint(imported_roots))

    def test_csv_provider_filters_symbol_date_range_and_max_bars(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "bars.csv"
            input_path.write_text(
                "\n".join(
                    [
                        "symbol,timestamp,close",
                        "AAPL,2026-01-01T00:00:00Z,99.0",
                        "MSTR,2026-01-01T00:00:00Z,100.0",
                        "MSTR,2026-01-01T00:15:00Z,101.0",
                        "MSTR,2026-01-01T00:30:00Z,102.0",
                        "MSTR,2026-01-03T00:00:00Z,103.0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            provider = CsvStaticHistoricalCloseProvider(input_path)
            request = EvidenceHistoricalCloseRequest(
                symbol="MSTR",
                timeframe="15Min",
                start="2026-01-01T00:00:00Z",
                end="2026-01-02T00:00:00Z",
                max_bars=2,
            )

            result = get_close_bars_for_request(provider, request)

        self.assertEqual(
            result,
            (
                CloseBar(timestamp="2026-01-01T00:00:00Z", close=100.0),
                CloseBar(timestamp="2026-01-01T00:15:00Z", close=101.0),
            ),
        )

    def test_csv_provider_rejects_missing_fields(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "bars.csv"
            input_path.write_text(
                "symbol,timestamp\nMSTR,2026-01-01T00:00:00Z\n",
                encoding="utf-8",
            )
            provider = CsvStaticHistoricalCloseProvider(input_path)
            request = EvidenceHistoricalCloseRequest(
                symbol="MSTR",
                timeframe="15Min",
                start="2026-01-01",
                end="2026-01-02",
            )

            with self.assertRaises(ValueError):
                get_close_bars_for_request(provider, request)

    def test_csv_provider_rejects_malformed_rows(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "bars.csv"
            input_path.write_text(
                "symbol,timestamp,close\nMSTR,2026-01-01T00:00:00Z,not-a-number\n",
                encoding="utf-8",
            )
            provider = CsvStaticHistoricalCloseProvider(input_path)
            request = EvidenceHistoricalCloseRequest(
                symbol="MSTR",
                timeframe="15Min",
                start="2026-01-01",
                end="2026-01-02",
            )

            with self.assertRaises(ValueError):
                get_close_bars_for_request(provider, request)

    def test_csv_provider_rejects_empty_input_path(self) -> None:
        with self.assertRaises(ValueError):
            CsvStaticHistoricalCloseProvider("")

    def test_cli_writes_json_only_to_caller_specified_output_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "bars.csv"
            output_path = Path(temp_dir) / "evidence" / "candidates.json"
            input_path.write_text(
                "\n".join(
                    [
                        "symbol,timestamp,close",
                        "MSTR,2026-01-01T00:00:00Z,200.0",
                        "MSTR,2026-01-01T00:15:00Z,203.0",
                        "MSTR,2026-01-01T00:30:00Z,206.0",
                        "MSTR,2026-01-01T00:45:00Z,209.0",
                        "MSTR,2026-01-01T01:00:00Z,211.0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "--provider",
                    "csv",
                    "--input-path",
                    str(input_path),
                    "--symbols",
                    "MSTR",
                    "--timeframe",
                    "15Min",
                    "--start-date",
                    "2026-01-01T00:00:00Z",
                    "--end-date",
                    "2026-01-02T00:00:00Z",
                    "--max-examples",
                    "10",
                    "--output-path",
                    str(output_path),
                ]
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["artifact_type"], "review_input_not_test")
        self.assertEqual(
            payload["candidates"][0]["reviewer_decision"],
            "PENDING_REVIEW",
        )
        self.assertEqual(
            payload["candidates"][0]["review_status"],
            "GENERATED_CANDIDATE_NOT_ACCEPTED",
        )

    def test_cli_uses_max_bars_separately_from_max_examples(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "bars.csv"
            output_path = Path(temp_dir) / "evidence" / "candidates.json"
            input_path.write_text(
                "\n".join(
                    [
                        "symbol,timestamp,close",
                        "MSTR,2026-01-01T00:00:00Z,200.0",
                        "MSTR,2026-01-01T00:15:00Z,203.0",
                        "MSTR,2026-01-01T00:30:00Z,206.0",
                        "MSTR,2026-01-01T00:45:00Z,209.0",
                        "MSTR,2026-01-01T01:00:00Z,211.0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "--provider",
                    "csv",
                    "--input-path",
                    str(input_path),
                    "--symbols",
                    "MSTR",
                    "--timeframe",
                    "15Min",
                    "--start-date",
                    "2026-01-01T00:00:00Z",
                    "--end-date",
                    "2026-01-02T00:00:00Z",
                    "--max-examples",
                    "10",
                    "--max-bars",
                    "3",
                    "--output-path",
                    str(output_path),
                ]
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["candidates"], [])

    def test_cli_fails_closed_for_non_csv_provider(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            main(
                [
                    "--provider",
                    "alpaca",
                    "--symbols",
                    "MSTR",
                    "--timeframe",
                    "15Min",
                    "--start-date",
                    "2026-01-01",
                    "--end-date",
                    "2026-01-02",
                    "--output-path",
                    "unused.json",
                ]
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("not approved", FAIL_CLOSED_MESSAGE)

    def test_mock_only_alpaca_provider_passes_request_values_to_client(self) -> None:
        client = FakeAlpacaClient(
            (
                FakeAlpacaBar("2026-01-01T00:00:00Z", 100.0),
                FakeAlpacaBar("2026-01-01T00:15:00Z", 101.0),
            )
        )
        provider = AlpacaEvidenceHistoricalCloseProvider(client)
        request = EvidenceHistoricalCloseRequest(
            symbol="mstr",
            timeframe="15Min",
            start="2026-01-01T00:00:00Z",
            end="2026-01-02T00:00:00Z",
            max_bars=2,
        )

        result = get_close_bars_for_request(provider, request)

        self.assertEqual(
            client.calls,
            [
                {
                    "symbol": "MSTR",
                    "timeframe": "15Min",
                    "start": "2026-01-01T00:00:00Z",
                    "end": "2026-01-02T00:00:00Z",
                    "limit": 2,
                }
            ],
        )
        self.assertEqual(
            result,
            (
                CloseBar(timestamp="2026-01-01T00:00:00Z", close=100.0),
                CloseBar(timestamp="2026-01-01T00:15:00Z", close=101.0),
            ),
        )

    def test_mock_only_alpaca_provider_honors_max_bars(self) -> None:
        client = FakeAlpacaClient(
            (
                FakeAlpacaBar("2026-01-01T00:00:00Z", 100.0),
                FakeAlpacaBar("2026-01-01T00:15:00Z", 101.0),
                FakeAlpacaBar("2026-01-01T00:30:00Z", 102.0),
            )
        )
        provider = AlpacaEvidenceHistoricalCloseProvider(client)
        request = EvidenceHistoricalCloseRequest(
            symbol="MSTR",
            timeframe="15Min",
            start="2026-01-01T00:00:00Z",
            end="2026-01-02T00:00:00Z",
            max_bars=2,
        )

        result = get_close_bars_for_request(provider, request)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[-1], CloseBar(timestamp="2026-01-01T00:15:00Z", close=101.0))

    def test_mock_only_alpaca_provider_rejects_malformed_bars(self) -> None:
        class MissingCloseBar:
            timestamp = "2026-01-01T00:00:00Z"

        client = FakeAlpacaClient((MissingCloseBar(),))
        provider = AlpacaEvidenceHistoricalCloseProvider(client)
        request = EvidenceHistoricalCloseRequest(
            symbol="MSTR",
            timeframe="15Min",
            start="2026-01-01",
            end="2026-01-02",
        )

        with self.assertRaises(ValueError):
            get_close_bars_for_request(provider, request)

    def test_mock_only_alpaca_provider_requires_injected_client(self) -> None:
        with self.assertRaises(ValueError):
            AlpacaEvidenceHistoricalCloseProvider(None)

        with self.assertRaises(ValueError):
            AlpacaEvidenceHistoricalCloseProvider(object())


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
