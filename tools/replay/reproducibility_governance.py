"""Pure in-memory reproducibility rules governance (Gate D Unit 5).

This module defines deterministic reproducibility rule identifiers, a governed
versioned reproducibility authority, and pure validators over already-loaded
reproducibility rule and governance record metadata. It runs no replay, runs no
evaluation, reads no packages, discovers no packages, selects no packages,
touches no filesystem, computes no scores, performs no attribution, experiment,
baseline-vs-candidate, or as-of execution, and carries no promotion, broker,
strategy, risk, execution, paper-trading, or live-trading authority.

A reproducibility governance record declares that a future, separately approved
evaluation run satisfies the determinism prerequisites (pinned commit identity,
deterministic vocabulary versions, canonical serialization, hash-verified
inputs, immutable evidence, stable ordering, environment-independent
comparison). Mutable, nondeterministic, or environment-dependent declarations
fail closed. Declaring reproducibility here runs nothing and authorizes nothing.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders reproducibility rules as the fifth Gate D
implementation unit, following metric (Unit 1), attribution (Unit 2),
experiment registry (Unit 3), and package-set (Unit 4) governance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REPRODUCIBILITY_GOVERNANCE = "reproducibility_governance_in_memory_only"
REPRODUCIBILITY_GOVERNANCE_VERSION = "0.1-reproducibility"
SUPPORTED_REPRODUCIBILITY_GOVERNANCE_VERSIONS: tuple[str, ...] = (
    REPRODUCIBILITY_GOVERNANCE_VERSION,
)
REPRODUCIBILITY_GOVERNANCE_RESULT = "reproducibility_governance_result"

# Reproducibility rule identifiers: determinism prerequisites a governance
# record must declare.
REPRO_PINNED_COMMIT_IDENTITY = "pinned_commit_identity"
REPRO_DETERMINISTIC_VOCABULARY_VERSIONS = "deterministic_vocabulary_versions"
REPRO_CANONICAL_SERIALIZATION = "canonical_serialization"
REPRO_HASH_VERIFIED_INPUTS = "hash_verified_inputs"
REPRO_IMMUTABLE_EVIDENCE = "immutable_evidence"
REPRO_STABLE_ORDERING = "stable_ordering"
REPRO_ENVIRONMENT_INDEPENDENT_COMPARISON = "environment_independent_comparison"

KNOWN_REPRODUCIBILITY_RULES: tuple[str, ...] = (
    REPRO_PINNED_COMMIT_IDENTITY,
    REPRO_DETERMINISTIC_VOCABULARY_VERSIONS,
    REPRO_CANONICAL_SERIALIZATION,
    REPRO_HASH_VERIFIED_INPUTS,
    REPRO_IMMUTABLE_EVIDENCE,
    REPRO_STABLE_ORDERING,
    REPRO_ENVIRONMENT_INDEPENDENT_COMPARISON,
)

# Record marker fields that indicate non-reproducible evidence and fail closed.
NONDETERMINISTIC_MARKER_FIELDS: tuple[str, ...] = (
    "mutable_inputs",
    "nondeterministic_order",
    "environment_dependent",
)

# Record fields that would imply authority this governance must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
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
    "strategy_authority",
    "risk_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

REPRODUCIBILITY_GOVERNANCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_reproducibility_governance_version",
    "unsupported_reproducibility_governance_version",
    "missing_rule_identifier",
    "unknown_rule_identifier",
    "duplicate_rule_identifier",
    "empty_rule_set",
    "missing_pinned_commit_declaration",
    "missing_canonical_serialization_declaration",
    "missing_hash_verification_declaration",
    "missing_immutable_evidence_declaration",
    "missing_stable_ordering_declaration",
    "missing_environment_independent_comparison_declaration",
    "mutable_input_marker",
    "nondeterministic_order_marker",
    "environment_dependent_marker",
    "malformed_record",
    "authority_bearing_field_present",
)

REPRODUCIBILITY_GOVERNANCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "reproducibility_rule_governance_only",
    "evidence_only",
    "non_authoritative",
    "deterministic_reproducible_evidence_only",
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
class ReproducibilityGovernance:
    """Static governed reproducibility rule vocabulary and version."""

    version: str = REPRODUCIBILITY_GOVERNANCE_VERSION
    known_rules: tuple[str, ...] = KNOWN_REPRODUCIBILITY_RULES
    authority_boundary: tuple[str, ...] = (
        REPRODUCIBILITY_GOVERNANCE_AUTHORITY_BOUNDARY
    )


@dataclass(frozen=True, slots=True)
class ReproducibilityGovernanceFailClosedConditions:
    """Static fail-closed condition vocabulary for reproducibility governance."""

    conditions: tuple[str, ...] = REPRODUCIBILITY_GOVERNANCE_FAIL_CLOSED_CONDITIONS


def is_known_reproducibility_rule(identifier: object) -> bool:
    """Return True only for an exactly-known governed reproducibility rule."""

    return isinstance(identifier, str) and identifier in KNOWN_REPRODUCIBILITY_RULES


def validate_reproducibility_rule_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded reproducibility rule record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("reproducibility rule record must be already-loaded metadata")

    _validate_version(record)

    identifier = record.get("rule_identifier")
    if not identifier:
        raise ValueError("missing rule identifier")
    if not isinstance(identifier, str) or identifier not in KNOWN_REPRODUCIBILITY_RULES:
        raise ValueError(f"unknown rule identifier: '{identifier}'")

    _reject_authority_fields(record)
    return _governed_result(rule_identifiers=(identifier,))


def validate_reproducibility_governance_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded reproducibility governance record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError(
            "reproducibility governance record must be already-loaded metadata"
        )

    _validate_version(record)

    rules = record.get("reproducibility_rules")
    if not isinstance(rules, (tuple, list)):
        raise TypeError("reproducibility rules must be a tuple or list")
    if not rules:
        raise ValueError("empty rule set")
    seen: set[str] = set()
    for identifier in rules:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("missing rule identifier")
        if identifier not in KNOWN_REPRODUCIBILITY_RULES:
            raise ValueError(f"unknown rule identifier: '{identifier}'")
        if identifier in seen:
            raise ValueError(f"duplicate rule identifier: '{identifier}'")
        seen.add(identifier)

    _validate_required_declarations(record)
    _reject_nondeterministic_markers(record)
    _reject_authority_fields(record)
    return _governed_result(rule_identifiers=tuple(rules))


def _validate_version(record: Mapping[str, Any]) -> None:
    version = record.get("reproducibility_governance_version")
    if not version:
        raise ValueError("missing reproducibility governance version")
    if version not in SUPPORTED_REPRODUCIBILITY_GOVERNANCE_VERSIONS:
        raise ValueError(f"unsupported reproducibility governance version: '{version}'")


def _validate_required_declarations(record: Mapping[str, Any]) -> None:
    if not record.get("pinned_commit"):
        raise ValueError("missing pinned commit declaration")
    if record.get("canonical_serialization") is not True:
        raise ValueError("missing canonical serialization declaration")
    if record.get("hash_verified_inputs") is not True:
        raise ValueError("missing hash verification declaration")
    if record.get("immutable_evidence") is not True:
        raise ValueError("missing immutable evidence declaration")
    if record.get("stable_ordering") is not True:
        raise ValueError("missing stable ordering declaration")
    if record.get("environment_independent_comparison") is not True:
        raise ValueError(
            "missing environment independent comparison declaration"
        )


def _reject_nondeterministic_markers(record: Mapping[str, Any]) -> None:
    if record.get("mutable_inputs"):
        raise ValueError("mutable input marker")
    if record.get("nondeterministic_order"):
        raise ValueError("nondeterministic order marker")
    if record.get("environment_dependent"):
        raise ValueError("environment dependent marker")


def _reject_authority_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(*, rule_identifiers: tuple[str, ...]) -> dict[str, Any]:
    return {
        "result_type": REPRODUCIBILITY_GOVERNANCE_RESULT,
        "reproducibility_governance_version": REPRODUCIBILITY_GOVERNANCE_VERSION,
        "rule_identifiers": rule_identifiers,
        "evidence_only": True,
        "non_authoritative": True,
        "deterministic_reproducible_evidence_only": True,
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
        "authority_boundary": REPRODUCIBILITY_GOVERNANCE_AUTHORITY_BOUNDARY,
    }
