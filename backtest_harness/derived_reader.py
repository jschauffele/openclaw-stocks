"""Local-only derived adjusted-series reader for Phase 1B."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import pandas as pd

from backtest_harness.config import BacktestHarnessConfig
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode


REQUIRED_DERIVED_COLUMNS = (
    "date",
    "ticker",
    "computed_adjClose",
    "adjustment_method",
    "adjustment_method_version",
    "source_manifest_id",
)
OPTIONAL_DERIVED_COLUMNS = ("ingest_run_id",)
FORBIDDEN_COLUMNS = ("adjClose", "adj_close")
RETURN_COLUMNS = (
    "date",
    "ticker",
    "computed_adjClose",
    "adjustment_method",
    "adjustment_method_version",
    "source_manifest_id",
    "ingest_run_id",
)


def read_derived_adjusted_series(config: BacktestHarnessConfig) -> pd.DataFrame:
    if not isinstance(config, BacktestHarnessConfig):
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, "config must be BacktestHarnessConfig")
    if not config.derived_root.exists():
        raise BacktestHarnessError(
            HarnessFailureCode.MISSING_DERIVED_DATA,
            f"missing derived root: {config.derived_root}",
        )

    frames = []
    for ticker in config.universe:
        path = _select_latest_manifest_file(config.derived_root, ticker)
        frames.append(_read_and_validate_ticker(path, ticker))

    if not frames:
        return pd.DataFrame(columns=RETURN_COLUMNS)
    combined = pd.concat(frames, ignore_index=True)
    duplicate_rows = combined.duplicated(subset=["ticker", "date"], keep=False)
    if duplicate_rows.any():
        raise BacktestHarnessError(HarnessFailureCode.DUPLICATE_TICKER_DATE, "duplicate ticker/date rows")
    combined = combined.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)
    return combined.loc[:, RETURN_COLUMNS].copy(deep=True)


def _select_latest_manifest_file(derived_root: Path, ticker: str) -> Path:
    part = derived_root / f"ticker={ticker}"
    if not part.exists():
        raise BacktestHarnessError(HarnessFailureCode.MISSING_DERIVED_DATA, f"missing derived partition for {ticker}")
    files = sorted(part.glob("tiingo-*.parquet"))
    if not files:
        raise BacktestHarnessError(HarnessFailureCode.MISSING_DERIVED_DATA, f"missing derived parquet for {ticker}")

    candidates: list[tuple[str, Path]] = []
    seen_manifest_paths: dict[str, Path] = {}
    for path in files:
        try:
            frame = pd.read_parquet(path, columns=["source_manifest_id"])
        except Exception as exc:  # noqa: BLE001
            raise BacktestHarnessError(
                HarnessFailureCode.SCHEMA_MISMATCH,
                f"unable to read source_manifest_id from {path}: {type(exc).__name__}",
            ) from exc
        manifest_ids = _non_empty_unique_strings(frame["source_manifest_id"], "source_manifest_id")
        if len(manifest_ids) != 1:
            raise BacktestHarnessError(HarnessFailureCode.MANIFEST_CONFLICT, f"{path} has {len(manifest_ids)} manifest ids")
        manifest_id = manifest_ids[0]
        previous = seen_manifest_paths.get(manifest_id)
        if previous is not None:
            raise BacktestHarnessError(
                HarnessFailureCode.MANIFEST_CONFLICT,
                f"duplicate source_manifest_id {manifest_id} in {previous} and {path}",
            )
        seen_manifest_paths[manifest_id] = path
        candidates.append((manifest_id, path))
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def _read_and_validate_ticker(path: Path, expected_ticker: str) -> pd.DataFrame:
    try:
        frame = pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001
        raise BacktestHarnessError(
            HarnessFailureCode.MISSING_DERIVED_DATA,
            f"unable to read derived parquet for {expected_ticker}: {type(exc).__name__}",
        ) from exc
    for column in FORBIDDEN_COLUMNS:
        if column in frame.columns:
            raise BacktestHarnessError(HarnessFailureCode.VENDOR_ADJCLOSE_FORBIDDEN, f"forbidden column {column}")
    missing = [column for column in REQUIRED_DERIVED_COLUMNS if column not in frame.columns]
    if missing:
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, f"missing columns: {missing}")
    allowed_columns = set(REQUIRED_DERIVED_COLUMNS).union(OPTIONAL_DERIVED_COLUMNS)
    unexpected = sorted(set(frame.columns).difference(allowed_columns))
    if unexpected:
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, f"unexpected columns: {unexpected}")
    if "ingest_run_id" not in frame.columns:
        frame = frame.copy()
        frame["ingest_run_id"] = ""

    frame = frame.loc[:, RETURN_COLUMNS].copy()
    frame["ticker"] = frame["ticker"].astype(str).str.strip().str.upper()
    if set(frame["ticker"]) != {expected_ticker}:
        raise BacktestHarnessError(HarnessFailureCode.INVALID_TICKER, f"ticker mismatch for {expected_ticker}")

    parsed_dates = pd.to_datetime(frame["date"], errors="coerce")
    if parsed_dates.isna().any():
        raise BacktestHarnessError(HarnessFailureCode.UNPARSEABLE_DATE, f"unparseable date in {expected_ticker}")
    frame["date"] = parsed_dates.dt.normalize()
    if frame.duplicated(subset=["ticker", "date"], keep=False).any():
        raise BacktestHarnessError(HarnessFailureCode.DUPLICATE_TICKER_DATE, f"duplicate dates for {expected_ticker}")

    manifest_ids = _non_empty_unique_strings(frame["source_manifest_id"], "source_manifest_id")
    if len(manifest_ids) != 1:
        raise BacktestHarnessError(HarnessFailureCode.MANIFEST_CONFLICT, f"{expected_ticker} has {len(manifest_ids)} manifest ids")
    if frame["adjustment_method"].astype(str).str.strip().eq("").any():
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, f"missing adjustment_method for {expected_ticker}")
    if frame["adjustment_method_version"].astype(str).str.strip().eq("").any():
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, f"missing adjustment_method_version for {expected_ticker}")

    prices = pd.to_numeric(frame["computed_adjClose"], errors="coerce")
    if prices.isna().any() or not prices.map(lambda value: math.isfinite(float(value)) and float(value) > 0).all():
        raise BacktestHarnessError(HarnessFailureCode.INVALID_PRICE, f"invalid computed_adjClose for {expected_ticker}")
    frame["computed_adjClose"] = prices.astype(float)
    return frame.sort_values("date", kind="mergesort").reset_index(drop=True)


def _non_empty_unique_strings(values: Iterable[object], field_name: str) -> list[str]:
    strings = sorted({str(value).strip() for value in values if str(value).strip()})
    if not strings:
        raise BacktestHarnessError(HarnessFailureCode.MISSING_MANIFEST_LINEAGE, f"missing {field_name}")
    return strings
