from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.evidence.collect_3_close_evidence import FAIL_CLOSED_MESSAGE, main
from tools.evidence.three_close_evidence_scanner import (
    ARTIFACT_TYPE,
    DEFAULT_SCANNER_SETTINGS,
    FALSE_POSITIVE_REVIEW_1,
    FALSE_POSITIVE_REVIEW_3,
    POSITIVE_CONTROL_3,
    REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED,
    REVIEWER_DECISION_PENDING_REVIEW,
    SCANNER_VERSION,
    CloseBar,
    scan_three_close_evidence_candidates,
    write_evidence_candidates_json,
)


FORBIDDEN_IMPORT_ROOTS = {
    "main",
    "config",
    "alpaca_broker_adapter",
    "alpaca_data_provider",
    "broker_factory",
    "broker_interface",
    "event_logger",
    "event_reader",
    "execution_engine",
    "execution_use_case",
    "ibkr_broker_adapter",
    "ibkr_submit_reconciliation_workflow",
    "observation_logger",
    "reporting",
    "risk_engine",
    "state_manager",
}


def bars(*closes: float) -> tuple[CloseBar, ...]:
    return tuple(
        CloseBar(timestamp=f"2026-01-{index + 1:02d}T00:00:00Z", close=close)
        for index, close in enumerate(closes)
    )


class ThreeCloseEvidenceScannerTests(unittest.TestCase):
    def test_identifies_positive_control_3_steady_continuation_candidate(self) -> None:
        candidates = scan_three_close_evidence_candidates(
            symbol="mstr",
            timeframe="1Day",
            bars=bars(200.0, 203.0, 206.0, 209.0, 211.0),
            source_provider="fake_in_memory",
            evidence_type="paper",
            generated_at="2026-01-01T00:00:00+00:00",
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.fixture_name, POSITIVE_CONTROL_3)
        self.assertEqual(candidate.symbol, "MSTR")
        self.assertEqual(candidate.signal_window_closes, (200.0, 203.0, 206.0, 209.0))
        self.assertEqual(candidate.follow_through_closes, (211.0,))
        self.assertEqual(candidate.fixture_effect, "supports_fixture")
        self.assertTrue(candidate.uses_close_only_data)
        self.assertEqual(candidate.reviewer_decision, REVIEWER_DECISION_PENDING_REVIEW)
        self.assertEqual(
            candidate.review_status,
            REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED,
        )

    def test_identifies_false_positive_review_1_shallow_drift_candidate(self) -> None:
        candidates = scan_three_close_evidence_candidates(
            symbol="AAPL",
            timeframe="1Day",
            bars=bars(100.0, 100.05, 100.10, 100.15, 100.12),
            source_provider="fake_in_memory",
            evidence_type="historical",
            generated_at="2026-01-01T00:00:00+00:00",
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.fixture_name, FALSE_POSITIVE_REVIEW_1)
        self.assertEqual(candidate.signal_window_closes, (100.0, 100.05, 100.10, 100.15))
        self.assertEqual(candidate.follow_through_closes, (100.12,))
        self.assertEqual(candidate.fixture_effect, "supports_fixture")
        self.assertTrue(candidate.uses_close_only_data)
        self.assertEqual(candidate.reviewer_decision, REVIEWER_DECISION_PENDING_REVIEW)
        self.assertEqual(
            candidate.review_status,
            REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED,
        )

    def test_identifies_false_positive_review_3_choppy_recovery_candidate(self) -> None:
        candidates = scan_three_close_evidence_candidates(
            symbol="MSFT",
            timeframe="1Day",
            bars=bars(100.0, 99.80, 100.05, 100.20, 100.35, 100.10),
            source_provider="fake_in_memory",
            evidence_type="paper",
            generated_at="2026-01-01T00:00:00+00:00",
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.fixture_name, FALSE_POSITIVE_REVIEW_3)
        self.assertEqual(
            candidate.signal_window_closes,
            (100.0, 99.80, 100.05, 100.20, 100.35),
        )
        self.assertEqual(candidate.follow_through_closes, (100.10,))
        self.assertEqual(candidate.fixture_effect, "supports_fixture")
        self.assertTrue(candidate.uses_close_only_data)
        self.assertEqual(candidate.reviewer_decision, REVIEWER_DECISION_PENDING_REVIEW)
        self.assertEqual(
            candidate.review_status,
            REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED,
        )

    def test_writes_json_artifact_only_to_caller_specified_path(self) -> None:
        candidates = scan_three_close_evidence_candidates(
            symbol="MSTR",
            timeframe="1Day",
            bars=bars(200.0, 203.0, 206.0, 209.0, 211.0),
            source_provider="fake_in_memory",
            evidence_type="paper",
            generated_at="2026-01-01T00:00:00+00:00",
        )

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "candidate.json"
            written_path = write_evidence_candidates_json(candidates, output_path)
            payload = json.loads(written_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["artifact_type"], ARTIFACT_TYPE)
        self.assertEqual(payload["scanner_version"], SCANNER_VERSION)
        self.assertEqual(
            payload["scanner_settings"]["shallow_drift_max_delta"],
            DEFAULT_SCANNER_SETTINGS.shallow_drift_max_delta,
        )
        self.assertEqual(
            payload["scanner_settings"]["steady_continuation_min_delta"],
            DEFAULT_SCANNER_SETTINGS.steady_continuation_min_delta,
        )
        self.assertEqual(
            payload["scanner_settings"][
                "steady_continuation_max_to_min_delta_ratio"
            ],
            DEFAULT_SCANNER_SETTINGS.steady_continuation_max_to_min_delta_ratio,
        )
        self.assertIn("not strategy thresholds", payload["scanner_settings"]["meaning"])
        self.assertEqual(payload["candidates"][0]["fixture_name"], POSITIVE_CONTROL_3)
        self.assertEqual(payload["candidates"][0]["source_provider"], "fake_in_memory")
        self.assertEqual(
            payload["candidates"][0]["reviewer_decision"],
            REVIEWER_DECISION_PENDING_REVIEW,
        )
        self.assertEqual(
            payload["candidates"][0]["review_status"],
            REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED,
        )

    def test_cli_fails_closed_without_fetching_data(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            main(
                [
                    "--symbols",
                    "MSTR",
                    "--timeframe",
                    "1Day",
                    "--start-date",
                    "2026-01-01",
                    "--end-date",
                    "2026-01-31",
                    "--output-path",
                    "unused.json",
                ]
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("not approved", FAIL_CLOSED_MESSAGE)

    def test_evidence_tools_do_not_import_forbidden_runtime_modules(self) -> None:
        for relative_path in [
            "tools/evidence/three_close_evidence_scanner.py",
            "tools/evidence/collect_3_close_evidence.py",
            "tools/evidence/read_only_historical_data_adapter.py",
        ]:
            with self.subTest(path=relative_path):
                tree = ast.parse(Path(relative_path).read_text(encoding="utf-8"))
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
