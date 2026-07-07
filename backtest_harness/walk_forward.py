"""Deterministic walk-forward date splitter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    fold_id: str
    train_dates: tuple[pd.Timestamp, ...]
    test_dates: tuple[pd.Timestamp, ...]

    def __post_init__(self) -> None:
        if not self.fold_id.strip():
            raise BacktestHarnessError(HarnessFailureCode.MISSING_SPLIT_ID, "fold_id must be non-empty")
        validate_fold_invariants(self)


def generate_walk_forward_folds(
    date_index: Iterable[object],
    *,
    train_window_length: int,
    test_window_length: int,
    expanding: bool,
) -> tuple[WalkForwardFold, ...]:
    dates = _normalize_sorted_unique_dates(date_index)
    _validate_window_lengths(train_window_length, test_window_length)
    folds: list[WalkForwardFold] = []
    train_start = 0
    train_end = train_window_length
    fold_number = 1

    while train_end + test_window_length <= len(dates):
        test_end = train_end + test_window_length
        fold = WalkForwardFold(
            fold_id=f"fold_{fold_number:04d}",
            train_dates=tuple(dates[0 if expanding else train_start:train_end]),
            test_dates=tuple(dates[train_end:test_end]),
        )
        folds.append(fold)
        fold_number += 1
        if expanding:
            train_end = test_end
        else:
            train_start += test_window_length
            train_end += test_window_length

    validate_walk_forward_folds(tuple(folds))
    return tuple(folds)


def validate_walk_forward_folds(folds: tuple[WalkForwardFold, ...]) -> None:
    previous_test_dates: set[pd.Timestamp] = set()
    previous_max_test_date: pd.Timestamp | None = None
    seen_fold_ids: set[str] = set()
    for fold in folds:
        if fold.fold_id in seen_fold_ids:
            raise BacktestHarnessError(HarnessFailureCode.MISSING_SPLIT_ID, f"duplicate fold_id: {fold.fold_id}")
        seen_fold_ids.add(fold.fold_id)
        validate_fold_invariants(fold)
        test_dates = set(fold.test_dates)
        if previous_test_dates.intersection(test_dates):
            raise BacktestHarnessError(HarnessFailureCode.TRAIN_TEST_OVERLAP, "test windows overlap across folds")
        if previous_max_test_date is not None and min(fold.test_dates) <= previous_max_test_date:
            raise BacktestHarnessError(HarnessFailureCode.TRAIN_TEST_OVERLAP, "test windows are not strictly ordered")
        previous_test_dates.update(test_dates)
        previous_max_test_date = max(fold.test_dates)


def validate_fold_invariants(fold: WalkForwardFold) -> None:
    if not fold.train_dates:
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "train_dates must be non-empty")
    if not fold.test_dates:
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "test_dates must be non-empty")
    if set(fold.train_dates).intersection(fold.test_dates):
        raise BacktestHarnessError(HarnessFailureCode.TRAIN_TEST_OVERLAP, "train/test dates overlap within fold")
    if max(fold.train_dates) >= min(fold.test_dates):
        raise BacktestHarnessError(
            HarnessFailureCode.TRAIN_TEST_OVERLAP,
            "every test date must be strictly after every train date",
        )
    _assert_strictly_increasing(fold.train_dates, "train_dates")
    _assert_strictly_increasing(fold.test_dates, "test_dates")


def _normalize_sorted_unique_dates(date_index: Iterable[object]) -> tuple[pd.Timestamp, ...]:
    dates = tuple(pd.to_datetime(list(date_index), errors="coerce"))
    if not dates:
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "date_index must be non-empty")
    if any(pd.isna(date) for date in dates):
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "date_index contains unparseable date")
    normalized = tuple(pd.Timestamp(date).normalize() for date in dates)
    if len(set(normalized)) != len(normalized):
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "date_index must be unique")
    _assert_strictly_increasing(normalized, "date_index")
    return normalized


def _validate_window_lengths(train_window_length: int, test_window_length: int) -> None:
    if not isinstance(train_window_length, int) or not isinstance(test_window_length, int):
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "window lengths must be integers")
    if train_window_length <= 0 or test_window_length <= 0:
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, "window lengths must be positive")


def _assert_strictly_increasing(dates: tuple[pd.Timestamp, ...], field_name: str) -> None:
    for left, right in zip(dates, dates[1:]):
        if right <= left:
            raise BacktestHarnessError(HarnessFailureCode.INVALID_SPLIT_CONFIG, f"{field_name} must be strictly increasing")
