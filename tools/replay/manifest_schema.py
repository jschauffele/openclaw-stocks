"""Pure in-memory manifest schema vocabulary.

This module defines static vocabulary and frozen value containers only. It does
not build manifests, serialize data, hash evidence, create packages, touch the
filesystem, capture runtime artifacts, evaluate strategies, or authorize
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


MANIFEST_SCHEMA_VERSION = "0.1-vocabulary"

ManifestSchemaVersion: TypeAlias = str
ManifestFieldName: TypeAlias = str
ManifestSectionName: TypeAlias = str
ManifestSectionStatusValue: TypeAlias = str
ManifestLifecycleStatusValue: TypeAlias = str
ManifestAuthorityBoundaryName: TypeAlias = str

MANIFEST_REQUIRED_FIELDS: tuple[str, ...] = (
    "canonical_run_id",
    "package_schema_version",
    "manifest_schema_version",
    "lifecycle_status",
    "lifecycle_reason",
    "created_at",
    "source_artifact_references",
    "section_status",
    "section_provenance",
    "section_redaction_status",
    "evidence_only",
    "non_authoritative",
)

MANIFEST_OPTIONAL_FIELDS: tuple[str, ...] = (
    "package_id",
    "source_commit",
    "source_branch",
    "source_runtime_version",
    "generator_name",
    "generator_version",
    "generator_authority_boundary",
    "source_artifact_type",
    "source_artifact_path_or_reference",
    "source_artifact_run_id",
    "source_artifact_timestamp",
    "source_artifact_provenance",
    "source_artifact_redaction_status",
    "section_id",
    "section_type",
    "section_authority",
    "section_source_reference",
    "section_run_id",
    "completeness_status",
    "completeness_reason",
    "missing_sections",
    "not_applicable_sections",
    "unavailable_sections",
    "stale_sections",
    "untrusted_sections",
    "annotations",
    "corrections",
    "invalidation_references",
    "supersession_references",
    "reviewer_notes",
)

MANIFEST_FUTURE_ONLY_FIELDS: tuple[str, ...] = (
    "finalized_at",
    "invalidated_at",
    "superseded_by",
    "section_hash",
    "hash_algorithm",
    "section_hashes",
    "manifest_hash",
    "package_hash",
    "integrity_status",
    "complete_replay_package_authority",
    "finalized_immutable_replay_package_authority",
    "replay_based_evaluation_authority",
    "replay_based_promotion_authority",
    "broker_api_authority",
    "execution_permission",
    "live_trading_authority",
)

MANIFEST_FIELDS: tuple[str, ...] = (
    *MANIFEST_REQUIRED_FIELDS,
    *MANIFEST_OPTIONAL_FIELDS,
    *MANIFEST_FUTURE_ONLY_FIELDS,
)

MANIFEST_SECTION_NAMES: tuple[str, ...] = (
    "package_identity",
    "schema",
    "source_control",
    "run_identity",
    "replay_window",
    "environment_classification",
    "package_status",
    "configuration_references",
    "market_input_references",
    "strategy_decision_references",
    "portfolio_risk_snapshot_references",
    "broker_visible_state_references",
    "reconciliation_risk_references",
    "event_order_references",
    "attribution",
    "integrity",
    "immutability",
    "authority_boundary",
)

MANIFEST_SECTION_STATUS: tuple[str, ...] = (
    "present",
    "absent",
    "not_applicable",
    "disabled",
    "unavailable",
    "stale",
    "redacted",
    "untrusted",
    "malformed",
    "invalidated",
    "unknown",
)

MANIFEST_LIFECYCLE_STATUS: tuple[str, ...] = ("draft",)

MANIFEST_FUTURE_LIFECYCLE_STATUS: tuple[str, ...] = (
    "finalized",
    "invalidated",
    "superseded",
)

MANIFEST_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "evidence_only",
    "non_authoritative",
    "complete_replay_package_authority",
    "finalized_immutable_replay_package_authority",
    "replay_based_evaluation_authority",
    "replay_based_promotion_authority",
    "broker_api_authority",
    "execution_permission",
    "live_trading_authority",
)

MANIFEST_SCHEMA = "manifest_schema_vocabulary_only"


@dataclass(frozen=True, slots=True)
class ManifestField:
    """A static manifest field vocabulary entry."""

    name: ManifestFieldName
    required: bool
    future_only: bool = False


@dataclass(frozen=True, slots=True)
class ManifestSection:
    """A static manifest section vocabulary entry."""

    name: ManifestSectionName
    status: ManifestSectionStatusValue = "unknown"
    future_only: bool = False


@dataclass(frozen=True, slots=True)
class ManifestSectionStatus:
    """Static section status vocabulary."""

    values: tuple[str, ...] = MANIFEST_SECTION_STATUS


@dataclass(frozen=True, slots=True)
class ManifestLifecycleStatus:
    """Static lifecycle status vocabulary."""

    values: tuple[str, ...] = MANIFEST_LIFECYCLE_STATUS
    future_values: tuple[str, ...] = MANIFEST_FUTURE_LIFECYCLE_STATUS


@dataclass(frozen=True, slots=True)
class ManifestAuthorityBoundary:
    """Static manifest authority-boundary vocabulary."""

    values: tuple[str, ...] = MANIFEST_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class ManifestSchema:
    """Static manifest schema vocabulary container."""

    schema_version: ManifestSchemaVersion = MANIFEST_SCHEMA_VERSION
    fields: tuple[str, ...] = MANIFEST_FIELDS
    required_fields: tuple[str, ...] = MANIFEST_REQUIRED_FIELDS
    optional_fields: tuple[str, ...] = MANIFEST_OPTIONAL_FIELDS
    future_only_fields: tuple[str, ...] = MANIFEST_FUTURE_ONLY_FIELDS
    section_names: tuple[str, ...] = MANIFEST_SECTION_NAMES
    section_statuses: tuple[str, ...] = MANIFEST_SECTION_STATUS
    lifecycle_statuses: tuple[str, ...] = MANIFEST_LIFECYCLE_STATUS
    future_lifecycle_statuses: tuple[str, ...] = MANIFEST_FUTURE_LIFECYCLE_STATUS
    authority_boundary: tuple[str, ...] = MANIFEST_AUTHORITY_BOUNDARY
