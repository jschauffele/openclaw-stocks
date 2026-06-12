"""Pure in-memory attribution vocabulary and versioning for Gate D governance.

This module defines governed evaluation attribution cause identifier vocabulary
and a deterministic attribution vocabulary version only. It performs no
attribution computation, computes no scores, reads no files, reads no replay
packages, executes no evaluation, and carries no experiment-registry,
package-set, reproducibility, baseline-vs-candidate, as-of, promotion, broker,
execution, strategy, risk, paper-trading, or live-trading authority.

An attribution identifier names a cause dimension a future, separately approved
attribution engine might explain a result difference by. Naming a cause here
does not compute attribution, does not evaluate any package, and does not
authorize any downstream behavior.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders attribution vocabulary + versioning as the second
Gate D implementation unit, following metric vocabulary (Unit 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


ATTRIBUTION_VOCABULARY = "attribution_vocabulary_in_memory_only"
ATTRIBUTION_VOCABULARY_VERSION = "0.1-attribution-vocab"
SUPPORTED_ATTRIBUTION_VOCABULARY_VERSIONS: tuple[str, ...] = (
    ATTRIBUTION_VOCABULARY_VERSION,
)
ATTRIBUTION_VOCABULARY_RESULT = "attribution_vocabulary_result"

# Governed attribution cause identifiers. Each names a cause dimension a future
# attribution engine might explain a difference by; none carries computation or
# authority.
ATTRIBUTION_STRATEGY_LOGIC_CHANGE = "strategy_logic_change"
ATTRIBUTION_PARAMETER_CHANGE = "parameter_change"
ATTRIBUTION_MARKET_DATA_CHANGE = "market_data_change"
ATTRIBUTION_PORTFOLIO_STATE_CHANGE = "portfolio_state_change"
ATTRIBUTION_ALLOCATION_RULE_CHANGE = "allocation_rule_change"
ATTRIBUTION_RISK_GOVERNANCE_CHANGE = "risk_governance_change"
ATTRIBUTION_EXPOSURE_CAP_CHANGE = "exposure_cap_change"
ATTRIBUTION_EXECUTION_ASSUMPTION_CHANGE = "execution_assumption_change"

KNOWN_ATTRIBUTION_IDENTIFIERS: tuple[str, ...] = (
    ATTRIBUTION_STRATEGY_LOGIC_CHANGE,
    ATTRIBUTION_PARAMETER_CHANGE,
    ATTRIBUTION_MARKET_DATA_CHANGE,
    ATTRIBUTION_PORTFOLIO_STATE_CHANGE,
    ATTRIBUTION_ALLOCATION_RULE_CHANGE,
    ATTRIBUTION_RISK_GOVERNANCE_CHANGE,
    ATTRIBUTION_EXPOSURE_CAP_CHANGE,
    ATTRIBUTION_EXECUTION_ASSUMPTION_CHANGE,
)

# Record fields that would imply authority this vocabulary must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "attribution_execution",
    "evaluation_execution",
    "experiment_registry",
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

ATTRIBUTION_VOCABULARY_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "unknown_attribution_identifier",
    "missing_attribution_identifier",
    "missing_attribution_vocabulary_version",
    "unsupported_attribution_vocabulary_version",
    "duplicate_attribution_identifier",
    "empty_attribution_identifier_set",
    "malformed_attribution_record",
    "authority_bearing_field_present",
)

ATTRIBUTION_VOCABULARY_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "vocabulary_and_versioning_only",
    "evidence_only",
    "non_authoritative",
    "no_attribution_execution",
    "no_scoring",
    "no_evaluation_execution",
    "no_filesystem_reads",
    "no_package_reads",
    "no_experiment_registry",
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
class AttributionVocabulary:
    """Static governed attribution vocabulary and version."""

    version: str = ATTRIBUTION_VOCABULARY_VERSION
    known_identifiers: tuple[str, ...] = KNOWN_ATTRIBUTION_IDENTIFIERS
    authority_boundary: tuple[str, ...] = ATTRIBUTION_VOCABULARY_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class AttributionVocabularyFailClosedConditions:
    """Static fail-closed condition vocabulary for attribution vocabulary."""

    conditions: tuple[str, ...] = ATTRIBUTION_VOCABULARY_FAIL_CLOSED_CONDITIONS


def is_known_attribution_identifier(identifier: object) -> bool:
    """Return True only for an exactly-known governed attribution identifier."""

    return isinstance(identifier, str) and identifier in KNOWN_ATTRIBUTION_IDENTIFIERS


def validate_attribution_identifier_set(identifiers: object) -> dict[str, Any]:
    """Validate a set of attribution identifiers, or fail closed.

    Every identifier must be exactly known and unique. Returns governed
    non-authoritative metadata; raises ValueError/TypeError otherwise.
    """

    if not isinstance(identifiers, (tuple, list)):
        raise TypeError(
            "attribution identifiers must be an already-loaded tuple or list"
        )
    if not identifiers:
        raise ValueError("empty attribution identifier set")
    seen: set[str] = set()
    for identifier in identifiers:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("missing attribution identifier")
        if identifier not in KNOWN_ATTRIBUTION_IDENTIFIERS:
            raise ValueError(f"unknown attribution identifier: '{identifier}'")
        if identifier in seen:
            raise ValueError(f"duplicate attribution identifier: '{identifier}'")
        seen.add(identifier)
    return _governed_result(attribution_identifiers=tuple(identifiers))


def validate_attribution_vocabulary_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded attribution vocabulary record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("attribution vocabulary record must be already-loaded metadata")

    identifier = record.get("attribution_identifier")
    if not identifier:
        raise ValueError("missing attribution identifier")
    if (
        not isinstance(identifier, str)
        or identifier not in KNOWN_ATTRIBUTION_IDENTIFIERS
    ):
        raise ValueError(f"unknown attribution identifier: '{identifier}'")

    version = record.get("attribution_vocabulary_version")
    if not version:
        raise ValueError("missing attribution vocabulary version")
    if version not in SUPPORTED_ATTRIBUTION_VOCABULARY_VERSIONS:
        raise ValueError(f"unsupported attribution vocabulary version: '{version}'")

    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")

    return _governed_result(
        attribution_identifiers=(identifier,),
        attribution_vocabulary_version=version,
    )


def _governed_result(
    *,
    attribution_identifiers: tuple[str, ...],
    attribution_vocabulary_version: str = ATTRIBUTION_VOCABULARY_VERSION,
) -> dict[str, Any]:
    return {
        "result_type": ATTRIBUTION_VOCABULARY_RESULT,
        "attribution_vocabulary_version": attribution_vocabulary_version,
        "attribution_identifiers": attribution_identifiers,
        "evidence_only": True,
        "non_authoritative": True,
        "attribution_execution": False,
        "scoring": False,
        "evaluation_execution": False,
        "experiment_registry": False,
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
        "authority_boundary": ATTRIBUTION_VOCABULARY_AUTHORITY_BOUNDARY,
    }
