"""Offline validation checks for Phase 1 Tiingo ingestion."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from data_layer.adjustments import reconstruct_adj_close
from data_layer.schema import duplicate_date_ticker_rows

TOL_LOOSE = 0.005
TOL_TIGHT = 0.001
PASS_WITHIN_LOOSE_PCT = 99.0
SPLIT_CONTINUITY_REVIEW_THRESHOLD = 0.25
SUSPICIOUS_YIELD = 0.10
MAX_MISSING_WEEKDAYS_PER_YEAR = 15


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    metrics: dict
    messages: list[str]


def reconcile_vendor_adjclose(df: pd.DataFrame) -> CheckResult:
    valid = (
        df["close"].notna()
        & (df["close"] > 0)
        & df["adjClose"].notna()
        & (df["adjClose"] > 0)
        & df["divCash"].notna()
        & df["splitFactor"].notna()
    )
    excluded = int((~valid).sum())
    calc = reconstruct_adj_close(df)
    vendor = df["adjClose"]
    rel = ((calc - vendor).abs() / vendor.abs().clip(lower=1e-12))[valid]
    absdev = (calc - vendor).abs()[valid]
    n = int(valid.sum())
    if n == 0:
        return CheckResult("reconcile", False, {"rows_tested": 0, "rows_excluded": excluded}, ["no_valid_rows"])

    max_abs = float(absdev.max())
    max_rel = float(rel.max())
    med_rel = float(rel.median())
    within_loose = float((rel <= TOL_LOOSE).mean() * 100)
    within_tight = float((rel <= TOL_TIGHT).mean() * 100)
    worst_date = df.loc[rel.idxmax(), "date"]
    passed = within_loose >= PASS_WITHIN_LOOSE_PCT and max_rel <= TOL_LOOSE
    return CheckResult(
        "reconcile",
        passed,
        {
            "rows_tested": n,
            "rows_excluded": excluded,
            "max_absolute_deviation": max_abs,
            "max_percentage_deviation": max_rel,
            "median_percentage_deviation": med_rel,
            "rows_within_0_5pct": within_loose,
            "rows_within_0_1pct": within_tight,
            "worst_date": str(pd.to_datetime(worst_date).date()),
        },
        [] if passed else ["vendor_reconciliation_failure"],
    )


def check_gaps(df: pd.DataFrame) -> CheckResult:
    dates = pd.to_datetime(df["date"]).sort_values()
    if dates.empty:
        return CheckResult("gaps", False, {}, ["no_dates"])
    first, last = dates.iloc[0], dates.iloc[-1]
    all_weekdays = pd.bdate_range(first, last)
    have = set(dates)
    missing = [d for d in all_weekdays if d not in have]
    years = max((last - first).days / 365.25, 1e-9)
    per_year = len(missing) / years
    passed = per_year <= MAX_MISSING_WEEKDAYS_PER_YEAR
    return CheckResult(
        "gaps",
        passed,
        {"missing_weekdays": len(missing), "missing_weekdays_per_year": per_year, "threshold": MAX_MISSING_WEEKDAYS_PER_YEAR},
        [] if passed else ["gap_review_required"],
    )


def check_split_continuity(df: pd.DataFrame) -> CheckResult:
    ordered = df.sort_values("date").reset_index(drop=True)
    events = ordered[ordered["splitFactor"] != 1.0]
    suspicious = []
    for idx, row in events.iterrows():
        if idx == 0:
            continue
        prev = ordered.iloc[idx - 1]
        adj_change = row["adjClose"] / prev["adjClose"] - 1.0
        if abs(adj_change) > SPLIT_CONTINUITY_REVIEW_THRESHOLD:
            suspicious.append({"date": str(row["date"]), "adjusted_close_change": float(adj_change)})
    return CheckResult(
        "split_continuity",
        True,
        {"split_events": int(len(events)), "suspicious_events": suspicious},
        [] if not suspicious else ["large_split_date_move_observed"],
    )


def check_dividends(df: pd.DataFrame) -> CheckResult:
    divs = df[df["divCash"] > 0]
    flagged = []
    for _, row in divs.iterrows():
        implied_yield = row["divCash"] / row["close"] if row["close"] else float("inf")
        if implied_yield > SUSPICIOUS_YIELD:
            flagged.append({"date": str(row["date"]), "implied_yield": float(implied_yield)})
    return CheckResult(
        "dividends",
        True,
        {"dividend_events": int(len(divs)), "flagged_events": flagged, "single_event_review_threshold": SUSPICIOUS_YIELD},
        [] if not flagged else ["large_dividend_event_observed"],
    )


def check_duplicates(df: pd.DataFrame) -> CheckResult:
    duplicates = duplicate_date_ticker_rows(df)
    return CheckResult(
        "duplicates",
        duplicates.empty,
        {"duplicate_date_ticker_rows": int(len(duplicates))},
        [] if duplicates.empty else ["duplicate_date_ticker"],
    )
