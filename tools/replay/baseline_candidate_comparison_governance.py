"""Pure in-memory baseline-vs-candidate comparison rules governance (Gate D Unit 7).

This module defines deterministic comparison rule identifiers, baseline identity
rules, candidate identity pairing rules, and a governed versioned authority over
already-loaded comparison rule and baseline-vs-candidate pairing record
metadata. It executes no comparison, computes no scores, runs no strategy,
generates no signals, runs no risk/execution/replay/evaluation logic, reads no
packages, discovers no packages, selects no packages, touches no filesystem,
performs no attribution, experiment, or as-of logic, and carries no promotion,
broker, strategy/risk/execution, paper-trading, or live-trading authority.

A pairing record declares that an approved baseline and a candidate are eligible
to be compared by a future, separately approved comparison engine. Baseline and
candidate identity are strictly distinct: a baseline must be explicitly
baseline-marked (and not candidate-marked); a candidate must be explicitly
candidate-marked (and not production/approved/live-marked). Mismatched run
scope, mutable evidence, or missing immutability/reproducibility/version
declarations fail closed. Governing a pairing here compares nothing and
authorizes nothing.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders baseline-vs-candidate comparison rules as the seventh
Gate D implementation unit, following metric (Unit 1), attribution (Unit 2),
experiment registry (Unit 3), package-set (Unit 4), reproducibility (Unit 5),
and candidate strategy (Unit 6) governance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.candidate_strategy_governance import (
    is_valid_candidate_strategy_identifier,
    is_valid_parameter_set_identifier as is_valid_candidate_parameter_set_identifier,
)


COMPARISON_GOVERNANCE = "baseline_candidate_comparison_governance_in_memory_only"
COMPARISON_GOVERNANCE_VERSION = "0.1-comparison"
SUPPORTED_COMPARISON_GOVERNANCE_VERSIONS: tuple[str, ...] = (
    COMPARISON_GOVERNANCE_VERSION,
)
COMPARISON_GOVERNANCE_RESULT = "baseline_candidate_comparison_governance_result"

BASELINE_STRATEGY_ID_PREFIX = "baseline_strategy_"
BASELINE_PARAMETER_SET_ID_PREFIX = "baseline_paramset_"
COMPARISON_IDENTIFIER_MAX_LENGTH = 128
_IDENTIFIER_BODY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-"
)

# Comparison rule identifiers: the eligibility dimensions a pairing must declare.
COMPARE_RUN_SCOPE_ALIGNED = "compare_run_scope_aligned"
COMPARE_IMMUTABLE_EVIDENCE = "compare_immutable_evidence"
COMPARE_REPRODUCIBILITY_DECLARED = "compare_reproducibility_declared"
COMPARE_STRATEGY_IDENTITY_VERSIONED = "compare_strategy_identity_versioned"
COMPARE_PARAMETER_SET_VERSIONED = "compare_parameter_set_versioned"
COMPARE_BASELINE_CANDIDATE_DISTINCT = "compare_baseline_candidate_distinct"

KNOWN_COMPARISON_RULES: tuple[str, ...] = (
    COMPARE_RUN_SCOPE_ALIGNED,
    COMPARE_IMMUTABLE_EVIDENCE,
    COMPARE_REPRODUCIBILITY_DECLARED,
    COMPARE_STRATEGY_IDENTITY_VERSIONED,
    COMPARE_PARAMETER_SET_VERSIONED,
    COMPARE_BASELINE_CANDIDATE_DISTINCT,
)

# Markers that assert production/approved/live identity; forbidden on candidates.
CANDIDATE_FORBIDDEN_MARKER_FIELDS: tuple[str, ...] = (
    "production",
    "approved",
    "live",
    "promoted",
)

# Record fields that would imply authority this governance must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "comparison_execution",
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
    "as_of_feature_logic",
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

COMPARISON_GOVERNANCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_comparison_governance_version",
    "unsupported_comparison_governance_version",
    "missing_rule_identifier",
    "unknown_rule_identifier",
    "duplicate_rule_identifier",
    "empty_rule_set",
    "missing_baseline_record",
    "missing_candidate_record",
    "malformed_baseline_identifier",
    "malformed_candidate_identifier",
    "missing_baseline_marker",
    "missing_candidate_marker",
    "candidate_marker_on_baseline",
    "production_approved_live_marker_on_candidate",
    "mismatched_run_scope",
    "mutable_evidence_marker",
    "missing_immutability_declaration",
    "missing_reproducibility_declaration",
    "missing_strategy_version",
    "missing_parameter_set_version",
    "malformed_record",
    "authority_bearing_field_present",
)

COMPARISON_GOVERNANCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "baseline_candidate_comparison_rule_governance_only",
    "evidence_only",
    "non_authoritative",
    "baseline_distinct_from_candidate",
    "no_comparison_execution",
    "no_scoring",
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
    "no_attribution_execution",
    "no_experiment_execution",
    "no_as_of_feature_logic",
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_approval",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class BaselineCandidateComparisonGovernance:
    """Static governed comparison rule vocabulary and version."""

    version: str = COMPARISON_GOVERNANCE_VERSION
    known_rules: tuple[str, ...] = KNOWN_COMPARISON_RULES
    authority_boundary: tuple[str, ...] = COMPARISON_GOVERNANCE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class BaselineCandidateComparisonFailClosedConditions:
    """Static fail-closed condition vocabulary for comparison governance."""

    conditions: tuple[str, ...] = COMPARISON_GOVERNANCE_FAIL_CLOSED_CONDITIONS


def _is_valid_identifier(identifier: object, prefix: str) -> bool:
    if not isinstance(identifier, str):
        return False
    if not identifier.startswith(prefix):
        return False
    if len(identifier) <= len(prefix):
        return False
    if len(identifier) > COMPARISON_IDENTIFIER_MAX_LENGTH:
        return False
    if ".." in identifier or "order_state" in identifier:
        return False
    body = identifier[len(prefix):]
    return all(char in _IDENTIFIER_BODY_CHARS for char in body)


def is_valid_baseline_strategy_identifier(identifier: object) -> bool:
    """Return True only for a well-formed approved-baseline strategy identifier."""

    return _is_valid_identifier(identifier, BASELINE_STRATEGY_ID_PREFIX)


def is_valid_baseline_parameter_set_identifier(identifier: object) -> bool:
    """Return True only for a well-formed baseline parameter-set identifier."""

    return _is_valid_identifier(identifier, BASELINE_PARAMETER_SET_ID_PREFIX)


def is_known_comparison_rule(identifier: object) -> bool:
    """Return True only for an exactly-known governed comparison rule."""

    return isinstance(identifier, str) and identifier in KNOWN_COMPARISON_RULES


def validate_comparison_rule_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded comparison rule record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("comparison rule record must be already-loaded metadata")
    _validate_version(record)
    identifier = record.get("rule_identifier")
    if not identifier:
        raise ValueError("missing rule identifier")
    if not isinstance(identifier, str) or identifier not in KNOWN_COMPARISON_RULES:
        raise ValueError(f"unknown rule identifier: '{identifier}'")
    _reject_authority_fields(record)
    return _governed_result(comparison_rules=(identifier,))


def validate_baseline_candidate_pairing_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded baseline-vs-candidate pairing record."""

    if not isinstance(record, Mapping):
        raise TypeError("pairing record must be already-loaded metadata")
    _validate_version(record)
    rules = _validate_rule_list(record.get("comparison_rules"))

    baseline = record.get("baseline")
    if not isinstance(baseline, Mapping) or not baseline:
        raise ValueError("missing baseline record")
    candidate = record.get("candidate")
    if not isinstance(candidate, Mapping) or not candidate:
        raise ValueError("missing candidate record")

    baseline_scope = _validate_baseline_record(baseline)
    candidate_scope = _validate_candidate_record(candidate)
    if baseline_scope != candidate_scope:
        raise ValueError("mismatched run scope")

    _reject_authority_fields(record)
    return _governed_result(
        comparison_rules=rules,
        baseline_strategy_id=baseline["strategy_id"],
        candidate_strategy_id=candidate["strategy_id"],
    )


def _validate_baseline_record(baseline: Mapping[str, Any]) -> str:
    strategy_id = baseline.get("strategy_id")
    if not strategy_id or not is_valid_baseline_strategy_identifier(strategy_id):
        raise ValueError(f"malformed baseline identifier: '{strategy_id}'")
    if baseline.get("is_baseline") is not True:
        raise ValueError("missing baseline marker")
    if baseline.get("is_candidate"):
        raise ValueError("candidate marker on baseline record")
    if not baseline.get("strategy_version"):
        raise ValueError("missing strategy version")
    parameter_set_id = baseline.get("parameter_set_id")
    if not parameter_set_id or not is_valid_baseline_parameter_set_identifier(
        parameter_set_id
    ):
        raise ValueError(f"malformed baseline identifier: '{parameter_set_id}'")
    if not baseline.get("parameter_set_version"):
        raise ValueError("missing parameter set version")
    return _validate_shared_evidence_markers(baseline)


def _validate_candidate_record(candidate: Mapping[str, Any]) -> str:
    strategy_id = candidate.get("strategy_id")
    if not strategy_id or not is_valid_candidate_strategy_identifier(strategy_id):
        raise ValueError(f"malformed candidate identifier: '{strategy_id}'")
    if candidate.get("is_candidate") is not True:
        raise ValueError("missing candidate marker")
    for field in CANDIDATE_FORBIDDEN_MARKER_FIELDS:
        if candidate.get(field):
            raise ValueError("production/approved/live marker on candidate")
    if candidate.get("is_baseline"):
        raise ValueError("production/approved/live marker on candidate")
    if not candidate.get("strategy_version"):
        raise ValueError("missing strategy version")
    parameter_set_id = candidate.get("parameter_set_id")
    if not parameter_set_id or not is_valid_candidate_parameter_set_identifier(
        parameter_set_id
    ):
        raise ValueError(f"malformed candidate identifier: '{parameter_set_id}'")
    if not candidate.get("parameter_set_version"):
        raise ValueError("missing parameter set version")
    return _validate_shared_evidence_markers(candidate)


def _validate_shared_evidence_markers(record: Mapping[str, Any]) -> str:
    if record.get("mutable_evidence"):
        raise ValueError("mutable evidence marker")
    if record.get("immutable_evidence") is not True:
        raise ValueError("missing immutability declaration")
    if record.get("reproducibility_declared") is not True:
        raise ValueError("missing reproducibility declaration")
    run_scope = record.get("run_scope")
    if not run_scope:
        raise ValueError("mismatched run scope")
    _reject_authority_fields(record)
    return run_scope


def _validate_version(record: Mapping[str, Any]) -> None:
    version = record.get("comparison_governance_version")
    if not version:
        raise ValueError("missing comparison governance version")
    if version not in SUPPORTED_COMPARISON_GOVERNANCE_VERSIONS:
        raise ValueError(f"unsupported comparison governance version: '{version}'")


def _validate_rule_list(rules: object) -> tuple[str, ...]:
    if not isinstance(rules, (tuple, list)):
        raise TypeError("comparison rules must be a tuple or list")
    if not rules:
        raise ValueError("empty rule set")
    seen: set[str] = set()
    for identifier in rules:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("missing rule identifier")
        if identifier not in KNOWN_COMPARISON_RULES:
            raise ValueError(f"unknown rule identifier: '{identifier}'")
        if identifier in seen:
            raise ValueError(f"duplicate rule identifier: '{identifier}'")
        seen.add(identifier)
    return tuple(rules)


def _reject_authority_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(
    *,
    comparison_rules: tuple[str, ...],
    baseline_strategy_id: str = "",
    candidate_strategy_id: str = "",
) -> dict[str, Any]:
    return {
        "result_type": COMPARISON_GOVERNANCE_RESULT,
        "comparison_governance_version": COMPARISON_GOVERNANCE_VERSION,
        "comparison_rules": comparison_rules,
        "baseline_strategy_id": baseline_strategy_id,
        "candidate_strategy_id": candidate_strategy_id,
        "evidence_only": True,
        "non_authoritative": True,
        "baseline_distinct_from_candidate": True,
        "comparison_execution": False,
        "scoring": False,
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
        "attribution_execution": False,
        "experiment_execution": False,
        "as_of_feature_logic": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": COMPARISON_GOVERNANCE_AUTHORITY_BOUNDARY,
    }
