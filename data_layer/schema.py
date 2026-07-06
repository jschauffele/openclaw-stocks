"""Append-stable canonical row schema and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

CANONICAL_FIELDS = [
    "date",
    "ticker",
    "source_symbol",
    "source",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "divCash",
    "splitFactor",
    "ingest_run_id",
    "payload_hash",
    "data_quality_flags",
]

DATA_VALUE_FIELDS = ["open", "high", "low", "close", "volume", "divCash", "splitFactor"]

ROW_LEVEL_FLAGS = {
    "raw_close_only",
    "missing_required_field",
    "duplicate_date_ticker",
    "source_conflict",
    "unresolved_source_conflict",
    "gap_review_required",
    "split_event",
    "dividend_event",
    "suspicious_split_continuity",
    "real_market_move_verified",
    "vendor_reconciliation_failure",
    "quarantined",
}

TICKER_UNIVERSE_METADATA = {
    "insufficient_history",
    "delisted_candidate",
    "active_adverse_control",
    "non_generalizable_universe",
}

TIINGO_REQUIRED_FIELDS = {
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adjClose",
    "divCash",
    "splitFactor",
}

TIINGO_HARD_FAIL_FIELDS = {"close", "adjClose", "divCash", "splitFactor"}


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: list[str]
    warnings: list[str]


def validate_tiingo_payload(payload: list[dict]) -> ValidationResult:
    if not isinstance(payload, list) or not payload:
        return ValidationResult(False, ["empty_or_unexpected_payload"], [])
    present = set(payload[0])
    errors = [f"missing_required_field:{name}" for name in sorted(TIINGO_HARD_FAIL_FIELDS - present)]
    warnings = [f"missing_soft_field:{name}" for name in sorted(TIINGO_REQUIRED_FIELDS - present - TIINGO_HARD_FAIL_FIELDS)]
    return ValidationResult(not errors, errors, warnings)


def flags_for_vendor_row(row: dict) -> list[str]:
    flags: list[str] = []
    try:
        if float(row.get("splitFactor", 1.0)) != 1.0:
            flags.append("split_event")
    except (TypeError, ValueError):
        flags.append("missing_required_field")
    try:
        if float(row.get("divCash", 0.0)) > 0:
            flags.append("dividend_event")
    except (TypeError, ValueError):
        flags.append("missing_required_field")
    return flags


def normalize_tiingo_payload(
    payload: list[dict],
    *,
    ticker: str,
    source_symbol: str,
    ingest_run_id: str,
    payload_hash: str,
) -> pd.DataFrame:
    result = validate_tiingo_payload(payload)
    if not result.passed:
        raise ValueError(";".join(result.errors))

    rows = []
    for row in payload:
        rows.append(
            {
                "date": pd.to_datetime(row["date"], utc=True).date().isoformat(),
                "ticker": ticker,
                "source_symbol": source_symbol,
                "source": "tiingo",
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "divCash": row.get("divCash"),
                "splitFactor": row.get("splitFactor"),
                "ingest_run_id": ingest_run_id,
                "payload_hash": payload_hash,
                "data_quality_flags": flags_for_vendor_row(row),
            }
        )
    frame = pd.DataFrame(rows, columns=CANONICAL_FIELDS)
    return validate_canonical_frame(frame)


def validate_canonical_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [field for field in CANONICAL_FIELDS if field not in frame.columns]
    extra = [field for field in frame.columns if field not in CANONICAL_FIELDS]
    if missing:
        raise ValueError(f"canonical_missing_fields:{missing}")
    if extra:
        raise ValueError(f"canonical_extra_fields:{extra}")
    invalid_flags = sorted(_invalid_flags(frame["data_quality_flags"]))
    if invalid_flags:
        raise ValueError(f"canonical_invalid_row_flags:{invalid_flags}")
    return frame[CANONICAL_FIELDS].copy()


def duplicate_date_ticker_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame.duplicated(["date", "ticker"], keep=False)]


def detect_data_value_rewrites(existing: pd.DataFrame, incoming: pd.DataFrame) -> list[dict]:
    """Compare data values only, keyed by (date, ticker), per C1."""
    if existing.empty or incoming.empty:
        return []
    left = existing.set_index(["date", "ticker"])
    right = incoming.set_index(["date", "ticker"])
    rewrites = []
    for key in left.index.intersection(right.index):
        old = left.loc[key]
        new = right.loc[key]
        if isinstance(old, pd.DataFrame) or isinstance(new, pd.DataFrame):
            rewrites.append({"date": key[0], "ticker": key[1], "field": "duplicate_date_ticker"})
            continue
        for field in DATA_VALUE_FIELDS:
            if not _same_value(old[field], new[field]):
                rewrites.append(
                    {
                        "date": key[0],
                        "ticker": key[1],
                        "field": field,
                        "stored": old[field],
                        "incoming": new[field],
                    }
                )
    return rewrites


def _same_value(left: object, right: object) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    try:
        return abs(float(left) - float(right)) <= 1e-12
    except (TypeError, ValueError):
        return left == right


def _invalid_flags(values: Iterable[object]) -> set[str]:
    invalid: set[str] = set()
    for value in values:
        flags = value if isinstance(value, list) else []
        invalid.update(flag for flag in flags if flag not in ROW_LEVEL_FLAGS)
    return invalid

