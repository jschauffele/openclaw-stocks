from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType

import tools.replay.draft_envelope as draft_envelope
import tools.replay.canonical_bytes as canonical_bytes
import tools.replay.canonical_json as canonical_json
import tools.replay.hashing as hashing
import tools.replay.integrity as integrity
import tools.replay.manifest_schema as manifest_schema
import tools.replay.offline_mapper as offline_mapper
import tools.replay.package_layout as package_layout
import tools.replay.package_schema as package_schema
from tools.replay.draft_envelope import build_draft_replay_envelope
from tools.replay.offline_mapper import build_replay_package
from tools.replay.package_schema import (
    AUTHORITY_BOUNDARY,
    ENVELOPE_SECTIONS,
    OUT_OF_SCOPE,
    ReplayInputBundle,
)


EVIDENCE_CANDIDATE_DIR = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "3_close_trend_confirmation"
    / "local_alpaca_2026_01_02_to_2026_05_24"
)
RISK_BLOCKED_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "replay"
    / "event_streams"
    / "risk_blocked"
    / "run_2026-05-29T19:45:04Z_8b7033.jsonl"
)
RISK_BLOCKED_FIXTURE_SHA256 = (
    "8c68bb94ea663997874b28c705820b78ca45808cd5fd4a36363582bdcc72aca4"
)
FUTURE_DRAFT_ENVELOPE_MODULE = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "draft_envelope.py"
)
FUTURE_PACKAGE_CREATION_MODULES = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "package_writer.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "package_creator.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "package_creation.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "manifest_writer.py",
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "manifest_generator.py"
    ),
)
FUTURE_MANIFEST_SCHEMA_MODULES = (
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "manifest_constants.py"
    ),
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "manifest_builder.py",
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "deterministic_serializer.py"
    ),
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "canonical_serializer.py"
    ),
)
MANIFEST_SCHEMA_MODULE = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "manifest_schema.py"
)
FUTURE_DETERMINISTIC_SERIALIZATION_MODULES = (
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "serialization_constants.py"
    ),
)
CANONICAL_JSON_MODULE = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "canonical_json.py"
)
CANONICAL_BYTES_MODULE = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "canonical_bytes.py"
)
REPLAY_PACKAGE_SPECIFICATION = (
    Path(__file__).resolve().parents[1] / "docs" / "replay_package_specification.md"
)
IMPLEMENTATION_PREREQUISITE_MAP = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "replay_evaluation_implementation_prerequisite_map.md"
)
EVALUATION_INFRASTRUCTURE_ARCHITECTURE = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "evaluation_infrastructure_architecture.md"
)
REPLAY_SOURCE_MODULES = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "draft_envelope.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "offline_mapper.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "package_schema.py",
)
FORBIDDEN_DRAFT_ENVELOPE_NAMES = (
    "Path",
    "os",
    "subprocess",
    "socket",
    "hashlib",
    "main",
    "broker",
    "alpaca",
    "ibkr",
    "reporting",
    "state_manager",
    "event_logger",
    "observation_logger",
    "runtime_visibility_writer",
    "runtime_visibility_orchestrator",
    "runtime_visibility_provider_composer",
    "open",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "touch",
    "replace",
    "rename",
    "unlink",
    "rmdir",
)
FORBIDDEN_PACKAGE_CREATION_NAMES = (
    *FORBIDDEN_DRAFT_ENVELOPE_NAMES,
    "package_writer",
    "package_creator",
    "package_creation",
    "manifest_writer",
    "manifest_generator",
    "hash_writer",
    "integrity_validator",
    "storage_writer",
    "runtime_capture",
    "file_ingestion",
)
FORBIDDEN_PACKAGE_CREATION_IMPLEMENTATION_NAMES = (
    "PACKAGE_CREATION",
    "PACKAGE_CREATION_CONSTANTS",
    "PACKAGE_BUILDER_TYPES",
    "PACKAGE_CREATION_MODULE",
    "PACKAGE_LAYOUT_CONSTANTS",
    "PACKAGE_LAYOUT",
    "PACKAGE_ID",
    "CANONICAL_RUN_ID",
    "REPLAY_PACKAGE_BUILDER",
    "COMPLETE_REPLAY_PACKAGE",
    "PACKAGE_COMPLETENESS",
    "MANIFEST_GENERATION",
    "CANONICAL_BYTE_OUTPUT",
    "PackageCreation",
    "PackageBuilder",
    "PackageBuilderInput",
    "PackageBuilderOutput",
    "PackageCreationModule",
    "PackageLayout",
    "PackageIdentity",
    "PackageId",
    "CanonicalRunId",
    "ReplayPackageBuilder",
    "CompleteReplayPackage",
    "PackageCompleteness",
    "ManifestGeneration",
    "build_replay_package_file",
    "build_package_layout",
    "build_package_identity",
    "build_package_id",
    "build_package_manifest",
    "generate_manifest",
    "generate_replay_package",
    "create_replay_package",
    "create_package",
    "assemble_replay_package",
    "assemble_package",
    "validate_package_creation",
    "validate_package_layout",
    "validate_package_identity",
    "write_package",
    "write_replay_package",
)
FUTURE_PACKAGE_IDENTITY_LAYOUT_MODULES = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "package_layout.py",
)
FUTURE_PACKAGE_IDENTITY_LAYOUT_SCOPE_RELAXABLE_NAMES = (
    "PACKAGE_IDENTITY",
    "PACKAGE_LAYOUT",
    "PACKAGE_ID",
    "CANONICAL_RUN_ID",
    "PackageIdentity",
    "PackageLayout",
    "PackageId",
    "CanonicalRunId",
)
PACKAGE_IDENTITY_LAYOUT_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "PACKAGE_CREATION",
    "PACKAGE_CREATION_CONSTANTS",
    "PACKAGE_BUILDER_TYPES",
    "PACKAGE_CREATION_MODULE",
    "PACKAGE_DIRECTORY",
    "PACKAGE_DIRECTORIES",
    "PACKAGE_PATH",
    "REPLAY_PACKAGE_BUILDER",
    "COMPLETE_REPLAY_PACKAGE",
    "PACKAGE_COMPLETENESS",
    "MANIFEST_GENERATION",
    "PackageCreation",
    "PackageBuilder",
    "PackageBuilderInput",
    "PackageBuilderOutput",
    "PackageCreationModule",
    "PackageDirectory",
    "PackagePath",
    "ReplayPackageBuilder",
    "CompleteReplayPackage",
    "PackageCompleteness",
    "ManifestGeneration",
    "build_replay_package_file",
    "build_package_directory",
    "create_package_directory",
    "build_package_manifest",
    "generate_manifest",
    "generate_replay_package",
    "create_replay_package",
    "create_package",
    "assemble_replay_package",
    "assemble_package",
    "validate_package_creation",
    "write_package",
    "write_replay_package",
    "open",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "hashlib",
    "compute_hash",
    "calculate_hash",
    "build_hash",
    "build_section_hash",
    "build_manifest_hash",
    "build_package_hash",
    "validate_hash",
    "validate_integrity",
    "verify_integrity",
    "StorageFinalization",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
FUTURE_MANIFEST_GENERATION_MODULES = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "manifest_builder.py",
)
FUTURE_MANIFEST_GENERATION_SCOPE_RELAXABLE_NAMES = (
    "MANIFEST_GENERATION",
    "MANIFEST_BUILDER",
    "DRAFT_MANIFEST",
    "MANIFEST_INPUT",
    "MANIFEST_FIELD_ELIGIBILITY",
    "MANIFEST_PROVENANCE_ELIGIBILITY",
    "MANIFEST_REDACTION_ELIGIBILITY",
    "MANIFEST_RUN_ID_ALIGNMENT",
    "MANIFEST_SOURCE_REFERENCE_ELIGIBILITY",
    "ManifestGeneration",
    "ManifestBuilder",
    "DraftManifest",
    "ManifestInput",
    "ManifestFieldEligibility",
    "ManifestProvenanceEligibility",
    "ManifestRedactionEligibility",
    "ManifestRunIdAlignment",
    "ManifestSourceReferenceEligibility",
    "build_draft_manifest",
    "build_in_memory_manifest",
)
MANIFEST_GENERATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "PACKAGE_CREATION",
    "PACKAGE_DIRECTORY",
    "PACKAGE_PATH",
    "PackageCreation",
    "PackageDirectory",
    "PackagePath",
    "ReplayPackageCreation",
    "CompleteReplayPackage",
    "PackageCompleteness",
    "generate_manifest",
    "create_manifest",
    "write_manifest",
    "serialize_manifest",
    "package_manifest",
    "replay_manifest",
    "open",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "hashlib",
    "compute_hash",
    "calculate_hash",
    "build_hash",
    "build_section_hash",
    "build_manifest_hash",
    "build_package_hash",
    "validate_hash",
    "validate_integrity",
    "verify_integrity",
    "StorageFinalization",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
FORBIDDEN_MANIFEST_SCHEMA_NAMES = (
    *FORBIDDEN_PACKAGE_CREATION_NAMES,
    "manifest_schema",
    "manifest_constants",
    "manifest_builder",
    "deterministic_serializer",
    "canonical_serializer",
    "hash_manifest",
    "hash_package",
)
FORBIDDEN_MANIFEST_SCHEMA_IMPLEMENTATION_NAMES = (
    "MANIFEST_SCHEMA_VERSION",
    "MANIFEST_SCHEMA",
    "MANIFEST_FIELDS",
    "MANIFEST_REQUIRED_FIELDS",
    "MANIFEST_OPTIONAL_FIELDS",
    "MANIFEST_SECTION_STATUS",
    "MANIFEST_LIFECYCLE_STATUS",
    "MANIFEST_AUTHORITY_BOUNDARY",
    "ManifestSchema",
    "ManifestSchemaVersion",
    "ManifestField",
    "ManifestSection",
    "ManifestSectionStatus",
    "ManifestLifecycleStatus",
    "ManifestAuthorityBoundary",
    "ManifestBuilder",
    "ManifestGeneration",
    "build_manifest_schema",
    "build_manifest",
    "generate_manifest",
    "validate_manifest_schema",
    "validate_manifest",
    "create_manifest",
    "package_manifest",
    "replay_manifest",
)
FUTURE_MANIFEST_SCHEMA_SCOPE_RELAXABLE_NAMES = (
    "MANIFEST_SCHEMA_VERSION",
    "MANIFEST_SCHEMA",
    "MANIFEST_FIELDS",
    "MANIFEST_REQUIRED_FIELDS",
    "MANIFEST_OPTIONAL_FIELDS",
    "MANIFEST_SECTION_STATUS",
    "MANIFEST_LIFECYCLE_STATUS",
    "ManifestSchema",
    "ManifestField",
    "ManifestSectionStatus",
)
MANIFEST_SCHEMA_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "ManifestBuilder",
    "ManifestGeneration",
    "build_manifest",
    "generate_manifest",
    "validate_manifest",
    "create_manifest",
    "package_manifest",
    "replay_manifest",
    "CanonicalBytes",
    "HashComputation",
    "IntegrityValidation",
    "PackageLayout",
    "PackageIdentity",
    "StorageFinalization",
    "RuntimeCapture",
    "ReplayPackageCreation",
    "EvaluationEngine",
    "PromotionGate",
)
FORBIDDEN_SERIALIZATION_NAMES = (
    *FORBIDDEN_MANIFEST_SCHEMA_NAMES,
    "serialization_constants",
    "canonical_json",
    "canonical_bytes",
    "serialize_manifest",
    "serialize_package",
    "manifest_hash_authority",
    "package_hash_authority",
    "canonical_byte_generation",
    "deterministic_serialization_authority",
)
FORBIDDEN_SERIALIZATION_IMPLEMENTATION_NAMES = (
    "SERIALIZATION_SCHEMA",
    "SERIALIZATION_VERSION",
    "SERIALIZATION_CONSTANTS",
    "CANONICAL_JSON",
    "CANONICAL_BYTES",
    "CANONICAL_SERIALIZATION",
    "CANONICAL_SERIALIZER",
    "SERIALIZER_INPUT",
    "SERIALIZER_OUTPUT",
    "SERIALIZATION_TYPES",
    "MANIFEST_SERIALIZATION",
    "PACKAGE_SERIALIZATION",
    "SerializationSchema",
    "SerializationVersion",
    "CanonicalJson",
    "CanonicalBytes",
    "CanonicalSerializer",
    "SerializationInput",
    "SerializationOutput",
    "ManifestSerialization",
    "PackageSerialization",
    "build_canonical_json",
    "build_canonical_bytes",
    "serialize_manifest",
    "serialize_package",
    "serialize_section",
    "canonicalize_json",
    "canonicalize_manifest",
    "canonicalize_package",
    "generate_canonical_bytes",
    "validate_serialization",
    "validate_canonical_bytes",
)
FUTURE_SERIALIZATION_SCOPE_RELAXABLE_NAMES = (
    "SERIALIZATION_SCHEMA",
    "SERIALIZATION_VERSION",
    "SERIALIZATION_CONSTANTS",
    "CANONICAL_JSON",
    "CANONICAL_BYTES",
    "CANONICAL_SERIALIZATION",
    "CANONICAL_SERIALIZER",
    "SERIALIZER_INPUT",
    "SERIALIZER_OUTPUT",
    "SERIALIZATION_TYPES",
    "SerializationSchema",
    "SerializationVersion",
    "CanonicalJson",
    "CanonicalBytes",
    "CanonicalSerializer",
    "SerializationInput",
    "SerializationOutput",
    "canonicalize_json",
    "validate_serialization",
)
CANONICAL_JSON_IMPLEMENTED_NAMES = (
    "SERIALIZATION_SCHEMA",
    "SERIALIZATION_VERSION",
    "SERIALIZATION_CONSTANTS",
    "CANONICAL_JSON",
    "CANONICAL_SERIALIZATION",
    "CANONICAL_SERIALIZER",
    "SERIALIZER_INPUT",
    "SERIALIZER_OUTPUT",
    "SERIALIZATION_TYPES",
    "SerializationSchema",
    "SerializationVersion",
    "CanonicalJson",
    "CanonicalSerializer",
    "SerializationInput",
    "SerializationOutput",
    "canonicalize_json",
    "validate_serialization",
)
FUTURE_CANONICAL_BYTES_SCOPE_RELAXABLE_NAMES = (
    "CANONICAL_BYTES",
    "CanonicalBytes",
    "build_canonical_bytes",
    "validate_canonical_bytes",
)
CANONICAL_BYTES_SCOPE_INPUT_MODEL = "canonical_json_text_only"
CANONICAL_BYTES_SCOPE_ENCODING = "utf-8"
CANONICAL_BYTES_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "MANIFEST_SERIALIZATION",
    "PACKAGE_SERIALIZATION",
    "ManifestSerialization",
    "PackageSerialization",
    "serialize_manifest",
    "serialize_package",
    "serialize_section",
    "canonicalize_manifest",
    "canonicalize_package",
    "generate_canonical_bytes",
    "HashComputation",
    "IntegrityValidation",
    "PackageLayout",
    "PackageIdentity",
    "ReplayPackageCreation",
    "StorageFinalization",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
FUTURE_HASHING_INTEGRITY_MODULES = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "hashing.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "integrity.py",
)
FUTURE_HASHING_INTEGRITY_SCOPE_RELAXABLE_NAMES = (
    "HASH_ALGORITHM",
    "HASH_VERSION",
    "INTEGRITY_STATUS",
    "HashAlgorithm",
    "HashVersion",
    "IntegrityStatus",
)
HASHING_INTEGRITY_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "HASH_CONSTANTS",
    "HASH_HELPER",
    "HASH_HELPERS",
    "SECTION_HASH",
    "MANIFEST_HASH",
    "PACKAGE_HASH",
    "INTEGRITY_VALIDATION",
    "CANONICAL_HASH_INPUT",
    "SectionHash",
    "ManifestHash",
    "PackageHash",
    "IntegrityValidation",
    "IntegrityValidator",
    "HashInput",
    "CanonicalHashInput",
    "compute_hash",
    "calculate_hash",
    "build_hash",
    "build_section_hash",
    "build_manifest_hash",
    "build_package_hash",
    "compute_section_hash",
    "compute_manifest_hash",
    "compute_package_hash",
    "validate_integrity",
    "verify_integrity",
    "validate_hash",
    "hash_manifest",
    "hash_package",
    "hash_section",
    "hashlib",
    "MANIFEST_SERIALIZATION",
    "PACKAGE_SERIALIZATION",
    "ManifestSerialization",
    "PackageSerialization",
    "serialize_manifest",
    "serialize_package",
    "PackageLayout",
    "PackageIdentity",
    "ReplayPackageCreation",
    "StorageFinalization",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
SERIALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "MANIFEST_SERIALIZATION",
    "PACKAGE_SERIALIZATION",
    "ManifestSerialization",
    "PackageSerialization",
    "build_canonical_bytes",
    "serialize_manifest",
    "serialize_package",
    "serialize_section",
    "canonicalize_manifest",
    "canonicalize_package",
    "generate_canonical_bytes",
    "validate_canonical_bytes",
    "HashComputation",
    "IntegrityValidation",
    "PackageLayout",
    "PackageIdentity",
    "ReplayPackageCreation",
    "StorageFinalization",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
FORBIDDEN_HASHING_INTEGRITY_IMPLEMENTATION_NAMES = (
    "HASH_ALGORITHM",
    "HASH_VERSION",
    "HASH_CONSTANTS",
    "HASH_HELPER",
    "HASH_HELPERS",
    "SECTION_HASH",
    "MANIFEST_HASH",
    "PACKAGE_HASH",
    "INTEGRITY_STATUS",
    "INTEGRITY_VALIDATION",
    "CANONICAL_HASH_INPUT",
    "HashAlgorithm",
    "HashVersion",
    "SectionHash",
    "ManifestHash",
    "PackageHash",
    "IntegrityStatus",
    "IntegrityValidation",
    "IntegrityValidator",
    "HashInput",
    "CanonicalHashInput",
    "build_section_hash",
    "build_manifest_hash",
    "build_package_hash",
    "compute_hash",
    "compute_section_hash",
    "compute_manifest_hash",
    "compute_package_hash",
    "validate_integrity",
    "validate_hash",
    "hash_manifest",
    "hash_package",
    "hash_section",
)
FORBIDDEN_STORAGE_IMMUTABILITY_IMPLEMENTATION_NAMES = (
    "STORAGE_ROOT",
    "STORAGE_PATH",
    "STORAGE_CONSTANTS",
    "PACKAGE_DIRECTORY",
    "PACKAGE_DIRECTORIES",
    "PACKAGE_PATH",
    "PACKAGE_LAYOUT",
    "FINALIZATION_STATE",
    "FINALIZED_PACKAGE",
    "IMMUTABILITY_ENFORCEMENT",
    "IMMUTABLE_PACKAGE",
    "RETENTION_INDEX",
    "DISCOVERY_INDEX",
    "STORAGE_INDEX",
    "StorageRoot",
    "StoragePath",
    "PackageDirectory",
    "PackagePath",
    "PackageLayout",
    "FinalizationState",
    "FinalizedPackage",
    "ImmutablePackage",
    "ImmutabilityEnforcement",
    "RetentionIndex",
    "DiscoveryIndex",
    "StorageIndex",
    "build_storage_path",
    "build_package_directory",
    "create_package_directory",
    "write_replay_package",
    "write_manifest",
    "write_package_file",
    "finalize_package",
    "mark_finalized",
    "enforce_immutability",
    "validate_storage_root",
    "validate_package_path",
    "build_retention_index",
    "build_discovery_index",
    "build_storage_index",
)
FUTURE_RUNTIME_CAPTURE_MODULES = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "runtime_capture.py",
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "runtime_artifacts.py"
    ),
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "source_path_ingestion.py"
    ),
)
FORBIDDEN_RUNTIME_CAPTURE_IMPLEMENTATION_NAMES = (
    "RUNTIME_CAPTURE",
    "RUNTIME_CAPTURE_CONSTANTS",
    "RUNTIME_CAPTURE_TYPES",
    "RUNTIME_CAPTURE_MODULE",
    "SOURCE_ARTIFACT",
    "SOURCE_REFERENCE",
    "SOURCE_PATH",
    "FILE_PATH_INGESTION",
    "ARTIFACT_DISCOVERY",
    "ARTIFACT_COPY",
    "RUNTIME_ARTIFACT",
    "RuntimeCapture",
    "RuntimeCaptureInput",
    "RuntimeCaptureOutput",
    "RuntimeCaptureModule",
    "SourceArtifact",
    "SourceReference",
    "SourcePath",
    "ArtifactDiscovery",
    "ArtifactCopy",
    "RuntimeArtifact",
    "capture_runtime_artifacts",
    "discover_runtime_artifacts",
    "ingest_runtime_artifact",
    "ingest_source_path",
    "copy_runtime_artifact",
    "read_runtime_artifact",
    "build_runtime_capture",
    "validate_runtime_capture",
    "build_source_reference",
    "build_source_path",
    "capture_jsonl",
    "capture_last_run_report",
    "capture_observations",
    "capture_runtime_visibility",
    "SOURCE_ARTIFACT_PATH",
    "CAPTURE_SOURCE",
    "CAPTURED_ARTIFACT",
    "JSONL_CAPTURE",
    "LAST_RUN_REPORT_CAPTURE",
    "OBSERVATION_CAPTURE",
    "RUNTIME_VISIBILITY_CAPTURE",
    "capture_jsonl_event_stream",
    "ingest_runtime_file",
    "read_runtime_file",
    "build_capture_manifest",
    "RuntimeCaptureResult",
    "RuntimeArtifactCapture",
    "RuntimeCaptureSource",
    "RuntimeCaptureWriter",
    "SourcePathIngestion",
)
FORBIDDEN_EVALUATION_PROMOTION_IMPLEMENTATION_NAMES = (
    "EVALUATION_ENGINE",
    "EVALUATION_AUTHORITY",
    "PROMOTION_AUTHORITY",
    "PROMOTION_GATE",
    "ATTRIBUTION_LOGIC",
    "ATTRIBUTION_ENGINE",
    "EXPERIMENT_REGISTRY",
    "SCORING_METRICS",
    "REPLAY_PACKAGE_SCORING",
    "BACKTEST_RUNNER",
    "REPLAY_RUNNER",
    "STRATEGY_PROMOTION",
    "STRATEGY_PROMOTION_GATE",
    "METRIC_VOCABULARY",
    "ATTRIBUTION_VOCABULARY",
    "EXPERIMENT_ID",
    "PACKAGE_SET",
    "EvaluationEngine",
    "EvaluationAuthority",
    "PromotionAuthority",
    "PromotionGate",
    "AttributionLogic",
    "AttributionEngine",
    "ExperimentRegistry",
    "ScoringMetrics",
    "ReplayPackageScoring",
    "BacktestRunner",
    "ReplayRunner",
    "StrategyPromotion",
    "StrategyPromotionGate",
    "MetricVocabulary",
    "AttributionVocabulary",
    "ExperimentId",
    "PackageSet",
    "build_evaluation_engine",
    "build_attribution_logic",
    "build_experiment_registry",
    "build_scoring_metrics",
    "score_replay_package",
    "evaluate_replay_package",
    "evaluate_strategy_candidate",
    "compare_strategy_candidate",
    "promote_strategy",
    "approve_promotion",
    "create_promotion_gate",
    "run_backtest",
    "run_replay_evaluation",
)


def _event_payloads() -> list[dict]:
    return [
        {
            "schema_version": 1,
            "run_id": "run_1",
            "event_id": "evt_0001",
            "event_type": "data",
            "stage": "market_input_captured",
            "timestamp_utc": "2026-05-01T14:30:00Z",
            "timestamp": "2026-05-01T14:30:00Z",
            "status": "ok",
            "payload": {
                "symbol": "AAPL",
                "timeframe": "5Min",
                "candles": [{"close": 100.0}],
            },
        },
        {
            "schema_version": 1,
            "run_id": "run_1",
            "event_id": "evt_0002",
            "event_type": "strategy",
            "stage": "strategy_evaluated",
            "timestamp_utc": "2026-05-01T14:31:00Z",
            "timestamp": "2026-05-01T14:31:00Z",
            "status": "ok",
            "payload": {
                "signal": "buy",
                "decision": "buy",
                "action": "buy",
                "reason": "test_signal",
            },
        },
        {
            "schema_version": 1,
            "run_id": "run_1",
            "event_id": "evt_0003",
            "event_type": "risk",
            "stage": "risk_check",
            "timestamp_utc": "2026-05-01T14:32:00Z",
            "timestamp": "2026-05-01T14:32:00Z",
            "status": "ok",
            "payload": {"passed": True, "symbol": "AAPL", "qty": 1},
        },
    ]


def _run_report() -> dict:
    return {
        "run_id": "run_1",
        "timestamp": "2026-05-01T14:33:00Z",
        "trigger_source": "test",
        "result": "success",
        "reason": "paper_order_submitted",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 1,
        "orchestration": {
            "runtime_visibility": {
                "runtime_visibility_reports": [],
                "runtime_visibility_blocking": False,
                "runtime_visibility_reason": "runtime_visibility_clear",
            }
        },
    }


def _observations() -> list[dict]:
    return [
        {
            "timestamp_utc": "2026-05-01T14:33:00Z",
            "run_id": "run_1",
            "symbol": "AAPL",
            "signal": "buy",
            "action": "buy",
            "result": "success",
            "reason": "test_signal",
        }
    ]


def _order_state() -> dict:
    return {
        "run_id": "run_1",
        "timestamp": "2026-05-01T14:33:00Z",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 1,
        "mode": "paper_submit",
    }


def _runtime_visibility() -> dict:
    return {
        "run_id": "run_1",
        "runtime_visibility_reports": [],
        "runtime_visibility_blocking": False,
        "runtime_visibility_reason": "runtime_visibility_clear",
    }


def _complete_replay_inputs() -> dict:
    return {
        "events": _event_payloads(),
        "run_report": _run_report(),
        "observations": _observations(),
        "order_state": _order_state(),
        "runtime_visibility": _runtime_visibility(),
    }


def _committed_candidate_artifacts() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(EVIDENCE_CANDIDATE_DIR.glob("*_candidates.json"))
    ]


def _risk_blocked_fixture_events() -> list[dict]:
    fixture_bytes = RISK_BLOCKED_FIXTURE.read_bytes()
    return [
        json.loads(line)
        for line in fixture_bytes.decode("utf-8").splitlines()
        if line
    ]


def test_risk_blocked_event_stream_fixture_guard() -> None:
    assert RISK_BLOCKED_FIXTURE.is_file()

    fixture_bytes = RISK_BLOCKED_FIXTURE.read_bytes()
    assert hashlib.sha256(fixture_bytes).hexdigest() == RISK_BLOCKED_FIXTURE_SHA256

    events = _risk_blocked_fixture_events()

    assert len(events) == 10
    assert {event["run_id"] for event in events} == {
        "run_2026-05-29T19:45:04Z_8b7033"
    }
    assert [event["event_id"] for event in events] == [
        f"evt_{index:04d}" for index in range(1, 11)
    ]
    assert [event["stage"] for event in events] == [
        "startup",
        "config",
        "market_session",
        "fetch",
        "market_input_captured",
        "strategy_evaluated",
        "duplicate_check",
        "risk_check",
        "reconcile",
        "completion",
    ]

    terminal_event = events[-1]
    assert terminal_event["stage"] == "completion"
    assert terminal_event["status"] == "blocked"
    assert (
        terminal_event["payload"]["reason"]
        == "projected_exposure_exceeds_max_position_size"
    )

    for event in events:
        for field in (
            "schema_version",
            "timestamp_utc",
            "event_type",
            "stage",
            "status",
        ):
            assert event.get(field) is not None


def test_risk_blocked_event_stream_fixture_maps_as_incomplete_evidence_only_package() -> None:
    events = _risk_blocked_fixture_events()

    package = build_replay_package(events=events)

    assert package["package_status"]["status"] == "incomplete"
    assert package["package_status"]["section_statuses"] == {
        "events": "present",
        "run_report": "absent",
        "observations": "absent",
        "order_state": "absent",
        "runtime_visibility": "absent",
    }
    assert package["package_status"]["run_id_alignment"] == {
        "aligned": True,
        "canonical_run_id": "run_2026-05-29T19:45:04Z_8b7033",
        "mismatches": {},
    }
    assert package["run_identity"]["run_id"] == (
        "run_2026-05-29T19:45:04Z_8b7033"
    )
    assert package["event_order_references"]["events"] == events
    assert package["event_order_references"]["events"] is not events
    assert package["market_input_references"]["events"] == [events[4]]
    assert package["strategy_decision_references"]["events"] == [events[5]]
    assert package["reconciliation_risk_references"]["events"] == [
        events[6],
        events[7],
        events[8],
    ]
    assert package["configuration_references"] == {
        "status": "absent",
        "reason": "not_supplied",
    }
    assert package["portfolio_risk_snapshot_references"] == {
        "status": "absent",
        "reason": "portfolio_risk_reference_not_supplied",
    }
    assert package["broker_visible_state_references"] == {
        "status": "absent",
        "reason": "broker_visible_reference_not_supplied",
    }
    assert package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert package["immutability"]["reason"] == "deferred_until_storage_gate"
    assert package["authority_boundary"]["evidence_only"] is True
    assert package["authority_boundary"]["non_authoritative"] is True
    assert package["authority_boundary"]["no_execution_authority"] is True
    assert package["authority_boundary"]["no_broker_authority"] is True
    assert package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert package["out_of_scope"]["artifact_writer"] is True
    assert package["out_of_scope"]["runtime_capture"] is True
    assert package["out_of_scope"]["storage"] is True
    assert package["out_of_scope"]["replay_based_promotion_decisions"] is True


def test_draft_replay_envelope_source_preserves_writer_boundaries() -> None:
    inputs = _complete_replay_inputs()
    original_inputs = deepcopy(inputs)

    envelope = build_draft_replay_envelope(
        ReplayInputBundle(**inputs)
    )

    assert inputs == original_inputs
    assert envelope["lifecycle_status"] == "draft"
    assert envelope["evidence_only"] is True
    assert envelope["non_authoritative"] is True
    assert envelope["complete_replay_package_authority"] is False
    assert envelope["writer_authority"] is False
    assert envelope["filesystem_writes"] is False
    assert envelope["package_directory_creation"] is False
    assert envelope["file_path_ingestion"] is False
    assert envelope["manifest_creation"] is False
    assert envelope["hashing_integrity_enforcement"] is False
    assert envelope["runtime_capture"] is False
    assert envelope["storage_finalization_immutability"] is False
    assert envelope["evaluation_or_promotion"] is False
    assert envelope["broker_api_authority"] is False
    assert envelope["canonical_chronology"] == "event_jsonl"

    mapper_package = envelope["mapper_package"]
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True
    assert mapper_package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert mapper_package["immutability"]["reason"] == "deferred_until_storage_gate"

    event_only_envelope = build_draft_replay_envelope(
        {"events": _risk_blocked_fixture_events()}
    )

    assert event_only_envelope["lifecycle_status"] == "draft"
    assert event_only_envelope["complete_replay_package_authority"] is False
    assert (
        event_only_envelope["mapper_package"]["package_status"]["status"]
        == "incomplete"
    )
    assert event_only_envelope["mapper_package"]["event_order_references"][
        "events"
    ]

    try:
        build_draft_replay_envelope(RISK_BLOCKED_FIXTURE)  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == (
            "draft envelope scaffold accepts loaded replay inputs only"
        )
    else:
        raise AssertionError("expected TypeError")

    for forbidden_name in FORBIDDEN_DRAFT_ENVELOPE_NAMES:
        assert (
            forbidden_name
            not in build_draft_replay_envelope.__code__.co_names
        )


def test_draft_envelope_source_module_remains_pure_in_memory() -> None:
    assert FUTURE_DRAFT_ENVELOPE_MODULE.is_file()
    assert "draft" in build_draft_replay_envelope.__name__

    loaded_dict_envelope = build_draft_replay_envelope(
        _complete_replay_inputs()
    )
    bundle_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )

    assert loaded_dict_envelope["lifecycle_status"] == "draft"
    assert bundle_envelope["lifecycle_status"] == "draft"
    for envelope in (loaded_dict_envelope, bundle_envelope):
        assert envelope["evidence_only"] is True
        assert envelope["non_authoritative"] is True
        assert envelope["complete_replay_package_authority"] is False
        assert envelope["writer_authority"] is False
        assert envelope["canonical_chronology"] == "event_jsonl"
        assert envelope["filesystem_writes"] is False
        assert envelope["package_directory_creation"] is False
        assert envelope["file_path_ingestion"] is False
        assert envelope["manifest_creation"] is False
        assert envelope["hashing_integrity_enforcement"] is False
        assert envelope["runtime_capture"] is False
        assert envelope["storage_finalization_immutability"] is False
        assert envelope["evaluation_or_promotion"] is False
        assert envelope["broker_api_authority"] is False

    event_only_envelope = build_draft_replay_envelope(
        {"events": _risk_blocked_fixture_events()}
    )
    assert (
        event_only_envelope["mapper_package"]["package_status"]["status"]
        == "incomplete"
    )
    assert event_only_envelope["complete_replay_package_authority"] is False

    try:
        build_draft_replay_envelope(str(RISK_BLOCKED_FIXTURE))  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == (
            "draft envelope scaffold accepts loaded replay inputs only"
        )
    else:
        raise AssertionError("expected TypeError")

    assert (
        loaded_dict_envelope["mapper_package"]["package_status"]["status"]
        == "complete"
    )
    assert loaded_dict_envelope["complete_replay_package_authority"] is False
    assert loaded_dict_envelope["mapper_package"]["authority_boundary"][
        "non_authoritative"
    ] is True

    helper_names = build_draft_replay_envelope.__code__.co_names
    for forbidden_name in FORBIDDEN_DRAFT_ENVELOPE_NAMES:
        assert forbidden_name not in helper_names


def test_replay_package_creation_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Replay Package Creation Authority Contract" in spec_text
    assert "governance-only and is not\nimplemented yet" in spec_text
    assert "does not approve tests, code, package creation\nconstants" in spec_text
    assert "package builder types, package creation modules" in spec_text
    assert "package layout\nconstants" in spec_text
    assert "canonical byte generation, hash computation" in spec_text
    assert "Replay package creation rules must be source-controlled" in spec_text
    assert "Package layout authority must be explicitly governed" in spec_text
    assert "Package identity authority must be explicitly governed" in spec_text
    assert "`canonical_run_id` and governed `package_id` rules" in spec_text
    assert "Already-loaded envelope dictionaries may remain draft-only" in spec_text
    assert "Future manifest inputs require manifest generation authority" in spec_text
    assert "Future source references require source-reference authority" in spec_text
    assert "Future approved source paths require source path authority" in spec_text
    assert "Future copied artifacts require artifact copying authority" in spec_text
    assert "Future runtime-captured artifacts require runtime capture authority" in spec_text
    assert "The first future package-creation lifecycle state" in spec_text
    assert "`draft` only" in spec_text
    assert "Draft-only package assembly" in spec_text
    assert '`package_status == "complete"` remains' in spec_text
    assert "mapper bucket completeness only" in spec_text
    assert "Complete replay package authority must require explicit package creation" in spec_text
    assert "Manifest generation authority before package creation" in spec_text
    assert "Deterministic serialization authority before package creation" in spec_text
    assert "Canonical byte authority before package creation" in spec_text
    assert "Hashing and integrity validation before package creation" in spec_text
    assert "Storage and finalization authority before package creation" in spec_text
    assert "Runtime capture authority before package creation" in spec_text
    assert "Provenance must be explicit before package creation" in spec_text
    assert "Redaction status must be explicit before package creation" in spec_text
    assert "Source-reference authority must be explicit before package creation" in spec_text
    assert "Runtime terminal completion requirements must be explicit" in spec_text
    assert "Missing `run_id` must fail closed" in spec_text
    assert "Mixed `run_id` must fail closed" in spec_text
    assert "Stale artifacts must fail closed" in spec_text
    assert "Malformed artifacts must fail closed" in spec_text
    assert "Missing terminal completion must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Invalid redaction status must fail closed" in spec_text
    assert "Unknown source references must fail closed" in spec_text
    assert "Sensitive data exposure must stop package creation" in spec_text
    assert "Ambiguous package identity must fail closed" in spec_text
    assert "Package creation must remain separate from runtime capture" in spec_text
    assert "Package creation must remain separate from storage and finalization" in spec_text
    assert "Package creation must remain separate from evaluation and promotion" in spec_text
    assert "Package creation must not call `main.py`" in spec_text
    assert "Package creation must not stop or start timers" in spec_text
    assert "Package creation must not call broker/API/TWS/Alpaca/IBKR" in spec_text
    assert "must not respond to or remediate blocked buy/sell signals" in spec_text
    assert "Replay package creation cannot authorize manifest authority" in spec_text
    assert "Package creation output cannot become\nmanifest truth" in spec_text

    for module_path in FUTURE_PACKAGE_CREATION_MODULES:
        assert not module_path.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    event_only_envelope = build_draft_replay_envelope(
        {"events": _risk_blocked_fixture_events()}
    )
    report_only_package = build_replay_package(
        events=[],
        run_report=_run_report(),
    )

    for envelope in (complete_inputs_envelope, event_only_envelope):
        assert envelope["lifecycle_status"] == "draft"
        assert envelope["evidence_only"] is True
        assert envelope["non_authoritative"] is True
        assert envelope["complete_replay_package_authority"] is False
        assert envelope["writer_authority"] is False
        assert envelope["filesystem_writes"] is False
        assert envelope["package_directory_creation"] is False
        assert envelope["file_path_ingestion"] is False
        assert envelope["manifest_creation"] is False
        assert envelope["hashing_integrity_enforcement"] is False
        assert envelope["runtime_capture"] is False
        assert envelope["storage_finalization_immutability"] is False
        assert envelope["evaluation_or_promotion"] is False
        assert envelope["broker_api_authority"] is False
        assert envelope["canonical_chronology"] == "event_jsonl"
        assert "replay_package_authority" not in envelope
        assert "package_creation_authority" not in envelope
        assert "manifest_authority" not in envelope
        assert "canonical_byte_authority" not in envelope
        assert "hash_integrity_authority" not in envelope
        assert "storage_finalization_authority" not in envelope
        assert "runtime_capture_authority" not in envelope
        assert "evaluation_authority" not in envelope
        assert "promotion_authority" not in envelope
        assert "execution_permission" not in envelope
        assert "live_trading_authority" not in envelope
        assert "finalized_immutable_replay_package_authority" not in envelope

    assert (
        complete_inputs_envelope["mapper_package"]["package_status"]["status"]
        == "complete"
    )
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert complete_inputs_envelope["mapper_package"]["authority_boundary"][
        "non_authoritative"
    ] is True

    assert (
        event_only_envelope["mapper_package"]["package_status"]["status"]
        == "incomplete"
    )
    assert event_only_envelope["complete_replay_package_authority"] is False
    assert event_only_envelope["mapper_package"]["run_identity"]["run_id"] == (
        "run_2026-05-29T19:45:04Z_8b7033"
    )

    assert report_only_package["package_status"]["status"] == "incomplete"
    assert report_only_package["event_order_references"] == {
        "status": "absent",
        "reason": "events_not_supplied",
    }
    assert report_only_package["configuration_references"]["run_report"] == _run_report()
    assert report_only_package["authority_boundary"]["non_authoritative"] is True
    assert report_only_package["out_of_scope"]["artifact_writer"] is True
    assert report_only_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert report_only_package["out_of_scope"]["storage"] is True
    assert report_only_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert report_only_package["out_of_scope"]["runtime_capture"] is True
    assert report_only_package["out_of_scope"]["broker_live_api_work"] is True
    assert report_only_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for module in (draft_envelope, offline_mapper, package_schema):
        module_names = set(module.__dict__)
        for forbidden_name in FORBIDDEN_PACKAGE_CREATION_NAMES:
            assert forbidden_name not in module_names
        for value in module.__dict__.values():
            if isinstance(value, FunctionType):
                assert set(FORBIDDEN_PACKAGE_CREATION_NAMES).isdisjoint(
                    value.__code__.co_names
                )

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_PACKAGE_CREATION_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_manifest_schema_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Manifest Schema Authority Contract" in spec_text
    assert "must remain separate from manifest generation" in spec_text
    assert "remain separate from mapper completeness" in spec_text
    assert "package_status == \"complete\"" in spec_text
    assert "only in-memory bucket completeness" in spec_text

    for module_path in FUTURE_MANIFEST_SCHEMA_MODULES:
        assert not module_path.exists()
    assert MANIFEST_SCHEMA_MODULE.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]
    event_only_envelope = build_draft_replay_envelope(
        {"events": _risk_blocked_fixture_events()}
    )

    assert complete_inputs_envelope["lifecycle_status"] == "draft"
    assert event_only_envelope["lifecycle_status"] == "draft"
    assert complete_inputs_envelope["manifest_creation"] is False
    assert event_only_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True
    assert mapper_package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert mapper_package["immutability"]["reason"] == "deferred_until_storage_gate"
    assert (
        event_only_envelope["mapper_package"]["package_status"]["status"]
        == "incomplete"
    )

    absent_authority_keys = (
        "manifest_schema_authority",
        "manifest_authority",
        "manifest_schema_implementation",
        "manifest_constants",
        "manifest_builder",
        "manifest_generation_authority",
        "deterministic_serialization",
        "canonical_serialization",
        "package_creation_authority",
        "storage_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "broker_authority",
        "finalized_immutable_replay_package_authority",
        "invalidated_package_authority",
        "superseded_package_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    for module in (draft_envelope, offline_mapper, package_schema):
        module_names = set(module.__dict__)
        for forbidden_name in FORBIDDEN_MANIFEST_SCHEMA_NAMES:
            assert forbidden_name not in module_names
        for value in module.__dict__.values():
            if isinstance(value, FunctionType):
                assert set(FORBIDDEN_MANIFEST_SCHEMA_NAMES).isdisjoint(
                    value.__code__.co_names
                )

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_MANIFEST_SCHEMA_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_manifest_schema_vocabulary_types_are_in_memory_only() -> None:
    assert manifest_schema.MANIFEST_SCHEMA_VERSION == "0.1-vocabulary"
    assert manifest_schema.MANIFEST_SCHEMA == "manifest_schema_vocabulary_only"
    assert "canonical_run_id" in manifest_schema.MANIFEST_REQUIRED_FIELDS
    assert "section_provenance" in manifest_schema.MANIFEST_REQUIRED_FIELDS
    assert "section_redaction_status" in manifest_schema.MANIFEST_REQUIRED_FIELDS
    assert "package_id" in manifest_schema.MANIFEST_OPTIONAL_FIELDS
    assert "generator_authority_boundary" in manifest_schema.MANIFEST_OPTIONAL_FIELDS
    assert "finalized_at" in manifest_schema.MANIFEST_FUTURE_ONLY_FIELDS
    assert "manifest_hash" in manifest_schema.MANIFEST_FUTURE_ONLY_FIELDS
    assert "live_trading_authority" in manifest_schema.MANIFEST_FUTURE_ONLY_FIELDS
    assert set(manifest_schema.MANIFEST_REQUIRED_FIELDS).isdisjoint(
        manifest_schema.MANIFEST_OPTIONAL_FIELDS
    )
    assert set(manifest_schema.MANIFEST_REQUIRED_FIELDS).isdisjoint(
        manifest_schema.MANIFEST_FUTURE_ONLY_FIELDS
    )
    assert set(manifest_schema.MANIFEST_OPTIONAL_FIELDS).isdisjoint(
        manifest_schema.MANIFEST_FUTURE_ONLY_FIELDS
    )
    assert manifest_schema.MANIFEST_LIFECYCLE_STATUS == ("draft",)
    assert manifest_schema.MANIFEST_FUTURE_LIFECYCLE_STATUS == (
        "finalized",
        "invalidated",
        "superseded",
    )
    assert set(manifest_schema.MANIFEST_SECTION_STATUS) == {
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
    }
    assert "absent" in manifest_schema.MANIFEST_SECTION_STATUS
    assert "not_applicable" in manifest_schema.MANIFEST_SECTION_STATUS
    assert "broker_api_authority" in manifest_schema.MANIFEST_AUTHORITY_BOUNDARY
    assert "execution_permission" in manifest_schema.MANIFEST_AUTHORITY_BOUNDARY
    assert "live_trading_authority" in manifest_schema.MANIFEST_AUTHORITY_BOUNDARY

    schema = manifest_schema.ManifestSchema()
    field = manifest_schema.ManifestField(name="canonical_run_id", required=True)
    section_status = manifest_schema.ManifestSectionStatus()

    assert schema.schema_version == manifest_schema.MANIFEST_SCHEMA_VERSION
    assert schema.required_fields == manifest_schema.MANIFEST_REQUIRED_FIELDS
    assert schema.optional_fields == manifest_schema.MANIFEST_OPTIONAL_FIELDS
    assert schema.future_only_fields == manifest_schema.MANIFEST_FUTURE_ONLY_FIELDS
    assert schema.lifecycle_statuses == ("draft",)
    assert field.name == "canonical_run_id"
    assert field.required is True
    assert field.future_only is False
    assert section_status.values == manifest_schema.MANIFEST_SECTION_STATUS

    module_names = set(manifest_schema.__dict__)
    for allowed_name in FUTURE_MANIFEST_SCHEMA_SCOPE_RELAXABLE_NAMES:
        assert allowed_name in module_names
    for downstream_name in MANIFEST_SCHEMA_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_names


def test_manifest_schema_implementation_scope_guard_remains_test_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Unit 1: Manifest Schema Vocabulary/Types" in map_text
    assert "first eventual code candidate only after this map" in map_text
    assert "is recorded and guarded" in map_text
    assert "pure in-memory vocabulary/types only" in map_text
    assert "Filesystem access allowed: no." in map_text
    assert "Runtime artifact access allowed: no." in map_text
    assert "Broker/API access allowed: no." in map_text
    assert "Execution/live trading authority allowed: no." in map_text
    assert "no manifest generation, package creation, serialization" in map_text
    assert "hashing,\n  storage, runtime capture, evaluation, promotion" in map_text
    assert "## Manifest Schema Authority Contract" in spec_text
    assert "Manifest schema authority remains governance-only" in spec_text
    assert "must remain separate from manifest generation" in spec_text
    assert "must also\nremain separate from mapper completeness" in spec_text
    assert "cannot\nbe treated as complete replay package authority" in spec_text

    assert set(FUTURE_MANIFEST_SCHEMA_SCOPE_RELAXABLE_NAMES).issubset(
        FORBIDDEN_MANIFEST_SCHEMA_IMPLEMENTATION_NAMES
    )
    assert set(FUTURE_MANIFEST_SCHEMA_SCOPE_RELAXABLE_NAMES).isdisjoint(
        MANIFEST_SCHEMA_SCOPE_DOWNSTREAM_DENIED_NAMES
    )

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "manifest_generation_authority",
        "deterministic_serialization_authority",
        "canonical_byte_generation",
        "hash_computation_authority",
        "integrity_validation_authority",
        "package_layout_authority",
        "package_identity_authority",
        "package_creation_authority",
        "filesystem_read_authority",
        "filesystem_write_authority",
        "storage_finalization_authority",
        "runtime_artifact_access_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "broker_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for downstream_name in MANIFEST_SCHEMA_SCOPE_DOWNSTREAM_DENIED_NAMES:
            assert downstream_name not in module_text

    module_text = MANIFEST_SCHEMA_MODULE.read_text(encoding="utf-8")
    for downstream_name in MANIFEST_SCHEMA_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_text


def test_deterministic_serialization_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Deterministic Serialization Authority Contract" in spec_text
    assert "governance-only and is not\nimplemented yet" in spec_text
    assert "does not approve tests, code, serializer" in spec_text
    assert "Serializer\ninput eligibility must be explicitly governed" in spec_text
    assert "Canonical JSON scope" in spec_text
    assert "Event JSONL chronology" in spec_text
    assert "String encoding must be UTF-8" in spec_text
    assert "`null`, absent fields, and `not_applicable`" in spec_text
    assert "`stale`, `malformed`, `untrusted`, and `invalidated`" in spec_text
    assert "Timestamp precision must be explicit" in spec_text
    assert "Unsupported value types must fail closed" in spec_text
    assert "cannot authorize manifest authority" in spec_text

    for module_path in FUTURE_DETERMINISTIC_SERIALIZATION_MODULES:
        assert not module_path.exists()
    assert CANONICAL_JSON_MODULE.exists()
    assert CANONICAL_BYTES_MODULE.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["canonical_chronology"] == "event_jsonl"
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True
    assert mapper_package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert mapper_package["immutability"]["reason"] == "deferred_until_storage_gate"

    absent_authority_keys = (
        "deterministic_serialization_authority",
        "canonical_serialization_authority",
        "canonical_byte_generation",
        "canonical_json",
        "canonical_bytes",
        "canonical_serializer",
        "serializer_constants",
        "serialization_types",
        "serializer_input",
        "serializer_output",
        "manifest_serialization_authority",
        "package_serialization_authority",
        "serialize_manifest",
        "serialize_package",
        "manifest_hash_authority",
        "package_hash_authority",
        "integrity_validation_authority",
        "storage_finalization_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    for module in (draft_envelope, offline_mapper, package_schema):
        module_names = set(module.__dict__)
        for forbidden_name in FORBIDDEN_SERIALIZATION_NAMES:
            assert forbidden_name not in module_names
        for value in module.__dict__.values():
            if isinstance(value, FunctionType):
                assert set(FORBIDDEN_SERIALIZATION_NAMES).isdisjoint(
                    value.__code__.co_names
                )

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_SERIALIZATION_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_deterministic_serialization_scope_guard_remains_test_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Unit 2: Deterministic Serialization And Canonical Bytes" in map_text
    assert "manifest vocabulary and serializer\n  input model are stable" in map_text
    assert "canonical ordering, chronology preservation" in map_text
    assert "unsupported type\n  fail-closed behavior" in map_text
    assert "Filesystem access allowed: no." in map_text
    assert "Runtime artifact access allowed: no." in map_text
    assert "Broker/API access allowed: no." in map_text
    assert "Execution/live trading authority allowed: no." in map_text

    assert "## Deterministic Serialization Authority Contract" in spec_text
    assert "Serializer\ninput eligibility must be explicitly governed" in spec_text
    assert "Canonical JSON scope" in spec_text
    assert "manifest-shaped\n  dictionary" in spec_text
    assert "Object keys must use deterministic canonical ordering" in spec_text
    assert "Recursive object ordering" in spec_text
    assert "chronology-preserving lists" in spec_text
    assert "must not be\n  accidentally sorted" in spec_text
    assert "Unsupported value types must fail closed" in spec_text
    assert "Ambiguous floats must fail closed" in spec_text
    assert "Ambiguous, missing, non-UTC, or unsupported timestamp" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Sensitive or redacted fields must not leak" in spec_text
    assert "does not\n  approve hashing" in spec_text

    assert set(FUTURE_SERIALIZATION_SCOPE_RELAXABLE_NAMES).issubset(
        FORBIDDEN_SERIALIZATION_IMPLEMENTATION_NAMES
    )
    assert set(FUTURE_SERIALIZATION_SCOPE_RELAXABLE_NAMES).isdisjoint(
        SERIALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES
    )

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["canonical_chronology"] == "event_jsonl"
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "manifest_generation_authority",
        "manifest_serialization_authority",
        "package_serialization_authority",
        "canonical_byte_generation",
        "hash_computation_authority",
        "integrity_validation_authority",
        "package_layout_authority",
        "package_identity_authority",
        "package_creation_authority",
        "filesystem_read_authority",
        "filesystem_write_authority",
        "storage_finalization_authority",
        "runtime_artifact_access_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "broker_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    guarded_source_modules = (*REPLAY_SOURCE_MODULES, MANIFEST_SCHEMA_MODULE)
    for module_path in guarded_source_modules:
        module_text = module_path.read_text(encoding="utf-8")
        for downstream_name in SERIALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            assert downstream_name not in module_text


def test_canonical_json_text_helper_is_deterministic_and_in_memory_only() -> None:
    left = {
        "z": "last",
        "nested": {"b": 2, "a": 1},
        "events": [{"seq": 2}, {"seq": 1}],
        "text": "München",
        "flag": True,
        "missing": None,
    }
    right = {
        "text": "München",
        "missing": None,
        "events": [{"seq": 2}, {"seq": 1}],
        "nested": {"a": 1, "b": 2},
        "flag": True,
        "z": "last",
    }

    canonical_text = canonical_json.canonicalize_json(left)

    assert canonical_text == canonical_json.canonicalize_json(right)
    assert canonical_text == (
        '{"events":[{"seq":2},{"seq":1}],"flag":true,"missing":null,'
        '"nested":{"a":1,"b":2},"text":"München","z":"last"}'
    )
    assert " " not in canonical_text
    assert "\n" not in canonical_text
    assert '[{"seq":2},{"seq":1}]' in canonical_text
    assert "\\u00" not in canonical_text

    schema = canonical_json.SerializationSchema()
    version = canonical_json.SerializationVersion()
    formatter = canonical_json.CanonicalJson()
    serializer = canonical_json.CanonicalSerializer()
    output = canonical_json.SerializationOutput(text=canonical_text)
    input_model = canonical_json.SerializationInput(value=left)

    assert schema.version == canonical_json.SERIALIZATION_VERSION
    assert schema.output_model == "canonical_json_text"
    assert version.value == canonical_json.SERIALIZATION_VERSION
    assert formatter.format_name == "json"
    assert serializer.name == "canonicalize_json"
    assert output.text == canonical_text
    assert input_model.value is left


def test_canonical_json_fails_closed_for_unsupported_or_ambiguous_values() -> None:
    unsupported_values = (
        {"float": 1.25},
        {"object": object()},
        {1: "non_string_key"},
        {"tuple": (1, 2)},
    )

    for value in unsupported_values:
        try:
            canonical_json.canonicalize_json(value)
        except TypeError:
            pass
        else:
            raise AssertionError(f"expected TypeError for {value!r}")


def test_canonical_json_does_not_introduce_downstream_authority() -> None:
    module_names = set(canonical_json.__dict__)
    for allowed_name in CANONICAL_JSON_IMPLEMENTED_NAMES:
        assert allowed_name in module_names
    for downstream_name in SERIALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_names
    assert "CANONICAL_BYTES" not in module_names
    assert "CanonicalBytes" not in module_names

    module_text = CANONICAL_JSON_MODULE.read_text(encoding="utf-8")
    for downstream_name in SERIALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_text
    for forbidden_name in (
        "CANONICAL_BYTES",
        "canonical_bytes",
        "encode",
        "hashlib",
        "open(",
        "write_text",
        "write_bytes",
        "mkdir",
        "Path(",
        "main.py",
        "broker",
        "alpaca",
        "ibkr",
    ):
        assert forbidden_name not in module_text

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True


def test_canonical_bytes_scope_guard_remains_test_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Unit 2: Deterministic Serialization And Canonical Bytes" in map_text
    assert "Candidate files: future `tools/replay/canonical_json.py`" in map_text
    assert "`tools/replay/canonical_bytes.py`" in map_text
    assert "no manifest generation, package creation, hash" in map_text
    assert "Filesystem access allowed: no." in map_text
    assert "Runtime artifact access allowed: no." in map_text
    assert "Broker/API access allowed: no." in map_text
    assert "Execution/live trading authority allowed: no." in map_text

    assert "Required future byte and text rules" in spec_text
    assert "String encoding must be UTF-8" in spec_text
    assert "Serialization must produce stable bytes" in spec_text
    assert "Serialization may be a prerequisite for hashing" in spec_text
    assert "this contract does not\n  approve hashing" in spec_text
    assert "Future hashing may use only canonical serialized bytes" in spec_text

    assert CANONICAL_BYTES_SCOPE_INPUT_MODEL == "canonical_json_text_only"
    assert CANONICAL_BYTES_SCOPE_ENCODING == "utf-8"
    assert set(FUTURE_CANONICAL_BYTES_SCOPE_RELAXABLE_NAMES).issubset(
        FORBIDDEN_SERIALIZATION_IMPLEMENTATION_NAMES
    )
    assert set(FUTURE_CANONICAL_BYTES_SCOPE_RELAXABLE_NAMES).isdisjoint(
        CANONICAL_BYTES_SCOPE_DOWNSTREAM_DENIED_NAMES
    )
    assert "generate_canonical_bytes" not in FUTURE_CANONICAL_BYTES_SCOPE_RELAXABLE_NAMES
    assert CANONICAL_BYTES_MODULE.exists()

    module_text = CANONICAL_JSON_MODULE.read_text(encoding="utf-8")
    for downstream_name in CANONICAL_BYTES_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_text
    assert "CANONICAL_BYTES" not in module_text
    assert "CanonicalBytes" not in module_text
    assert "build_canonical_bytes" not in module_text
    assert "validate_canonical_bytes" not in module_text

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["canonical_chronology"] == "event_jsonl"
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "canonical_byte_generation",
        "manifest_serialization_authority",
        "package_serialization_authority",
        "hash_computation_authority",
        "integrity_validation_authority",
        "package_layout_authority",
        "package_identity_authority",
        "package_creation_authority",
        "filesystem_read_authority",
        "filesystem_write_authority",
        "storage_finalization_authority",
        "runtime_artifact_access_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "broker_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package


def test_canonical_bytes_helper_encodes_canonical_json_text_only() -> None:
    canonical_text = canonical_json.canonicalize_json(
        {"text": "München", "events": [{"seq": 2}, {"seq": 1}]}
    )
    canonical_output = canonical_bytes.build_canonical_bytes(canonical_text)
    vocabulary = canonical_bytes.CanonicalBytes()

    assert isinstance(canonical_output, bytes)
    assert canonical_output == canonical_text.encode("utf-8")
    assert canonical_output.decode("utf-8") == canonical_text
    assert vocabulary.input_model == "canonical_json_text"
    assert vocabulary.output_model == "canonical_json_utf8_bytes"
    assert vocabulary.encoding == "utf-8"
    assert canonical_bytes.CANONICAL_BYTES == "utf8_canonical_json_bytes"
    assert canonical_bytes.CANONICAL_BYTES_ENCODING == "utf-8"


def test_canonical_bytes_fails_closed_for_non_string_input() -> None:
    non_string_inputs = (
        {"already": "object"},
        ["already", "array"],
        b'{"already":"bytes"}',
        123,
        None,
    )

    for value in non_string_inputs:
        try:
            canonical_bytes.build_canonical_bytes(value)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError(f"expected TypeError for {value!r}")


def test_canonical_bytes_does_not_introduce_downstream_authority() -> None:
    module_names = set(canonical_bytes.__dict__)
    for allowed_name in FUTURE_CANONICAL_BYTES_SCOPE_RELAXABLE_NAMES:
        assert allowed_name in module_names
    for downstream_name in CANONICAL_BYTES_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_names

    module_text = CANONICAL_BYTES_MODULE.read_text(encoding="utf-8")
    for downstream_name in CANONICAL_BYTES_SCOPE_DOWNSTREAM_DENIED_NAMES:
        assert downstream_name not in module_text
    for forbidden_name in (
        "json.dumps",
        "canonicalize_json",
        "hashlib",
        "open(",
        "write_text",
        "write_bytes",
        "mkdir",
        "Path(",
        "main.py",
        "broker",
        "alpaca",
        "ibkr",
    ):
        assert forbidden_name not in module_text

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True


def test_hashing_integrity_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Hashing and Integrity Authority Contract" in spec_text
    assert "governance-only and is not implemented" in spec_text
    assert "does not approve tests, code, hash constants" in spec_text
    assert "Hash algorithm\nand hash version authority" in spec_text
    assert "approved canonical byte input" in spec_text
    assert "Canonical byte input depends\non deterministic serialization authority" in spec_text
    assert "Manifest hash scope depends on\nmanifest schema authority" in spec_text
    assert "Placeholder hash fields must not imply computed hash authority" in spec_text
    assert "Section hash scope must define" in spec_text
    assert "Manifest hash scope must define" in spec_text
    assert "Package hash scope must define" in spec_text
    assert "integrity status vocabulary" in spec_text
    assert "Hash mismatch must fail closed" in spec_text
    assert "Mixed-`run_id` hash inputs must fail closed" in spec_text
    assert "Unknown source references must fail closed" in spec_text
    assert "Correction, invalidation, and supersession lineage" in spec_text
    assert "cannot authorize replay package creation" in spec_text

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["integrity"]["status"] == "absent"
    assert mapper_package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert mapper_package["immutability"]["status"] == "absent"
    assert mapper_package["immutability"]["reason"] == "deferred_until_storage_gate"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "hash_algorithm",
        "hash_version",
        "section_hash",
        "manifest_hash",
        "package_hash",
        "canonical_hash_input",
        "hash_computation_authority",
        "canonical_byte_authority",
        "canonical_byte_generation",
        "manifest_serialization_authority",
        "package_serialization_authority",
        "hash_authority",
        "integrity_authority",
        "manifest_hash_authority",
        "package_hash_authority",
        "integrity_validation_authority",
        "integrity_validator",
        "storage_finalization_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_HASHING_INTEGRITY_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_hashing_integrity_scope_guard_records_unit3_vocabulary_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 3: Hash Algorithm/Version And Integrity Status Vocabulary" in (
        map_text
    )
    assert "blocked until canonical byte authority exists" in map_text
    assert "`tools/replay/hashing.py`" in map_text
    assert "`tools/replay/integrity.py`" in map_text
    assert "no hash computation if the scope is vocabulary only" in map_text
    assert "no integrity validation, no package creation, no storage" in map_text
    assert "placeholder hash fields cannot imply computed hash" in map_text

    assert CANONICAL_BYTES_MODULE.exists()
    assert "Hash algorithm\nand hash version authority" in spec_text
    assert "integrity status vocabulary" in spec_text
    assert "Hashing depends on approved canonical byte input" in spec_text
    assert "Hash output must not create package completeness" in spec_text
    assert "Required future integrity status vocabulary" in spec_text

    assert FUTURE_HASHING_INTEGRITY_SCOPE_RELAXABLE_NAMES == (
        "HASH_ALGORITHM",
        "HASH_VERSION",
        "INTEGRITY_STATUS",
        "HashAlgorithm",
        "HashVersion",
        "IntegrityStatus",
    )
    assert not (
        set(FUTURE_HASHING_INTEGRITY_SCOPE_RELAXABLE_NAMES)
        & set(HASHING_INTEGRITY_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    for future_module in FUTURE_HASHING_INTEGRITY_MODULES:
        assert future_module.exists()

    assert hashing.HASH_ALGORITHM == "sha256"
    assert hashing.HASH_VERSION == "v1"
    assert hashing.HashAlgorithm().name == hashing.HASH_ALGORITHM
    assert hashing.HashVersion().value == hashing.HASH_VERSION
    assert integrity.INTEGRITY_STATUS == (
        "missing",
        "present",
        "unavailable",
        "not_validated",
    )
    assert integrity.IntegrityStatus().values == integrity.INTEGRITY_STATUS

    module_names = set(hashing.__dict__) | set(integrity.__dict__)
    for relaxable_name in FUTURE_HASHING_INTEGRITY_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names

    for denied_name in (
        "compute_hash",
        "calculate_hash",
        "build_hash",
        "build_section_hash",
        "build_manifest_hash",
        "build_package_hash",
        "validate_hash",
        "validate_integrity",
        "verify_integrity",
        "hashlib",
        "SECTION_HASH",
        "sha256",
        "ManifestSerialization",
        "PackageLayout",
        "ReplayPackageCreation",
        "StorageFinalization",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        if denied_name != "sha256":
            assert denied_name in HASHING_INTEGRITY_SCOPE_DOWNSTREAM_DENIED_NAMES
            assert denied_name not in FUTURE_HASHING_INTEGRITY_SCOPE_RELAXABLE_NAMES
        assert denied_name not in module_names

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["integrity"]["status"] == "absent"
    assert mapper_package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in HASHING_INTEGRITY_SCOPE_DOWNSTREAM_DENIED_NAMES:
            assert denied_name not in module_text

    for module_path in FUTURE_HASHING_INTEGRITY_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        assert "hashlib" not in module_text
        assert "sha256(" not in module_text
        for denied_name in HASHING_INTEGRITY_SCOPE_DOWNSTREAM_DENIED_NAMES:
            assert denied_name not in module_text


def test_package_identity_layout_scope_guard_records_unit4_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 4: Package Identity And Package Layout Rules" in map_text
    assert "blocked until manifest vocabulary and section\n  status semantics" in (
        map_text
    )
    assert "`tools/replay/package_layout.py`" in map_text
    assert "package-identity tests" in map_text
    assert "no package directories, filesystem writes" in map_text
    assert "no directories or packages are created" in map_text
    assert "layout rules are not package creation authority" in map_text

    assert "Package layout authority must be explicitly governed" in spec_text
    assert "Package identity authority must be explicitly governed" in spec_text
    assert "`canonical_run_id` and governed `package_id` rules" in spec_text
    assert "Ambiguous package identity must fail closed" in spec_text

    assert FUTURE_PACKAGE_IDENTITY_LAYOUT_SCOPE_RELAXABLE_NAMES == (
        "PACKAGE_IDENTITY",
        "PACKAGE_LAYOUT",
        "PACKAGE_ID",
        "CANONICAL_RUN_ID",
        "PackageIdentity",
        "PackageLayout",
        "PackageId",
        "CanonicalRunId",
    )
    assert not (
        set(FUTURE_PACKAGE_IDENTITY_LAYOUT_SCOPE_RELAXABLE_NAMES)
        & set(PACKAGE_IDENTITY_LAYOUT_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    for future_module in FUTURE_PACKAGE_IDENTITY_LAYOUT_MODULES:
        assert future_module.exists()

    assert package_layout.PACKAGE_IDENTITY == "package_identity_vocabulary_only"
    assert package_layout.PACKAGE_LAYOUT == "package_layout_vocabulary_only"
    assert package_layout.PACKAGE_ID == "package_id"
    assert package_layout.CANONICAL_RUN_ID == "canonical_run_id"
    assert package_layout.PACKAGE_IDENTITY_FIELDS == (
        package_layout.CANONICAL_RUN_ID,
        package_layout.PACKAGE_ID,
    )
    assert package_layout.PACKAGE_LAYOUT_SECTIONS == (
        "package_identity",
        "manifest",
        "source_artifact_references",
        "integrity",
        "authority_boundary",
    )
    assert package_layout.PackageId().field_name == package_layout.PACKAGE_ID
    assert (
        package_layout.CanonicalRunId().field_name
        == package_layout.CANONICAL_RUN_ID
    )
    assert package_layout.PackageIdentity().fields == (
        package_layout.CANONICAL_RUN_ID,
        package_layout.PACKAGE_ID,
    )
    assert (
        package_layout.PackageLayout().sections
        == package_layout.PACKAGE_LAYOUT_SECTIONS
    )
    assert "no_package_creation" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_filesystem_access" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_manifest_generation" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_hash_computation" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_integrity_validation" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_storage_finalization" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_runtime_capture" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_broker_authority" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY
    assert "no_execution_authority" in package_layout.PACKAGE_LAYOUT_AUTHORITY_BOUNDARY

    module_names = set(package_layout.__dict__)
    for relaxable_name in FUTURE_PACKAGE_IDENTITY_LAYOUT_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names

    for denied_name in (
        "PACKAGE_CREATION",
        "PACKAGE_DIRECTORY",
        "PACKAGE_PATH",
        "ManifestGeneration",
        "create_replay_package",
        "create_package_directory",
        "write_package",
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "hashlib",
        "compute_hash",
        "validate_integrity",
        "StorageFinalization",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name in PACKAGE_IDENTITY_LAYOUT_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FUTURE_PACKAGE_IDENTITY_LAYOUT_SCOPE_RELAXABLE_NAMES

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["file_path_ingestion"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in PACKAGE_IDENTITY_LAYOUT_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text

    for module_path in FUTURE_PACKAGE_IDENTITY_LAYOUT_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        assert "hashlib" not in module_text
        for denied_name in PACKAGE_IDENTITY_LAYOUT_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text


def test_manifest_generation_scope_guard_records_unit5_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 5: Manifest Generation" in map_text
    assert "Prerequisite dependencies: manifest schema vocabulary/types" in map_text
    assert "package identity\n  rules" in map_text
    assert "section status semantics, provenance/redaction fields" in map_text
    assert "`tools/replay/manifest_builder.py`" in map_text
    assert "manifest-generation tests" in map_text
    assert "in-memory manifest object generation" in map_text
    assert "required/optional field\n  handling" in map_text
    assert "fail-closed malformed inputs" in map_text
    assert "missing provenance/redaction\n  status" in map_text
    assert "mixed run_id" in map_text
    assert "unknown source references" in map_text
    assert "need to write files" in map_text
    assert "manifest output is not package creation" in map_text
    assert "Filesystem access allowed: no." in map_text
    assert "Runtime artifact access allowed: no." in map_text
    assert "Broker/API access allowed: no." in map_text
    assert "Execution/live trading authority allowed: no." in map_text

    assert "Future manifest inputs require manifest generation authority" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Unknown source references must fail closed" in spec_text
    assert "Mixed `run_id` must fail closed" in spec_text
    assert "Need filesystem reads or writes" in spec_text
    assert "Implied manifest generation authority" in spec_text

    assert FUTURE_MANIFEST_GENERATION_SCOPE_RELAXABLE_NAMES == (
        "MANIFEST_GENERATION",
        "MANIFEST_BUILDER",
        "DRAFT_MANIFEST",
        "MANIFEST_INPUT",
        "MANIFEST_FIELD_ELIGIBILITY",
        "MANIFEST_PROVENANCE_ELIGIBILITY",
        "MANIFEST_REDACTION_ELIGIBILITY",
        "MANIFEST_RUN_ID_ALIGNMENT",
        "MANIFEST_SOURCE_REFERENCE_ELIGIBILITY",
        "ManifestGeneration",
        "ManifestBuilder",
        "DraftManifest",
        "ManifestInput",
        "ManifestFieldEligibility",
        "ManifestProvenanceEligibility",
        "ManifestRedactionEligibility",
        "ManifestRunIdAlignment",
        "ManifestSourceReferenceEligibility",
        "build_draft_manifest",
        "build_in_memory_manifest",
    )
    assert not (
        set(FUTURE_MANIFEST_GENERATION_SCOPE_RELAXABLE_NAMES)
        & set(MANIFEST_GENERATION_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    for future_module in FUTURE_MANIFEST_GENERATION_MODULES:
        assert not future_module.exists()

    for denied_name in (
        "PACKAGE_CREATION",
        "PACKAGE_DIRECTORY",
        "ReplayPackageCreation",
        "generate_manifest",
        "create_manifest",
        "write_manifest",
        "serialize_manifest",
        "package_manifest",
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "hashlib",
        "compute_hash",
        "build_manifest_hash",
        "validate_integrity",
        "StorageFinalization",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name in MANIFEST_GENERATION_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FUTURE_MANIFEST_GENERATION_SCOPE_RELAXABLE_NAMES

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in MANIFEST_GENERATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text


def test_storage_immutability_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert (
        "## Storage, Finalization, and Immutability Authority Contract"
        in spec_text
    )
    assert "governance-only and\nis not implemented yet" in spec_text
    assert "does not approve tests, code, storage\nconstants" in spec_text
    assert "filesystem reads, filesystem\nwrites" in spec_text
    assert "Storage rules must be source-controlled before implementation" in spec_text
    assert "Storage root authority must be explicitly governed" in spec_text
    assert "Package path authority must be explicitly governed" in spec_text
    assert "Package directory naming authority must be explicitly governed" in spec_text
    assert "`canonical_run_id` and `package_id` naming rules" in spec_text
    assert "Package layout authority must exist before storage paths" in spec_text
    assert "Package creation authority must exist before finalized package storage" in spec_text
    assert "Manifest schema authority must exist before finalized package metadata" in spec_text
    assert "Deterministic serialization authority must exist before storage" in spec_text
    assert "Hashing and integrity validation must exist before finalization" in spec_text
    assert "Finalization preconditions must be explicit" in spec_text
    assert "Minimum future lifecycle states are `draft`, `finalized`, `invalidated`" in spec_text
    assert "Finalized evidence must be immutable and no-overwrite" in spec_text
    assert "Invalidated and superseded packages must remain discoverable" in spec_text
    assert "append-only and lineage-preserving" in spec_text
    assert "Retention authority remains future-only" in spec_text
    assert "Discovery authority remains future-only" in spec_text
    assert "Index authority remains future-only" in spec_text
    assert "Immutable evidence must remain distinct from derived reports" in spec_text
    assert "Provenance must be explicit before storage" in spec_text
    assert "Source-reference authority must be explicit before storage" in spec_text
    assert "`run_id` alignment must be explicit before storage" in spec_text
    assert "Mixed-`run_id` storage inputs must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Invalid redaction status must fail closed" in spec_text
    assert "Sensitive data exposure must stop storage" in spec_text
    assert "Attempted overwrite of finalized evidence must fail closed" in spec_text
    assert "cannot authorize manifest authority" in spec_text
    assert "replay package creation, package authority, package\ncompleteness" in spec_text

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["file_path_ingestion"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["immutability"]["status"] == "absent"
    assert mapper_package["immutability"]["reason"] == "deferred_until_storage_gate"
    assert mapper_package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "storage_root",
        "storage_path",
        "storage_constants",
        "package_root",
        "package_dir",
        "package_directory",
        "package_path",
        "package_layout",
        "finalization_state",
        "finalized_package",
        "immutability_marker",
        "immutability_enforcement",
        "immutable_package",
        "retention_index",
        "discovery_index",
        "storage_index",
        "storage_authority",
        "finalization_authority",
        "immutability_authority",
        "retention_authority",
        "discovery_authority",
        "index_authority",
        "package_creation_authority",
        "package_completeness_authority",
        "runtime_capture_authority",
        "evaluation_authority",
        "promotion_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_STORAGE_IMMUTABILITY_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_runtime_capture_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Runtime Capture Authority Contract" in spec_text
    assert "governance-only and is not implemented yet" in spec_text
    assert "does not approve tests, code, runtime capture constants" in spec_text
    assert "source artifact discovery, source path\ningestion" in spec_text
    assert "artifact copying, filesystem reads, filesystem writes" in spec_text
    assert "Runtime capture rules must be source-controlled" in spec_text
    assert "Already-loaded dictionaries and `ReplayInputBundle`" in spec_text
    assert "Path-like runtime artifact inputs remain forbidden" in spec_text
    assert "Source artifact authority must be explicitly governed" in spec_text
    assert "Source reference authority must be explicitly governed" in spec_text
    assert "Source path authority must be explicitly governed" in spec_text
    assert "Runtime artifact discovery authority must be explicitly governed" in spec_text
    assert "File path ingestion authority must be explicitly governed" in spec_text
    assert "Artifact copying authority must be explicitly governed" in spec_text
    assert "Eligible runtime artifact vocabulary must be explicitly governed" in spec_text
    assert "JSONL event streams remain canonical event chronology" in spec_text
    assert "Terminal completion event requirements must be explicit" in spec_text
    assert "`last_run_report.json` remains a derived operational summary" in spec_text
    assert "Observations remain separate append-only evidence" in spec_text
    assert "must be run-filtered\n  before future capture" in spec_text
    assert "Runtime visibility remains observed/readiness evidence only" in spec_text
    assert "Runtime capture inputs must have strict `run_id` alignment" in spec_text
    assert "Provenance must be explicit before runtime capture" in spec_text
    assert "Redaction status must be explicit before runtime capture" in spec_text
    assert "Missing `run_id` must fail closed" in spec_text
    assert "Mixed-`run_id` artifacts must fail closed" in spec_text
    assert "Stale artifacts must fail closed" in spec_text
    assert "Malformed artifacts must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Invalid redaction status must fail closed" in spec_text
    assert "Storage and finalization authority must exist before runtime capture" in spec_text
    assert "Package creation authority must exist before runtime capture" in spec_text
    assert "Runtime capture must remain separate from manifest generation" in spec_text
    assert "Runtime capture must remain separate from package creation" in spec_text
    assert "Runtime capture must remain separate from storage and finalization" in spec_text
    assert "Runtime capture must remain separate from evaluation and promotion" in spec_text
    assert "Runtime capture must not call `main.py`" in spec_text
    assert "Runtime capture must not stop or start timers" in spec_text
    assert "Runtime capture must not call broker/API/TWS/Alpaca/IBKR" in spec_text
    assert "must not respond to or remediate blocked buy/sell signals" in spec_text
    assert "Runtime capture cannot authorize manifest authority" in spec_text
    assert "replay package creation, package authority, package completeness" in spec_text

    for module_path in FUTURE_RUNTIME_CAPTURE_MODULES:
        assert not module_path.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["file_path_ingestion"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["manifest_creation"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert complete_inputs_envelope["canonical_chronology"] == "event_jsonl"
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "runtime_capture_authority",
        "runtime_capture_constants",
        "runtime_capture_types",
        "runtime_capture_module",
        "runtime_artifact_ingestion",
        "source_artifact_discovery",
        "source_path_ingestion",
        "file_path_ingestion_authority",
        "artifact_copying_authority",
        "artifact_discovery_authority",
        "source_artifact_authority",
        "source_reference_authority",
        "source_artifact_path",
        "runtime_artifact_path",
        "capture_manifest",
        "canonical_byte_generation_authority",
        "package_creation_authority",
        "package_completeness_authority",
        "storage_authority",
        "filesystem_read_authority",
        "filesystem_write_authority",
        "manifest_generation_authority",
        "deterministic_serialization_authority",
        "hashing_integrity_authority",
        "storage_finalization_authority",
        "evaluation_authority",
        "promotion_authority",
        "broker_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    try:
        build_draft_replay_envelope(RISK_BLOCKED_FIXTURE)  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == (
            "draft envelope scaffold accepts loaded replay inputs only"
        )
    else:
        raise AssertionError("expected TypeError")

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_RUNTIME_CAPTURE_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_evaluation_promotion_boundary_remains_unimplemented() -> None:
    architecture_text = EVALUATION_INFRASTRUCTURE_ARCHITECTURE.read_text(
        encoding="utf-8"
    )
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Evaluation and Promotion Authority Contract" in architecture_text
    assert "governance-only and is not\nimplemented yet" in architecture_text
    assert "does not approve tests, code, evaluation\nengines" in architecture_text
    assert "attribution logic, experiment registries, scoring metrics" in architecture_text
    assert "replay\npackage scoring" in architecture_text
    assert "backtest or replay runners" in architecture_text
    assert "strategy promotion gates" in architecture_text
    assert "Evaluation and promotion rules must be source-controlled" in architecture_text
    assert "Evaluation cannot consume evidence as authoritative" in architecture_text
    assert "Trusted scoring requires complete replay package authority" in architecture_text
    assert "Governance-grade evaluation requires finalized and immutable" in architecture_text
    assert "Draft or incomplete packages may support only exploratory" in architecture_text
    assert "Metric vocabulary must be governed before scoring" in architecture_text
    assert "Metric versioning must be governed before scoring" in architecture_text
    assert "Attribution vocabulary must be governed before attribution" in architecture_text
    assert "Attribution versioning must be governed before attribution" in architecture_text
    assert "Experiment identifiers must be governed before experiments" in architecture_text
    assert "Experiment registry authority must be governed before experiments" in architecture_text
    assert "Package-set inclusion and exclusion rules must be governed" in architecture_text
    assert "Reproducibility rules must be governed before evaluation" in architecture_text
    assert "Candidate strategy identity and versioning" in architecture_text
    assert "Candidate parameter identity and versioning" in architecture_text
    assert "Baseline versus candidate comparison rules" in architecture_text
    assert "As-of feature availability and decision-time evidence rules" in architecture_text
    assert "Incomplete, mutable, stale, untrusted, mixed-run, unhashable" in architecture_text
    assert "provenance-defective, redaction-defective" in architecture_text
    assert "Evaluation reports, metrics, comparisons, and recommendations" in architecture_text
    assert "must not create\n  promotion authority" in architecture_text
    assert "Evaluation output must remain separate from strategy promotion" in architecture_text
    assert "Strategy promotion must require a separate explicit promotion gate" in architecture_text
    assert "approval, monitoring, rollback, rejection" in architecture_text
    assert "Promotion output must not create broker authority" in architecture_text
    assert "AI recommendations, shadow outputs, paper validation, and metrics" in architecture_text
    assert "submit orders, cancel orders, flatten\n  positions" in architecture_text
    assert "Evaluation and promotion output cannot become runtime truth" in architecture_text
    assert "This docs contract does not approve\ntests, code, replay package scoring" in architecture_text
    assert "Replay package output does not authorize strategy evaluation" in spec_text
    assert "Replay-based promotion decisions" in spec_text

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["hashing_integrity_enforcement"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    absent_authority_keys = (
        "evaluation_authority",
        "promotion_authority",
        "scoring_authority",
        "attribution_authority",
        "experiment_registry_authority",
        "replay_package_scoring_authority",
        "backtest_runner_authority",
        "replay_runner_authority",
        "strategy_promotion_gate",
        "promotion_gate_authority",
        "package_set_authority",
        "metric_vocabulary_authority",
        "attribution_vocabulary_authority",
        "experiment_identifier_authority",
        "strategy_promotion_authority",
        "broker_authority",
        "execution_permission",
        "live_trading_authority",
    )
    for key in absent_authority_keys:
        assert key not in complete_inputs_envelope
        assert key not in mapper_package

    for module_path in REPLAY_SOURCE_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_EVALUATION_PROMOTION_IMPLEMENTATION_NAMES:
            assert forbidden_name not in module_text


def test_mapper_returns_documented_top_level_envelope_sections() -> None:
    package = build_replay_package(events=_event_payloads())

    assert tuple(package) == ENVELOPE_SECTIONS


def test_mapper_uses_in_memory_inputs_and_preserves_source_payload_shapes() -> None:
    inputs = _complete_replay_inputs()
    events = inputs["events"]
    run_report = inputs["run_report"]
    observations = inputs["observations"]
    order_state = inputs["order_state"]
    runtime_visibility = inputs["runtime_visibility"]

    package = build_replay_package(
        events=events,
        run_report=run_report,
        observations=observations,
        order_state=order_state,
        runtime_visibility=runtime_visibility,
    )

    assert package["package_status"]["status"] == "complete"
    assert package["run_identity"]["run_id"] == "run_1"
    assert package["event_order_references"]["events"] == events
    assert package["configuration_references"]["run_report"] == run_report
    assert package["reconciliation_risk_references"]["observations"] == observations
    assert (
        package["portfolio_risk_snapshot_references"]["order_state"]
        == order_state
    )
    assert (
        package["broker_visible_state_references"]["runtime_visibility"]
        == runtime_visibility
    )
    assert package["authority_boundary"] == AUTHORITY_BOUNDARY


def test_missing_sections_are_marked_absent_without_inventing_facts() -> None:
    package = build_replay_package(events=[])

    assert package["package_status"]["status"] == "incomplete"
    assert package["package_status"]["section_statuses"] == {
        "events": "absent",
        "run_report": "absent",
        "observations": "absent",
        "order_state": "absent",
        "runtime_visibility": "absent",
    }
    assert package["package_identity"] == {
        "status": "absent",
        "reason": "run_id_not_supplied",
    }
    assert package["event_order_references"] == {
        "status": "absent",
        "reason": "events_not_supplied",
    }
    assert package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert package["immutability"]["reason"] == "deferred_until_storage_gate"


def test_event_stream_replay_fixture_is_useful_but_not_complete_or_authoritative() -> None:
    events = _event_payloads()

    package = build_replay_package(events=events)

    assert package["package_status"]["status"] == "incomplete"
    assert package["package_status"]["section_statuses"] == {
        "events": "present",
        "run_report": "absent",
        "observations": "absent",
        "order_state": "absent",
        "runtime_visibility": "absent",
    }
    assert package["run_identity"]["run_id"] == "run_1"
    assert package["event_order_references"]["events"] == events
    assert package["authority_boundary"]["evidence_only"] is True
    assert package["authority_boundary"]["no_execution_authority"] is True
    assert package["authority_boundary"]["no_broker_authority"] is True
    assert package["authority_boundary"]["no_strategy_behavior_change"] is True
    assert package["out_of_scope"]["artifact_writer"] is True
    assert package["out_of_scope"]["runtime_capture"] is True
    assert package["out_of_scope"]["broker_live_api_work"] is True
    assert package["out_of_scope"]["replay_based_promotion_decisions"] is True


def test_mixed_event_run_ids_cannot_be_treated_as_complete_replay_package() -> None:
    inputs = _complete_replay_inputs()
    inputs["events"][1]["run_id"] = "run_2"

    package = build_replay_package(**inputs)

    assert package["package_status"]["status"] == "incomplete"
    assert package["run_identity"]["run_id"] == "run_1"


def test_run_report_run_id_mismatch_cannot_override_event_stream_identity() -> None:
    inputs = _complete_replay_inputs()
    inputs["run_report"]["run_id"] = "run_2"

    package = build_replay_package(**inputs)

    assert package["package_status"]["status"] == "incomplete"
    assert package["run_identity"]["run_id"] == "run_1"


def test_order_state_run_id_mismatch_cannot_be_treated_as_aligned() -> None:
    inputs = _complete_replay_inputs()
    inputs["order_state"]["run_id"] = "run_2"

    package = build_replay_package(**inputs)

    assert package["package_status"]["status"] == "incomplete"


def test_observation_run_id_mismatch_cannot_be_treated_as_aligned() -> None:
    inputs = _complete_replay_inputs()
    inputs["observations"][0]["run_id"] = "run_2"

    package = build_replay_package(**inputs)

    assert package["package_status"]["status"] == "incomplete"


def test_runtime_visibility_run_id_mismatch_cannot_be_treated_as_aligned() -> None:
    inputs = _complete_replay_inputs()
    inputs["runtime_visibility"]["run_id"] = "run_2"

    package = build_replay_package(**inputs)

    assert package["package_status"]["status"] == "incomplete"


def test_mapper_does_not_mutate_inputs_or_return_input_objects_by_identity() -> None:
    inputs = _complete_replay_inputs()
    events = inputs["events"]
    run_report = inputs["run_report"]
    observations = inputs["observations"]
    order_state = inputs["order_state"]
    runtime_visibility = inputs["runtime_visibility"]
    original_inputs = deepcopy(inputs)
    original = (
        repr(events),
        repr(run_report),
        repr(observations),
        repr(order_state),
        repr(runtime_visibility),
    )

    package = build_replay_package(
        events=events,
        run_report=run_report,
        observations=observations,
        order_state=order_state,
        runtime_visibility=runtime_visibility,
    )

    assert (
        repr(events),
        repr(run_report),
        repr(observations),
        repr(order_state),
        repr(runtime_visibility),
    ) == original
    assert inputs == original_inputs
    assert package["event_order_references"]["events"] is not events
    assert package["configuration_references"]["run_report"] is not run_report
    assert package["reconciliation_risk_references"]["observations"] is not observations
    assert package["portfolio_risk_snapshot_references"]["order_state"] is not order_state
    assert (
        package["broker_visible_state_references"]["runtime_visibility"]
        is not runtime_visibility
    )


def test_partial_candidate_artifact_shape_maps_to_incomplete_replay_package() -> None:
    run_id = "run_2026-05-26T13:45:27Z_efa92a"
    market_input_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0001",
        "event_type": "data",
        "stage": "market_input_captured",
        "timestamp_utc": "2026-05-26T13:45:28Z",
        "timestamp": "2026-05-26T13:45:28Z",
        "status": "ok",
        "payload": {
            "symbol": "AAPL",
            "timeframe": "5Min",
            "source": "alpaca",
            "adjustment": "raw",
            "adjusted": False,
            "warnings": [],
            "candles": [
                {
                    "timestamp": "2026-05-26T13:30:00+00:00",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.5,
                    "close": 100.4,
                    "volume": 1000.0,
                },
                {
                    "timestamp": "2026-05-26T13:35:00+00:00",
                    "open": 100.4,
                    "high": 101.4,
                    "low": 100.1,
                    "close": 100.9,
                    "volume": 1100.0,
                },
                {
                    "timestamp": "2026-05-26T13:40:00+00:00",
                    "open": 100.9,
                    "high": 101.8,
                    "low": 100.6,
                    "close": 101.5,
                    "volume": 1200.0,
                },
            ],
        },
    }
    strategy_evaluated_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0002",
        "event_type": "strategy",
        "stage": "strategy_evaluated",
        "timestamp_utc": "2026-05-26T13:45:29Z",
        "timestamp": "2026-05-26T13:45:29Z",
        "status": "ok",
        "payload": {
            "signal": "buy",
            "decision": "buy",
            "action": "buy",
            "reason": "percent_change_meets_buy_threshold",
            "previous_close": 100.9,
            "latest_close": 101.5,
            "price_delta": 0.6,
            "percent_change": 0.5946481665014867,
            "three_close_percent_change": 1.095617529880476,
        },
    }
    action_proposal_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0003",
        "event_type": "strategy",
        "stage": "action_proposal",
        "timestamp_utc": "2026-05-26T13:45:30Z",
        "timestamp": "2026-05-26T13:45:30Z",
        "status": "blocked",
        "payload": {
            "signal": "buy",
            "decision": "buy",
            "action": "buy",
            "reason": "strategy_hold",
        },
    }
    completion_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0004",
        "event_type": "system",
        "stage": "completion",
        "timestamp_utc": "2026-05-26T13:45:31Z",
        "timestamp": "2026-05-26T13:45:31Z",
        "status": "blocked",
        "payload": {"reason": "strategy_hold"},
    }
    events = [
        market_input_event,
        strategy_evaluated_event,
        action_proposal_event,
        completion_event,
    ]
    observations = [
        {
            "timestamp_utc": "2026-05-26T13:45:30Z",
            "run_id": run_id,
            "symbol": "AAPL",
            "signal": "buy",
            "action": "buy",
            "result": "blocked",
            "reason": "strategy_hold",
            "previous_close": 100.9,
            "latest_close": 101.5,
            "price_delta": 0.6,
            "percent_change": 0.5946481665014867,
            "three_close_percent_change": 1.095617529880476,
            "signal_timeframe": "5Min",
            "signal_limit": 5,
            "latest_candle_timestamp": "2026-05-26T13:40:00+00:00",
        }
    ]

    package = build_replay_package(events=events, observations=observations)

    assert package["package_status"]["status"] == "incomplete"
    assert package["package_status"]["section_statuses"] == {
        "events": "present",
        "run_report": "absent",
        "observations": "present",
        "order_state": "absent",
        "runtime_visibility": "absent",
    }
    assert package["event_order_references"]["events"] == events
    assert package["event_order_references"]["events"] is not events
    assert package["market_input_references"]["events"] == [market_input_event]
    assert package["market_input_references"]["events"][0] is not market_input_event
    assert package["strategy_decision_references"]["events"] == [
        strategy_evaluated_event,
        action_proposal_event,
    ]
    assert completion_event in package["event_order_references"]["events"]
    assert package["reconciliation_risk_references"]["observations"] == observations
    assert (
        package["reconciliation_risk_references"]["observations"]
        is not observations
    )
    assert package["configuration_references"] == {
        "status": "absent",
        "reason": "not_supplied",
    }
    assert package["portfolio_risk_snapshot_references"] == {
        "status": "absent",
        "reason": "portfolio_risk_reference_not_supplied",
    }
    assert package["broker_visible_state_references"] == {
        "status": "absent",
        "reason": "broker_visible_reference_not_supplied",
    }


def test_mapper_rejects_non_loaded_input_shapes() -> None:
    try:
        build_replay_package(events={"run_id": "run_1"})  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "events must be a list of dictionaries"
    else:
        raise AssertionError("expected TypeError")

    try:
        build_replay_package(events=str(EVIDENCE_CANDIDATE_DIR))  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "events must be a list of dictionaries"
    else:
        raise AssertionError("expected TypeError")

    try:
        build_replay_package(events=[], run_report=[])  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "optional replay inputs must be dictionaries"
    else:
        raise AssertionError("expected TypeError")


def test_committed_three_close_candidate_jsons_are_review_inputs_not_replay_packages() -> None:
    artifacts = _committed_candidate_artifacts()

    assert {artifact["artifact_type"] for artifact in artifacts} == {
        "review_input_not_test",
    }
    assert {artifact["schema"] for artifact in artifacts} == {
        "openclaw_3_close_evidence_candidates_v1",
    }

    for artifact in artifacts:
        assert "package_status" not in artifact
        assert "event_order_references" not in artifact
        assert "authority_boundary" not in artifact
        assert "out_of_scope" not in artifact
        assert artifact["candidates"]
        for candidate in artifact["candidates"]:
            assert candidate["reviewer_decision"] == "PENDING_REVIEW"
            assert candidate["review_status"] == "GENERATED_CANDIDATE_NOT_ACCEPTED"


def test_candidate_artifacts_cannot_be_promoted_to_complete_replay_packages() -> None:
    artifacts = _committed_candidate_artifacts()

    for artifact in artifacts:
        package = build_replay_package(
            events=artifact["candidates"],
            run_report=artifact,
        )

        assert package["package_status"]["status"] == "incomplete"
        assert package["package_status"]["section_statuses"] == {
            "events": "present",
            "run_report": "present",
            "observations": "absent",
            "order_state": "absent",
            "runtime_visibility": "absent",
        }
        assert package["market_input_references"] == {
            "status": "absent",
            "reason": "market_input_event_not_supplied",
        }
        assert package["portfolio_risk_snapshot_references"] == {
            "status": "present",
            "run_report": artifact,
            "order_state": None,
        }
        assert package["broker_visible_state_references"] == {
            "status": "present",
            "run_report": artifact,
            "runtime_visibility": None,
        }
        assert package["integrity"]["reason"] == "deferred_until_integrity_gate"
        assert package["immutability"]["reason"] == "deferred_until_storage_gate"
        assert package["authority_boundary"] == AUTHORITY_BOUNDARY
        assert package["out_of_scope"] == OUT_OF_SCOPE
        assert package["out_of_scope"]["artifact_writer"] is True
        assert package["out_of_scope"]["runtime_capture"] is True
        assert package["out_of_scope"]["storage"] is True
        assert package["out_of_scope"]["broker_live_api_work"] is True
        assert package["out_of_scope"]["replay_based_promotion_decisions"] is True


def test_import_isolation_and_no_side_effect_fragments() -> None:
    forbidden_modules = {
        "main",
        "config",
        "broker_factory",
        "broker_interface",
        "alpaca",
        "ibkr",
        "ib_insync",
        "event_logger",
        "observation_logger",
        "reporting",
        "state_manager",
        "runtime_visibility_preflight",
        "runtime_visibility_orchestrator",
        "runtime_visibility_provider_composer",
    }

    assert forbidden_modules.isdisjoint(sys.modules)
    for module in (package_schema, offline_mapper, draft_envelope):
        assert not any(hasattr(module, name) for name in forbidden_modules)

    forbidden_names = {
        "open",
        "Path",
        "environ",
        "getenv",
        "load_dotenv",
        "socket",
        "requests",
        "urllib",
        "subprocess",
        "append_observation",
        "persist_report",
        "log_event",
        "initialize_event_logger",
        "write_order_state",
        "write_run_report",
    }

    for module in (package_schema, offline_mapper, draft_envelope):
        for value in module.__dict__.values():
            if isinstance(value, FunctionType):
                assert forbidden_names.isdisjoint(value.__code__.co_names)
