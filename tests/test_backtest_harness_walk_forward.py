import pandas as pd
import pytest

from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode
from backtest_harness.serialization import stable_sha256
from backtest_harness.walk_forward import WalkForwardFold, generate_walk_forward_folds, validate_walk_forward_folds


def test_splitter_rolling_happy_path_exact_boundaries() -> None:
    dates = pd.bdate_range("2026-01-01", periods=100)

    folds = generate_walk_forward_folds(
        dates,
        train_window_length=20,
        test_window_length=10,
        expanding=False,
    )

    assert len(folds) == 8
    assert folds[0].fold_id == "fold_0001"
    assert folds[0].train_dates == tuple(dates[:20])
    assert folds[0].test_dates == tuple(dates[20:30])
    assert folds[1].train_dates == tuple(dates[10:30])
    assert folds[1].test_dates == tuple(dates[30:40])
    assert folds[-1].train_dates == tuple(dates[70:90])
    assert folds[-1].test_dates == tuple(dates[90:100])


def test_splitter_expanding_happy_path_exact_boundaries() -> None:
    dates = pd.bdate_range("2026-01-01", periods=50)

    folds = generate_walk_forward_folds(
        dates,
        train_window_length=20,
        test_window_length=10,
        expanding=True,
    )

    assert len(folds) == 3
    assert folds[0].train_dates == tuple(dates[:20])
    assert folds[0].test_dates == tuple(dates[20:30])
    assert folds[1].train_dates == tuple(dates[:30])
    assert folds[1].test_dates == tuple(dates[30:40])
    assert folds[2].train_dates == tuple(dates[:40])
    assert folds[2].test_dates == tuple(dates[40:50])


def test_splitter_rejects_train_test_overlap_within_fold() -> None:
    dates = pd.bdate_range("2026-01-01", periods=5)

    with pytest.raises(BacktestHarnessError) as excinfo:
        WalkForwardFold(
            fold_id="bad",
            train_dates=tuple(dates[:3]),
            test_dates=tuple(dates[2:5]),
        )

    assert excinfo.value.code == HarnessFailureCode.TRAIN_TEST_OVERLAP


def test_splitter_rejects_non_forward_test_window() -> None:
    dates = pd.bdate_range("2026-01-01", periods=5)

    with pytest.raises(BacktestHarnessError) as excinfo:
        WalkForwardFold(
            fold_id="bad",
            train_dates=tuple(dates[1:4]),
            test_dates=(dates[0], dates[4]),
        )

    assert excinfo.value.code == HarnessFailureCode.TRAIN_TEST_OVERLAP


def test_splitter_rejects_overlapping_test_windows_across_folds() -> None:
    dates = pd.bdate_range("2026-01-01", periods=10)
    folds = (
        WalkForwardFold("fold_0001", tuple(dates[:4]), tuple(dates[4:7])),
        WalkForwardFold("fold_0002", tuple(dates[:5]), tuple(dates[6:9])),
    )

    with pytest.raises(BacktestHarnessError) as excinfo:
        validate_walk_forward_folds(folds)

    assert excinfo.value.code == HarnessFailureCode.TRAIN_TEST_OVERLAP


def test_splitter_rejects_unsorted_or_duplicate_date_index() -> None:
    dates = pd.to_datetime(["2026-01-02", "2026-01-01", "2026-01-01"])

    with pytest.raises(BacktestHarnessError) as excinfo:
        generate_walk_forward_folds(
            dates,
            train_window_length=2,
            test_window_length=1,
            expanding=False,
        )

    assert excinfo.value.code == HarnessFailureCode.INVALID_SPLIT_CONFIG


def test_splitter_serialization_is_deterministic() -> None:
    dates = pd.bdate_range("2026-01-01", periods=40)
    folds = generate_walk_forward_folds(
        dates,
        train_window_length=20,
        test_window_length=10,
        expanding=False,
    )
    payload = [
        {
            "fold_id": fold.fold_id,
            "train_dates": [date.date().isoformat() for date in fold.train_dates],
            "test_dates": [date.date().isoformat() for date in fold.test_dates],
        }
        for fold in folds
    ]

    assert stable_sha256(payload) == stable_sha256(list(payload))
