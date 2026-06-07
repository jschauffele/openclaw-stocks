"""Pure in-memory runtime artifact discovery metadata validation helper.

This module validates already-loaded runtime artifact discovery metadata only.
It does not read files, read runtime logs, ingest paths, copy artifacts, capture
runtime output, evaluate or promote strategies, call broker APIs, authorize
execution, approve paper trading, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.integrity_validation import VALID_REDACTION_STATUS


RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY = "runtime_artifact_discovery_authority"
RUNTIME_ARTIFACT_DISCOVERY_RESULT = "runtime_artifact_discovery_result"
RUNTIME_ARTIFACT_CANDIDATE = "runtime_artifact_candidate"
RUNTIME_ARTIFACT_ELIGIBILITY_RESULT = "runtime_artifact_eligibility_result"
RUNTIME_ARTIFACT_INVENTORY_RESULT = "runtime_artifact_inventory_result"
RUNTIME_ARTIFACT_SOURCE_REFERENCE_BINDING = (
    "runtime_artifact_source_reference_binding"
)
RUNTIME_ARTIFACT_SOURCE_PATH_METADATA = "runtime_artifact_source_path_metadata"
RUNTIME_ARTIFACT_NO_ACCESS_RESULT = "runtime_artifact_no_access_result"
RUNTIME_ARTIFACT_TERMINAL_COMPLETION_PREREQUISITE = (
    "runtime_artifact_terminal_completion_prerequisite"
)
RUNTIME_ARTIFACT_RUN_ID_ALIGNMENT_RESULT = "runtime_artifact_run_id_alignment_result"
RUNTIME_ARTIFACT_PROVENANCE_RESULT = "runtime_artifact_provenance_result"
RUNTIME_ARTIFACT_REDACTION_RESULT = "runtime_artifact_redaction_result"
RUNTIME_ARTIFACT_DISCOVERY_PREREQUISITE = "runtime_artifact_discovery_prerequisite"
RUNTIME_CAPTURE_PREREQUISITE = "runtime_capture_prerequisite"
ELIGIBLE_RUNTIME_ARTIFACT_VOCABULARY = "eligible_runtime_artifact_vocabulary"
DISCOVERED_RUNTIME_ARTIFACT_METADATA = "discovered_runtime_artifact_metadata"
RUNTIME_ARTIFACT_DISCOVERY_FAILURE = "runtime_artifact_discovery_failure"

RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "metadata_only",
    "no_runtime_log_access",
    "no_file_reads",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_capture",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_strategy_risk_execution_behavior",
    "no_broker_api_authority",
    "no_execution_authority",
    "no_paper_trading_authority",
    "no_live_trading_authority",
)

RUNTIME_ARTIFACT_DISCOVERY_PREREQUISITES: tuple[str, ...] = (
    "canonical_run_id_alignment",
    "source_artifact_authority_result_present_and_valid",
    "source_references_present_and_known",
    "source_artifact_provenance_present_and_valid",
    "source_artifact_redaction_status_present_and_valid",
    "eligible_runtime_artifact_vocabulary_explicit",
    "terminal_completion_rules_explicit",
    "runtime_artifact_provenance_present_and_valid",
    "runtime_artifact_redaction_status_present_and_valid",
    "no_runtime_log_access",
    "no_file_reads",
    "no_source_path_ingestion",
    "no_file_path_ingestion",
    "no_artifact_copying",
    "no_runtime_artifact_capture",
    "no_evaluation_dependent_inputs",
    "no_broker_dependent_inputs",
    "no_strategy_risk_execution_inputs",
    "no_paper_live_authority",
)

RUNTIME_ARTIFACT_DISCOVERY_FAIL_CLOSED_BOUNDARIES: tuple[str, ...] = (
    "missing_source_artifact_authority_result",
    "failed_source_artifact_authority_result",
    "missing_source_references",
    "unknown_source_references",
    "ambiguous_source_references",
    "missing_eligible_runtime_artifact_vocabulary",
    "malformed_eligible_runtime_artifact_vocabulary",
    "missing_terminal_completion_rule",
    "failed_terminal_completion_rule",
    "missing_runtime_artifact_provenance",
    "malformed_runtime_artifact_provenance",
    "missing_runtime_artifact_redaction_status",
    "invalid_runtime_artifact_redaction_status",
    "sensitive_data_exposure",
    "stale_runtime_artifact_metadata",
    "malformed_runtime_artifact_metadata",
    "mixed_run_id",
    "runtime_log_dependency",
    "runtime_path_dependency",
    "file_read_dependency",
    "file_path_ingestion_dependency",
    "source_path_ingestion_dependency",
    "artifact_copying_dependency",
    "runtime_capture_dependency",
    "evaluation_dependency",
    "broker_dependency",
    "strategy_risk_execution_dependency",
    "runtime_artifact_discovery_as_runtime_capture",
    "runtime_artifact_discovery_as_evaluation_approval",
    "runtime_artifact_discovery_as_execution_permission",
    "runtime_artifact_discovery_as_paper_trading_authority",
    "runtime_artifact_discovery_as_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDiscoveryAuthority:
    """Static runtime artifact discovery authority vocabulary."""

    name: str = RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY
    authority_boundary: tuple[str, ...] = (
        RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY_BOUNDARY
    )


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDiscoveryResult:
    """Static runtime artifact discovery result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_DISCOVERY_RESULT


@dataclass(frozen=True, slots=True)
class RuntimeArtifactCandidate:
    """Already-loaded runtime artifact candidate metadata."""

    artifact_id: str
    artifact_type: str
    source_reference: str
    canonical_run_id: str
    provenance: str
    redaction_status: str
    eligible: bool = True
    source_path_metadata: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeArtifactEligibilityResult:
    """Static runtime artifact eligibility result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_ELIGIBILITY_RESULT


@dataclass(frozen=True, slots=True)
class RuntimeArtifactInventoryResult:
    """Static runtime artifact inventory result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_INVENTORY_RESULT


@dataclass(frozen=True, slots=True)
class RuntimeArtifactSourceReferenceBinding:
    """Static runtime artifact source-reference binding vocabulary."""

    name: str = RUNTIME_ARTIFACT_SOURCE_REFERENCE_BINDING


@dataclass(frozen=True, slots=True)
class RuntimeArtifactSourcePathMetadata:
    """Static runtime artifact source-path metadata vocabulary."""

    name: str = RUNTIME_ARTIFACT_SOURCE_PATH_METADATA


@dataclass(frozen=True, slots=True)
class RuntimeArtifactNoAccessResult:
    """Static no-access result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_NO_ACCESS_RESULT
    authority_boundary: tuple[str, ...] = (
        RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY_BOUNDARY
    )


@dataclass(frozen=True, slots=True)
class RuntimeArtifactTerminalCompletionPrerequisite:
    """Static terminal completion prerequisite vocabulary."""

    name: str = RUNTIME_ARTIFACT_TERMINAL_COMPLETION_PREREQUISITE


@dataclass(frozen=True, slots=True)
class RuntimeArtifactRunIdAlignmentResult:
    """Static run_id alignment result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_RUN_ID_ALIGNMENT_RESULT


@dataclass(frozen=True, slots=True)
class RuntimeArtifactProvenanceResult:
    """Static runtime artifact provenance result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_PROVENANCE_RESULT


@dataclass(frozen=True, slots=True)
class RuntimeArtifactRedactionResult:
    """Static runtime artifact redaction result vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_REDACTION_RESULT


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDiscoveryPrerequisite:
    """Static runtime artifact discovery prerequisite vocabulary."""

    name: str = RUNTIME_ARTIFACT_DISCOVERY_PREREQUISITE


@dataclass(frozen=True, slots=True)
class RuntimeCapturePrerequisite:
    """Static runtime capture prerequisite vocabulary."""

    name: str = RUNTIME_CAPTURE_PREREQUISITE


@dataclass(frozen=True, slots=True)
class EligibleRuntimeArtifactVocabulary:
    """Static eligible runtime artifact vocabulary."""

    name: str = ELIGIBLE_RUNTIME_ARTIFACT_VOCABULARY


@dataclass(frozen=True, slots=True)
class DiscoveredRuntimeArtifactMetadata:
    """Static discovered runtime artifact metadata vocabulary."""

    name: str = DISCOVERED_RUNTIME_ARTIFACT_METADATA


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDiscoveryFailure:
    """Static fail-closed runtime artifact discovery vocabulary."""

    result_type: str = RUNTIME_ARTIFACT_DISCOVERY_FAILURE


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDiscoveryInput:
    """Already-loaded runtime artifact discovery metadata."""

    canonical_run_id: str
    source_artifact_authority_result: Mapping[str, Any]
    source_references: tuple[str, ...]
    known_source_references: tuple[str, ...]
    eligible_runtime_artifact_vocabulary: tuple[str, ...]
    terminal_completion_rule: Mapping[str, Any]
    runtime_artifact_candidates: tuple[Mapping[str, Any], ...]
    runtime_artifact_provenance: str
    runtime_artifact_redaction_status: str
    input_run_ids: tuple[str, ...]
    sensitive_data_status: str = "clear"
    stale_runtime_artifact_metadata: bool = False
    malformed_runtime_artifact_metadata: bool = False
    ambiguous_source_references: bool = False
    runtime_log_dependent: bool = False
    runtime_path_dependent: bool = False
    file_read_dependent: bool = False
    source_path_ingestion_dependent: bool = False
    file_path_ingestion_dependent: bool = False
    artifact_copying_dependent: bool = False
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


def validate_runtime_artifact_discovery(
    discovery_metadata: RuntimeArtifactDiscoveryInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate runtime artifact discovery over already-loaded metadata."""

    return build_runtime_artifact_discovery_result(discovery_metadata)


def build_runtime_artifact_discovery_result(
    discovery_metadata: RuntimeArtifactDiscoveryInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build runtime artifact discovery metadata without artifact access."""

    normalized = _normalize_discovery_metadata(discovery_metadata)
    candidates = _validate_discovery_metadata(normalized)
    return {
        "result_type": RUNTIME_ARTIFACT_DISCOVERY_RESULT,
        "canonical_run_id": normalized.canonical_run_id,
        "source_references": tuple(normalized.source_references),
        "known_source_references": tuple(normalized.known_source_references),
        "eligible_runtime_artifact_vocabulary": tuple(
            normalized.eligible_runtime_artifact_vocabulary
        ),
        "terminal_completion_rule": dict(normalized.terminal_completion_rule),
        "runtime_artifact_candidates": candidates,
        "runtime_artifact_provenance": normalized.runtime_artifact_provenance,
        "runtime_artifact_redaction_status": (
            normalized.runtime_artifact_redaction_status
        ),
        "runtime_artifact_discovery_authority": True,
        "evidence_only": True,
        "metadata_only": True,
        "runtime_log_access": False,
        "file_reads": False,
        "source_path_ingestion": False,
        "file_path_ingestion": False,
        "artifact_copying": False,
        "runtime_artifact_capture": False,
        "runtime_capture": False,
        "evaluation_or_promotion": False,
        "strategy_risk_execution_behavior": False,
        "broker_api_authority": False,
        "execution_authority": False,
        "paper_trading_authority": False,
        "live_trading_authority": False,
        "prerequisites": RUNTIME_ARTIFACT_DISCOVERY_PREREQUISITES,
        "fail_closed_boundaries": (
            RUNTIME_ARTIFACT_DISCOVERY_FAIL_CLOSED_BOUNDARIES
        ),
        "authority_boundary": RUNTIME_ARTIFACT_DISCOVERY_AUTHORITY_BOUNDARY,
    }


def build_runtime_artifact_inventory_result(
    discovery_metadata: RuntimeArtifactDiscoveryInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Build a runtime artifact inventory result without artifact access."""

    return {
        **build_runtime_artifact_discovery_result(discovery_metadata),
        "result_type": RUNTIME_ARTIFACT_INVENTORY_RESULT,
    }


def validate_eligible_runtime_artifact_vocabulary(
    discovery_metadata: RuntimeArtifactDiscoveryInput | Mapping[str, Any],
) -> tuple[str, ...]:
    """Return validated eligible runtime artifact vocabulary."""

    normalized = _normalize_discovery_metadata(discovery_metadata)
    _validate_vocabulary(normalized.eligible_runtime_artifact_vocabulary)
    return tuple(normalized.eligible_runtime_artifact_vocabulary)


def validate_runtime_artifact_candidates(
    discovery_metadata: RuntimeArtifactDiscoveryInput | Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Return validated runtime artifact candidate metadata."""

    normalized = _normalize_discovery_metadata(discovery_metadata)
    _reject_forbidden_dependencies(normalized)
    _validate_run_identity(normalized)
    _validate_source_artifact_authority(normalized)
    _validate_source_references(normalized)
    _validate_vocabulary(normalized.eligible_runtime_artifact_vocabulary)
    _validate_terminal_completion_rule(normalized.terminal_completion_rule)
    _validate_runtime_artifact_metadata(normalized)
    return _validate_candidates(normalized)


def _normalize_discovery_metadata(
    discovery_metadata: RuntimeArtifactDiscoveryInput | Mapping[str, Any],
) -> RuntimeArtifactDiscoveryInput:
    if isinstance(discovery_metadata, RuntimeArtifactDiscoveryInput):
        return discovery_metadata
    if not isinstance(discovery_metadata, Mapping):
        raise TypeError("runtime artifact discovery input must be loaded metadata")
    return RuntimeArtifactDiscoveryInput(**discovery_metadata)


def _validate_discovery_metadata(
    discovery_metadata: RuntimeArtifactDiscoveryInput,
) -> tuple[dict[str, Any], ...]:
    _reject_forbidden_dependencies(discovery_metadata)
    _validate_run_identity(discovery_metadata)
    _validate_source_artifact_authority(discovery_metadata)
    _validate_source_references(discovery_metadata)
    _validate_vocabulary(discovery_metadata.eligible_runtime_artifact_vocabulary)
    _validate_terminal_completion_rule(discovery_metadata.terminal_completion_rule)
    _validate_runtime_artifact_metadata(discovery_metadata)
    return _validate_candidates(discovery_metadata)


def _reject_forbidden_dependencies(
    discovery_metadata: RuntimeArtifactDiscoveryInput,
) -> None:
    if discovery_metadata.malformed_runtime_artifact_metadata:
        raise ValueError("malformed runtime artifact metadata")
    if discovery_metadata.stale_runtime_artifact_metadata:
        raise ValueError("stale runtime artifact metadata")
    if discovery_metadata.ambiguous_source_references:
        raise ValueError("ambiguous source references")
    if discovery_metadata.runtime_log_dependent:
        raise ValueError("runtime log dependency")
    if discovery_metadata.runtime_path_dependent:
        raise ValueError("runtime path dependency")
    if discovery_metadata.file_read_dependent:
        raise ValueError("file read dependency")
    if discovery_metadata.source_path_ingestion_dependent:
        raise ValueError("source path ingestion dependency")
    if discovery_metadata.file_path_ingestion_dependent:
        raise ValueError("file path ingestion dependency")
    if discovery_metadata.artifact_copying_dependent:
        raise ValueError("artifact copying dependency")
    if discovery_metadata.runtime_capture_dependent or (
        discovery_metadata.attempted_runtime_capture
    ):
        raise ValueError("runtime artifact discovery is not runtime capture")
    if discovery_metadata.evaluation_dependent or (
        discovery_metadata.attempted_evaluation_approval
    ):
        raise ValueError("runtime artifact discovery is not evaluation approval")
    if discovery_metadata.broker_dependent:
        raise ValueError("broker dependency")
    if discovery_metadata.strategy_risk_execution_dependent:
        raise ValueError("strategy/risk/execution dependency")
    if discovery_metadata.attempted_execution_permission:
        raise ValueError("runtime artifact discovery is not execution permission")
    if discovery_metadata.attempted_paper_trading_authority or (
        discovery_metadata.paper_trading_authority
    ):
        raise ValueError("runtime artifact discovery is not paper trading authority")
    if discovery_metadata.attempted_live_trading_authority or (
        discovery_metadata.live_trading_authority
    ):
        raise ValueError("runtime artifact discovery is not live trading authority")


def _validate_run_identity(discovery_metadata: RuntimeArtifactDiscoveryInput) -> None:
    if not discovery_metadata.canonical_run_id:
        raise ValueError("canonical_run_id is required")
    for run_id in discovery_metadata.input_run_ids:
        if run_id != discovery_metadata.canonical_run_id:
            raise ValueError("mixed run_id runtime artifact metadata")


def _validate_source_artifact_authority(
    discovery_metadata: RuntimeArtifactDiscoveryInput,
) -> None:
    result = discovery_metadata.source_artifact_authority_result
    if not isinstance(result, Mapping) or not result:
        raise ValueError("source artifact authority result is required")
    if result.get("source_artifact_authority") is not True:
        raise ValueError("source artifact authority result must be valid")
    if result.get("metadata_only") is not True:
        raise ValueError("source artifact authority result must be metadata-only")
    if result.get("runtime_artifact_discovery") is not False:
        raise ValueError("source artifact authority must not discover artifacts")
    if result.get("runtime_capture") is not False:
        raise ValueError("source artifact authority must not capture runtime data")
    if result.get("canonical_run_id") != discovery_metadata.canonical_run_id:
        raise ValueError("mixed run_id runtime artifact metadata")


def _validate_source_references(
    discovery_metadata: RuntimeArtifactDiscoveryInput,
) -> None:
    if not discovery_metadata.source_references:
        raise ValueError("missing source references")
    known_references = set(discovery_metadata.known_source_references)
    if not known_references:
        raise ValueError("unknown source references")
    for source_reference in discovery_metadata.source_references:
        if source_reference not in known_references:
            raise ValueError("unknown source references")


def _validate_vocabulary(vocabulary: tuple[str, ...]) -> None:
    if not vocabulary:
        raise ValueError("missing eligible runtime artifact vocabulary")
    for artifact_type in vocabulary:
        if not isinstance(artifact_type, str) or not artifact_type:
            raise ValueError("malformed eligible runtime artifact vocabulary")


def _validate_terminal_completion_rule(rule: Mapping[str, Any]) -> None:
    if not isinstance(rule, Mapping) or not rule:
        raise ValueError("missing terminal completion rule")
    if rule.get("required") is not True:
        raise ValueError("missing terminal completion rule")
    if rule.get("satisfied") is not True:
        raise ValueError("failed terminal completion rule")


def _validate_runtime_artifact_metadata(
    discovery_metadata: RuntimeArtifactDiscoveryInput,
) -> None:
    if not isinstance(discovery_metadata.runtime_artifact_provenance, str):
        raise ValueError("malformed runtime artifact provenance")
    if not discovery_metadata.runtime_artifact_provenance:
        raise ValueError("missing runtime artifact provenance")
    if not discovery_metadata.runtime_artifact_redaction_status:
        raise ValueError("missing runtime artifact redaction status")
    if discovery_metadata.runtime_artifact_redaction_status not in (
        VALID_REDACTION_STATUS
    ):
        raise ValueError("invalid runtime artifact redaction status")
    if discovery_metadata.sensitive_data_status != "clear":
        raise ValueError("sensitive data exposure")


def _validate_candidates(
    discovery_metadata: RuntimeArtifactDiscoveryInput,
) -> tuple[dict[str, Any], ...]:
    if not discovery_metadata.runtime_artifact_candidates:
        raise ValueError("malformed runtime artifact metadata")
    candidates = tuple(
        _normalize_candidate(candidate)
        for candidate in discovery_metadata.runtime_artifact_candidates
    )
    vocabulary = set(discovery_metadata.eligible_runtime_artifact_vocabulary)
    source_references = set(discovery_metadata.source_references)
    validated = []
    for candidate in candidates:
        if not candidate.artifact_id:
            raise ValueError("malformed runtime artifact metadata")
        if candidate.canonical_run_id != discovery_metadata.canonical_run_id:
            raise ValueError("mixed run_id runtime artifact metadata")
        if candidate.artifact_type not in vocabulary:
            raise ValueError("malformed eligible runtime artifact vocabulary")
        if candidate.source_reference not in source_references:
            raise ValueError("unknown source references")
        if not candidate.eligible:
            raise ValueError("malformed runtime artifact metadata")
        if not isinstance(candidate.provenance, str) or not candidate.provenance:
            raise ValueError("malformed runtime artifact provenance")
        if candidate.redaction_status not in VALID_REDACTION_STATUS:
            raise ValueError("invalid runtime artifact redaction status")
        if candidate.source_path_metadata is not None and not isinstance(
            candidate.source_path_metadata,
            str,
        ):
            raise ValueError("malformed runtime artifact metadata")
        validated.append(
            {
                "artifact_id": candidate.artifact_id,
                "artifact_type": candidate.artifact_type,
                "source_reference": candidate.source_reference,
                "canonical_run_id": candidate.canonical_run_id,
                "provenance": candidate.provenance,
                "redaction_status": candidate.redaction_status,
                "eligible": candidate.eligible,
                "source_path_metadata": candidate.source_path_metadata,
                "runtime_log_access": False,
                "file_reads": False,
                "source_path_ingestion": False,
                "file_path_ingestion": False,
                "artifact_copying": False,
                "runtime_artifact_capture": False,
                "runtime_capture": False,
            }
        )
    return tuple(validated)


def _normalize_candidate(
    candidate: RuntimeArtifactCandidate | Mapping[str, Any],
) -> RuntimeArtifactCandidate:
    if isinstance(candidate, RuntimeArtifactCandidate):
        return candidate
    if not isinstance(candidate, Mapping):
        raise TypeError("runtime artifact candidate must be loaded metadata")
    return RuntimeArtifactCandidate(**candidate)
