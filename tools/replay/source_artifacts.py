"""Pure in-memory source artifact authority metadata validation helper.

This module validates already-loaded source-reference and source-artifact
metadata only. It does not read files, ingest paths, discover artifacts, copy
artifacts, capture runtime output, evaluate or promote strategies, call broker
APIs, authorize execution, approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


SOURCE_ARTIFACT_AUTHORITY = "source_artifact_authority_metadata_only"
SOURCE_REFERENCE_AUTHORITY = "source_reference_authority_metadata_only"
SOURCE_PATH_AUTHORITY = "source_path_authority_metadata_only"
RUNTIME_SOURCE_ARTIFACT = "runtime_source_artifact_metadata_only"
RUNTIME_SOURCE_REFERENCE = "runtime_source_reference_metadata_only"
RUNTIME_SOURCE_PATH = "runtime_source_path_metadata_only"
ABSENT_SOURCE_ARTIFACT_DECLARATION = "absent_source_artifact_declaration"
NOT_APPLICABLE_SOURCE_ARTIFACT_DECLARATION = (
    "not_applicable_source_artifact_declaration"
)
SOURCE_ARTIFACT_ELIGIBILITY_RESULT = "source_artifact_eligibility_result"
SOURCE_ARTIFACT_PROVENANCE_RESULT = "source_artifact_provenance_result"
SOURCE_ARTIFACT_REDACTION_RESULT = "source_artifact_redaction_result"
SOURCE_ARTIFACT_KNOWN_REFERENCE_RESULT = "source_artifact_known_reference_result"
SOURCE_ARTIFACT_NO_ACCESS_RESULT = "source_artifact_no_access_result"
SOURCE_ARTIFACT_DISCOVERY_PREREQUISITE = "source_artifact_discovery_prerequisite"
RUNTIME_ARTIFACT_DISCOVERY_PREREQUISITE = (
    "runtime_artifact_discovery_prerequisite"
)

SOURCE_ARTIFACT_AUTHORITY_RESULT = "source_artifact_authority_result"
SOURCE_ARTIFACT_ALLOWED_ELIGIBILITY: tuple[str, ...] = (
    "eligible",
    "absent",
    "not_applicable",
)

SOURCE_ARTIFACT_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "no_file_reads",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_runtime_artifact_discovery",
    "no_artifact_copying",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

SOURCE_ARTIFACT_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "source_references_present_and_known",
    "absent_or_not_applicable_declaration_when_no_artifact_exists",
    "source_artifact_provenance_present_and_valid",
    "source_artifact_redaction_status_present_and_valid",
    "source_artifact_eligibility_explicit",
    "source_path_identity_explicit_when_path_metadata_exists",
    "no_runtime_log_access",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_discovery",
    "no_runtime_capture",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
    "no_strategy_risk_execution_inputs",
    "no_paper_live_authority",
)

SOURCE_ARTIFACT_FAIL_CLOSED_BOUNDARIES: tuple[str, ...] = (
    "missing_source_references",
    "unknown_source_references",
    "ambiguous_source_references",
    "missing_absent_or_not_applicable_declaration",
    "malformed_absent_or_not_applicable_declaration",
    "missing_source_artifact_provenance",
    "malformed_source_artifact_provenance",
    "missing_source_artifact_redaction_status",
    "invalid_source_artifact_redaction_status",
    "sensitive_data_exposure",
    "stale_source_artifact_metadata",
    "malformed_source_artifact_metadata",
    "mixed_run_id",
    "runtime_log_dependency",
    "runtime_path_dependency",
    "file_path_ingestion_dependency",
    "artifact_copying_dependency",
    "runtime_artifact_discovery_dependency",
    "runtime_capture_dependency",
    "evaluation_dependency",
    "broker_dependency",
    "strategy_risk_execution_dependency",
    "source_artifact_authority_as_runtime_capture",
    "source_artifact_authority_as_evaluation_approval",
    "source_artifact_authority_as_execution_permission",
    "source_artifact_authority_as_paper_trading_authority",
    "source_artifact_authority_as_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class SourceArtifactAuthority:
    """Static source artifact authority vocabulary."""

    name: str = SOURCE_ARTIFACT_AUTHORITY
    authority_boundary: tuple[str, ...] = SOURCE_ARTIFACT_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class SourceReferenceAuthority:
    """Static source reference authority vocabulary."""

    name: str = SOURCE_REFERENCE_AUTHORITY


@dataclass(frozen=True, slots=True)
class SourcePathAuthority:
    """Static source path metadata authority vocabulary."""

    name: str = SOURCE_PATH_AUTHORITY


@dataclass(frozen=True, slots=True)
class RuntimeSourceArtifact:
    """Static runtime source artifact metadata vocabulary."""

    name: str = RUNTIME_SOURCE_ARTIFACT


@dataclass(frozen=True, slots=True)
class RuntimeSourceReference:
    """Static runtime source reference metadata vocabulary."""

    name: str = RUNTIME_SOURCE_REFERENCE


@dataclass(frozen=True, slots=True)
class RuntimeSourcePath:
    """Static runtime source path metadata vocabulary."""

    name: str = RUNTIME_SOURCE_PATH


@dataclass(frozen=True, slots=True)
class AbsentSourceArtifactDeclaration:
    """Source artifact is explicitly absent for a known reference."""

    canonical_run_id: str
    source_reference: str
    provenance: str = "recorded"
    redaction_status: str = "not_required"
    declaration_type: str = ABSENT_SOURCE_ARTIFACT_DECLARATION


@dataclass(frozen=True, slots=True)
class NotApplicableSourceArtifactDeclaration:
    """Source artifact is explicitly not applicable for a known reference."""

    canonical_run_id: str
    source_reference: str
    provenance: str = "recorded"
    redaction_status: str = "not_required"
    declaration_type: str = NOT_APPLICABLE_SOURCE_ARTIFACT_DECLARATION


@dataclass(frozen=True, slots=True)
class SourceArtifactEligibilityResult:
    """Static source artifact eligibility result vocabulary."""

    result_type: str = SOURCE_ARTIFACT_ELIGIBILITY_RESULT


@dataclass(frozen=True, slots=True)
class SourceArtifactProvenanceResult:
    """Static source artifact provenance result vocabulary."""

    result_type: str = SOURCE_ARTIFACT_PROVENANCE_RESULT


@dataclass(frozen=True, slots=True)
class SourceArtifactRedactionResult:
    """Static source artifact redaction result vocabulary."""

    result_type: str = SOURCE_ARTIFACT_REDACTION_RESULT


@dataclass(frozen=True, slots=True)
class SourceArtifactKnownReferenceResult:
    """Static known source reference result vocabulary."""

    result_type: str = SOURCE_ARTIFACT_KNOWN_REFERENCE_RESULT


@dataclass(frozen=True, slots=True)
class SourceArtifactNoAccessResult:
    """Static no-access result vocabulary."""

    result_type: str = SOURCE_ARTIFACT_NO_ACCESS_RESULT
    authority_boundary: tuple[str, ...] = SOURCE_ARTIFACT_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class SourceArtifactDiscoveryPrerequisite:
    """Static source artifact discovery prerequisite vocabulary."""

    name: str = SOURCE_ARTIFACT_DISCOVERY_PREREQUISITE


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDiscoveryPrerequisite:
    """Static runtime artifact discovery prerequisite vocabulary."""

    name: str = RUNTIME_ARTIFACT_DISCOVERY_PREREQUISITE


@dataclass(frozen=True, slots=True)
class SourceArtifactAuthorityInput:
    """Already-loaded source metadata eligible for authority validation."""

    canonical_run_id: str
    source_references: tuple[str, ...]
    known_source_references: tuple[str, ...]
    source_artifact_provenance: str
    source_artifact_redaction_status: str
    source_artifact_eligibility: str
    input_run_ids: tuple[str, ...]
    source_path_identity: str | None = None
    artifact_exists: bool = True
    absent_source_artifact_declaration: Mapping[str, Any] | None = None
    not_applicable_source_artifact_declaration: Mapping[str, Any] | None = None
    sensitive_data_status: str = "clear"
    stale_source_artifact_metadata: bool = False
    malformed_source_artifact_metadata: bool = False
    ambiguous_source_references: bool = False
    runtime_log_dependent: bool = False
    runtime_path_dependent: bool = False
    file_path_ingestion_dependent: bool = False
    artifact_copying_dependent: bool = False
    runtime_artifact_discovery_dependent: bool = False
    runtime_capture_dependent: bool = False
    evaluation_dependent: bool = False
    broker_dependent: bool = False
    strategy_risk_execution_dependent: bool = False
    attempted_runtime_capture: bool = False
    attempted_evaluation_approval: bool = False
    attempted_execution_permission: bool = False
    attempted_paper_trading_authority: bool = False
    attempted_live_trading_authority: bool = False
    paper_trading_authority: bool = False
    live_trading_authority: bool = False


def declare_absent_source_artifact(
    canonical_run_id: str,
    source_reference: str,
    *,
    provenance: str = "recorded",
    redaction_status: str = "not_required",
) -> dict[str, Any]:
    """Declare an absent source artifact without granting artifact access."""

    return _declaration_result(
        declaration_type=ABSENT_SOURCE_ARTIFACT_DECLARATION,
        canonical_run_id=canonical_run_id,
        source_reference=source_reference,
        provenance=provenance,
        redaction_status=redaction_status,
    )


def declare_not_applicable_source_artifact(
    canonical_run_id: str,
    source_reference: str,
    *,
    provenance: str = "recorded",
    redaction_status: str = "not_required",
) -> dict[str, Any]:
    """Declare a not-applicable source artifact without granting access."""

    return _declaration_result(
        declaration_type=NOT_APPLICABLE_SOURCE_ARTIFACT_DECLARATION,
        canonical_run_id=canonical_run_id,
        source_reference=source_reference,
        provenance=provenance,
        redaction_status=redaction_status,
    )


def validate_source_artifact_authority(
    source_metadata: SourceArtifactAuthorityInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate source artifact authority over already-loaded metadata."""

    return build_source_artifact_authority_result(source_metadata)


def build_source_artifact_authority_result(
    source_metadata: SourceArtifactAuthorityInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build source artifact authority metadata without artifact access."""

    normalized = _normalize_source_metadata(source_metadata)
    absent_declaration, not_applicable_declaration = _validate_source_metadata(
        normalized
    )
    return {
        "result_type": SOURCE_ARTIFACT_AUTHORITY_RESULT,
        "canonical_run_id": normalized.canonical_run_id,
        "source_references": tuple(normalized.source_references),
        "known_source_references": tuple(normalized.known_source_references),
        "source_path_identity": normalized.source_path_identity,
        "artifact_exists": normalized.artifact_exists,
        "absent_source_artifact_declaration": absent_declaration,
        "not_applicable_source_artifact_declaration": not_applicable_declaration,
        "source_artifact_eligibility": normalized.source_artifact_eligibility,
        "source_artifact_provenance": normalized.source_artifact_provenance,
        "source_artifact_redaction_status": (
            normalized.source_artifact_redaction_status
        ),
        "source_artifact_authority": True,
        "source_reference_authority": True,
        "source_path_authority": True,
        "evidence_only": True,
        "metadata_only": True,
        "runtime_log_access": False,
        "source_path_ingestion": False,
        "file_path_ingestion": False,
        "runtime_artifact_discovery": False,
        "artifact_copying": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "strategy_risk_execution_behavior": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "prerequisites": SOURCE_ARTIFACT_PREREQUISITES,
        "fail_closed_boundaries": SOURCE_ARTIFACT_FAIL_CLOSED_BOUNDARIES,
        "authority_boundary": SOURCE_ARTIFACT_AUTHORITY_BOUNDARY,
    }


def validate_source_references_only(
    source_metadata: SourceArtifactAuthorityInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate known source-reference metadata without artifact access."""

    return build_source_artifact_authority_result(source_metadata)


def _normalize_source_metadata(
    source_metadata: SourceArtifactAuthorityInput | Mapping[str, Any],
) -> SourceArtifactAuthorityInput:
    if isinstance(source_metadata, SourceArtifactAuthorityInput):
        return source_metadata
    if not isinstance(source_metadata, Mapping):
        raise TypeError("source artifact authority input must be loaded metadata")
    return SourceArtifactAuthorityInput(**source_metadata)


def _validate_source_metadata(
    source_metadata: SourceArtifactAuthorityInput,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    _reject_forbidden_dependencies(source_metadata)
    _validate_source_run_identity(source_metadata)
    _validate_source_references(source_metadata)
    _validate_source_artifact_metadata(source_metadata)
    return _validate_artifact_declarations(source_metadata)


def _reject_forbidden_dependencies(
    source_metadata: SourceArtifactAuthorityInput,
) -> None:
    if source_metadata.malformed_source_artifact_metadata:
        raise ValueError("malformed source artifact metadata")
    if source_metadata.stale_source_artifact_metadata:
        raise ValueError("stale source artifact metadata")
    if source_metadata.ambiguous_source_references:
        raise ValueError("ambiguous source references")
    if source_metadata.runtime_log_dependent:
        raise ValueError("runtime log dependency")
    if source_metadata.runtime_path_dependent:
        raise ValueError("runtime path dependency")
    if source_metadata.file_path_ingestion_dependent:
        raise ValueError("file path ingestion dependency")
    if source_metadata.artifact_copying_dependent:
        raise ValueError("artifact copying dependency")
    if source_metadata.runtime_artifact_discovery_dependent:
        raise ValueError("runtime artifact discovery dependency")
    if source_metadata.runtime_capture_dependent or (
        source_metadata.attempted_runtime_capture
    ):
        raise ValueError("source artifact authority is not runtime capture")
    if source_metadata.evaluation_dependent or (
        source_metadata.attempted_evaluation_approval
    ):
        raise ValueError("source artifact authority is not evaluation approval")
    if source_metadata.broker_dependent:
        raise ValueError("broker dependency")
    if source_metadata.strategy_risk_execution_dependent:
        raise ValueError("strategy/risk/execution dependency")
    if source_metadata.attempted_execution_permission:
        raise ValueError("source artifact authority is not execution permission")
    if source_metadata.attempted_paper_trading_authority or (
        source_metadata.paper_trading_authority
    ):
        raise ValueError("source artifact authority is not paper trading authority")
    if source_metadata.attempted_live_trading_authority or (
        source_metadata.live_trading_authority
    ):
        raise ValueError("source artifact authority is not live trading authority")


def _validate_source_run_identity(
    source_metadata: SourceArtifactAuthorityInput,
) -> None:
    if not source_metadata.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    for run_id in source_metadata.input_run_ids:
        if run_id != source_metadata.canonical_run_id:
            raise ValueError("mixed run_id source artifact metadata")


def _validate_source_references(
    source_metadata: SourceArtifactAuthorityInput,
) -> None:
    if not source_metadata.source_references:
        raise ValueError("missing source references")
    known_references = set(source_metadata.known_source_references)
    if not known_references:
        raise ValueError("unknown source references")
    for source_reference in source_metadata.source_references:
        if source_reference not in known_references:
            raise ValueError("unknown source references")


def _validate_source_artifact_metadata(
    source_metadata: SourceArtifactAuthorityInput,
) -> None:
    if not isinstance(source_metadata.source_artifact_provenance, str):
        raise ValueError("malformed source artifact provenance")
    if not source_metadata.source_artifact_provenance:
        raise ValueError("missing source artifact provenance")
    if not source_metadata.source_artifact_redaction_status:
        raise ValueError("missing source artifact redaction status")
    if source_metadata.source_artifact_redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid source artifact redaction status")
    if source_metadata.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")
    if source_metadata.source_artifact_eligibility not in (
        SOURCE_ARTIFACT_ALLOWED_ELIGIBILITY
    ):
        raise ValueError("source artifact eligibility must be explicit")
    if source_metadata.source_path_identity is not None and not isinstance(
        source_metadata.source_path_identity,
        str,
    ):
        raise ValueError("source path identity must be metadata")
    if source_metadata.source_path_identity == "":
        raise ValueError("source path identity must be explicit")


def _validate_artifact_declarations(
    source_metadata: SourceArtifactAuthorityInput,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    absent_declaration = _normalize_declaration(
        source_metadata.absent_source_artifact_declaration
    )
    not_applicable_declaration = _normalize_declaration(
        source_metadata.not_applicable_source_artifact_declaration
    )
    declarations = tuple(
        declaration
        for declaration in (absent_declaration, not_applicable_declaration)
        if declaration is not None
    )
    if source_metadata.artifact_exists:
        if declarations:
            raise ValueError("malformed absent or not-applicable declaration")
        return None, None
    if len(declarations) != 1:
        raise ValueError("missing absent or not-applicable declaration")
    declaration = declarations[0]
    _validate_declaration(source_metadata, declaration)
    if declaration["declaration_type"] == ABSENT_SOURCE_ARTIFACT_DECLARATION:
        return declaration, None
    if declaration["declaration_type"] == NOT_APPLICABLE_SOURCE_ARTIFACT_DECLARATION:
        return None, declaration
    raise ValueError("malformed absent or not-applicable declaration")


def _normalize_declaration(
    declaration: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if declaration is None:
        return None
    if not isinstance(declaration, Mapping):
        raise ValueError("malformed absent or not-applicable declaration")
    return dict(declaration)


def _validate_declaration(
    source_metadata: SourceArtifactAuthorityInput,
    declaration: Mapping[str, Any],
) -> None:
    if declaration.get("declaration_type") not in (
        ABSENT_SOURCE_ARTIFACT_DECLARATION,
        NOT_APPLICABLE_SOURCE_ARTIFACT_DECLARATION,
    ):
        raise ValueError("malformed absent or not-applicable declaration")
    if declaration.get("canonical_run_id") != source_metadata.canonical_run_id:
        raise ValueError("mixed run_id source artifact metadata")
    source_reference = declaration.get("source_reference")
    if source_reference not in source_metadata.source_references:
        raise ValueError("unknown source references")
    provenance = declaration.get("provenance")
    if not isinstance(provenance, str) or not provenance:
        raise ValueError("malformed source artifact provenance")
    redaction_status = declaration.get("redaction_status")
    if redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid source artifact redaction status")
    if declaration.get("source_artifact_present") is not False:
        raise ValueError("malformed absent or not-applicable declaration")


def _declaration_result(
    *,
    declaration_type: str,
    canonical_run_id: str,
    source_reference: str,
    provenance: str,
    redaction_status: str,
) -> dict[str, Any]:
    return {
        "declaration_type": declaration_type,
        "canonical_run_id": canonical_run_id,
        "source_reference": source_reference,
        "provenance": provenance,
        "redaction_status": redaction_status,
        "source_artifact_present": False,
        "runtime_log_access": False,
        "source_path_ingestion": False,
        "file_path_ingestion": False,
        "runtime_artifact_discovery": False,
        "artifact_copying": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "strategy_risk_execution_behavior": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
    }
