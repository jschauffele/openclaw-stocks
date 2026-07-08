from pathlib import Path

import pandas as pd
import pytest

from backtest_harness import BacktestHarnessConfig
from backtest_harness.candidate_001_adapter import candidate_001_replay_adapter
from backtest_harness.dispatch import replay_signal_dispatch
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode
from backtest_harness.report import build_replay_report, write_replay_report
from backtest_harness.serialization import stable_sha256
from backtest_harness.walk_forward import WalkForwardFold, generate_walk_forward_folds


PHASE1_UNIVERSE_LABEL = "UNIVERSE=PHASE1_PLUMBING;NON_GENERALIZABLE_RESEARCH_RESULT=true"


def _write_fixture(root: Path, ticker: str, rows: list[dict]) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    part = root / "tiingo" / "derived" / f"ticker={ticker}"
    part.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(part / f"{manifest}.parquet", index=False)


def _row(ticker: str, date: pd.Timestamp, price: float) -> dict:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    return {
        "date": date.date().isoformat(),
        "ticker": ticker,
        "computed_adjClose": price,
        "adjustment_method": "crsp_style_back_adjustment",
        "adjustment_method_version": "1.0",
        "ingest_run_id": manifest,
        "source_manifest_id": manifest,
    }


def _config_with_fixture(tmp_path: Path, tickers: tuple[str, ...] = ("AAPL",)) -> BacktestHarnessConfig:
    dates = pd.bdate_range("2026-01-01", periods=12)
    for ticker_index, ticker in enumerate(tickers):
        _write_fixture(
            tmp_path,
            ticker,
            [_row(ticker, date, 100.0 + ticker_index + index) for index, date in enumerate(dates)],
        )
    return BacktestHarnessConfig(data_root=tmp_path, universe=tickers)


def _folds() -> tuple[WalkForwardFold, ...]:
    dates = pd.bdate_range("2026-01-01", periods=12)
    return generate_walk_forward_folds(
        dates,
        train_window_length=5,
        test_window_length=3,
        expanding=False,
    )


def _records() -> tuple[dict, ...]:
    return (
        {
            "date": "2026-01-08",
            "ticker": "AAPL",
            "signal": "buy",
            "inputs_end_date": "2026-01-08",
            "evaluator_id": "candidate_001",
        },
        {
            "date": "2026-01-09",
            "ticker": "AAPL",
            "signal": "hold",
            "inputs_end_date": "2026-01-09",
            "evaluator_id": "candidate_001",
        },
    )


def _assert_report_sha_verifies(report: dict) -> None:
    report_without_hash = dict(report)
    observed_hash = report_without_hash.pop("report_sha256")
    assert observed_hash == stable_sha256(report_without_hash)


def test_replay_report_is_deterministic_and_hash_verifiable(tmp_path) -> None:
    config = _config_with_fixture(tmp_path)
    folds = _folds()
    first_report = build_replay_report(_records(), config=config, folds=folds, universe_label=PHASE1_UNIVERSE_LABEL)
    second_report = build_replay_report(_records(), config=config, folds=folds, universe_label=PHASE1_UNIVERSE_LABEL)
    first_path = tmp_path / "first_report.json"
    second_path = tmp_path / "second_report.json"

    write_replay_report(first_report, first_path)
    write_replay_report(second_report, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first_report["report_sha256"] == second_report["report_sha256"]
    _assert_report_sha_verifies(first_report)


def test_replay_report_rejects_missing_universe_label(tmp_path) -> None:
    config = _config_with_fixture(tmp_path)

    with pytest.raises(BacktestHarnessError) as excinfo:
        build_replay_report(_records(), config=config, folds=_folds(), universe_label="")

    assert excinfo.value.code == HarnessFailureCode.MISSING_UNIVERSE_LABEL


def test_end_to_end_candidate_001_replay_report_hash_is_stable(tmp_path) -> None:
    config = _config_with_fixture(tmp_path, ("AAPL", "MSFT"))
    derived_frame = pd.concat(
        [
            pd.read_parquet(next((tmp_path / "tiingo" / "derived" / f"ticker={ticker}").glob("*.parquet")))
            for ticker in config.universe
        ],
        ignore_index=True,
    )
    folds = generate_walk_forward_folds(
        pd.bdate_range("2026-01-01", periods=12),
        train_window_length=5,
        test_window_length=3,
        expanding=False,
    )

    def run_once(path: Path) -> dict:
        records = []
        for fold in folds:
            records.extend(
                replay_signal_dispatch(
                    derived_frame,
                    decision_dates=fold.test_dates,
                    strategy=candidate_001_replay_adapter,
                    evaluator_id="candidate_001",
                )
            )
        report = build_replay_report(records, config=config, folds=folds, universe_label=PHASE1_UNIVERSE_LABEL)
        write_replay_report(report, path)
        return report

    first_report = run_once(tmp_path / "first_end_to_end.json")
    second_report = run_once(tmp_path / "second_end_to_end.json")

    for record in first_report["records"]:
        assert record["inputs_end_date"] <= record["date"]
    assert first_report["report_sha256"] == second_report["report_sha256"]
    _assert_report_sha_verifies(first_report)


def test_real_data_aapl_replay_report_smoke() -> None:
    real_config = BacktestHarnessConfig(
        data_root=Path("/Users/openclawcontrol/openclaw-market-data"),
        universe=("AAPL",),
    )
    if not real_config.derived_root.exists() or not (real_config.derived_root / "ticker=AAPL").exists():
        pytest.skip("real derived AAPL data root absent")
    from backtest_harness.derived_reader import read_derived_adjusted_series

    derived_frame = read_derived_adjusted_series(real_config)
    dates = tuple(pd.Series(pd.to_datetime(derived_frame["date"].unique())).sort_values().iloc[-30:])
    folds = generate_walk_forward_folds(
        dates,
        train_window_length=20,
        test_window_length=5,
        expanding=False,
    )
    records = []
    for fold in folds:
        records.extend(
            replay_signal_dispatch(
                derived_frame,
                decision_dates=fold.test_dates,
                strategy=candidate_001_replay_adapter,
                evaluator_id="candidate_001",
            )
        )
    report = build_replay_report(records, config=real_config, folds=folds, universe_label=PHASE1_UNIVERSE_LABEL)
    write_replay_report(report, Path("research") / "phase_1b_m3_real_data_smoke_report.json")

    assert {"harness_version", "evaluator_id", "universe", "data_provenance", "folds", "records", "report_sha256"}.issubset(report)
    _assert_report_sha_verifies(report)
