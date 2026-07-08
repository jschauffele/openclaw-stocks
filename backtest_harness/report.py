"""Deterministic replay report construction for Phase 1B."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from backtest_harness.config import BacktestHarnessConfig
from backtest_harness.derived_reader import read_derived_adjusted_series
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode
from backtest_harness.serialization import canonical_json_bytes, stable_sha256
from backtest_harness.walk_forward import WalkForwardFold


HARNESS_VERSION = "phase_1b"
REQUIRED_UNIVERSE_LABEL = "UNIVERSE=PHASE1_PLUMBING"
REQUIRED_RESEARCH_LABEL = "NON_GENERALIZABLE_RESEARCH_RESULT=true"


def build_replay_report(
    records: Iterable[dict[str, Any]],
    *,
    config: BacktestHarnessConfig,
    folds: tuple[WalkForwardFold, ...],
    universe_label: str,
) -> dict[str, Any]:
    _validate_universe_label(universe_label)
    normalized_records = tuple(dict(record) for record in records)
    evaluator_id = _single_evaluator_id(normalized_records)
    derived_frame = read_derived_adjusted_series(config)
    report_without_hash = {
        "harness_version": HARNESS_VERSION,
        "evaluator_id": evaluator_id,
        "universe": {
            "label": universe_label,
            "UNIVERSE": "PHASE1_PLUMBING",
            "NON_GENERALIZABLE_RESEARCH_RESULT": True,
            "tickers": list(config.universe),
        },
        "data_provenance": {
            "data_root": str(config.data_root),
            "derived_root": str(config.derived_root),
            "adjustment_method_version": sorted(
                str(value) for value in derived_frame["adjustment_method_version"].unique()
            ),
            "source_manifest_id": sorted(str(value) for value in derived_frame["source_manifest_id"].unique()),
        },
        "folds": [_serialize_fold(fold) for fold in folds],
        "signal_counts": _signal_counts(normalized_records, folds),
        "records": list(normalized_records),
    }
    return {
        **report_without_hash,
        "report_sha256": stable_sha256(report_without_hash),
    }


def write_replay_report(report: dict[str, Any], path: Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_json_bytes(report))


def _validate_universe_label(universe_label: str) -> None:
    if not isinstance(universe_label, str) or not universe_label.strip():
        raise BacktestHarnessError(HarnessFailureCode.MISSING_UNIVERSE_LABEL, "universe_label must be non-empty")
    parts = {part.strip() for part in universe_label.split(";") if part.strip()}
    if REQUIRED_UNIVERSE_LABEL not in parts or REQUIRED_RESEARCH_LABEL not in parts:
        raise BacktestHarnessError(
            HarnessFailureCode.MISSING_UNIVERSE_LABEL,
            "universe_label must include PHASE1_PLUMBING and research-result labels",
        )


def _single_evaluator_id(records: tuple[dict[str, Any], ...]) -> str:
    evaluator_ids = sorted({str(record.get("evaluator_id", "")).strip() for record in records if record.get("evaluator_id")})
    if len(evaluator_ids) != 1:
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, "records must contain exactly one evaluator_id")
    return evaluator_ids[0]


def _serialize_fold(fold: WalkForwardFold) -> dict[str, Any]:
    return {
        "fold_id": fold.fold_id,
        "train_dates": [date.date().isoformat() for date in fold.train_dates],
        "test_dates": [date.date().isoformat() for date in fold.test_dates],
    }


def _signal_counts(records: tuple[dict[str, Any], ...], folds: tuple[WalkForwardFold, ...]) -> dict[str, Any]:
    records_by_fold: dict[str, list[dict[str, Any]]] = {fold.fold_id: [] for fold in folds}
    fold_by_test_date = {
        date.date().isoformat(): fold.fold_id
        for fold in folds
        for date in fold.test_dates
    }
    for record in records:
        fold_id = fold_by_test_date.get(str(record["date"]))
        if fold_id is not None:
            records_by_fold[fold_id].append(record)
    return {
        "per_fold": {
            fold_id: _counts_by_ticker(fold_records)
            for fold_id, fold_records in records_by_fold.items()
        },
        "total": _counts_by_ticker(records),
    }


def _counts_by_ticker(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {}
    for record in records:
        ticker = str(record["ticker"])
        signal = str(record["signal"])
        if ticker not in counts:
            counts[ticker] = Counter({"buy": 0, "hold": 0})
        counts[ticker][signal] += 1
    return {
        ticker: {"buy": counter["buy"], "hold": counter["hold"]}
        for ticker, counter in sorted(counts.items())
    }
