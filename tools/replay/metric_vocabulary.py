"""Pure in-memory metric vocabulary and versioning for Gate D governance.

This module defines governed evaluation metric identifier vocabulary and a
deterministic metric vocabulary version only. It computes no scores, reads no
files, reads no replay packages, executes no evaluation, performs no
attribution, and carries no promotion, broker, execution, strategy, risk,
paper-trading, or live-trading authority.

A metric identifier names a comparison dimension a future, separately approved
scoring engine might compute over finalized immutable replay-package evidence.
Naming a metric here does not compute it, does not evaluate any package, and
does not authorize any downstream behavior.

Governance basis: Gate D Record D1 (evaluation prerequisite governance
contract), which orders metric vocabulary + versioning as the first Gate D
implementation unit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


METRIC_VOCABULARY = "metric_vocabulary_in_memory_only"
METRIC_VOCABULARY_VERSION = "0.1-metric-vocab"
SUPPORTED_METRIC_VOCABULARY_VERSIONS: tuple[str, ...] = (METRIC_VOCABULARY_VERSION,)
METRIC_VOCABULARY_RESULT = "metric_vocabulary_result"

# Governed metric identifiers. Each names a comparison dimension over recorded
# replay-package evidence; none carries computation or authority.
METRIC_TERMINAL_STATUS_MATCH = "terminal_status_match"
METRIC_DECISION_ACTION_MATCH = "decision_action_match"
METRIC_SIGNAL_RESULT_MATCH = "signal_result_match"
METRIC_RECONCILIATION_RESULT_MATCH = "reconciliation_result_match"
METRIC_RISK_DECISION_MATCH = "risk_decision_match"

KNOWN_METRIC_IDENTIFIERS: tuple[str, ...] = (
    METRIC_TERMINAL_STATUS_MATCH,
    METRIC_DECISION_ACTION_MATCH,
    METRIC_SIGNAL_RESULT_MATCH,
    METRIC_RECONCILIATION_RESULT_MATCH,
    METRIC_RISK_DECISION_MATCH,
)

# Record fields that would imply authority this vocabulary must never carry.
FORBIDDEN_AUTHORITY_FIELDS: tuple[str, ...] = (
    "scoring",
    "score",
    "evaluation_execution",
    "attribution",
    "promotion_authority",
    "broker_api_authority",
    "execution_authority",
    "strategy_authority",
    "risk_authority",
    "paper_trading_authority",
    "live_trading_authority",
)

METRIC_VOCABULARY_FAIL_CLOSED_CONDITIONS: tuple[str, ...] = (
    "unknown_metric_identifier",
    "missing_metric_identifier",
    "missing_metric_vocabulary_version",
    "unsupported_metric_vocabulary_version",
    "duplicate_metric_identifier",
    "empty_metric_identifier_set",
    "malformed_metric_record",
    "authority_bearing_field_present",
)

METRIC_VOCABULARY_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "vocabulary_and_versioning_only",
    "evidence_only",
    "non_authoritative",
    "no_scoring",
    "no_evaluation_execution",
    "no_attribution",
    "no_filesystem_reads",
    "no_package_reads",
    "no_experiment_registry",
    "no_package_set_selection",
    "no_baseline_vs_candidate_comparison",
    "no_promotion_or_strategy_promotion",
    "no_broker_api_authority",
    "no_execution_permission",
    "no_strategy_risk_execution_behavior",
    "no_paper_trading_approval",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class MetricVocabulary:
    """Static governed metric vocabulary and version."""

    version: str = METRIC_VOCABULARY_VERSION
    known_identifiers: tuple[str, ...] = KNOWN_METRIC_IDENTIFIERS
    authority_boundary: tuple[str, ...] = METRIC_VOCABULARY_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class MetricVocabularyFailClosedConditions:
    """Static fail-closed condition vocabulary for metric vocabulary."""

    conditions: tuple[str, ...] = METRIC_VOCABULARY_FAIL_CLOSED_CONDITIONS


def is_known_metric_identifier(identifier: object) -> bool:
    """Return True only for an exactly-known governed metric identifier."""

    return isinstance(identifier, str) and identifier in KNOWN_METRIC_IDENTIFIERS


def validate_metric_identifier_set(identifiers: object) -> dict[str, Any]:
    """Validate a set of metric identifiers, or fail closed.

    Every identifier must be exactly known and unique. Returns governed
    non-authoritative metadata; raises ValueError/TypeError otherwise.
    """

    if not isinstance(identifiers, (tuple, list)):
        raise TypeError("metric identifiers must be an already-loaded tuple or list")
    if not identifiers:
        raise ValueError("empty metric identifier set")
    seen: set[str] = set()
    for identifier in identifiers:
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("missing metric identifier")
        if identifier not in KNOWN_METRIC_IDENTIFIERS:
            raise ValueError(f"unknown metric identifier: '{identifier}'")
        if identifier in seen:
            raise ValueError(f"duplicate metric identifier: '{identifier}'")
        seen.add(identifier)
    return _governed_result(metric_identifiers=tuple(identifiers))


def validate_metric_vocabulary_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-loaded metric vocabulary record, or fail closed."""

    if not isinstance(record, Mapping):
        raise TypeError("metric vocabulary record must be already-loaded metadata")

    identifier = record.get("metric_identifier")
    if not identifier:
        raise ValueError("missing metric identifier")
    if not isinstance(identifier, str) or identifier not in KNOWN_METRIC_IDENTIFIERS:
        raise ValueError(f"unknown metric identifier: '{identifier}'")

    version = record.get("metric_vocabulary_version")
    if not version:
        raise ValueError("missing metric vocabulary version")
    if version not in SUPPORTED_METRIC_VOCABULARY_VERSIONS:
        raise ValueError(f"unsupported metric vocabulary version: '{version}'")

    for field in FORBIDDEN_AUTHORITY_FIELDS:
        if record.get(field):
            raise ValueError(f"authority-bearing field present: '{field}'")

    return _governed_result(
        metric_identifiers=(identifier,),
        metric_vocabulary_version=version,
    )


def _governed_result(
    *,
    metric_identifiers: tuple[str, ...],
    metric_vocabulary_version: str = METRIC_VOCABULARY_VERSION,
) -> dict[str, Any]:
    return {
        "result_type": METRIC_VOCABULARY_RESULT,
        "metric_vocabulary_version": metric_vocabulary_version,
        "metric_identifiers": metric_identifiers,
        "evidence_only": True,
        "non_authoritative": True,
        "scoring": False,
        "evaluation_execution": False,
        "attribution": False,
        "experiment_registry": False,
        "package_set_selection": False,
        "baseline_vs_candidate_comparison": False,
        "filesystem_reads": False,
        "package_reads": False,
        "promotion_authority": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "strategy_risk_execution_behavior": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "authority_boundary": METRIC_VOCABULARY_AUTHORITY_BOUNDARY,
    }
