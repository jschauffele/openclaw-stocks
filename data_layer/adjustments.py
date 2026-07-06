"""CRSP-style adjusted-close reconstruction and synthetic self-test."""

from __future__ import annotations

import pandas as pd

ADJUSTMENT_METHOD = "crsp_style_back_adjustment"
ADJUSTMENT_METHOD_VERSION = "1.0"


def reconstruct_adj_close(df: pd.DataFrame) -> pd.Series:
    """
    CRSP-style back-adjustment from raw close + divCash + splitFactor.

    Working backward from the most recent bar, a dividend D and split S on
    ex-date i scale all prior days' factor by ((prevClose - D) / prevClose) / S.
    """
    close = df["close"].to_numpy()
    div = df["divCash"].to_numpy()
    split = df["splitFactor"].to_numpy()
    n = len(df)

    adjusted = [0.0] * n
    factor = 1.0
    for i in range(n - 1, -1, -1):
        adjusted[i] = close[i] * factor
        if i > 0:
            prev_close = close[i - 1]
            event_factor = 1.0
            if div[i] > 0 and prev_close > 0:
                event_factor *= (prev_close - div[i]) / prev_close
            if split[i] != 1.0 and split[i] > 0:
                event_factor /= split[i]
            factor *= event_factor
    return pd.Series(adjusted, index=df.index, name="computed_adjClose")


def build_derived_adjusted_series(
    canonical: pd.DataFrame,
    *,
    source_manifest_id: str,
) -> pd.DataFrame:
    ordered = canonical.sort_values(["ticker", "date"]).copy()
    pieces = []
    for ticker, group in ordered.groupby("ticker", sort=True):
        group = group.sort_values("date").copy()
        group["computed_adjClose"] = reconstruct_adj_close(group)
        group["adjustment_method"] = ADJUSTMENT_METHOD
        group["adjustment_method_version"] = ADJUSTMENT_METHOD_VERSION
        group["source_manifest_id"] = source_manifest_id
        pieces.append(
            group[
                [
                    "date",
                    "ticker",
                    "computed_adjClose",
                    "adjustment_method",
                    "adjustment_method_version",
                    "ingest_run_id",
                    "source_manifest_id",
                ]
            ]
        )
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def selftest() -> tuple[bool, pd.DataFrame]:
    dates = pd.bdate_range("2024-01-01", periods=8)
    close = [100.0, 102.0, 51.0, 51.5, 52.0, 51.5, 52.5, 53.0]
    split = [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    div = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    df = pd.DataFrame({"date": dates, "close": close, "splitFactor": split, "divCash": div})
    calc = reconstruct_adj_close(df)
    f_div = (52.0 - 1.0) / 52.0
    exp1 = 102.0 * f_div / 2.0
    exp4 = 52.0 * f_div
    ok = (
        abs(calc.iloc[-1] - 53.0) < 1e-9
        and abs(calc.iloc[1] - exp1) < 1e-9
        and abs(calc.iloc[4] - exp4) < 1e-9
    )
    report = pd.DataFrame({"date": dates.date, "close": close, "computed_adjClose": calc.round(8)})
    return ok, report

