"""Pure in-memory as-of feature availability + decision-time evidence governance.

This module (Gate D Unit 8, the final Gate D prerequisite unit) defines
deterministic as-of evidence, decision-time evidence, and feature availability
rule identifiers, a governed versioned authority, and pure validators over
already-loaded as-of evidence record metadata. It enforces the no-look-ahead
rule (`available_at_timestamp <= decision_timestamp`) over caller-supplied
canonical UTC ISO-8601 timestamps. It computes no as-of features, generates no
features, executes no comparison, computes no scores, runs no strategy/signal/
risk/execution/replay/evaluation logic, reads no packages, discovers no
packages, selects no packages, touches no filesystem, performs no attribution
or experiment execution, and carries no promotion, broker, strategy/risk/
execution, paper-trading, or live-trading authority.

An as-of evidence record declares that a feature/evidence item was observable
at decision time. Evidence available after the decision time, future-dated,
post-decision, leaked, mutable, or missing the required no-look-ahead /
immutability / reproducibility declarations fails closed. Governing as-of
evidence here computes nothing and authorizes nothing.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders as-of feature availability + decision-time evidence
rules as the eighth and final Gate D implementation unit, following metric
(Unit 1) through baseline-vs-candidate comparison (Unit 7) governance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


ASOF_GOVERNANCE = "asof_evidence_governance_in_memory_only"
ASOF_GOVERNANCE_VERSION = "0.1-asof-evidence"
SUPPORTED_ASOF_GOVERNANCE_VERSIONS: tuple[str, ...] = (ASOF_GOVERNANCE_VERSION,)
ASOF_GOVERNANCE_RESULT = "asof_evidence_governance_result"

# As-of evidence rule identifiers.
ASOF_AVAILABILITY_BEFORE_DECISION = "asof_availability_before_decision"
ASOF_NO_LOOK_AHEAD = "asof_no_look_ahead"
ASOF_FRESHNESS_BOUNDED = "asof_freshness_bounded"

KNOWN_ASOF_EVIDENCE_RULES: tuple[str, ...] = (
    ASOF_AVAILABILITY_BEFORE_DECISION,
    ASOF_NO_LOOK_AHEAD,
    ASOF_FRESHNESS_BOUNDED,
)

# Decision-time evidence rule identifiers.
DECISION_TIME_DECLARED = "decision_time_declared"
DECISION_TIME_PRE_DECISION_SNAPSHOT = "decision_time_pre_decision_snapshot"

KNOWN_DECISION_TIME_RULES: tuple[str, ...] = (
    DECISION_TIME_DECLARED,
    DECISION_TIME_PRE_DECISION_SNAPSHOT,
)

# Feature availability rule identifiers.
FEATURE_AVAILABILITY_PROVEN = "feature_availability_proven"
FEATURE_PROVENANCE_VERSIONED = "feature_provenance_versioned"
FEATURE_REVISION_DISTINGUISHED = "feature_revision_distinguished"

KNOWN_FEATURE_AVAILABILITY_RULES: tuple[str, ...] = (
    FEATURE_AVAILABILITY_PROVEN,
    FEATURE_PROVENANCE_VERSIONED,
    FEATURE_REVISION_DISTINGUISHED,
)

KNOWN_ASOF_RULES: tuple[str, ...] = (
    *KNOWN_ASOF_EVIDENCE_RULES,
    *KNOWN_DECISION_TIME_RULES,
    *KNOWN_FEATURE_AVAILABILITY_RULES,
)

# Markers that indicate look-ahead / leaked / mutable evidence; all fail closed.
NONDETERMINISTIC_MARKER_FIELDS: tuple[str, ...] = (
    "future_dated",
    "post_decision",
    "leaked",
    "mutable_evidence",
)

# Record fields that would imply authority this governance must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "asof_computation_execution",
    "feature_generation",
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
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

ASOF_GOVERNANCE_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "missing_asof_governance_version",
    "unsupported_asof_governance_version",
    "missing_rule_identifier",
    "unknown_rule_identifier",
    "duplicate_rule_identifier",
    "empty_rule_set",
    "missing_decision_timestamp",
    "missing_available_at_timestamp",
    "malformed_timestamp",
    "evidence_availability_after_decision_time",
    "post_decision_observation",
    "future_dated_evidence_marker",
    "post_decision_evidence_marker",
    "leaked_evidence_marker",
    "missing_no_look_ahead_declaration",
    "mutable_evidence_marker",
    "missing_immutability_declaration",
    "missing_reproducibility_declaration",
    "malformed_record",
    "authority_bearing_field_present",
)

ASOF_GOVERNANCE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "asof_decision_time_evidence_rule_governance_only",
    "evidence_only",
    "non_authoritative",
    "no_look_ahead_enforced",
    "no_asof_computation_execution",
    "no_feature_generation",
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
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_approval",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class AsOfEvidenceGovernance:
    """Static governed as-of evidence rule vocabulary and version."""

    version: str = ASOF_GOVERNANCE_VERSION
    known_rules: tuple[str, ...] = KNOWN_ASOF_RULES
    authority_boundary: tuple[str, ...] = ASOF_GOVERNANCE_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class AsOfEvidenceGovernanceFailClosedConditions:
    """Static fail-closed condition vocabulary for as-of evidence governance."""

    conditions: tuple[str, ...] = ASOF_GOVERNANCE_FAIL_CLOSED_CONDITIONS


def is_known_asof_evidence_rule(identifier: object) -> bool:
    """Return True only for an exactly-known as-of evidence rule."""

    return isinstance(identifier, str) and identifier in KNOWN_ASOF_EVIDENCE_RULES


def is_known_decision_time_rule(identifier: object) -> bool:
    """Return True only for an exactly-known decision-time evidence rule."""

    return isinstance(identifier, str) and identifier in KNOWN_DECISION_TIME_RULES


def is_known_feature_availability_rule(identifier: object) -> bool:
    """Return True only for an exactly-known feature availability rule."""

    return (
        isinstance(identifier, str)
        and identifier in KNOWN_FEATURE_AVAILABILITY_RULES
    )


def is_known_asof_rule(identifier: object) -> bool:
    """Return True only for any exactly-known governed as-of rule."""

    return isinstance(identifier, str) and identifier in KNOWN_ASOF_RULES


def _is_utc_iso8601(value: object) -> bool:
    """Return True only for a canonical ``YYYY-MM-DDTHH:MM:SSZ`` UTC timestamp."""

    if not isinstance(value, str) or len(value) != 20:
        return False
    if value[4] != "-" or value[7] != "-" or value[10] != "T":
        return False
    if value[13] != ":" or value[16] != ":" or value[19] != "Z":
        return False
    digits = value[0:4] + value[5:7] + value[8:10] + value[11:13] + value[14:16] + value[17:19]
    return digits.isdigit()


def validate_asof_rule_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded as-of rule record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("as-of rule record must be already-loaded metadata")
    _validate_version(record)
    identifier = record.get("rule_identifier")
    if not identifier:
        raise ValueError("missing rule identifier")
    if not isinstance(identifier, str) or identifier not in KNOWN_ASOF_RULES:
        raise ValueError(f"unknown rule identifier: '{identifier}'")
    _reject_authority_fields(record)
    return _governed_result(asof_rules=(identifier,))


def validate_asof_evidence_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded as-of evidence record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("as-of evidence record must be already-loaded metadata")

    _validate_version(record)
    rules = _validate_rule_list(record.get("asof_rules"))

    decision_timestamp = record.get("decision_timestamp")
    if not decision_timestamp:
        raise ValueError("missing decision timestamp")
    if not _is_utc_iso8601(decision_timestamp):
        raise ValueError("malformed timestamp")

    available_at = record.get("available_at_timestamp")
    if not available_at:
        raise ValueError("missing available_at timestamp")
    if not _is_utc_iso8601(available_at):
        raise ValueError("malformed timestamp")
    if available_at > decision_timestamp:
        raise ValueError("evidence availability after decision time")

    observation_timestamp = record.get("observation_timestamp")
    if observation_timestamp is not None:
        if not _is_utc_iso8601(observation_timestamp):
            raise ValueError("malformed timestamp")
        if observation_timestamp > decision_timestamp:
            raise ValueError("post-decision evidence")

    _reject_look_ahead_markers(record)
    _require_declarations(record)
    _reject_authority_fields(record)
    return _governed_result(
        asof_rules=rules,
        decision_timestamp=decision_timestamp,
        available_at_timestamp=available_at,
    )


def _validate_version(record: Mapping[str, Any]) -> None:
    version = record.get("asof_governance_version")
    if not version:
        raise ValueError("missing as-of governance version")
    if version not in SUPPORTED_ASOF_GOVERNANCE_VERSIONS:
        raise ValueError(f"unsupported as-of governance version: '{version}'")


def _validate_rule_list(rules: object) -> tuple[str, ...]:
    if not isinstance(rules, (tuple, list)):
        raise TypeError("as-of rules must be a tuple or list")
    if not rules:
        raise ValueError("empty rule set")
    seen: set[str] = set()
    for identifier in rules:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("missing rule identifier")
        if identifier not in KNOWN_ASOF_RULES:
            raise ValueError(f"unknown rule identifier: '{identifier}'")
        if identifier in seen:
            raise ValueError(f"duplicate rule identifier: '{identifier}'")
        seen.add(identifier)
    return tuple(rules)


def _reject_look_ahead_markers(record: Mapping[str, Any]) -> None:
    if record.get("future_dated"):
        raise ValueError("future-dated evidence marker")
    if record.get("post_decision"):
        raise ValueError("post-decision evidence marker")
    if record.get("leaked"):
        raise ValueError("leaked evidence marker")
    if record.get("mutable_evidence"):
        raise ValueError("mutable evidence marker")


def _require_declarations(record: Mapping[str, Any]) -> None:
    if record.get("no_look_ahead") is not True:
        raise ValueError("missing no-look-ahead declaration")
    if record.get("immutable_evidence") is not True:
        raise ValueError("missing immutability declaration")
    if record.get("reproducibility_declared") is not True:
        raise ValueError("missing reproducibility declaration")


def _reject_authority_fields(record: Mapping[str, Any]) -> None:
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")


def _governed_result(
    *,
    asof_rules: tuple[str, ...],
    decision_timestamp: str = "",
    available_at_timestamp: str = "",
) -> dict[str, Any]:
    return {
        "result_type": ASOF_GOVERNANCE_RESULT,
        "asof_governance_version": ASOF_GOVERNANCE_VERSION,
        "asof_rules": asof_rules,
        "decision_timestamp": decision_timestamp,
        "available_at_timestamp": available_at_timestamp,
        "evidence_only": True,
        "non_authoritative": True,
        "no_look_ahead_enforced": True,
        "asof_computation_execution": False,
        "feature_generation": False,
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
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": ASOF_GOVERNANCE_AUTHORITY_BOUNDARY,
    }
