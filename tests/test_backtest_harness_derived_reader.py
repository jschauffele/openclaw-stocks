from pathlib import Path

import pandas as pd
import pytest

from backtest_harness import BacktestHarnessConfig, read_derived_adjusted_series
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode


def _write_fixture(root: Path, ticker: str, manifest_id: str, rows: list[dict], name: str | None = None) -> Path:
    part = root / "tiingo" / "derived" / f"ticker={ticker}"
    part.mkdir(parents=True, exist_ok=True)
    path = part / (name or f"{manifest_id}.parquet")
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def _row(ticker: str, date: str, price: float, manifest_id: str) -> dict:
    return {
        "date": date,
        "ticker": ticker,
        "computed_adjClose": price,
        "adjustment_method": "crsp_style_back_adjustment",
        "adjustment_method_version": "1.0",
        "ingest_run_id": manifest_id,
        "source_manifest_id": manifest_id,
    }


def _config(tmp_path: Path, universe=("AAPL",)) -> BacktestHarnessConfig:
    return BacktestHarnessConfig(data_root=tmp_path, universe=universe)


def test_reader_selects_latest_source_manifest_id(tmp_path) -> None:
    older = "tiingo-20260101T000000Z-aaaaaaaaaaaa"
    newer = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    _write_fixture(tmp_path, "AAPL", older, [_row("AAPL", "2026-01-02", 100.0, older)], f"{older}.parquet")
    _write_fixture(tmp_path, "AAPL", newer, [_row("AAPL", "2026-01-03", 101.0, newer)], f"{newer}.parquet")

    frame = read_derived_adjusted_series(_config(tmp_path))

    assert frame["source_manifest_id"].unique().tolist() == [newer]
    assert frame["computed_adjClose"].tolist() == [101.0]
    assert frame.columns.tolist() == [
        "date",
        "ticker",
        "computed_adjClose",
        "adjustment_method",
        "adjustment_method_version",
        "source_manifest_id",
        "ingest_run_id",
    ]


def test_reader_rejects_missing_derived_root(tmp_path) -> None:
    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.MISSING_DERIVED_DATA


def test_reader_rejects_vendor_adjclose_column(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    row = _row("AAPL", "2026-01-03", 101.0, manifest)
    row["adjClose"] = 101.0
    _write_fixture(tmp_path, "AAPL", manifest, [row], f"{manifest}.parquet")

    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.VENDOR_ADJCLOSE_FORBIDDEN


def test_reader_rejects_duplicate_dates(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    _write_fixture(
        tmp_path,
        "AAPL",
        manifest,
        [_row("AAPL", "2026-01-03", 101.0, manifest), _row("AAPL", "2026-01-03", 102.0, manifest)],
        f"{manifest}.parquet",
    )

    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.DUPLICATE_TICKER_DATE


def test_reader_rejects_unparseable_dates(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    _write_fixture(tmp_path, "AAPL", manifest, [_row("AAPL", "not-a-date", 101.0, manifest)], f"{manifest}.parquet")

    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.UNPARSEABLE_DATE


def test_reader_rejects_missing_manifest_lineage(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    row = _row("AAPL", "2026-01-03", 101.0, manifest)
    row["source_manifest_id"] = ""
    _write_fixture(tmp_path, "AAPL", manifest, [row], f"{manifest}.parquet")

    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.MISSING_MANIFEST_LINEAGE


def test_reader_rejects_non_finite_or_non_positive_price(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    _write_fixture(tmp_path, "AAPL", manifest, [_row("AAPL", "2026-01-03", 0.0, manifest)], f"{manifest}.parquet")

    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.INVALID_PRICE


def test_reader_rejects_manifest_conflict(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    _write_fixture(tmp_path, "AAPL", manifest, [_row("AAPL", "2026-01-03", 101.0, manifest)], "tiingo-a.parquet")
    _write_fixture(tmp_path, "AAPL", manifest, [_row("AAPL", "2026-01-04", 102.0, manifest)], "tiingo-b.parquet")

    with pytest.raises(BacktestHarnessError) as excinfo:
        read_derived_adjusted_series(_config(tmp_path))

    assert excinfo.value.code == HarnessFailureCode.MANIFEST_CONFLICT


def test_reader_returns_copy_isolated_frame(tmp_path) -> None:
    manifest = "tiingo-20260102T000000Z-bbbbbbbbbbbb"
    _write_fixture(tmp_path, "AAPL", manifest, [_row("AAPL", "2026-01-03", 101.0, manifest)], f"{manifest}.parquet")

    first = read_derived_adjusted_series(_config(tmp_path))
    first.loc[0, "computed_adjClose"] = 999.0
    second = read_derived_adjusted_series(_config(tmp_path))

    assert second.loc[0, "computed_adjClose"] == 101.0
