"""Pure in-memory experiment identifier + registry authority governance.

This module defines deterministic experiment identifier shape rules and a
governed, versioned experiment registry authority over already-loaded registry
record metadata only. It runs no experiments, persists no registry, computes no
scores, performs no attribution or evaluation execution, reads no files, reads
no replay packages, and carries no package-set, reproducibility,
baseline-vs-candidate, as-of, promotion, broker, strategy, risk, execution,
paper-trading, or live-trading authority.

Registering an experiment identity here does not run an experiment, does not
write any registry, and does not authorize any downstream behavior. Registry
records governed here must be immutable evidence: mutable records fail closed.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders experiment identifier + registry authority as the
third Gate D implementation unit, following metric (Unit 1) and attribution
(Unit 2) vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


EXPERIMENT_REGISTRY = "experiment_registry_in_memory_only"
EXPERIMENT_REGISTRY_VERSION = "0.1-experiment-registry"
SUPPORTED_EXPERIMENT_REGISTRY_VERSIONS: tuple[str, ...] = (
    EXPERIMENT_REGISTRY_VERSION,
)
EXPERIMENT_REGISTRY_AUTHORITY = "experiment_registry_authority_metadata_only"
EXPERIMENT_REGISTRY_RESULT = "experiment_registry_result"

EXPERIMENT_ID_PREFIX = "exp_"
EXPERIMENT_ID_MAX_LENGTH = 128
_EXPERIMENT_ID_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

EXPERIMENT_STATUS_REGISTERED = "registered"
EXPERIMENT_STATUS_CLOSED = "closed"
KNOWN_EXPERIMENT_STATUSES: tuple[str, ...] = (
    EXPERIMENT_STATUS_REGISTERED,
    EXPERIMENT_STATUS_CLOSED,
)

# Record fields that would imply authority this governance must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "experiment_execution",
    "registry_persistence",
    "attribution_execution",
    "evaluation_execution",
    "package_set_selection",
    "reproducibility_engine",
    "baseline_vs_candidate_comparison",
    "as_of_feature_logic",
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

EXPERIMENT_REGISTRY_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_experiment_identifier",
    "malformed_experiment_identifier",
    "missing_experiment_registry_version",
    "unsupported_experiment_registry_version",
    "missing_experiment_registry_authority",
    "unknown_experiment_registry_authority",
    "unknown_experiment_status",
    "missing_experiment_scope",
    "mutable_registry_record",
    "missing_immutability_marker",
    "duplicate_experiment_identifier",
    "empty_experiment_registry_record_set",
    "malformed_registry_record",
    "authority_bearing_field_present",
)

EXPERIMENT_REGISTRY_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "identifier_and_registry_governance_only",
    "evidence_only",
    "non_authoritative",
    "immutable_registry_records_only",
    "no_experiment_execution",
    "no_registry_persistence",
    "no_scoring",
    "no_attribution_execution",
    "no_evaluation_execution",
    "no_filesystem_reads",
    "no_package_reads",
    "no_package_set_selection",
    "no_reproducibility_engine",
    "no_baseline_vs_candidate_comparison",
    "no_as_of_feature_logic",
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_approval",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class ExperimentRegistry:
    """Static governed experiment registry authority and version."""

    version: str = EXPERIMENT_REGISTRY_VERSION
    authority: str = EXPERIMENT_REGISTRY_AUTHORITY
    known_statuses: tuple[str, ...] = KNOWN_EXPERIMENT_STATUSES
    authority_boundary: tuple[str, ...] = EXPERIMENT_REGISTRY_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class ExperimentRegistryFailClosedConditions:
    """Static fail-closed condition vocabulary for the experiment registry."""

    conditions: tuple[str, ...] = EXPERIMENT_REGISTRY_FAIL_CLOSED_CONDITIONS


def is_valid_experiment_identifier(identifier: object) -> bool:
    """Return True only for a deterministically well-formed experiment id."""

    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(EXPERIMENT_ID_PREFIX):
        return False
    if len(identifier) <= len(EXPERIMENT_ID_PREFIX):
        return False
    if len(identifier) > EXPERIMENT_ID_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(EXPERIMENT_ID_PREFIX):]
    return all(char in _EXPERIMENT_ID_BODY_CHARS for char in body)


def validate_experiment_identifier(identifier: object) -> dict[str, Any]:
    """Validate a single experiment identifier shape, or fail closed."""

    if identifier is None or identifier == "":
        raise ValueError("missing experiment identifier")
    if not is_valid_experiment_identifier(identifier):
        raise ValueError(f"malformed experiment identifier: '{identifier}'")
    return _governed_result(experiment_identifiers=(identifier,))


def validate_experiment_registry_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded immutable registry record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("experiment registry record must be already-loaded metadata")

    identifier = record.get("experiment_id")
    if not identifier:
        raise ValueError("missing experiment identifier")
    if not is_valid_experiment_identifier(identifier):
        raise ValueError(f"malformed experiment identifier: '{identifier}'")

    version = record.get("experiment_registry_version")
    if not version:
        raise ValueError("missing experiment registry version")
    if version not in SUPPORTED_EXPERIMENT_REGISTRY_VERSIONS:
        raise ValueError(f"unsupported experiment registry version: '{version}'")

    authority = record.get("experiment_registry_authority")
    if not authority:
        raise ValueError("missing experiment registry authority")
    if authority != EXPERIMENT_REGISTRY_AUTHORITY:
        raise ValueError("unknown experiment registry authority")

    status = record.get("experiment_status")
    if not status:
        raise ValueError("missing experiment status")
    if status not in KNOWN_EXPERIMENT_STATUSES:
        raise ValueError(f"unknown experiment status: '{status}'")

    start_scope = record.get("start_scope")
    end_scope = record.get("end_scope")
    if not start_scope or not end_scope:
        raise ValueError("missing experiment scope")

    if record.get("mutable"):
        raise ValueError("mutable registry record")
    if record.get("immutable") is not True:
        raise ValueError("missing immutability marker")

    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")

    return _governed_result(
        experiment_identifiers=(identifier,),
        experiment_registry_version=version,
    )


def validate_experiment_registry_record_set(records: object) -> dict[str, Any]:
    """Validate a set of immutable registry records with unique ids, or fail closed."""

    if not isinstance(records, (tuple, list)):
        raise TypeError("experiment registry records must be a tuple or list")
    if not records:
        raise ValueError("empty experiment registry record set")
    seen: set[str] = set()
    for record in records:
        result = validate_experiment_registry_record(record)
        identifier = result["experiment_identifiers"][0]
        if identifier in seen:
            raise ValueError(f"duplicate experiment identifier: '{identifier}'")
        seen.add(identifier)
    return _governed_result(experiment_identifiers=tuple(sorted(seen)))


def _governed_result(
    *,
    experiment_identifiers: tuple[str, ...],
    experiment_registry_version: str = EXPERIMENT_REGISTRY_VERSION,
) -> dict[str, Any]:
    return {
        "result_type": EXPERIMENT_REGISTRY_RESULT,
        "experiment_registry_version": experiment_registry_version,
        "experiment_registry_authority": EXPERIMENT_REGISTRY_AUTHORITY,
        "experiment_identifiers": experiment_identifiers,
        "evidence_only": True,
        "non_authoritative": True,
        "immutable_registry_records_only": True,
        "experiment_execution": False,
        "registry_persistence": False,
        "scoring": False,
        "attribution_execution": False,
        "evaluation_execution": False,
        "package_set_selection": False,
        "reproducibility_engine": False,
        "baseline_vs_candidate_comparison": False,
        "as_of_feature_logic": False,
        "filesystem_reads": False,
        "package_reads": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": EXPERIMENT_REGISTRY_AUTHORITY_BOUNDARY,
    }
