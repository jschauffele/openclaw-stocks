"""Pure in-memory package-set inclusion/exclusion rules governance (Gate D).

This module defines deterministic package-set rule identifiers (inclusion and
exclusion), a governed versioned package-set governance authority, and pure
validators over already-loaded rule and package-set governance record metadata.
It reads no replay packages, discovers no packages, selects no packages,
touches no filesystem, computes no scores, performs no attribution, experiment,
evaluation, reproducibility, baseline-vs-candidate, or as-of execution, and
carries no promotion, broker, strategy, risk, execution, paper-trading, or
live-trading authority.

Declaring inclusion/exclusion rules here does not read, discover, or select any
package; it only governs which finalized, immutable replay-package evidence a
future, separately approved evaluation set may consider. Mutable, draft,
unfinalized, or conflicting evidence fails closed.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders package-set inclusion/exclusion rules as the fourth
Gate D implementation unit, following metric (Unit 1), attribution (Unit 2),
and experiment registry (Unit 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


PACKAGE_SET_GOVERNANCE = "package_set_governance_in_memory_only"
PACKAGE_SET_GOVERNANCE_VERSION = "0.1-package-set"
SUPPORTED_PACKAGE_SET_GOVERNANCE_VERSIONS: tuple[str, ...] = (
    PACKAGE_SET_GOVERNANCE_VERSION,
)
PACKAGE_SET_GOVERNANCE_RESULT = "package_set_governance_result"

RULE_KIND_INCLUSION = "inclusion"
RULE_KIND_EXCLUSION = "exclusion"
KNOWN_RULE_KINDS: tuple[str, ...] = (RULE_KIND_INCLUSION, RULE_KIND_EXCLUSION)

# Inclusion rule identifiers: conditions under which a package MAY be included.
INCLUDE_FINALIZED_IMMUTABLE = "include_finalized_immutable"
INCLUDE_RUN_ID_ALIGNED = "include_run_id_aligned"
INCLUDE_HASH_VERIFIED = "include_hash_verified"
INCLUDE_TERMINAL_COMPLETION_ELIGIBLE = "include_terminal_completion_eligible"

KNOWN_INCLUSION_RULES: tuple[str, ...] = (
    INCLUDE_FINALIZED_IMMUTABLE,
    INCLUDE_RUN_ID_ALIGNED,
    INCLUDE_HASH_VERIFIED,
    INCLUDE_TERMINAL_COMPLETION_ELIGIBLE,
)

# Exclusion rule identifiers: conditions under which a package MUST be excluded.
EXCLUDE_DRAFT_OR_INCOMPLETE = "exclude_draft_or_incomplete"
EXCLUDE_MUTABLE = "exclude_mutable"
EXCLUDE_STALE = "exclude_stale"
EXCLUDE_MIXED_RUN_ID = "exclude_mixed_run_id"
EXCLUDE_UNHASHABLE_OR_HASH_MISMATCH = "exclude_unhashable_or_hash_mismatch"
EXCLUDE_INVALIDATED = "exclude_invalidated"
EXCLUDE_ERROR_TERMINAL_STATUS = "exclude_error_terminal_status"

KNOWN_EXCLUSION_RULES: tuple[str, ...] = (
    EXCLUDE_DRAFT_OR_INCOMPLETE,
    EXCLUDE_MUTABLE,
    EXCLUDE_STALE,
    EXCLUDE_MIXED_RUN_ID,
    EXCLUDE_UNHASHABLE_OR_HASH_MISMATCH,
    EXCLUDE_INVALIDATED,
    EXCLUDE_ERROR_TERMINAL_STATUS,
)

KNOWN_PACKAGE_SET_RULES: tuple[str, ...] = (
    *KNOWN_INCLUSION_RULES,
    *KNOWN_EXCLUSION_RULES,
)

# Record fields that would imply authority this governance must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "package_reads",
    "package_discovery",
    "package_selection_execution",
    "attribution_execution",
    "experiment_execution",
    "evaluation_execution",
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

PACKAGE_SET_GOVERNANCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_package_set_governance_version",
    "unsupported_package_set_governance_version",
    "missing_rule_identifier",
    "unknown_rule_identifier",
    "unknown_rule_kind",
    "rule_kind_mismatch",
    "duplicate_rule_identifier",
    "empty_inclusion_rule_set",
    "empty_exclusion_rule_set",
    "conflicting_include_exclude",
    "empty_package_reference_set",
    "missing_immutable_evidence_marker",
    "mutable_package_marker",
    "missing_finalization_marker",
    "malformed_record",
    "authority_bearing_field_present",
)

PACKAGE_SET_GOVERNANCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "inclusion_exclusion_rule_governance_only",
    "evidence_only",
    "non_authoritative",
    "finalized_immutable_evidence_only",
    "no_package_reads",
    "no_package_discovery",
    "no_package_selection_execution",
    "no_filesystem_reads",
    "no_scoring",
    "no_attribution_execution",
    "no_experiment_execution",
    "no_evaluation_execution",
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
class PackageSetGovernance:
    """Static governed package-set rule vocabulary and version."""

    version: str = PACKAGE_SET_GOVERNANCE_VERSION
    inclusion_rules: tuple[str, ...] = KNOWN_INCLUSION_RULES
    exclusion_rules: tuple[str, ...] = KNOWN_EXCLUSION_RULES
    authority_boundary: tuple[str, ...] = PACKAGE_SET_GOVERNANCE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class PackageSetGovernanceFailClosedConditions:
    """Static fail-closed condition vocabulary for package-set governance."""

    conditions: tuple[str, ...] = PACKAGE_SET_GOVERNANCE_FAIL_CLOSED_CONDITIONS


def is_known_inclusion_rule(identifier: object) -> bool:
    """Return True only for an exactly-known governed inclusion rule."""

    return isinstance(identifier, str) and identifier in KNOWN_INCLUSION_RULES


def is_known_exclusion_rule(identifier: object) -> bool:
    """Return True only for an exactly-known governed exclusion rule."""

    return isinstance(identifier, str) and identifier in KNOWN_EXCLUSION_RULES


def is_known_package_set_rule(identifier: object) -> bool:
    """Return True only for an exactly-known governed package-set rule."""

    return isinstance(identifier, str) and identifier in KNOWN_PACKAGE_SET_RULES


def validate_package_set_rule_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded package-set rule record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("package-set rule record must be already-loaded metadata")

    version = record.get("package_set_governance_version")
    if not version:
        raise ValueError("missing package set governance version")
    if version not in SUPPORTED_PACKAGE_SET_GOVERNANCE_VERSIONS:
        raise ValueError(f"unsupported package set governance version: '{version}'")

    rule_kind = record.get("rule_kind")
    if not rule_kind:
        raise ValueError("missing rule kind")
    if rule_kind not in KNOWN_RULE_KINDS:
        raise ValueError(f"unknown rule kind: '{rule_kind}'")

    identifier = record.get("rule_identifier")
    if not identifier:
        raise ValueError("missing rule identifier")
    if not isinstance(identifier, str) or identifier not in KNOWN_PACKAGE_SET_RULES:
        raise ValueError(f"unknown rule identifier: '{identifier}'")

    allowed = (
        KNOWN_INCLUSION_RULES
        if rule_kind == RULE_KIND_INCLUSION
        else KNOWN_EXCLUSION_RULES
    )
    if identifier not in allowed:
        raise ValueError(f"rule kind mismatch for '{identifier}'")

    _reject_authority_fields(record)
    return _governed_result(rule_identifiers=(identifier,))


def validate_package_set_governance_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one already-loaded package-set governance record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("package-set governance record must be already-loaded metadata")

    version = record.get("package_set_governance_version")
    if not version:
        raise ValueError("missing package set governance version")
    if version not in SUPPORTED_PACKAGE_SET_GOVERNANCE_VERSIONS:
        raise ValueError(f"unsupported package set governance version: '{version}'")

    inclusion_rules = _validate_rule_list(
        record.get("inclusion_rules"), KNOWN_INCLUSION_RULES, RULE_KIND_INCLUSION
    )
    exclusion_rules = _validate_rule_list(
        record.get("exclusion_rules"), KNOWN_EXCLUSION_RULES, RULE_KIND_EXCLUSION
    )
    if set(inclusion_rules) & set(exclusion_rules):
        raise ValueError("conflicting include/exclude rules")

    included_ids = tuple(record.get("included_package_ids", ()))
    excluded_ids = tuple(record.get("excluded_package_ids", ()))
    if set(included_ids) & set(excluded_ids):
        raise ValueError("conflicting include/exclude rules")

    references = record.get("package_references")
    if not isinstance(references, (tuple, list)) or not references:
        raise ValueError("empty package reference set")
    for reference in references:
        _validate_package_reference(reference)

    _reject_authority_fields(record)
    return _governed_result(
        rule_identifiers=(*inclusion_rules, *exclusion_rules),
    )


def _validate_rule_list(
    rules: object,
    known: tuple[str, ...],
    rule_kind: str,
) -> tuple[str, ...]:
    if not isinstance(rules, (tuple, list)):
        raise TypeError(f"{rule_kind} rules must be a tuple or list")
    if not rules:
        raise ValueError(f"empty {rule_kind} rule set")
    seen: set[str] = set()
    for identifier in rules:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("missing rule identifier")
        if identifier not in known:
            raise ValueError(f"unknown rule identifier: '{identifier}'")
        if identifier in seen:
            raise ValueError(f"duplicate rule identifier: '{identifier}'")
        seen.add(identifier)
    return tuple(rules)


def _validate_package_reference(reference: object) -> None:
    if not isinstance(reference, Mapping):
        raise TypeError("package reference must be already-loaded metadata")
    if reference.get("mutable"):
        raise ValueError("mutable package marker")
    if reference.get("immutable") is not True:
        raise ValueError("missing immutable evidence marker")
    finalized = reference.get("finalized") is True or (
        reference.get("lifecycle_status") == "finalized"
    )
    if not finalized:
        raise ValueError("missing finalization marker")
    _reject_authority_fields(reference)


def _reject_authority_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(*, rule_identifiers: tuple[str, ...]) -> dict[str, Any]:
    return {
        "result_type": PACKAGE_SET_GOVERNANCE_RESULT,
        "package_set_governance_version": PACKAGE_SET_GOVERNANCE_VERSION,
        "rule_identifiers": rule_identifiers,
        "evidence_only": True,
        "non_authoritative": True,
        "finalized_immutable_evidence_only": True,
        "package_reads": False,
        "package_discovery": False,
        "package_selection_execution": False,
        "filesystem_reads": False,
        "scoring": False,
        "attribution_execution": False,
        "experiment_execution": False,
        "evaluation_execution": False,
        "reproducibility_engine": False,
        "baseline_vs_candidate_comparison": False,
        "as_of_feature_logic": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": PACKAGE_SET_GOVERNANCE_AUTHORITY_BOUNDARY,
    }
