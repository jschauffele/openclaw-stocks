"""D11 package inventory sufficiency audit over already-loaded metadata.

This module aggregates D14 package capture ledger records into a D11/D12
evidence inventory status. It validates metadata records only. It does not read
packages, discover package directories, capture packages, replay, score,
generate candidates, touch runtime state, call broker APIs, open Unit 12, or
grant any execution authority.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from tools.replay import package_capture_ledger


D11_INVENTORY_AUDIT_RESULT = "d11_inventory_audit_result"
D11_INSUFFICIENT = "D11_INSUFFICIENT"
D11_CRITERIA_MET_PENDING_REASSESSMENT = (
    "D11_CRITERIA_MET_PENDING_SEPARATE_GOVERNANCE_REASSESSMENT"
)
UNIT_12_BLOCKED = "UNIT_12_BLOCKED"
MIN_BASELINE_PACKAGE_COUNT = 8
MIN_REGULAR_SESSION_TRADING_DAYS = 3
MIN_DECISION_OUTCOME_DIVERSITY = 2
MAX_LATEST_CANDLE_LAG_SECONDS = 30 * 60

STRUCTURAL_VALID = "valid"
STRUCTURAL_INVALID = "invalid"
MARKET_DATA_VALID = "valid"
MARKET_DATA_CAVEATED = "recency_caveated"
MARKET_DATA_INVALID = "invalid"
INVENTORY_CLEAN = "clean"
INVENTORY_RECENCY_CAVEATED = "recency_caveated"
INVENTORY_QUARANTINED = "quarantined"

D11_INVENTORY_AUDIT_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "already_loaded_metadata_only",
    "d14_ledger_records_only",
    "read_only_with_respect_to_packages",
    "no_package_reads",
    "no_package_discovery",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_runtime_work",
    "no_broker_api_authority",
    "no_unit_12_opening",
    "no_execution_authority",
)


@dataclass(frozen=True, slots=True)
class _ValidatedRecord:
    source: Mapping[str, Any]
    validation: Mapping[str, Any]
    market_data: Mapping[str, Any]

    @property
    def d11_countable(self) -> bool:
        return (
            self.validation["sufficiency_count_eligible"] is True
            and self.market_data["inventory_classification"] == INVENTORY_CLEAN
        )


def audit_d11_inventory(
    ledger_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    *,
    pairing_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Audit already-loaded D14 ledger metadata against D11/D12 criteria."""

    records = list(ledger_records)
    pairings = list(pairing_records)
    valid: list[_ValidatedRecord] = []
    invalid: list[dict[str, str]] = []
    inventory_reports: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        try:
            validation = package_capture_ledger.validate_package_capture_ledger_record(
                record
            )
        except Exception as exc:  # noqa: BLE001 - audit reports fail-closed reasons.
            invalid.append(
                {
                    "index": str(index),
                    "run_id": str(record.get("run_id", "")),
                    "reason": str(exc),
                }
            )
            inventory_reports.append(_invalid_inventory_record_report(record, str(exc)))
            continue
        item = _ValidatedRecord(
            source=record,
            validation=validation,
            market_data=classify_market_data_quality(record),
        )
        valid.append(item)
        inventory_reports.append(_inventory_record_report(item))

    count_eligible = [
        item
        for item in valid
        if item.validation["sufficiency_count_eligible"] is True
    ]
    d11_countable = [item for item in count_eligible if item.d11_countable]
    baseline = [
        item
        for item in d11_countable
        if item.validation["evidence_membership"]
        == package_capture_ledger.EVIDENCE_MEMBERSHIP_BASELINE
    ]
    candidate = [
        item
        for item in d11_countable
        if item.validation["evidence_membership"]
        == package_capture_ledger.EVIDENCE_MEMBERSHIP_CANDIDATE
    ]
    trading_days = sorted(
        {
            str(item.source["capture_timestamp_utc"])[:10]
            for item in baseline
            if isinstance(item.source.get("capture_timestamp_utc"), str)
        }
    )
    symbols = sorted(
        {
            str(item.source["symbol"])
            for item in baseline
            if isinstance(item.source.get("symbol"), str) and item.source["symbol"]
        }
    )
    decision_outcomes = sorted(
        {
            str(item.source["decision_outcome"])
            for item in baseline
            if isinstance(item.source.get("decision_outcome"), str)
        }
    )
    pairing = _pairing_readiness(pairings, baseline, candidate)
    criteria = {
        "baseline_package_count": len(baseline) >= MIN_BASELINE_PACKAGE_COUNT,
        "regular_session_trading_days": (
            len(trading_days) >= MIN_REGULAR_SESSION_TRADING_DAYS
        ),
        "decision_outcome_diversity": (
            len(decision_outcomes) >= MIN_DECISION_OUTCOME_DIVERSITY
        ),
        "candidate_side_package_inventory": len(candidate) > 0,
        "baseline_vs_candidate_pairing_ready": pairing["ready"],
        "d14_compliant_ledger_records_present": len(count_eligible) > 0,
        "no_invalid_ledger_records": len(invalid) == 0,
    }
    all_criteria_met = all(criteria.values())
    return {
        "result_type": D11_INVENTORY_AUDIT_RESULT,
        "d11_status": (
            D11_CRITERIA_MET_PENDING_REASSESSMENT
            if all_criteria_met
            else D11_INSUFFICIENT
        ),
        "unit_12_status": UNIT_12_BLOCKED,
        "criteria": criteria,
        "counts": {
            "ledger_records": len(records),
            "valid_d14_records": len(valid),
            "invalid_records": len(invalid),
            "structurally_count_eligible_records": len(count_eligible),
            "count_eligible_records": len(d11_countable),
            "clean_records": sum(
                1
                for item in count_eligible
                if item.market_data["inventory_classification"] == INVENTORY_CLEAN
            ),
            "recency_caveated_records": sum(
                1
                for item in count_eligible
                if item.market_data["inventory_classification"]
                == INVENTORY_RECENCY_CAVEATED
            ),
            "quarantined_records": sum(
                1
                for item in count_eligible
                if item.market_data["inventory_classification"]
                == INVENTORY_QUARANTINED
            ),
            "baseline_count_eligible": len(baseline),
            "candidate_count_eligible": len(candidate),
            "regular_session_trading_days": len(trading_days),
            "symbols": len(symbols),
            "decision_outcomes": len(decision_outcomes),
        },
        "inventory_records": tuple(inventory_reports),
        "trading_days": tuple(trading_days),
        "symbols": tuple(symbols),
        "decision_outcomes": tuple(decision_outcomes),
        "invalid_records": tuple(invalid),
        "pairing": pairing,
        "minimums": {
            "baseline_package_count": MIN_BASELINE_PACKAGE_COUNT,
            "regular_session_trading_days": MIN_REGULAR_SESSION_TRADING_DAYS,
            "decision_outcome_diversity": MIN_DECISION_OUTCOME_DIVERSITY,
        },
        "jsonl_only_evidence_sufficient": False,
        "package_reads": False,
        "package_discovery": False,
        "package_capture": False,
        "replay": False,
        "scoring": False,
        "candidate_generation": False,
        "runtime_work": False,
        "broker_api_authority": False,
        "unit_12_opening": False,
        "execution_authority": False,
        "authority_boundary": D11_INVENTORY_AUDIT_AUTHORITY_BOUNDARY,
}


def classify_market_data_quality(record: Mapping[str, Any]) -> dict[str, Any]:
    """Classify package market-data quality from already-loaded metadata only."""

    run_timestamp = _run_timestamp(record)
    latest_candle_timestamp = _latest_candle_timestamp(record)
    data_warnings = _data_warnings(record)
    base = {
        "market_data_validity": MARKET_DATA_INVALID,
        "inventory_classification": INVENTORY_QUARANTINED,
        "d11_countable": False,
        "quarantine_reason": "",
        "caveat_reason": "",
        "latest_candle_timestamp": latest_candle_timestamp,
        "run_timestamp": run_timestamp,
        "data_warnings": data_warnings,
        "max_latest_candle_lag_seconds": MAX_LATEST_CANDLE_LAG_SECONDS,
    }

    if data_warnings:
        return {
            **base,
            "quarantine_reason": "market_input_captured_warnings_present",
        }
    if not run_timestamp:
        return {**base, "quarantine_reason": "missing_run_timestamp"}
    if not latest_candle_timestamp:
        return {**base, "quarantine_reason": "missing_latest_candle_timestamp"}

    run_dt = _parse_timestamp(run_timestamp)
    candle_dt = _parse_timestamp(latest_candle_timestamp)
    if run_dt is None:
        return {**base, "quarantine_reason": "malformed_run_timestamp"}
    if candle_dt is None:
        return {**base, "quarantine_reason": "malformed_latest_candle_timestamp"}
    if candle_dt.date() < run_dt.date():
        return {
            **base,
            "quarantine_reason": "latest_candle_prior_to_run_date",
        }
    if candle_dt.date() > run_dt.date():
        return {
            **base,
            "quarantine_reason": "latest_candle_after_run_date",
        }

    lag_seconds = (run_dt - candle_dt).total_seconds()
    if lag_seconds < 0:
        return {
            **base,
            "quarantine_reason": "latest_candle_after_run_timestamp",
        }
    if lag_seconds > MAX_LATEST_CANDLE_LAG_SECONDS:
        return {
            **base,
            "market_data_validity": MARKET_DATA_CAVEATED,
            "inventory_classification": INVENTORY_RECENCY_CAVEATED,
            "quarantine_reason": "",
            "caveat_reason": "latest_candle_lag_exceeds_threshold",
        }
    return {
        **base,
        "market_data_validity": MARKET_DATA_VALID,
        "inventory_classification": INVENTORY_CLEAN,
        "d11_countable": True,
    }


def _inventory_record_report(item: _ValidatedRecord) -> dict[str, Any]:
    market_data = item.market_data
    return {
        "run_id": item.validation["run_id"],
        "symbol": item.source.get("symbol", ""),
        "structural_validity": STRUCTURAL_VALID,
        "market_data_validity": market_data["market_data_validity"],
        "inventory_classification": market_data["inventory_classification"],
        "d11_countable": item.d11_countable,
        "quarantine_reason": market_data["quarantine_reason"],
        "caveat_reason": market_data["caveat_reason"],
        "latest_candle_timestamp": market_data["latest_candle_timestamp"],
        "run_timestamp": market_data["run_timestamp"],
        "data_warnings": market_data["data_warnings"],
    }


def _invalid_inventory_record_report(
    record: Mapping[str, Any], reason: str
) -> dict[str, Any]:
    market_data = classify_market_data_quality(record)
    return {
        "run_id": str(record.get("run_id", "")),
        "symbol": record.get("symbol", ""),
        "structural_validity": STRUCTURAL_INVALID,
        "market_data_validity": market_data["market_data_validity"],
        "inventory_classification": INVENTORY_QUARANTINED,
        "d11_countable": False,
        "quarantine_reason": f"structural_invalid: {reason}",
        "caveat_reason": "",
        "latest_candle_timestamp": market_data["latest_candle_timestamp"],
        "run_timestamp": market_data["run_timestamp"],
        "data_warnings": market_data["data_warnings"],
    }


def _run_timestamp(record: Mapping[str, Any]) -> str:
    explicit = record.get("run_timestamp")
    if isinstance(explicit, str) and explicit:
        return explicit
    run_id = record.get("run_id")
    if isinstance(run_id, str) and run_id.startswith("run_"):
        remainder = run_id[len("run_") :]
        timestamp, _, _suffix = remainder.partition("_")
        if timestamp:
            return timestamp
    return ""


def _latest_candle_timestamp(record: Mapping[str, Any]) -> str:
    value = record.get("latest_candle_timestamp")
    if isinstance(value, str):
        return value
    market_input = record.get("market_input_captured")
    if isinstance(market_input, Mapping):
        nested_value = market_input.get("latest_candle_timestamp")
        if isinstance(nested_value, str):
            return nested_value
    return ""


def _data_warnings(record: Mapping[str, Any]) -> tuple[str, ...]:
    collected: list[str] = []
    for key in (
        "data_warnings",
        "market_input_captured_warnings",
        "warnings",
    ):
        warnings = record.get(key)
        if isinstance(warnings, Sequence) and not isinstance(warnings, str):
            collected.extend(str(warning) for warning in warnings if str(warning))
    market_input = record.get("market_input_captured")
    if isinstance(market_input, Mapping):
        warnings = market_input.get("warnings")
        if isinstance(warnings, Sequence) and not isinstance(warnings, str):
            collected.extend(str(warning) for warning in warnings if str(warning))
    return tuple(collected)


def _parse_timestamp(value: str) -> datetime | None:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _pairing_readiness(
    pairings: Sequence[Mapping[str, Any]],
    baseline: Sequence[_ValidatedRecord],
    candidate: Sequence[_ValidatedRecord],
) -> dict[str, Any]:
    baseline_ids = {str(item.validation["run_id"]) for item in baseline}
    candidate_ids = {str(item.validation["run_id"]) for item in candidate}
    ready_pairs: list[dict[str, str]] = []
    invalid_pairs: list[dict[str, str]] = []
    for index, pair in enumerate(pairings):
        baseline_run_id = pair.get("baseline_run_id")
        candidate_run_id = pair.get("candidate_run_id")
        if (
            isinstance(baseline_run_id, str)
            and isinstance(candidate_run_id, str)
            and baseline_run_id in baseline_ids
            and candidate_run_id in candidate_ids
        ):
            ready_pairs.append(
                {
                    "baseline_run_id": baseline_run_id,
                    "candidate_run_id": candidate_run_id,
                }
            )
        else:
            invalid_pairs.append(
                {
                    "index": str(index),
                    "reason": "pairing does not reference counted baseline and candidate records",
                }
            )
    return {
        "ready": bool(ready_pairs),
        "ready_pairs": tuple(ready_pairs),
        "invalid_pairs": tuple(invalid_pairs),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Read inventory metadata JSON from stdin and print an audit result."""

    if argv is None:
        argv = sys.argv[1:]
    if argv:
        print("usage: python -m tools.replay.d11_inventory_audit < inventory.json")
        return 2
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, Mapping):
            raise TypeError("inventory payload must be a JSON object")
        records = payload.get("ledger_records", ())
        pairings = payload.get("pairing_records", ())
        if not isinstance(records, list):
            raise TypeError("ledger_records must be a list")
        if not isinstance(pairings, list):
            raise TypeError("pairing_records must be a list")
        result = audit_d11_inventory(records, pairing_records=pairings)
    except Exception as exc:  # noqa: BLE001 - CLI must fail closed.
        print(json.dumps({"error": str(exc), "d11_status": D11_INSUFFICIENT}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
