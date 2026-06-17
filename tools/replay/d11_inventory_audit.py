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
            continue
        valid.append(_ValidatedRecord(source=record, validation=validation))

    count_eligible = [
        item for item in valid if item.validation["sufficiency_count_eligible"] is True
    ]
    baseline = [
        item
        for item in count_eligible
        if item.validation["evidence_membership"]
        == package_capture_ledger.EVIDENCE_MEMBERSHIP_BASELINE
    ]
    candidate = [
        item
        for item in count_eligible
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
            "count_eligible_records": len(count_eligible),
            "baseline_count_eligible": len(baseline),
            "candidate_count_eligible": len(candidate),
            "regular_session_trading_days": len(trading_days),
            "symbols": len(symbols),
            "decision_outcomes": len(decision_outcomes),
        },
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
