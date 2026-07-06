"""Phase 1 Tiingo ingestion workflow.

This module implements the approved 21-step workflow. It keeps canonical rows
append-stable and treats adjusted close as a derived artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from data_layer.adjustments import ADJUSTMENT_METHOD, ADJUSTMENT_METHOD_VERSION, build_derived_adjusted_series, selftest
from data_layer.checks import check_dividends, check_duplicates, check_gaps, check_split_continuity, reconcile_vendor_adjclose
from data_layer.config_template import resolve_data_root
from data_layer.manifest import (
    budget_preflight,
    new_ingest_run_id,
    payload_hash,
    scrub_token,
    update_budget_ledger,
    write_manifest,
)
from data_layer.schema import detect_data_value_rewrites, normalize_tiingo_payload, validate_tiingo_payload

BASE_URL = "https://api.tiingo.com/tiingo/daily"
START_DATE = "1990-01-01"
REQUEST_SLEEP_S = 2.0
REQUIRED_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "MSTR", "PTON"]
FINAL_BLOCKED_PREFIX = "PHASE_1_INGESTION_IMPLEMENTATION_BLOCKED"
FINAL_OBSERVED = "PHASE_1_INGESTION_IMPLEMENTATION_OBSERVED"


class IngestBlocked(RuntimeError):
    pass


def tiingo_layout(data_root: Path) -> dict[str, Path]:
    base = data_root / "tiingo"
    return {
        "base": base,
        "raw_payloads": base / "raw_payloads",
        "canonical": base / "canonical",
        "derived": base / "derived",
        "corporate_actions": base / "corporate_actions",
        "supported_tickers": base / "supported_tickers",
        "manifests": base / "manifests",
        "validation_reports": base / "validation_reports",
        "quarantine": base / "quarantine",
    }


def ensure_layout(paths: dict[str, Path]) -> None:
    for key, path in paths.items():
        if key != "base":
            path.mkdir(parents=True, exist_ok=True)


def parquet_backend() -> str | None:
    for backend in ("pyarrow", "fastparquet"):
        try:
            __import__(backend)
            return backend
        except ImportError:
            continue
    return None


def is_inside_git_repo(path: Path) -> bool:
    probe = path.resolve()
    for current in [probe, *probe.parents]:
        if (current / ".git").exists():
            return True
    try:
        result = subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def preflight(data_root: Path, symbols: list[str]) -> dict:
    resolved = data_root.resolve()
    documents = (Path.home() / "Documents").resolve()
    if resolved == documents or documents in resolved.parents:
        raise IngestBlocked("output path appears to be iCloud-synced or under ~/Documents")
    if is_inside_git_repo(resolved):
        raise IngestBlocked("output path inside tracked repo without explicit approval")
    backend = parquet_backend()
    if backend is None:
        raise IngestBlocked("parquet backend missing")
    token = os.environ.get("TIINGO_API_TOKEN")
    if not token:
        raise IngestBlocked("missing token")
    ok, _report = selftest()
    if not ok:
        raise IngestBlocked("reconstruction self-test fails")
    paths = tiingo_layout(resolved)
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    budget = budget_preflight(paths["manifests"], symbols, month)
    if not budget["passed"]:
        raise IngestBlocked("planned pull would exceed free-tier unique-symbol budget")
    return {"data_root": str(resolved), "parquet_backend": backend, "month": month, "budget": budget}


def fetch_ticker(ticker: str, token: str) -> list[dict]:
    url = f"{BASE_URL}/{ticker}/prices"
    params = {"startDate": START_DATE, "format": "json", "token": token}
    try:
        response = requests.get(url, params=params, timeout=60)
    except requests.RequestException as exc:
        raise IngestBlocked(scrub_token(f"network unavailable: {exc}", token)) from exc
    content_type = response.headers.get("content-type", "")
    if response.status_code in {401, 403}:
        raise IngestBlocked(f"{response.status_code} auth failure")
    if response.status_code == 404:
        raise IngestBlocked(f"404 on approved required core ticker {ticker}")
    if response.status_code != 200:
        raise IngestBlocked(scrub_token(f"HTTP {response.status_code}: {response.text[:200]}", token))
    if "json" not in content_type.lower():
        raise IngestBlocked(scrub_token(f"HTTP 200 with non-JSON body: {response.text[:200]}", token))
    try:
        payload = response.json()
    except ValueError as exc:
        raise IngestBlocked("non-JSON response") from exc
    if not isinstance(payload, list) or not payload:
        raise IngestBlocked("non-JSON response")
    return payload


def frame_from_payload(payload: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(payload)
    frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None).dt.normalize()
    return frame.sort_values("date").reset_index(drop=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_partitioned_parquet(frame: pd.DataFrame, root: Path, run_id: str) -> list[str]:
    written = []
    for ticker, group in frame.groupby("ticker", sort=True):
        outdir = root / f"ticker={ticker}"
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"{run_id}.parquet"
        group.to_parquet(path, index=False)
        written.append(str(path))
    return written


def read_existing_canonical(root: Path, tickers: list[str]) -> pd.DataFrame:
    frames = []
    for ticker in tickers:
        part = root / f"ticker={ticker}"
        if part.exists():
            latest = sorted(part.glob("tiingo-*.parquet"))[-1:]
            if latest:
                frames.append(pd.read_parquet(latest[0]))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run_ingest(symbols: list[str], data_root: Path) -> dict:
    symbols = [symbol.upper() for symbol in symbols]
    run_id = new_ingest_run_id()
    pf = preflight(data_root, symbols)
    paths = tiingo_layout(Path(pf["data_root"]))
    ensure_layout(paths)
    token = os.environ["TIINGO_API_TOKEN"]
    manifest = {
        "ingest_run_id": run_id,
        "status": "started",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "symbols": symbols,
        "budget_preflight": pf["budget"],
        "parquet_backend": pf["parquet_backend"],
        "checks": {},
        "payload_hashes": {},
        "canonical_fields": [
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
        ],
        "derived_metadata": {
            "adjustment_method": ADJUSTMENT_METHOD,
            "adjustment_method_version": ADJUSTMENT_METHOD_VERSION,
            "source_manifest_id": run_id,
        },
    }
    canonical_frames = []
    validation = {"ingest_run_id": run_id, "tickers": {}}
    try:
        for index, symbol in enumerate(symbols):
            payload = fetch_ticker(symbol, token)
            digest = payload_hash(payload)
            manifest["payload_hashes"][symbol] = digest
            write_json(paths["raw_payloads"] / f"{run_id}_{symbol}.json", payload)
            schema_result = validate_tiingo_payload(payload)
            if not schema_result.passed:
                raise IngestBlocked(f"schema missing required fields for {symbol}: {schema_result.errors}")
            vendor_frame = frame_from_payload(payload)
            checks = [
                reconcile_vendor_adjclose(vendor_frame),
                check_gaps(vendor_frame),
                check_split_continuity(vendor_frame),
                check_dividends(vendor_frame),
            ]
            manifest["checks"][symbol] = {check.name: {"passed": check.passed, "metrics": check.metrics, "messages": check.messages} for check in checks}
            validation["tickers"][symbol] = manifest["checks"][symbol]
            if not all(check.passed for check in checks):
                raise IngestBlocked(f"unresolved validation conditions remain for {symbol}")
            canonical = normalize_tiingo_payload(
                payload,
                ticker=symbol,
                source_symbol=symbol,
                ingest_run_id=run_id,
                payload_hash=digest,
            )
            dup_check = check_duplicates(canonical)
            if not dup_check.passed:
                raise IngestBlocked(f"duplicate date/ticker conflict for {symbol}")
            canonical_frames.append(canonical)
            if index < len(symbols) - 1:
                time.sleep(REQUEST_SLEEP_S)

        incoming = pd.concat(canonical_frames, ignore_index=True)
        existing = read_existing_canonical(paths["canonical"], symbols)
        rewrites = detect_data_value_rewrites(existing, incoming)
        manifest["rewrite_detection"] = {"events": rewrites, "event_count": len(rewrites)}
        if rewrites:
            raise IngestBlocked("unexpected historical rewrite detected")
        canonical_paths = write_partitioned_parquet(incoming, paths["canonical"], run_id)
        derived = build_derived_adjusted_series(incoming, source_manifest_id=run_id)
        derived_paths = write_partitioned_parquet(derived, paths["derived"], run_id)
        budget_ledger = update_budget_ledger(paths["manifests"], symbols, pf["month"])
        validation["rewrite_detection"] = manifest["rewrite_detection"]
        validation["budget_ledger"] = budget_ledger
        validation["canonical_paths"] = canonical_paths
        validation["derived_paths"] = derived_paths
        write_json(paths["validation_reports"] / f"{run_id}.json", validation)
        manifest["budget_ledger"] = budget_ledger
        manifest["canonical_outputs"] = canonical_paths
        manifest["derived_outputs"] = derived_paths
        manifest["validation_report"] = str(paths["validation_reports"] / f"{run_id}.json")
        manifest["status"] = "observed"
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        manifest_path = write_manifest(paths["manifests"], manifest)
        return {"classification": FINAL_OBSERVED, "manifest": manifest, "manifest_path": str(manifest_path), "validation": validation}
    except Exception as exc:
        reason = scrub_token(str(exc), token if "token" in locals() else None)
        manifest["status"] = "failed"
        manifest["failure_reason"] = reason
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        try:
            write_json(paths["quarantine"] / f"{run_id}_failure.json", manifest)
            write_manifest(paths["manifests"], manifest)
        except OSError as write_exc:
            write_reason = scrub_token(str(write_exc), token if "token" in locals() else None)
            raise IngestBlocked(f"{reason}; failed to write failure artifacts: {write_reason}") from None
        raise IngestBlocked(reason) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenClaw Phase 1 Tiingo ingestion")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--symbols", nargs="+", default=REQUIRED_SYMBOLS)
    args = parser.parse_args(argv)
    data_root = resolve_data_root(args.data_root)
    try:
        result = run_ingest(args.symbols, data_root)
    except IngestBlocked as exc:
        print(f"{FINAL_BLOCKED_PREFIX} - {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    print(FINAL_OBSERVED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
