"""Pure in-memory candidate strategy identity + parameter versioning governance.

This module (Gate D Unit 6) defines deterministic candidate strategy identity
and version rules, deterministic candidate parameter-set identity and version
rules, and a governed versioned authority over already-loaded candidate strategy
and parameter-set record metadata. It carries no strategy behavior, no signal
generation, no risk logic, no execution logic, no replay or evaluation
execution, reads no packages, discovers no packages, selects no packages,
touches no filesystem, computes no scores, performs no attribution, experiment,
baseline-vs-candidate, or as-of logic, and carries no promotion, broker,
strategy/risk/execution, paper-trading, or live-trading authority.

Candidate identity is strictly distinct from approved production identity:
candidate strategy and parameter-set identifiers are namespaced (``cand_*``),
must be explicitly marked as candidate, and any production/approved/live marker
fails closed. Governing a candidate identity here runs nothing and authorizes
nothing.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders candidate strategy identity + parameter versioning as
the sixth Gate D implementation unit, following metric (Unit 1), attribution
(Unit 2), experiment registry (Unit 3), package-set (Unit 4), and
reproducibility (Unit 5) governance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


CANDIDATE_STRATEGY_GOVERNANCE = "candidate_strategy_governance_in_memory_only"
CANDIDATE_STRATEGY_GOVERNANCE_VERSION = "0.1-candidate-strategy"
SUPPORTED_CANDIDATE_STRATEGY_GOVERNANCE_VERSIONS: tuple[str, ...] = (
    CANDIDATE_STRATEGY_GOVERNANCE_VERSION,
)
CANDIDATE_STRATEGY_GOVERNANCE_RESULT = "candidate_strategy_governance_result"

CANDIDATE_STRATEGY_ID_PREFIX = "cand_strategy_"
CANDIDATE_PARAMETER_SET_ID_PREFIX = "cand_paramset_"
CANDIDATE_IDENTIFIER_MAX_LENGTH = 128
_IDENTIFIER_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

# Record fields that assert production/approved/live identity and fail closed:
# this vocabulary governs candidate evidence only, never production authority.
PRODUCTION_MARKER_FIELDS: tuple[str, ...] = (
    "production",
    "approved",
    "live",
    "promoted",
    "production_strategy",
    "approved_strategy",
    "live_strategy",
)

# Record fields that would imply authority this governance must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "strategy_behavior",
    "signal_generation",
    "risk_logic",
    "execution_logic",
    "replay_execution",
    "evaluation_execution",
    "package_reads",
    "package_discovery",
    "package_selection_execution",
    "attribution_execution",
    "experiment_execution",
    "baseline_vs_candidate_comparison",
    "as_of_feature_logic",
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

CANDIDATE_STRATEGY_GOVERNANCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_candidate_strategy_governance_version",
    "unsupported_candidate_strategy_governance_version",
    "missing_strategy_identifier",
    "malformed_strategy_identifier",
    "missing_strategy_version",
    "missing_parameter_set_identifier",
    "malformed_parameter_set_identifier",
    "missing_parameter_set_version",
    "missing_candidate_marker",
    "production_approved_live_marker_present",
    "mutable_parameter_marker",
    "missing_immutability_declaration",
    "duplicate_strategy_identifier",
    "duplicate_parameter_set_identifier",
    "empty_record_set",
    "malformed_record",
    "authority_bearing_field_present",
)

CANDIDATE_STRATEGY_GOVERNANCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "candidate_identity_and_versioning_governance_only",
    "evidence_only",
    "non_authoritative",
    "candidate_distinct_from_approved_production",
    "no_strategy_behavior",
    "no_signal_generation",
    "no_risk_logic",
    "no_execution_logic",
    "no_replay_execution",
    "no_evaluation_execution",
    "no_package_reads",
    "no_package_discovery",
    "no_package_selection_execution",
    "no_filesystem_reads",
    "no_scoring",
    "no_attribution_execution",
    "no_experiment_execution",
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
class CandidateStrategyGovernance:
    """Static governed candidate strategy/parameter governance and version."""

    version: str = CANDIDATE_STRATEGY_GOVERNANCE_VERSION
    strategy_id_prefix: str = CANDIDATE_STRATEGY_ID_PREFIX
    parameter_set_id_prefix: str = CANDIDATE_PARAMETER_SET_ID_PREFIX
    authority_boundary: tuple[str, ...] = (
        CANDIDATE_STRATEGY_GOVERNANCE_AUTHORITY_BOUNDARY
    )


@dataclass(frozen=True, slots=True)
class CandidateStrategyGovernanceFailClosedConditions:
    """Static fail-closed condition vocabulary for candidate strategy governance."""

    conditions: tuple[str, ...] = (
        CANDIDATE_STRATEGY_GOVERNANCE_FAIL_CLOSED_CONDITIONS
    )


def _is_valid_identifier(identifier: object, prefix: str) -> bool:
    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(prefix):
        return False
    if len(identifier) <= len(prefix):
        return False
    if len(identifier) > CANDIDATE_IDENTIFIER_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(prefix):]
    return all(char in _IDENTIFIER_BODY_CHARS for char in body)


def is_valid_candidate_strategy_identifier(identifier: object) -> bool:
    """Return True only for a well-formed candidate strategy identifier."""

    return _is_valid_identifier(identifier, CANDIDATE_STRATEGY_ID_PREFIX)


def is_valid_parameter_set_identifier(identifier: object) -> bool:
    """Return True only for a well-formed candidate parameter-set identifier."""

    return _is_valid_identifier(identifier, CANDIDATE_PARAMETER_SET_ID_PREFIX)


def validate_candidate_strategy_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded candidate strategy record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("candidate strategy record must be already-loaded metadata")

    _validate_version(record)

    strategy_id = record.get("strategy_id")
    if not strategy_id:
        raise ValueError("missing strategy identifier")
    if not is_valid_candidate_strategy_identifier(strategy_id):
        raise ValueError(f"malformed strategy identifier: '{strategy_id}'")

    if not record.get("strategy_version"):
        raise ValueError("missing strategy version")

    _require_candidate_marker(record)
    _reject_production_markers(record)
    _reject_authority_fields(record)
    return _governed_result(strategy_identifiers=(strategy_id,))


def validate_parameter_set_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded candidate parameter-set record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("parameter-set record must be already-loaded metadata")

    _validate_version(record)

    parameter_set_id = record.get("parameter_set_id")
    if not parameter_set_id:
        raise ValueError("missing parameter set identifier")
    if not is_valid_parameter_set_identifier(parameter_set_id):
        raise ValueError(f"malformed parameter set identifier: '{parameter_set_id}'")

    if not record.get("parameter_set_version"):
        raise ValueError("missing parameter set version")

    _require_candidate_marker(record)
    if record.get("mutable"):
        raise ValueError("mutable parameter marker")
    if record.get("immutable") is not True:
        raise ValueError("missing immutability declaration")
    _reject_production_markers(record)
    _reject_authority_fields(record)
    return _governed_result(parameter_set_identifiers=(parameter_set_id,))


def validate_candidate_strategy_record_set(records: object) -> dict[str, Any]:
    """Validate candidate strategy records with unique ids, or fail closed."""

    seen = _validate_record_set(
        records, validate_candidate_strategy_record, "strategy_identifiers"
    )
    return _governed_result(strategy_identifiers=tuple(sorted(seen)))


def validate_parameter_set_record_set(records: object) -> dict[str, Any]:
    """Validate parameter-set records with unique ids, or fail closed."""

    seen = _validate_record_set(
        records, validate_parameter_set_record, "parameter_set_identifiers"
    )
    return _governed_result(parameter_set_identifiers=tuple(sorted(seen)))


def _validate_record_set(records, validator, result_key) -> set[str]:
    if not isinstance(records, (tuple, list)):
        raise TypeError("records must be a tuple or list")
    if not records:
        raise ValueError("empty record set")
    seen: set[str] = set()
    for record in records:
        result = validator(record)
        identifier = result[result_key][0]
        if identifier in seen:
            label = (
                "strategy"
                if result_key == "strategy_identifiers"
                else "parameter set"
            )
            raise ValueError(f"duplicate {label} identifier: '{identifier}'")
        seen.add(identifier)
    return seen


def _validate_version(record: Mapping[str, Any]) -> None:
    version = record.get("candidate_strategy_governance_version")
    if not version:
        raise ValueError("missing candidate strategy governance version")
    if version not in SUPPORTED_CANDIDATE_STRATEGY_GOVERNANCE_VERSIONS:
        raise ValueError(
            f"unsupported candidate strategy governance version: '{version}'"
        )


def _require_candidate_marker(record: Mapping[str, Any]) -> None:
    if record.get("is_candidate") is not True:
        raise ValueError("missing candidate marker")


def _reject_production_markers(record: Mapping[str, Any]) -> None:
    for field in PRODUCTION_MARKER_FIELDS:
        if record.get(field):
            raise ValueError("production/approved/live marker present")


def _reject_authority_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(
    *,
    strategy_identifiers: tuple[str, ...] = (),
    parameter_set_identifiers: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "result_type": CANDIDATE_STRATEGY_GOVERNANCE_RESULT,
        "candidate_strategy_governance_version": (
            CANDIDATE_STRATEGY_GOVERNANCE_VERSION
        ),
        "strategy_identifiers": strategy_identifiers,
        "parameter_set_identifiers": parameter_set_identifiers,
        "evidence_only": True,
        "non_authoritative": True,
        "candidate_distinct_from_approved_production": True,
        "strategy_behavior": False,
        "signal_generation": False,
        "risk_logic": False,
        "execution_logic": False,
        "replay_execution": False,
        "evaluation_execution": False,
        "package_reads": False,
        "package_discovery": False,
        "package_selection_execution": False,
        "filesystem_reads": False,
        "scoring": False,
        "attribution_execution": False,
        "experiment_execution": False,
        "baseline_vs_candidate_comparison": False,
        "as_of_feature_logic": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": CANDIDATE_STRATEGY_GOVERNANCE_AUTHORITY_BOUNDARY,
    }
