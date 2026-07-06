"""Ingest manifest, hashing, token scrubbing, and monthly budget ledger."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BUDGET_LIMIT = 500


def new_ingest_run_id() -> str:
    return f"tiingo-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def scrub_token(text: str, token: str | None = None) -> str:
    scrubbed = text
    if token:
        scrubbed = scrubbed.replace(token, "[REDACTED_TOKEN]")
    scrubbed = re.sub(r"([?&]token=)[^&\s]+", r"\1[REDACTED_TOKEN]", scrubbed, flags=re.IGNORECASE)
    scrubbed = re.sub(r"(Authorization:\s*Token\s+)[^\s]+", r"\1[REDACTED_TOKEN]", scrubbed, flags=re.IGNORECASE)
    return scrubbed


def budget_ledger_path(manifests_dir: Path, month: str) -> Path:
    return manifests_dir / f"tiingo_symbol_budget_{month}.json"


def read_budget_ledger(manifests_dir: Path, month: str) -> dict:
    path = budget_ledger_path(manifests_dir, month)
    if not path.exists():
        return {"month": month, "limit": BUDGET_LIMIT, "symbols": []}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def budget_preflight(manifests_dir: Path, symbols: list[str], month: str) -> dict:
    ledger = read_budget_ledger(manifests_dir, month)
    already = set(ledger.get("symbols", []))
    planned = {symbol.upper() for symbol in symbols}
    new_symbols = sorted(planned - already)
    remaining_before = BUDGET_LIMIT - len(already)
    return {
        "month": month,
        "limit": BUDGET_LIMIT,
        "planned_symbols": sorted(planned),
        "already_counted_symbols": sorted(already.intersection(planned)),
        "new_unique_symbols": new_symbols,
        "new_unique_symbols_consumed": len(new_symbols),
        "remaining_before": remaining_before,
        "remaining_after": remaining_before - len(new_symbols),
        "passed": len(new_symbols) <= remaining_before,
    }


def update_budget_ledger(manifests_dir: Path, symbols: list[str], month: str) -> dict:
    ledger = read_budget_ledger(manifests_dir, month)
    all_symbols = sorted(set(ledger.get("symbols", [])) | {symbol.upper() for symbol in symbols})
    ledger = {"month": month, "limit": BUDGET_LIMIT, "symbols": all_symbols, "count": len(all_symbols)}
    path = budget_ledger_path(manifests_dir, month)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return ledger


def write_manifest(manifests_dir: Path, manifest: dict) -> Path:
    path = manifests_dir / f"{manifest['ingest_run_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path

