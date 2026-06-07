from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType

import pytest

import tools.replay.draft_envelope as draft_envelope
import tools.replay.canonical_bytes as canonical_bytes
import tools.replay.canonical_json as canonical_json
import tools.replay.filesystem_storage_authority as filesystem_storage_authority
import tools.replay.hash_computation as hash_computation
import tools.replay.hashing as hashing
import tools.replay.integrity as integrity
import tools.replay.integrity_validation as integrity_validation
import tools.replay.manifest_builder as manifest_builder
import tools.replay.manifest_schema as manifest_schema
import tools.replay.offline_mapper as offline_mapper
import tools.replay.package_completeness as package_completeness
import tools.replay.package_creation as package_creation
import tools.replay.package_layout as package_layout
import tools.replay.package_schema as package_schema
import tools.replay.storage_implementation as storage_implementation
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
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "manifest_writer.py",
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "manifest_generator.py"
    ),
)
PACKAGE_CREATION_MODULE = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "package_creation.py"
)
FUTURE_PACKAGE_CREATION_SCOPE_RELAXABLE_NAMES = (
    "PACKAGE_CREATION",
    "PACKAGE_BUILDER_TYPES",
    "PACKAGE_CREATION_MODULE",
    "DRAFT_REPLAY_PACKAGE",
    "DRAFT_PACKAGE_ASSEMBLY",
    "PACKAGE_CREATION_INPUT",
    "PACKAGE_CREATION_RESULT",
    "PackageCreation",
    "PackageBuilder",
    "PackageBuilderInput",
    "PackageBuilderOutput",
    "DraftReplayPackage",
    "DraftPackageAssembly",
    "PackageCreationInput",
    "PackageCreationResult",
    "build_draft_package",
    "assemble_draft_package",
    "create_draft_package",
)
PACKAGE_CREATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "PACKAGE_COMPLETENESS",
    "COMPLETE_REPLAY_PACKAGE",
    "FINALIZED_PACKAGE",
    "STORAGE_ROOT",
    "STORAGE_PATH",
    "PACKAGE_DIRECTORY",
    "PACKAGE_PATH",
    "FILESYSTEM_READ",
    "FILESYSTEM_WRITE",
    "PackageCompleteness",
    "CompleteReplayPackage",
    "FinalizedPackage",
    "StorageRoot",
    "StoragePath",
    "PackageDirectory",
    "PackagePath",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
    "open",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
)
FUTURE_MANIFEST_SCHEMA_MODULES = (
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "manifest_constants.py"
    ),
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
FUTURE_HASH_COMPUTATION_MODULES = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "hash_computation.py",
)
FUTURE_HASH_COMPUTATION_SCOPE_RELAXABLE_NAMES = (
    "SECTION_HASH",
    "MANIFEST_HASH",
    "PACKAGE_HASH",
    "HASH_COMPUTATION",
    "HASH_INPUT_ELIGIBILITY",
    "HASH_SCOPE",
    "SECTION_HASH_SCOPE",
    "MANIFEST_HASH_SCOPE",
    "PACKAGE_HASH_SCOPE",
    "CANONICAL_HASH_INPUT",
    "HashComputation",
    "HashInputEligibility",
    "HashScope",
    "SectionHash",
    "ManifestHash",
    "PackageHash",
    "SectionHashScope",
    "ManifestHashScope",
    "PackageHashScope",
    "CanonicalHashInput",
    "build_section_hash",
    "build_manifest_hash",
    "build_package_hash",
)
HASH_COMPUTATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "INTEGRITY_VALIDATION",
    "PACKAGE_COMPLETENESS",
    "PACKAGE_CREATION",
    "PACKAGE_DIRECTORY",
    "PACKAGE_PATH",
    "IntegrityValidation",
    "IntegrityValidator",
    "PackageCompleteness",
    "PackageCreation",
    "PackageDirectory",
    "PackagePath",
    "ReplayPackageCreation",
    "CompleteReplayPackage",
    "validate_hash",
    "validate_integrity",
    "verify_integrity",
    "create_replay_package",
    "create_package",
    "open",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "StorageFinalization",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
FUTURE_INTEGRITY_VALIDATION_MODULES = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "integrity_validation.py",
)
FUTURE_INTEGRITY_VALIDATION_SCOPE_RELAXABLE_NAMES = (
    "INTEGRITY_VALIDATION",
    "INTEGRITY_VALIDATOR",
    "EXPECTED_HASH_RECORD",
    "OBSERVED_HASH_RECORD",
    "INTEGRITY_VALIDATION_RESULT",
    "IntegrityValidation",
    "IntegrityValidator",
    "IntegrityValidationInput",
    "IntegrityValidationResult",
    "ExpectedHashRecord",
    "ObservedHashRecord",
    "validate_integrity",
    "verify_integrity",
    "validate_hash",
)
INTEGRITY_VALIDATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "PACKAGE_COMPLETENESS",
    "PACKAGE_CREATION",
    "PACKAGE_DIRECTORY",
    "PACKAGE_PATH",
    "CompleteReplayPackage",
    "PackageCompleteness",
    "PackageCreation",
    "PackageDirectory",
    "PackagePath",
    "ReplayPackageCreation",
    "assert_package_complete",
    "validate_package_completeness",
    "create_replay_package",
    "create_package",
    "build_package_directory",
    "create_package_directory",
    "open",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "StorageFinalization",
    "StorageRoot",
    "StoragePath",
    "FinalizedPackage",
    "ImmutabilityEnforcement",
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
FUTURE_STORAGE_FINALIZATION_MODULES = (
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "storage.py",
)
STORAGE_IMPLEMENTATION_MODULE = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "storage_implementation.py"
)
FILESYSTEM_STORAGE_AUTHORITY_MODULE = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "filesystem_storage_authority.py"
)
FUTURE_STORAGE_FINALIZATION_SCOPE_RELAXABLE_NAMES = (
    "STORAGE_ROOT",
    "STORAGE_PATH",
    "PACKAGE_DIRECTORY",
    "PACKAGE_PATH",
    "PACKAGE_LIFECYCLE_STATE",
    "FINALIZATION_STATE",
    "FINALIZED_PACKAGE",
    "INVALIDATED_PACKAGE",
    "SUPERSEDED_PACKAGE",
    "IMMUTABILITY_MARKER",
    "LINEAGE_REFERENCE",
    "CORRECTION_REFERENCE",
    "INVALIDATION_REFERENCE",
    "SUPERSESSION_REFERENCE",
    "StorageRoot",
    "StoragePath",
    "PackageDirectory",
    "PackagePath",
    "PackageLifecycleState",
    "FinalizationState",
    "FinalizedPackage",
    "InvalidatedPackage",
    "SupersededPackage",
    "ImmutabilityMarker",
    "LineageReference",
    "CorrectionReference",
    "InvalidationReference",
    "SupersessionReference",
)
STORAGE_FINALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "PACKAGE_CREATION",
    "PACKAGE_COMPLETENESS",
    "PackageCreation",
    "PackageCompleteness",
    "ReplayPackageCreation",
    "CompleteReplayPackage",
    "create_replay_package",
    "create_package",
    "assemble_replay_package",
    "validate_package_completeness",
    "assert_package_complete",
    "RUNTIME_CAPTURE",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
FILESYSTEM_STORAGE_AUTHORITY_SCOPE_RELAXABLE_NAMES = (
    "STORAGE_ROOT",
    "PACKAGE_PATH",
    "PACKAGE_DIRECTORY",
    "FILESYSTEM_READ_AUTHORITY",
    "FILESYSTEM_WRITE_AUTHORITY",
    "STORAGE_WRITER_AUTHORITY",
    "PATH_RESOLVER_AUTHORITY",
    "PACKAGE_DIRECTORY_RESOLVER_AUTHORITY",
    "StorageRoot",
    "PackagePath",
    "PackageDirectory",
    "FilesystemReadAuthority",
    "FilesystemWriteAuthority",
    "StorageWriterAuthority",
    "PathResolverAuthority",
    "PackageDirectoryResolverAuthority",
)
FILESYSTEM_STORAGE_AUTHORITY_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "STORAGE_FINALIZATION",
    "FINALIZED_PACKAGE",
    "IMMUTABILITY_ENFORCEMENT",
    "PACKAGE_COMPLETENESS",
    "RUNTIME_CAPTURE",
    "EVALUATION_PROMOTION",
    "BROKER_API_AUTHORITY",
    "EXECUTION_PERMISSION",
    "LIVE_TRADING_AUTHORITY",
    "StorageFinalization",
    "FinalizedPackage",
    "ImmutabilityEnforcement",
    "PackageCompleteness",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
STORAGE_IMPLEMENTATION_SCOPE_RELAXABLE_NAMES = (
    "STORAGE_IMPLEMENTATION",
    "STORAGE_LIFECYCLE_IMPLEMENTATION",
    "DRAFT_STORAGE_RECORD",
    "FINALIZED_STORAGE_RECORD",
    "STORAGE_FINALIZATION_RESULT",
    "IMMUTABILITY_MARKER",
    "LINEAGE_REFERENCE",
    "INVALIDATION_REFERENCE",
    "SUPERSESSION_REFERENCE",
    "NO_OVERWRITE_ENFORCEMENT_VOCABULARY",
    "STORAGE_WRITER_METADATA_INPUT",
    "STORAGE_WRITER_METADATA_RESULT",
    "StorageImplementation",
    "StorageLifecycleImplementation",
    "DraftStorageRecord",
    "FinalizedStorageRecord",
    "StorageFinalizationResult",
    "ImmutabilityMarker",
    "LineageReference",
    "InvalidationReference",
    "SupersessionReference",
    "NoOverwriteEnforcementVocabulary",
    "StorageWriterMetadataInput",
    "StorageWriterMetadataResult",
)
STORAGE_IMPLEMENTATION_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "ACTUAL_FILESYSTEM_READ",
    "ACTUAL_FILESYSTEM_WRITE",
    "PACKAGE_DIRECTORY_CREATION",
    "FINALIZED_STORAGE_BEHAVIOR",
    "IMMUTABILITY_ENFORCEMENT_BEHAVIOR",
    "PACKAGE_COMPLETENESS",
    "RUNTIME_CAPTURE",
    "EVALUATION_PROMOTION",
    "BROKER_API_AUTHORITY",
    "EXECUTION_PERMISSION",
    "LIVE_TRADING_AUTHORITY",
    "open",
    "read",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "PackageCompleteness",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
)
PACKAGE_COMPLETENESS_MODULE = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "replay"
    / "package_completeness.py"
)
PACKAGE_COMPLETENESS_SCOPE_RELAXABLE_NAMES = (
    "PACKAGE_COMPLETENESS",
    "COMPLETE_REPLAY_PACKAGE",
    "PACKAGE_COMPLETENESS_AUTHORITY",
    "PACKAGE_COMPLETENESS_RESULT",
    "PACKAGE_COMPLETENESS_VALIDATION",
    "COMPLETE_PACKAGE_EVIDENCE",
    "COMPLETE_PACKAGE_ELIGIBILITY",
    "COMPLETE_REPLAY_PACKAGE_AUTHORITY",
    "COMPLETENESS_MANIFEST_CHECK",
    "COMPLETENESS_HASH_CHECK",
    "COMPLETENESS_INTEGRITY_CHECK",
    "COMPLETENESS_STORAGE_CHECK",
    "COMPLETENESS_PROVENANCE_CHECK",
    "COMPLETENESS_REDACTION_CHECK",
    "COMPLETENESS_SOURCE_REFERENCE_CHECK",
    "PackageCompleteness",
    "CompleteReplayPackage",
    "PackageCompletenessAuthority",
    "PackageCompletenessResult",
    "PackageCompletenessValidation",
    "CompletePackageEvidence",
    "CompletePackageEligibility",
    "CompleteReplayPackageAuthority",
    "CompletenessManifestCheck",
    "CompletenessHashCheck",
    "CompletenessIntegrityCheck",
    "CompletenessStorageCheck",
    "CompletenessProvenanceCheck",
    "CompletenessRedactionCheck",
    "CompletenessSourceReferenceCheck",
)
PACKAGE_COMPLETENESS_SCOPE_DOWNSTREAM_DENIED_NAMES = (
    "PACKAGE_COMPLETENESS_IMPLEMENTATION",
    "ACTUAL_FILESYSTEM_READ",
    "ACTUAL_FILESYSTEM_WRITE",
    "PACKAGE_DIRECTORY_CREATION",
    "RUNTIME_CAPTURE",
    "EVALUATION_PROMOTION",
    "BROKER_API_AUTHORITY",
    "EXECUTION_PERMISSION",
    "LIVE_TRADING_AUTHORITY",
    "open",
    "read",
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "RuntimeCapture",
    "EvaluationEngine",
    "PromotionGate",
    "BrokerAuthority",
    "ExecutionPermission",
    "LiveTradingAuthority",
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


def _draft_manifest_input_dict(**overrides: object) -> dict:
    manifest_input = {
        "canonical_run_id": "run_unit5",
        "created_at": "2026-06-06T00:00:00Z",
        "source_artifact_references": (
            {
                "source_reference": "event_jsonl",
                "run_id": "run_unit5",
                "provenance": "recorded",
                "redaction_status": "not_required",
            },
        ),
        "section_status": {"package_identity": "present"},
        "section_provenance": {"package_identity": "recorded"},
        "section_redaction_status": {"package_identity": "not_required"},
        "section_source_reference": {"package_identity": "event_jsonl"},
    }
    manifest_input.update(overrides)
    return manifest_input


def _draft_manifest_input() -> manifest_builder.ManifestInput:
    return manifest_builder.ManifestInput(**_draft_manifest_input_dict())


def _hash_metadata(**overrides: object) -> dict:
    metadata = {
        "hash_algorithm": hashing.HASH_ALGORITHM,
        "hash_version": hashing.HASH_VERSION,
        "canonical_run_id": "run_unit6",
        "run_ids": ("run_unit6",),
        "provenance": "recorded",
        "redaction_status": "not_required",
        "sensitive_data_status": "clear",
        "source_reference": "event_jsonl",
        "known_source_references": ("event_jsonl",),
        "section_scope": "package_identity",
    }
    metadata.update(overrides)
    return metadata


def _draft_package_creation_input(**overrides: object) -> dict:
    canonical_payload = canonical_json.canonicalize_json({"section": "package"})
    canonical_input = canonical_bytes.build_canonical_bytes(canonical_payload)
    package_hash = hash_computation.build_package_hash(
        canonical_input,
        _hash_metadata(
            canonical_run_id="run_unit11",
            run_ids=("run_unit11",),
            package_scope="draft_package",
            section_scope=None,
        ),
    )
    integrity_result = integrity_validation.validate_integrity(package_hash, package_hash)
    package_input = {
        "canonical_run_id": "run_unit11",
        "package_identity": {
            "canonical_run_id": "run_unit11",
            "package_id": "package_run_unit11",
        },
        "manifest": manifest_builder.build_draft_manifest(
            _draft_manifest_input_dict(
                canonical_run_id="run_unit11",
                source_artifact_references=(
                    {
                        "source_reference": "event_jsonl",
                        "run_id": "run_unit11",
                        "provenance": "recorded",
                        "redaction_status": "not_required",
                    },
                ),
            )
        ),
        "canonical_bytes": canonical_input,
        "hash_records": (package_hash,),
        "integrity_validation_result": integrity_result,
        "provenance": "recorded",
        "redaction_status": "not_required",
        "source_references": ("event_jsonl",),
        "known_source_references": ("event_jsonl",),
        "input_run_ids": ("run_unit11",),
    }
    package_input.update(overrides)
    return package_input


def _filesystem_storage_authority_input(**overrides: object) -> dict:
    authority_input = {
        "canonical_run_id": "run_unit8_storage_authority",
        "storage_root": "replay_packages",
        "approved_storage_roots": ("replay_packages",),
        "package_path": "replay_packages/run_unit8_storage_authority",
        "approved_package_paths": ("replay_packages/run_unit8_storage_authority",),
        "package_directory": "run_unit8_storage_authority",
        "approved_package_directories": ("run_unit8_storage_authority",),
        "provenance": "recorded",
        "redaction_status": "not_required",
        "source_reference": "draft_package",
        "known_source_references": ("draft_package",),
        "input_run_ids": ("run_unit8_storage_authority",),
        "read_authority": True,
        "write_authority": True,
        "storage_writer_authority": True,
        "path_resolver_authority": True,
        "package_directory_resolver_authority": True,
    }
    authority_input.update(overrides)
    return authority_input


def _storage_writer_metadata_input(**overrides: object) -> dict:
    package_creation_result = package_creation.build_draft_package(
        _draft_package_creation_input()
    )
    filesystem_storage_authority_result = (
        filesystem_storage_authority.validate_filesystem_storage_authority(
            _filesystem_storage_authority_input(
                canonical_run_id="run_unit11",
                package_path="replay_packages/run_unit11",
                approved_package_paths=("replay_packages/run_unit11",),
                package_directory="run_unit11",
                approved_package_directories=("run_unit11",),
                input_run_ids=("run_unit11",),
            )
        )
    )
    storage_input = {
        "canonical_run_id": "run_unit11",
        "package_creation_result": package_creation_result,
        "filesystem_storage_authority_result": filesystem_storage_authority_result,
        "package_identity": {
            "canonical_run_id": "run_unit11",
            "package_id": "package_run_unit11",
        },
        "storage_root": "replay_packages",
        "package_path": "replay_packages/run_unit11",
        "package_directory": "run_unit11",
        "lifecycle_status": "draft",
        "provenance": "recorded",
        "redaction_status": "not_required",
        "source_reference": "draft_package",
        "known_source_references": ("draft_package",),
        "input_run_ids": ("run_unit11",),
        "package_completeness_authority": False,
    }
    storage_input.update(overrides)
    return storage_input


def _package_completeness_evidence(**overrides: object) -> dict:
    storage_implementation_result = storage_implementation.build_finalized_storage_record(
        _storage_writer_metadata_input(lifecycle_status="finalized")
    )
    package_creation_result = storage_implementation_result["package_creation_result"]
    completeness_evidence = {
        "canonical_run_id": "run_unit11",
        "package_identity": {
            "canonical_run_id": "run_unit11",
            "package_id": "package_run_unit11",
        },
        "package_creation_result": package_creation_result,
        "manifest": package_creation_result["manifest"],
        "canonical_bytes": package_creation_result["canonical_bytes"],
        "hash_records": package_creation_result["hash_records"],
        "integrity_validation_result": package_creation_result[
            "integrity_validation_result"
        ],
        "storage_implementation_result": storage_implementation_result,
        "storage_lifecycle_state": "finalized",
        "provenance": "recorded",
        "redaction_status": "not_required",
        "source_references": ("event_jsonl", "draft_package"),
        "known_source_references": ("event_jsonl", "draft_package"),
        "input_run_ids": ("run_unit11",),
    }
    completeness_evidence.update(overrides)
    return completeness_evidence


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


def test_package_creation_scope_guard_records_unit11_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 11: Replay Package Creation" in map_text
    assert "blocked until manifest generation, serialization" in map_text
    assert "hashing/integrity, package layout, and storage/finalization contracts" in (
        map_text
    )
    assert "Prerequisite dependencies: units 4, 5, 6, 7" in map_text
    assert "storage/finalization scope\n  for persisted/finalized packages" in (
        map_text
    )
    assert "draft-only assembly if approved" in map_text
    assert "package identity alignment" in map_text
    assert "provenance/redaction checks" in map_text
    assert "completeness prerequisites" in map_text
    assert "missing run_id" in map_text
    assert "mixed run_id" in map_text
    assert "stale/malformed artifacts" in map_text
    assert "implied runtime capture/storage" in map_text

    assert "## Replay Package Creation Authority Contract" in spec_text
    assert "Replay package creation authority remains governance-only" in spec_text
    assert "The first future package-creation lifecycle state" in spec_text
    assert "`draft` only" in spec_text
    assert "Draft-only package assembly" in spec_text
    assert "must remain non-finalized and\n  non-authoritative" in spec_text
    assert "Draft package creation must not imply finalized package authority" in (
        spec_text
    )
    assert "Draft package creation must not overwrite existing evidence" in spec_text
    assert "mapper bucket completeness only" in spec_text
    assert "Complete replay package authority must require explicit package creation" in (
        spec_text
    )
    assert "Manifest generation authority before package creation" in spec_text
    assert "Deterministic serialization authority before package creation" in spec_text
    assert "Canonical byte authority before package creation" in spec_text
    assert "Hashing and integrity validation before package creation" in spec_text
    assert "Storage and finalization authority before package creation" in spec_text
    assert "Runtime capture authority before package creation" in spec_text
    assert "Provenance must be explicit before package creation" in spec_text
    assert "Redaction status must be explicit before package creation" in spec_text
    assert "Source-reference authority must be explicit before package creation" in (
        spec_text
    )
    assert "Missing `run_id` must fail closed" in spec_text
    assert "Mixed `run_id` must fail closed" in spec_text
    assert "Stale artifacts must fail closed" in spec_text
    assert "Malformed artifacts must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Invalid redaction status must fail closed" in spec_text
    assert "Unknown source references must fail closed" in spec_text
    assert "Sensitive data exposure must stop package creation" in spec_text
    assert "Package creation must remain separate from storage and finalization" in (
        spec_text
    )
    assert "Package creation must remain separate from evaluation and promotion" in (
        spec_text
    )

    assert FUTURE_PACKAGE_CREATION_SCOPE_RELAXABLE_NAMES == (
        "PACKAGE_CREATION",
        "PACKAGE_BUILDER_TYPES",
        "PACKAGE_CREATION_MODULE",
        "DRAFT_REPLAY_PACKAGE",
        "DRAFT_PACKAGE_ASSEMBLY",
        "PACKAGE_CREATION_INPUT",
        "PACKAGE_CREATION_RESULT",
        "PackageCreation",
        "PackageBuilder",
        "PackageBuilderInput",
        "PackageBuilderOutput",
        "DraftReplayPackage",
        "DraftPackageAssembly",
        "PackageCreationInput",
        "PackageCreationResult",
        "build_draft_package",
        "assemble_draft_package",
        "create_draft_package",
    )
    assert not (
        set(FUTURE_PACKAGE_CREATION_SCOPE_RELAXABLE_NAMES)
        & set(PACKAGE_CREATION_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    package_creation_dependencies = (
        "package_layout_vocabulary",
        "manifest_generation",
        "canonical_serialization",
        "canonical_bytes",
        "hash_computation",
        "integrity_validation",
        "provenance",
        "redaction_status",
        "source_references",
        "run_id_alignment",
    )
    assert package_creation_dependencies == (
        "package_layout_vocabulary",
        "manifest_generation",
        "canonical_serialization",
        "canonical_bytes",
        "hash_computation",
        "integrity_validation",
        "provenance",
        "redaction_status",
        "source_references",
        "run_id_alignment",
    )

    package_creation_boundaries = (
        "draft_package_creation_is_not_finalized_storage",
        "package_creation_is_not_package_completeness",
        "in_memory_assembly_is_not_package_directories",
        "package_creation_is_not_evaluation_or_promotion",
        "no_filesystem_access_without_storage_gate",
    )
    assert package_creation_boundaries == (
        "draft_package_creation_is_not_finalized_storage",
        "package_creation_is_not_package_completeness",
        "in_memory_assembly_is_not_package_directories",
        "package_creation_is_not_evaluation_or_promotion",
        "no_filesystem_access_without_storage_gate",
    )

    package_creation_stop_conditions = (
        "missing_canonical_run_id",
        "mixed_run_id",
        "missing_package_identity",
        "missing_manifest",
        "missing_canonical_bytes",
        "missing_hash_records",
        "missing_integrity_validation_result",
        "failed_integrity_validation_result",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
        "stale_inputs",
        "malformed_inputs",
        "runtime_dependent_inputs",
        "filesystem_dependent_inputs_before_storage_authority",
        "evaluation_dependent_inputs",
    )
    assert package_creation_stop_conditions == (
        "missing_canonical_run_id",
        "mixed_run_id",
        "missing_package_identity",
        "missing_manifest",
        "missing_canonical_bytes",
        "missing_hash_records",
        "missing_integrity_validation_result",
        "failed_integrity_validation_result",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
        "stale_inputs",
        "malformed_inputs",
        "runtime_dependent_inputs",
        "filesystem_dependent_inputs_before_storage_authority",
        "evaluation_dependent_inputs",
    )

    for module_path in FUTURE_PACKAGE_CREATION_MODULES:
        assert not module_path.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["lifecycle_status"] == "draft"
    assert complete_inputs_envelope["evidence_only"] is True
    assert complete_inputs_envelope["non_authoritative"] is True
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert complete_inputs_envelope["writer_authority"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["file_path_ingestion"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert mapper_package["package_status"]["status"] == "complete"
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for denied_name in (
        "PACKAGE_COMPLETENESS",
        "FINALIZED_PACKAGE",
        "STORAGE_ROOT",
        "FILESYSTEM_READ",
        "FILESYSTEM_WRITE",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name in PACKAGE_CREATION_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FUTURE_PACKAGE_CREATION_SCOPE_RELAXABLE_NAMES

    for module_path in (
        *REPLAY_SOURCE_MODULES,
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
        *FUTURE_HASH_COMPUTATION_MODULES,
        *FUTURE_INTEGRITY_VALIDATION_MODULES,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in PACKAGE_CREATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text


def test_package_creation_helper_builds_draft_in_memory_only() -> None:
    assert PACKAGE_CREATION_MODULE.exists()
    assert package_creation.PACKAGE_CREATION == "draft_package_creation_in_memory_only"
    assert package_creation.PACKAGE_BUILDER_TYPES == "draft_package_builder_types"
    assert package_creation.PACKAGE_CREATION_MODULE == "package_creation"
    assert package_creation.DRAFT_REPLAY_PACKAGE == "draft_replay_package"
    assert package_creation.DRAFT_PACKAGE_ASSEMBLY == "draft_package_assembly"
    assert package_creation.PACKAGE_CREATION_INPUT == "package_creation_input"
    assert package_creation.PACKAGE_CREATION_RESULT == "package_creation_result"
    assert package_creation.PackageCreation().authority_boundary == (
        package_creation.PACKAGE_CREATION_AUTHORITY_BOUNDARY
    )
    assert package_creation.PackageBuilder().input_model == (
        package_creation.PACKAGE_CREATION_INPUT
    )
    assert package_creation.PackageBuilder().output_model == (
        package_creation.DRAFT_REPLAY_PACKAGE
    )
    assert package_creation.PackageBuilderOutput().authority_boundary == (
        package_creation.PACKAGE_CREATION_AUTHORITY_BOUNDARY
    )
    assert package_creation.PackageCreationResult().authority_boundary == (
        package_creation.PACKAGE_CREATION_AUTHORITY_BOUNDARY
    )

    package_input = _draft_package_creation_input()
    draft_package = package_creation.build_draft_package(package_input)

    assert draft_package == package_creation.assemble_draft_package(package_input)
    assert draft_package == package_creation.create_draft_package(package_input)
    assert draft_package["package_type"] == package_creation.DRAFT_REPLAY_PACKAGE
    assert draft_package["assembly_type"] == package_creation.DRAFT_PACKAGE_ASSEMBLY
    assert draft_package["lifecycle_status"] == "draft"
    assert draft_package["canonical_run_id"] == "run_unit11"
    assert draft_package["package_identity"]["package_id"] == "package_run_unit11"
    assert draft_package["manifest"]["canonical_run_id"] == "run_unit11"
    assert draft_package["canonical_bytes"] == package_input["canonical_bytes"]
    assert draft_package["hash_records"] == package_input["hash_records"]
    assert draft_package["integrity_validation_result"] == (
        package_input["integrity_validation_result"]
    )
    assert draft_package["evidence_only"] is True
    assert draft_package["non_authoritative"] is True
    assert draft_package["package_completeness"] is False
    assert draft_package["finalized_storage"] is False
    assert draft_package["filesystem_reads"] is False
    assert draft_package["filesystem_writes"] is False
    assert draft_package["package_directories"] is False
    assert draft_package["storage_finalization_immutability"] is False
    assert draft_package["runtime_capture"] is False
    assert draft_package["evaluation_or_promotion"] is False
    assert draft_package["broker_api_authority"] is False
    assert draft_package["execution_authority"] is False
    assert draft_package["live_trading_authority"] is False
    assert draft_package["authority_boundary"] == (
        package_creation.PACKAGE_CREATION_AUTHORITY_BOUNDARY
    )
    assert "no_package_completeness" in draft_package["authority_boundary"]
    assert "no_finalized_storage" in draft_package["authority_boundary"]
    assert "no_filesystem_reads" in draft_package["authority_boundary"]
    assert "no_filesystem_writes" in draft_package["authority_boundary"]
    assert "no_package_directories" in draft_package["authority_boundary"]
    assert "no_storage_finalization_immutability" in (
        draft_package["authority_boundary"]
    )
    assert "no_runtime_capture" in draft_package["authority_boundary"]
    assert "no_evaluation_or_promotion" in draft_package["authority_boundary"]
    assert "no_broker_authority" in draft_package["authority_boundary"]
    assert "no_execution_authority" in draft_package["authority_boundary"]
    assert "no_live_trading_authority" in draft_package["authority_boundary"]

    module_names = set(package_creation.__dict__)
    for relaxable_name in FUTURE_PACKAGE_CREATION_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names

    for denied_name in (
        "PACKAGE_COMPLETENESS",
        "FINALIZED_PACKAGE",
        "STORAGE_ROOT",
        "FILESYSTEM_READ",
        "FILESYSTEM_WRITE",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name not in module_names


def test_package_creation_helper_fails_closed_without_downstream_authority() -> None:
    base_input = _draft_package_creation_input()

    bad_cases = (
        ({**base_input, "canonical_run_id": ""}, ValueError),
        ({**base_input, "input_run_ids": ("run_unit11", "other")}, ValueError),
        ({**base_input, "package_identity": {}}, ValueError),
        ({**base_input, "manifest": {}}, ValueError),
        ({**base_input, "canonical_bytes": b""}, ValueError),
        ({**base_input, "hash_records": ()}, ValueError),
        ({**base_input, "integrity_validation_result": {}}, ValueError),
        (
            {
                **base_input,
                "integrity_validation_result": {
                    **base_input["integrity_validation_result"],
                    "integrity_status": "mismatch",
                    "hash_match": False,
                },
            },
            ValueError,
        ),
        ({**base_input, "provenance": ""}, ValueError),
        ({**base_input, "provenance": object()}, ValueError),
        ({**base_input, "redaction_status": ""}, ValueError),
        ({**base_input, "redaction_status": "unknown"}, ValueError),
        ({**base_input, "source_references": ("unknown",)}, ValueError),
        ({**base_input, "sensitive_data_status": "exposed"}, ValueError),
        ({**base_input, "stale_input": True}, ValueError),
        ({**base_input, "malformed_input": True}, ValueError),
        ({**base_input, "runtime_dependent": True}, ValueError),
        ({**base_input, "filesystem_dependent": True}, ValueError),
        ({**base_input, "evaluation_dependent": True}, ValueError),
        (object(), TypeError),
    )
    for bad_input, expected_error in bad_cases:
        with pytest.raises(expected_error):
            package_creation.build_draft_package(bad_input)

    module_text = PACKAGE_CREATION_MODULE.read_text(encoding="utf-8")
    assert "hashlib" not in module_text
    for denied_name in PACKAGE_CREATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
        if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
            continue
        assert denied_name not in module_text


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
        assert future_module.exists()

    assert (
        manifest_builder.MANIFEST_GENERATION
        == "draft_manifest_generation_in_memory_only"
    )
    assert manifest_builder.MANIFEST_BUILDER == "draft_manifest_builder_in_memory_only"
    assert manifest_builder.DRAFT_MANIFEST == "draft_manifest"
    assert manifest_builder.MANIFEST_INPUT == "manifest_input"
    assert manifest_builder.ManifestGeneration().authority_boundary == (
        manifest_builder.MANIFEST_GENERATION_AUTHORITY_BOUNDARY
    )
    assert manifest_builder.ManifestBuilder().output_model == (
        manifest_builder.DRAFT_MANIFEST
    )
    assert (
        manifest_builder.ManifestFieldEligibility().required_fields
        == manifest_schema.MANIFEST_REQUIRED_FIELDS
    )
    assert manifest_builder.ManifestProvenanceEligibility().required is True
    assert manifest_builder.ManifestRedactionEligibility().required is True
    assert manifest_builder.ManifestRunIdAlignment().required is True
    assert (
        manifest_builder.ManifestSourceReferenceEligibility()
        .known_references_required
        is True
    )

    manifest_input = _draft_manifest_input()
    draft_manifest = manifest_builder.build_draft_manifest(manifest_input)
    in_memory_manifest = manifest_builder.build_in_memory_manifest(manifest_input)

    assert draft_manifest == in_memory_manifest
    assert draft_manifest["canonical_run_id"] == manifest_input.canonical_run_id
    assert draft_manifest["package_id"] is None
    assert draft_manifest["manifest_schema_version"] == (
        manifest_schema.MANIFEST_SCHEMA_VERSION
    )
    assert draft_manifest["lifecycle_status"] == "draft"
    assert draft_manifest["evidence_only"] is True
    assert draft_manifest["non_authoritative"] is True
    assert draft_manifest["authority_boundary"] == (
        manifest_builder.MANIFEST_GENERATION_AUTHORITY_BOUNDARY
    )
    assert "no_package_creation" in draft_manifest["authority_boundary"]
    assert "no_filesystem_access" in draft_manifest["authority_boundary"]
    assert "no_hash_computation" in draft_manifest["authority_boundary"]
    assert "no_integrity_validation" in draft_manifest["authority_boundary"]
    assert "no_storage_finalization" in draft_manifest["authority_boundary"]
    assert "no_runtime_capture" in draft_manifest["authority_boundary"]
    assert "no_evaluation_or_promotion" in draft_manifest["authority_boundary"]
    assert "no_broker_authority" in draft_manifest["authority_boundary"]
    assert "no_execution_authority" in draft_manifest["authority_boundary"]
    assert "no_live_trading_authority" in draft_manifest["authority_boundary"]

    module_names = set(manifest_builder.__dict__)
    for relaxable_name in FUTURE_MANIFEST_GENERATION_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names

    for malformed_input in (
        object(),
        {},
        _draft_manifest_input_dict(canonical_run_id=""),
    ):
        with pytest.raises((TypeError, ValueError)):
            manifest_builder.build_draft_manifest(malformed_input)

    with pytest.raises(ValueError, match="mixed run_id"):
        manifest_builder.build_draft_manifest(
            _draft_manifest_input_dict(
                source_artifact_references=(
                    {
                        "source_reference": "event_jsonl",
                        "run_id": "other_run",
                        "provenance": "recorded",
                        "redaction_status": "not_required",
                    },
                )
            )
        )
    with pytest.raises(ValueError, match="provenance"):
        manifest_builder.build_draft_manifest(
            _draft_manifest_input_dict(section_provenance={})
        )
    with pytest.raises(ValueError, match="redaction"):
        manifest_builder.build_draft_manifest(
            _draft_manifest_input_dict(section_redaction_status={})
        )
    with pytest.raises(ValueError, match="known"):
        manifest_builder.build_draft_manifest(
            _draft_manifest_input_dict(
                section_source_reference={"package_identity": "unknown_source"}
            )
        )
    with pytest.raises(ValueError, match="filesystem"):
        manifest_builder.build_draft_manifest(
            _draft_manifest_input_dict(
                source_artifact_references=(
                    {
                        "source_reference": "event_jsonl",
                        "run_id": "run_unit5",
                        "provenance": "recorded",
                        "redaction_status": "not_required",
                        "source_path": "/tmp/run.jsonl",
                    },
                )
            )
        )

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

    for module_path in FUTURE_MANIFEST_GENERATION_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        assert "hashlib" not in module_text
        for denied_name in MANIFEST_GENERATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text


def test_hash_computation_scope_guard_records_unit6_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 6: Section/Package Hash Computation" in map_text
    assert "blocked until canonical bytes, hash" in map_text
    assert "algorithm/version, manifest generation, and section scopes exist" in (
        map_text
    )
    assert "Prerequisite dependencies: units 2, 3, and 5." in map_text
    assert "future hash computation module" in map_text
    assert "hash computation tests" in map_text
    assert "section hash, manifest hash, package hash distinction" in map_text
    assert "mixed\n  run_id fail-closed behavior" in map_text
    assert "missing provenance/redaction fail-closed" in map_text
    assert "no package completeness authority" in map_text
    assert "missing canonical bytes" in map_text
    assert "missing section scope" in map_text
    assert "unknown hash\n  version" in map_text
    assert "sensitive data exposure" in map_text
    assert "undefined redaction state" in map_text
    assert "hash output cannot create manifest authority" in map_text
    assert "package completeness" in map_text
    assert "Filesystem access allowed: no." in map_text
    assert "Runtime artifact access allowed: no." in map_text
    assert "Broker/API access allowed: no." in map_text
    assert "Execution/live trading authority allowed: no." in map_text

    assert "Required future section hash rules" in spec_text
    assert "Section hash inputs must be approved canonical serialized bytes only" in (
        spec_text
    )
    assert "Section hash scope must define whether it covers" in spec_text
    assert "Required future manifest hash rules" in spec_text
    assert "Manifest hash authority is separate from section hash authority" in (
        spec_text
    )
    assert "Manifest hash inputs must be approved canonical serialized manifest bytes" in (
        spec_text
    )
    assert "Required future package hash rules" in spec_text
    assert "Package hash authority is separate from section hash authority" in (
        spec_text
    )
    assert "Package hash inputs must be approved canonical serialized bytes only" in (
        spec_text
    )
    assert "Package hash must not imply package creation" in spec_text
    assert "Package hash must not imply package completeness" in spec_text
    assert "Mixed-`run_id` hash inputs must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Unknown source references must fail closed" in spec_text
    assert "Sensitive data exposure must stop hashing" in spec_text
    assert "Need filesystem reads or writes" in spec_text

    assert canonical_bytes.CANONICAL_BYTES_OUTPUT == "canonical_json_utf8_bytes"
    assert hashing.HASH_ALGORITHM == "sha256"
    assert hashing.HASH_VERSION == "v1"
    assert FUTURE_HASH_COMPUTATION_SCOPE_RELAXABLE_NAMES == (
        "SECTION_HASH",
        "MANIFEST_HASH",
        "PACKAGE_HASH",
        "HASH_COMPUTATION",
        "HASH_INPUT_ELIGIBILITY",
        "HASH_SCOPE",
        "SECTION_HASH_SCOPE",
        "MANIFEST_HASH_SCOPE",
        "PACKAGE_HASH_SCOPE",
        "CANONICAL_HASH_INPUT",
        "HashComputation",
        "HashInputEligibility",
        "HashScope",
        "SectionHash",
        "ManifestHash",
        "PackageHash",
        "SectionHashScope",
        "ManifestHashScope",
        "PackageHashScope",
        "CanonicalHashInput",
        "build_section_hash",
        "build_manifest_hash",
        "build_package_hash",
    )
    assert not (
        set(FUTURE_HASH_COMPUTATION_SCOPE_RELAXABLE_NAMES)
        & set(HASH_COMPUTATION_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    for future_module in FUTURE_HASH_COMPUTATION_MODULES:
        assert future_module.exists()

    assert hash_computation.SECTION_HASH == "section_hash"
    assert hash_computation.MANIFEST_HASH == "manifest_hash"
    assert hash_computation.PACKAGE_HASH == "package_hash"
    assert (
        hash_computation.HASH_COMPUTATION
        == "sha256_canonical_bytes_hash_computation"
    )
    assert hash_computation.HashInputEligibility().input_model == (
        hash_computation.CANONICAL_HASH_INPUT
    )
    assert hash_computation.HashInputEligibility().algorithm == hashing.HASH_ALGORITHM
    assert hash_computation.HashInputEligibility().version == hashing.HASH_VERSION
    assert hash_computation.HashComputation().authority_boundary == (
        hash_computation.HASH_COMPUTATION_AUTHORITY_BOUNDARY
    )
    assert hash_computation.SectionHash().hash_type == hash_computation.SECTION_HASH
    assert hash_computation.ManifestHash().hash_type == hash_computation.MANIFEST_HASH
    assert hash_computation.PackageHash().hash_type == hash_computation.PACKAGE_HASH
    assert hash_computation.SectionHashScope().name == (
        hash_computation.SECTION_HASH_SCOPE
    )
    assert hash_computation.ManifestHashScope().name == (
        hash_computation.MANIFEST_HASH_SCOPE
    )
    assert hash_computation.PackageHashScope().name == (
        hash_computation.PACKAGE_HASH_SCOPE
    )

    canonical_payload = canonical_json.canonicalize_json({"section": "identity"})
    canonical_input = canonical_bytes.build_canonical_bytes(canonical_payload)
    section_metadata = _hash_metadata(section_scope="package_identity")
    manifest_metadata = _hash_metadata(manifest_scope="draft_manifest")
    package_metadata = _hash_metadata(package_scope="draft_package")

    section_hash = hash_computation.build_section_hash(
        canonical_input,
        section_metadata,
    )
    manifest_hash = hash_computation.build_manifest_hash(
        canonical_input,
        manifest_metadata,
    )
    package_hash = hash_computation.build_package_hash(
        canonical_input,
        package_metadata,
    )

    assert section_hash["hash_type"] == hash_computation.SECTION_HASH
    assert manifest_hash["hash_type"] == hash_computation.MANIFEST_HASH
    assert package_hash["hash_type"] == hash_computation.PACKAGE_HASH
    assert section_hash["digest"] == manifest_hash["digest"] == package_hash["digest"]
    assert section_hash["hash_algorithm"] == hashing.HASH_ALGORITHM
    assert section_hash["hash_version"] == hashing.HASH_VERSION
    assert section_hash["evidence_only"] is True
    assert section_hash["non_authoritative"] is True
    assert "no_integrity_validation" in section_hash["authority_boundary"]
    assert "no_package_completeness" in section_hash["authority_boundary"]
    assert "no_package_creation" in section_hash["authority_boundary"]
    assert "no_filesystem_access" in section_hash["authority_boundary"]
    assert "no_storage_finalization" in section_hash["authority_boundary"]
    assert "no_runtime_capture" in section_hash["authority_boundary"]
    assert "no_broker_authority" in section_hash["authority_boundary"]
    assert "no_execution_authority" in section_hash["authority_boundary"]
    assert "no_live_trading_authority" in section_hash["authority_boundary"]

    assert hash_computation.build_section_hash(canonical_input, section_metadata) == (
        section_hash
    )

    for bad_input, bad_metadata, expected_error in (
        (canonical_payload, section_metadata, TypeError),
        (canonical_input, _hash_metadata(run_ids=("run_unit6", "other")), ValueError),
        (canonical_input, _hash_metadata(provenance=""), ValueError),
        (canonical_input, _hash_metadata(redaction_status=""), ValueError),
        (
            canonical_input,
            _hash_metadata(source_reference="unknown_source"),
            ValueError,
        ),
        (canonical_input, _hash_metadata(sensitive_data_status="unknown"), ValueError),
        (canonical_input, _hash_metadata(section_scope=""), ValueError),
        (canonical_input, _hash_metadata(source_path="/tmp/run.jsonl"), ValueError),
        (canonical_input, _hash_metadata(hash_algorithm="unknown"), ValueError),
        (canonical_input, _hash_metadata(hash_version="unknown"), ValueError),
    ):
        with pytest.raises(expected_error):
            hash_computation.build_section_hash(bad_input, bad_metadata)

    for denied_name in (
        "INTEGRITY_VALIDATION",
        "PACKAGE_COMPLETENESS",
        "PACKAGE_CREATION",
        "PACKAGE_DIRECTORY",
        "validate_hash",
        "validate_integrity",
        "verify_integrity",
        "create_replay_package",
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "StorageFinalization",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name in HASH_COMPUTATION_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FUTURE_HASH_COMPUTATION_SCOPE_RELAXABLE_NAMES

    hash_scope_stop_conditions = (
        "mixed_run_id",
        "missing_provenance",
        "missing_redaction_status",
        "unknown_source_references",
        "sensitive_data_ambiguity",
        "undefined_section_scope",
        "filesystem_dependent_inputs",
        "non_canonical_bytes_input",
        "missing_algorithm_version_metadata",
    )
    assert hash_scope_stop_conditions == (
        "mixed_run_id",
        "missing_provenance",
        "missing_redaction_status",
        "unknown_source_references",
        "sensitive_data_ambiguity",
        "undefined_section_scope",
        "filesystem_dependent_inputs",
        "non_canonical_bytes_input",
        "missing_algorithm_version_metadata",
    )

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
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
        for denied_name in HASH_COMPUTATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text

    for module_path in (
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in HASH_COMPUTATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text

    for module_path in FUTURE_HASH_COMPUTATION_MODULES:
        module_text = module_path.read_text(encoding="utf-8")
        assert "hashlib" in module_text
        for denied_name in HASH_COMPUTATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text


def test_integrity_validation_scope_guard_records_unit7_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 7: Integrity Validation" in map_text
    assert "blocked until hash computation, provenance" in map_text
    assert "redaction, source references, and run_id alignment rules exist" in (
        map_text
    )
    assert "Prerequisite dependencies: units 3 and 6 plus source/provenance" in (
        map_text
    )
    assert "future integrity validation module" in map_text
    assert "integrity validation\n  tests" in map_text
    assert "mismatch fail-closed behavior" in map_text
    assert "missing hash fail-closed\n  behavior" in map_text
    assert "provenance/redaction/source-reference failure cases" in map_text
    assert "missing hashes, mismatches, mixed run_id" in map_text
    assert "missing/invalid redaction status" in map_text
    assert "unknown source references" in map_text
    assert "sensitive data exposure" in map_text
    assert "validation result is not storage authority" in map_text
    assert "package creation authority" in map_text
    assert "Filesystem access allowed: no." in map_text
    assert "Runtime artifact access allowed: no." in map_text
    assert "Broker/API access allowed: no." in map_text
    assert "Execution/live trading authority allowed: no." in map_text

    assert "Required future integrity validation rules" in spec_text
    assert "Hash mismatch must fail closed" in spec_text
    assert "Missing required hash must fail closed" in spec_text
    assert "Mixed-`run_id` hash inputs must fail closed" in spec_text
    assert "Malformed provenance must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Invalid redaction state must fail closed" in spec_text
    assert "Unknown source references must fail closed" in spec_text
    assert "Sensitive data exposure must stop hashing, integrity validation" in (
        spec_text
    )
    assert "Integrity validation output remains non-authoritative" in spec_text
    assert "Hashing and integrity cannot authorize replay package creation" in (
        spec_text
    )
    assert "Need storage, finalization, or immutability" in spec_text
    assert "Need package creation" in spec_text
    assert "Need filesystem reads or writes" in spec_text

    assert integrity.INTEGRITY_STATUS == (
        "missing",
        "present",
        "unavailable",
        "not_validated",
    )
    assert integrity.IntegrityStatus().values == integrity.INTEGRITY_STATUS
    assert hash_computation.HASH_COMPUTATION_AUTHORITY_BOUNDARY.count(
        "no_integrity_validation"
    ) == 1
    assert FUTURE_INTEGRITY_VALIDATION_SCOPE_RELAXABLE_NAMES == (
        "INTEGRITY_VALIDATION",
        "INTEGRITY_VALIDATOR",
        "EXPECTED_HASH_RECORD",
        "OBSERVED_HASH_RECORD",
        "INTEGRITY_VALIDATION_RESULT",
        "IntegrityValidation",
        "IntegrityValidator",
        "IntegrityValidationInput",
        "IntegrityValidationResult",
        "ExpectedHashRecord",
        "ObservedHashRecord",
        "validate_integrity",
        "verify_integrity",
        "validate_hash",
    )
    assert not (
        set(FUTURE_INTEGRITY_VALIDATION_SCOPE_RELAXABLE_NAMES)
        & set(INTEGRITY_VALIDATION_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    integrity_scope_stop_conditions = (
        "hash_mismatch",
        "missing_hash",
        "mixed_run_id",
        "malformed_provenance",
        "missing_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
    )
    assert integrity_scope_stop_conditions == (
        "hash_mismatch",
        "missing_hash",
        "mixed_run_id",
        "malformed_provenance",
        "missing_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
    )

    validation_boundary = (
        "non_authoritative_until_later_package_gates",
        "no_package_completeness",
        "no_package_creation",
        "no_filesystem_access",
        "no_storage_finalization",
        "no_runtime_capture",
        "no_evaluation_or_promotion",
        "no_broker_authority",
        "no_execution_authority",
        "no_live_trading_authority",
    )
    assert validation_boundary == (
        "non_authoritative_until_later_package_gates",
        "no_package_completeness",
        "no_package_creation",
        "no_filesystem_access",
        "no_storage_finalization",
        "no_runtime_capture",
        "no_evaluation_or_promotion",
        "no_broker_authority",
        "no_execution_authority",
        "no_live_trading_authority",
    )

    for future_module in FUTURE_INTEGRITY_VALIDATION_MODULES:
        assert future_module.exists()

    assert (
        integrity_validation.INTEGRITY_VALIDATION
        == "in_memory_hash_record_integrity_validation"
    )
    assert integrity_validation.INTEGRITY_VALIDATOR == "hash_record_integrity_validator"
    assert integrity_validation.EXPECTED_HASH_RECORD == "expected_hash_record"
    assert integrity_validation.OBSERVED_HASH_RECORD == "observed_hash_record"
    assert (
        integrity_validation.INTEGRITY_VALIDATION_RESULT
        == "integrity_validation_result"
    )
    assert integrity_validation.IntegrityValidation().authority_boundary == (
        integrity_validation.INTEGRITY_VALIDATION_AUTHORITY_BOUNDARY
    )
    assert integrity_validation.IntegrityValidator().input_model == (
        "expected_hash_record:observed_hash_record"
    )
    assert integrity_validation.IntegrityValidationResult().authority_boundary == (
        integrity_validation.INTEGRITY_VALIDATION_AUTHORITY_BOUNDARY
    )

    canonical_payload = canonical_json.canonicalize_json({"section": "integrity"})
    canonical_input = canonical_bytes.build_canonical_bytes(canonical_payload)
    expected_hash = hash_computation.build_section_hash(
        canonical_input,
        _hash_metadata(section_scope="integrity"),
    )
    observed_hash = hash_computation.build_section_hash(
        canonical_input,
        _hash_metadata(section_scope="integrity"),
    )
    validation = integrity_validation.validate_integrity(
        expected_hash,
        observed_hash,
    )

    assert validation["result_type"] == (
        integrity_validation.INTEGRITY_VALIDATION_RESULT
    )
    assert validation["integrity_status"] == "valid"
    assert validation["reason"] == "hash_match"
    assert validation["hash_match"] is True
    assert validation["evidence_only"] is True
    assert validation["non_authoritative"] is True
    assert validation["package_completeness"] is False
    assert "no_package_completeness" in validation["authority_boundary"]
    assert "no_package_creation" in validation["authority_boundary"]
    assert "no_filesystem_access" in validation["authority_boundary"]
    assert "no_storage_finalization" in validation["authority_boundary"]
    assert "no_runtime_capture" in validation["authority_boundary"]
    assert "no_evaluation_or_promotion" in validation["authority_boundary"]
    assert "no_broker_authority" in validation["authority_boundary"]
    assert "no_execution_authority" in validation["authority_boundary"]
    assert "no_live_trading_authority" in validation["authority_boundary"]
    assert integrity_validation.verify_integrity(expected_hash, observed_hash) == (
        validation
    )
    assert integrity_validation.validate_hash(expected_hash, observed_hash) == (
        validation
    )

    mismatched_hash = {
        **observed_hash,
        "digest": "0" * 64,
    }
    mismatch_result = integrity_validation.validate_integrity(
        expected_hash,
        mismatched_hash,
    )
    assert mismatch_result["integrity_status"] == "mismatch"
    assert mismatch_result["reason"] == "hash_mismatch"
    assert mismatch_result["hash_match"] is False
    assert mismatch_result["evidence_only"] is True
    assert mismatch_result["non_authoritative"] is True
    assert mismatch_result["package_completeness"] is False

    bad_cases = (
        ({**expected_hash, "digest": ""}, observed_hash, ValueError),
        (expected_hash, {**observed_hash, "digest": ""}, ValueError),
        (
            expected_hash,
            {
                **observed_hash,
                "metadata": _hash_metadata(run_ids=("run_unit6", "other")),
            },
            ValueError,
        ),
        (
            expected_hash,
            {**observed_hash, "metadata": {"provenance": object()}},
            ValueError,
        ),
        (
            expected_hash,
            {**observed_hash, "metadata": _hash_metadata(provenance="")},
            ValueError,
        ),
        (
            expected_hash,
            {**observed_hash, "metadata": _hash_metadata(redaction_status="")},
            ValueError,
        ),
        (
            expected_hash,
            {
                **observed_hash,
                "metadata": _hash_metadata(redaction_status="unknown"),
            },
            ValueError,
        ),
        (
            expected_hash,
            {
                **observed_hash,
                "metadata": _hash_metadata(source_reference="unknown_source"),
            },
            ValueError,
        ),
        (
            expected_hash,
            {
                **observed_hash,
                "metadata": _hash_metadata(sensitive_data_status="exposed"),
            },
            ValueError,
        ),
    )
    for bad_expected, bad_observed, expected_error in bad_cases:
        with pytest.raises(expected_error):
            integrity_validation.validate_integrity(bad_expected, bad_observed)

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["hashing_integrity_enforcement"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
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

    for denied_name in (
        "PACKAGE_COMPLETENESS",
        "PACKAGE_CREATION",
        "PACKAGE_DIRECTORY",
        "create_replay_package",
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "StorageFinalization",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name in INTEGRITY_VALIDATION_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FUTURE_INTEGRITY_VALIDATION_SCOPE_RELAXABLE_NAMES

    for module_path in (
        *REPLAY_SOURCE_MODULES,
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
        *FUTURE_HASH_COMPUTATION_MODULES,
        *FUTURE_INTEGRITY_VALIDATION_MODULES,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in INTEGRITY_VALIDATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
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


def test_storage_finalization_scope_guard_records_unit8_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 8: Storage Root/Path/Lifecycle/Finalization/Immutability" in (
        map_text
    )
    assert "blocked until integrity validation, package layout" in map_text
    assert "and package creation authority exist" in map_text
    assert "Prerequisite dependencies: units 4, 7, and 11" in map_text
    assert "future storage lifecycle module and storage tests" in map_text
    assert "separate filesystem/storage gate" in map_text
    assert "root/path authority" in map_text
    assert "lifecycle states" in map_text
    assert "no-overwrite finalized\n  evidence" in map_text
    assert "correction/invalidation/supersession lineage" in map_text
    assert "unknown root" in map_text
    assert "missing path authority" in map_text
    assert "attempted overwrite" in map_text
    assert "missing integrity validation" in map_text
    assert "mixed run_id" in map_text
    assert "missing provenance" in map_text
    assert "missing or\n  invalid redaction status" in map_text
    assert "unknown source references" in map_text
    assert "sensitive data\n  exposure" in map_text
    assert "storage output cannot create package completeness" in map_text
    assert "Filesystem access allowed: no until a separate filesystem/storage" in (
        map_text
    )

    assert "## Storage, Finalization, and Immutability Authority Contract" in (
        spec_text
    )
    assert "does not approve tests, code, storage\nconstants" in spec_text
    assert "filesystem reads, filesystem\nwrites" in spec_text
    assert "Storage root authority must be explicitly governed" in spec_text
    assert "Package path authority must be explicitly governed" in spec_text
    assert "Package directory naming authority must be explicitly governed" in (
        spec_text
    )
    assert "Package creation authority must exist before finalized package storage" in (
        spec_text
    )
    assert "Minimum future lifecycle states are `draft`, `finalized`, `invalidated`" in (
        spec_text
    )
    assert "and\n  `superseded`" in spec_text
    assert "Finalized evidence must be immutable and no-overwrite" in spec_text
    assert "append-only and lineage-preserving" in spec_text
    assert "Corrections, invalidations, and supersessions must identify" in spec_text
    assert "Attempted overwrite of finalized evidence must fail closed" in spec_text
    assert "Immutable evidence must remain distinct from derived reports" in (
        spec_text
    )
    assert "Missing paths, unknown storage roots" in spec_text
    assert "Mixed-`run_id` storage inputs must fail closed" in spec_text
    assert "Missing provenance must fail closed" in spec_text
    assert "Missing redaction status must fail closed" in spec_text
    assert "Invalid redaction status must fail closed" in spec_text
    assert "Sensitive data exposure must stop storage" in spec_text
    assert "A future writer must not create package authority or package completeness" in (
        spec_text
    )
    assert "Storage, finalization, and immutability cannot authorize" in spec_text
    assert "runtime capture, evaluation, attribution,\npromotion" in spec_text

    assert FUTURE_STORAGE_FINALIZATION_SCOPE_RELAXABLE_NAMES == (
        "STORAGE_ROOT",
        "STORAGE_PATH",
        "PACKAGE_DIRECTORY",
        "PACKAGE_PATH",
        "PACKAGE_LIFECYCLE_STATE",
        "FINALIZATION_STATE",
        "FINALIZED_PACKAGE",
        "INVALIDATED_PACKAGE",
        "SUPERSEDED_PACKAGE",
        "IMMUTABILITY_MARKER",
        "LINEAGE_REFERENCE",
        "CORRECTION_REFERENCE",
        "INVALIDATION_REFERENCE",
        "SUPERSESSION_REFERENCE",
        "StorageRoot",
        "StoragePath",
        "PackageDirectory",
        "PackagePath",
        "PackageLifecycleState",
        "FinalizationState",
        "FinalizedPackage",
        "InvalidatedPackage",
        "SupersededPackage",
        "ImmutabilityMarker",
        "LineageReference",
        "CorrectionReference",
        "InvalidationReference",
        "SupersessionReference",
    )
    assert not (
        set(FUTURE_STORAGE_FINALIZATION_SCOPE_RELAXABLE_NAMES)
        & set(STORAGE_FINALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    lifecycle_states = ("draft", "finalized", "invalidated", "superseded")
    assert lifecycle_states == ("draft", "finalized", "invalidated", "superseded")

    storage_scope_boundaries = (
        "storage_root_authority_required",
        "package_path_authority_required",
        "package_directory_authority_required",
        "finalized_no_overwrite_required",
        "immutability_semantics_required",
        "lineage_semantics_required",
        "correction_invalidation_supersession_boundaries_required",
        "storage_is_not_package_creation",
        "finalization_is_not_package_completeness",
        "persistence_is_not_evaluation_or_promotion",
    )
    assert storage_scope_boundaries == (
        "storage_root_authority_required",
        "package_path_authority_required",
        "package_directory_authority_required",
        "finalized_no_overwrite_required",
        "immutability_semantics_required",
        "lineage_semantics_required",
        "correction_invalidation_supersession_boundaries_required",
        "storage_is_not_package_creation",
        "finalization_is_not_package_completeness",
        "persistence_is_not_evaluation_or_promotion",
    )

    storage_scope_stop_conditions = (
        "unknown_storage_root",
        "unknown_package_path",
        "missing_package_creation_authority",
        "missing_package_completeness_authority",
        "overwrite_attempt",
        "mixed_run_id",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_reference",
        "sensitive_data_exposure",
        "filesystem_dependent_inputs_before_storage_authority",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
    )
    assert storage_scope_stop_conditions == (
        "unknown_storage_root",
        "unknown_package_path",
        "missing_package_creation_authority",
        "missing_package_completeness_authority",
        "overwrite_attempt",
        "mixed_run_id",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_reference",
        "sensitive_data_exposure",
        "filesystem_dependent_inputs_before_storage_authority",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
    )

    for future_module in FUTURE_STORAGE_FINALIZATION_MODULES:
        assert not future_module.exists()

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
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for denied_name in (
        "PACKAGE_CREATION",
        "PACKAGE_COMPLETENESS",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name in STORAGE_FINALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FUTURE_STORAGE_FINALIZATION_SCOPE_RELAXABLE_NAMES

    for module_path in (
        *REPLAY_SOURCE_MODULES,
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
        *FUTURE_HASH_COMPUTATION_MODULES,
        *FUTURE_INTEGRITY_VALIDATION_MODULES,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in STORAGE_FINALIZATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            assert denied_name not in module_text


def test_filesystem_storage_authority_scope_guard_records_boundary_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "Any unit requiring filesystem reads or writes must wait for a" in (
        map_text
    )
    assert "separate filesystem/storage authority gate" in map_text
    assert "Candidate files: future storage lifecycle module and storage tests, only" in (
        map_text
    )
    assert "after a separate filesystem/storage gate" in map_text
    assert "no filesystem reads or writes before that separate" in map_text
    assert "no package directories" in map_text
    assert "Filesystem access allowed: no until a separate filesystem/storage" in (
        map_text
    )

    assert "Filesystem writer authority boundaries" in spec_text
    assert "This contract does not approve filesystem reads or filesystem writes" in (
        spec_text
    )
    assert "A future writer may write only approved package artifacts" in spec_text
    assert "A future writer may write only to approved storage roots" in spec_text
    assert "and package paths" in spec_text
    assert "A future writer must not create package authority or package completeness" in (
        spec_text
    )
    assert "A future writer must not overwrite finalized evidence" in spec_text
    assert "A future writer must not mutate runtime state" in spec_text
    assert "A future writer must not call `main.py`" in spec_text
    assert "A future writer must not call broker/API/TWS/Alpaca/IBKR" in spec_text
    assert "execution permission, strategy promotion, or live trading authority" in (
        spec_text
    )

    assert FILESYSTEM_STORAGE_AUTHORITY_SCOPE_RELAXABLE_NAMES == (
        "STORAGE_ROOT",
        "PACKAGE_PATH",
        "PACKAGE_DIRECTORY",
        "FILESYSTEM_READ_AUTHORITY",
        "FILESYSTEM_WRITE_AUTHORITY",
        "STORAGE_WRITER_AUTHORITY",
        "PATH_RESOLVER_AUTHORITY",
        "PACKAGE_DIRECTORY_RESOLVER_AUTHORITY",
        "StorageRoot",
        "PackagePath",
        "PackageDirectory",
        "FilesystemReadAuthority",
        "FilesystemWriteAuthority",
        "StorageWriterAuthority",
        "PathResolverAuthority",
        "PackageDirectoryResolverAuthority",
    )
    assert not (
        set(FILESYSTEM_STORAGE_AUTHORITY_SCOPE_RELAXABLE_NAMES)
        & set(FILESYSTEM_STORAGE_AUTHORITY_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    filesystem_storage_authority_boundaries = (
        "filesystem_storage_authority_required_before_unit8_implementation",
        "filesystem_storage_authority_is_not_finalized_storage_implementation",
        "filesystem_storage_authority_is_not_package_completeness",
        "filesystem_storage_authority_is_not_evaluation_or_promotion",
        "path_authority_is_not_runtime_artifact_capture",
        "runtime_logs_require_later_runtime_capture_gate",
        "no_broker_api_authority",
        "no_execution_or_live_trading_authority",
    )
    assert filesystem_storage_authority_boundaries == (
        "filesystem_storage_authority_required_before_unit8_implementation",
        "filesystem_storage_authority_is_not_finalized_storage_implementation",
        "filesystem_storage_authority_is_not_package_completeness",
        "filesystem_storage_authority_is_not_evaluation_or_promotion",
        "path_authority_is_not_runtime_artifact_capture",
        "runtime_logs_require_later_runtime_capture_gate",
        "no_broker_api_authority",
        "no_execution_or_live_trading_authority",
    )

    filesystem_storage_stop_conditions = (
        "unknown_storage_root",
        "unapproved_storage_root",
        "unknown_package_path",
        "unapproved_package_path",
        "unknown_package_directory",
        "unapproved_package_directory",
        "attempted_overwrite",
        "path_traversal",
        "absolute_path_injection",
        "symlink_ambiguity",
        "non_repo_path_ambiguity",
        "mixed_run_id",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
        "broker_dependent_inputs",
    )
    assert filesystem_storage_stop_conditions == (
        "unknown_storage_root",
        "unapproved_storage_root",
        "unknown_package_path",
        "unapproved_package_path",
        "unknown_package_directory",
        "unapproved_package_directory",
        "attempted_overwrite",
        "path_traversal",
        "absolute_path_injection",
        "symlink_ambiguity",
        "non_repo_path_ambiguity",
        "mixed_run_id",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
        "broker_dependent_inputs",
    )

    for future_module in FUTURE_STORAGE_FINALIZATION_MODULES:
        assert not future_module.exists()

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
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["file_path_artifact_ingestion"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for denied_name in (
        "STORAGE_FINALIZATION",
        "FINALIZED_PACKAGE",
        "IMMUTABILITY_ENFORCEMENT",
        "PACKAGE_COMPLETENESS",
        "RUNTIME_CAPTURE",
        "EVALUATION_PROMOTION",
        "BROKER_API_AUTHORITY",
        "EXECUTION_PERMISSION",
        "LIVE_TRADING_AUTHORITY",
    ):
        assert denied_name in FILESYSTEM_STORAGE_AUTHORITY_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in FILESYSTEM_STORAGE_AUTHORITY_SCOPE_RELAXABLE_NAMES

    for module_path in (
        *REPLAY_SOURCE_MODULES,
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
        *FUTURE_HASH_COMPUTATION_MODULES,
        *FUTURE_INTEGRITY_VALIDATION_MODULES,
        PACKAGE_CREATION_MODULE,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in FILESYSTEM_STORAGE_AUTHORITY_SCOPE_DOWNSTREAM_DENIED_NAMES:
            assert denied_name not in module_text


def test_filesystem_storage_authority_helper_validates_metadata_only() -> None:
    assert FILESYSTEM_STORAGE_AUTHORITY_MODULE.exists()
    assert filesystem_storage_authority.STORAGE_ROOT == "storage_root_authority"
    assert filesystem_storage_authority.PACKAGE_PATH == "package_path_authority"
    assert (
        filesystem_storage_authority.PACKAGE_DIRECTORY
        == "package_directory_authority"
    )
    assert filesystem_storage_authority.FILESYSTEM_READ_AUTHORITY == (
        "filesystem_read_authority_metadata_only"
    )
    assert filesystem_storage_authority.FILESYSTEM_WRITE_AUTHORITY == (
        "filesystem_write_authority_metadata_only"
    )
    assert filesystem_storage_authority.STORAGE_WRITER_AUTHORITY == (
        "storage_writer_authority_metadata_only"
    )
    assert filesystem_storage_authority.PATH_RESOLVER_AUTHORITY == (
        "path_resolver_authority_metadata_only"
    )
    assert filesystem_storage_authority.PACKAGE_DIRECTORY_RESOLVER_AUTHORITY == (
        "package_directory_resolver_authority_metadata_only"
    )
    assert filesystem_storage_authority.FilesystemStorageAuthority().authority_boundary == (
        filesystem_storage_authority.FILESYSTEM_STORAGE_AUTHORITY_BOUNDARY
    )
    assert filesystem_storage_authority.FilesystemStorageAuthorityResult().result_type == (
        filesystem_storage_authority.FILESYSTEM_STORAGE_AUTHORITY_RESULT
    )

    authority_input = _filesystem_storage_authority_input()
    result = filesystem_storage_authority.validate_filesystem_storage_authority(
        authority_input
    )

    assert result == filesystem_storage_authority.resolve_package_path_authority(
        authority_input
    )
    assert result == filesystem_storage_authority.resolve_package_directory_authority(
        authority_input
    )
    assert result["result_type"] == (
        filesystem_storage_authority.FILESYSTEM_STORAGE_AUTHORITY_RESULT
    )
    assert result["canonical_run_id"] == "run_unit8_storage_authority"
    assert result["storage_root"] == "replay_packages"
    assert result["package_path"] == "replay_packages/run_unit8_storage_authority"
    assert result["package_directory"] == "run_unit8_storage_authority"
    assert result["filesystem_read_authority"] is True
    assert result["filesystem_write_authority"] is True
    assert result["storage_writer_authority"] is True
    assert result["path_resolver_authority"] is True
    assert result["package_directory_resolver_authority"] is True
    assert result["evidence_only"] is True
    assert result["non_authoritative"] is True
    assert result["actual_filesystem_reads"] is False
    assert result["actual_filesystem_writes"] is False
    assert result["package_directory_creation"] is False
    assert result["finalized_storage"] is False
    assert result["immutability_enforcement"] is False
    assert result["package_completeness"] is False
    assert result["runtime_capture"] is False
    assert result["evaluation_or_promotion"] is False
    assert result["broker_api_authority"] is False
    assert result["execution_authority"] is False
    assert result["live_trading_authority"] is False
    assert result["authority_boundary"] == (
        filesystem_storage_authority.FILESYSTEM_STORAGE_AUTHORITY_BOUNDARY
    )
    assert "no_actual_filesystem_reads" in result["authority_boundary"]
    assert "no_actual_filesystem_writes" in result["authority_boundary"]
    assert "no_package_directory_creation" in result["authority_boundary"]
    assert "no_finalized_storage" in result["authority_boundary"]
    assert "no_immutability_enforcement" in result["authority_boundary"]
    assert "no_package_completeness" in result["authority_boundary"]
    assert "no_runtime_capture" in result["authority_boundary"]
    assert "no_evaluation_or_promotion" in result["authority_boundary"]
    assert "no_broker_authority" in result["authority_boundary"]
    assert "no_execution_authority" in result["authority_boundary"]
    assert "no_live_trading_authority" in result["authority_boundary"]

    module_names = set(filesystem_storage_authority.__dict__)
    for relaxable_name in FILESYSTEM_STORAGE_AUTHORITY_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names
    for denied_name in (
        "StorageFinalization",
        "FinalizedPackage",
        "ImmutabilityEnforcement",
        "PackageCompleteness",
        "RuntimeCapture",
        "EvaluationEngine",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name not in module_names


def test_filesystem_storage_authority_helper_fails_closed() -> None:
    base_input = _filesystem_storage_authority_input()

    bad_cases = (
        ({**base_input, "storage_root": ""}, ValueError),
        ({**base_input, "storage_root": "other"}, ValueError),
        ({**base_input, "package_path": ""}, ValueError),
        ({**base_input, "package_path": "other"}, ValueError),
        ({**base_input, "package_directory": ""}, ValueError),
        ({**base_input, "package_directory": "other"}, ValueError),
        ({**base_input, "overwrite_attempt": True}, ValueError),
        ({**base_input, "package_path": "../escape"}, ValueError),
        ({**base_input, "package_path": "/tmp/package"}, ValueError),
        ({**base_input, "symlink_status": "unknown"}, ValueError),
        ({**base_input, "repo_relative": False}, ValueError),
        (
            {
                **base_input,
                "input_run_ids": ("run_unit8_storage_authority", "other"),
            },
            ValueError,
        ),
        ({**base_input, "provenance": ""}, ValueError),
        ({**base_input, "provenance": object()}, ValueError),
        ({**base_input, "redaction_status": ""}, ValueError),
        ({**base_input, "redaction_status": "unknown"}, ValueError),
        ({**base_input, "source_reference": "unknown"}, ValueError),
        ({**base_input, "sensitive_data_status": "exposed"}, ValueError),
        ({**base_input, "runtime_dependent": True}, ValueError),
        ({**base_input, "evaluation_dependent": True}, ValueError),
        ({**base_input, "broker_dependent": True}, ValueError),
        (object(), TypeError),
    )
    for bad_input, expected_error in bad_cases:
        with pytest.raises(expected_error):
            filesystem_storage_authority.validate_filesystem_storage_authority(
                bad_input
            )

    module_text = FILESYSTEM_STORAGE_AUTHORITY_MODULE.read_text(encoding="utf-8")
    assert "from pathlib" not in module_text
    assert "import os" not in module_text
    assert "open(" not in module_text
    assert ".read(" not in module_text
    assert ".write(" not in module_text
    assert "write_text(" not in module_text
    assert "write_bytes(" not in module_text
    assert "mkdir(" not in module_text


def test_storage_implementation_scope_guard_records_unit8_code_boundary() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")

    assert "## Unit 8: Storage Root/Path/Lifecycle/Finalization/Immutability" in (
        map_text
    )
    assert "future storage lifecycle module and storage tests" in map_text
    assert "Filesystem access allowed: no until a separate filesystem/storage" in (
        map_text
    )
    assert "storage output cannot create package completeness" in map_text
    assert "This contract does not approve filesystem reads or filesystem writes" in (
        spec_text
    )
    assert "No filesystem\npath, package directory, package file" in spec_text
    assert "finalized package\nstate, or immutable package marker is authoritative" in (
        spec_text
    )
    assert "No filesystem\npath, package directory, package file" in spec_text
    assert "Finalized evidence must be immutable and no-overwrite" in spec_text
    assert "Corrections, annotations, invalidations, supersessions" in spec_text
    assert "append-only and lineage-preserving" in spec_text
    assert "Immutable evidence must remain distinct from derived reports" in (
        spec_text
    )
    assert "A future writer must not create package authority or package completeness" in (
        spec_text
    )

    assert STORAGE_IMPLEMENTATION_SCOPE_RELAXABLE_NAMES == (
        "STORAGE_IMPLEMENTATION",
        "STORAGE_LIFECYCLE_IMPLEMENTATION",
        "DRAFT_STORAGE_RECORD",
        "FINALIZED_STORAGE_RECORD",
        "STORAGE_FINALIZATION_RESULT",
        "IMMUTABILITY_MARKER",
        "LINEAGE_REFERENCE",
        "INVALIDATION_REFERENCE",
        "SUPERSESSION_REFERENCE",
        "NO_OVERWRITE_ENFORCEMENT_VOCABULARY",
        "STORAGE_WRITER_METADATA_INPUT",
        "STORAGE_WRITER_METADATA_RESULT",
        "StorageImplementation",
        "StorageLifecycleImplementation",
        "DraftStorageRecord",
        "FinalizedStorageRecord",
        "StorageFinalizationResult",
        "ImmutabilityMarker",
        "LineageReference",
        "InvalidationReference",
        "SupersessionReference",
        "NoOverwriteEnforcementVocabulary",
        "StorageWriterMetadataInput",
        "StorageWriterMetadataResult",
    )
    assert not (
        set(STORAGE_IMPLEMENTATION_SCOPE_RELAXABLE_NAMES)
        & set(STORAGE_IMPLEMENTATION_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    implementation_scope_boundaries = (
        "unit8_storage_implementation_after_package_creation_and_storage_authority",
        "code_and_test_lane_required_before_behavior_exists",
        "storage_scope_is_not_actual_filesystem_io",
        "storage_scope_is_not_package_completeness",
        "storage_scope_is_not_runtime_capture",
        "storage_scope_is_not_evaluation_or_promotion",
        "metadata_authority_is_not_executable_filesystem_write",
    )
    assert implementation_scope_boundaries == (
        "unit8_storage_implementation_after_package_creation_and_storage_authority",
        "code_and_test_lane_required_before_behavior_exists",
        "storage_scope_is_not_actual_filesystem_io",
        "storage_scope_is_not_package_completeness",
        "storage_scope_is_not_runtime_capture",
        "storage_scope_is_not_evaluation_or_promotion",
        "metadata_authority_is_not_executable_filesystem_write",
    )

    lifecycle_finalization_boundaries = (
        "draft",
        "finalized",
        "invalidated",
        "superseded",
        "append_only_lineage",
        "correction_lineage",
        "invalidation_lineage",
        "supersession_lineage",
        "no_overwrite_finalized_evidence",
        "derived_reports_distinct_from_immutable_evidence",
    )
    assert lifecycle_finalization_boundaries == (
        "draft",
        "finalized",
        "invalidated",
        "superseded",
        "append_only_lineage",
        "correction_lineage",
        "invalidation_lineage",
        "supersession_lineage",
        "no_overwrite_finalized_evidence",
        "derived_reports_distinct_from_immutable_evidence",
    )

    storage_implementation_stop_conditions = (
        "missing_filesystem_storage_authority_result",
        "failed_filesystem_storage_authority_result",
        "missing_package_creation_result",
        "missing_package_identity",
        "missing_storage_root",
        "missing_package_path",
        "missing_package_directory",
        "unknown_storage_root",
        "unapproved_storage_root",
        "unknown_package_path",
        "unapproved_package_path",
        "unknown_package_directory",
        "unapproved_package_directory",
        "attempted_overwrite",
        "path_traversal",
        "absolute_path_injection",
        "symlink_ambiguity",
        "non_repo_path_ambiguity",
        "mixed_run_id",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
        "broker_dependent_inputs",
        "missing_package_completeness_authority",
        "storage_output_as_complete_replay_package_authority",
    )
    assert storage_implementation_stop_conditions == (
        "missing_filesystem_storage_authority_result",
        "failed_filesystem_storage_authority_result",
        "missing_package_creation_result",
        "missing_package_identity",
        "missing_storage_root",
        "missing_package_path",
        "missing_package_directory",
        "unknown_storage_root",
        "unapproved_storage_root",
        "unknown_package_path",
        "unapproved_package_path",
        "unknown_package_directory",
        "unapproved_package_directory",
        "attempted_overwrite",
        "path_traversal",
        "absolute_path_injection",
        "symlink_ambiguity",
        "non_repo_path_ambiguity",
        "mixed_run_id",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "unknown_source_references",
        "sensitive_data_exposure",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
        "broker_dependent_inputs",
        "missing_package_completeness_authority",
        "storage_output_as_complete_replay_package_authority",
    )

    for future_module in FUTURE_STORAGE_FINALIZATION_MODULES:
        assert not future_module.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["storage_finalization_immutability"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert mapper_package["immutability"]["status"] == "absent"
    assert mapper_package["immutability"]["reason"] == "deferred_until_storage_gate"
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for denied_name in (
        "ACTUAL_FILESYSTEM_READ",
        "ACTUAL_FILESYSTEM_WRITE",
        "PACKAGE_DIRECTORY_CREATION",
        "PACKAGE_COMPLETENESS",
        "RUNTIME_CAPTURE",
        "EVALUATION_PROMOTION",
        "BROKER_API_AUTHORITY",
        "EXECUTION_PERMISSION",
        "LIVE_TRADING_AUTHORITY",
    ):
        assert denied_name in STORAGE_IMPLEMENTATION_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in STORAGE_IMPLEMENTATION_SCOPE_RELAXABLE_NAMES

    for module_path in (
        *REPLAY_SOURCE_MODULES,
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
        *FUTURE_HASH_COMPUTATION_MODULES,
        *FUTURE_INTEGRITY_VALIDATION_MODULES,
        PACKAGE_CREATION_MODULE,
        FILESYSTEM_STORAGE_AUTHORITY_MODULE,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in STORAGE_IMPLEMENTATION_SCOPE_DOWNSTREAM_DENIED_NAMES:
            if denied_name in {"open", "read", "write", "write_text", "write_bytes", "mkdir"}:
                continue
            assert denied_name not in module_text


def test_storage_implementation_helper_builds_metadata_only_records() -> None:
    assert STORAGE_IMPLEMENTATION_MODULE.exists()
    assert (
        storage_implementation.STORAGE_IMPLEMENTATION
        == "storage_implementation_metadata_only"
    )
    assert storage_implementation.STORAGE_LIFECYCLE_STATES == (
        "draft",
        "finalized",
        "invalidated",
        "superseded",
    )
    assert storage_implementation.StorageImplementation().authority_boundary == (
        storage_implementation.STORAGE_IMPLEMENTATION_AUTHORITY_BOUNDARY
    )
    assert storage_implementation.StorageLifecycleImplementation().states == (
        storage_implementation.STORAGE_LIFECYCLE_STATES
    )
    assert storage_implementation.StorageWriterMetadataResult().result_type == (
        storage_implementation.STORAGE_WRITER_METADATA_RESULT
    )

    draft_record = storage_implementation.build_draft_storage_record(
        _storage_writer_metadata_input()
    )
    finalized_record = storage_implementation.build_finalized_storage_record(
        _storage_writer_metadata_input(lifecycle_status="finalized")
    )
    finalization_result = storage_implementation.build_storage_finalization_result(
        _storage_writer_metadata_input(lifecycle_status="finalized")
    )
    invalidated_record = storage_implementation.invalidate_storage_record(
        _storage_writer_metadata_input(lifecycle_status="invalidated")
    )
    superseded_record = storage_implementation.supersede_storage_record(
        _storage_writer_metadata_input(lifecycle_status="superseded")
    )

    assert draft_record["record_type"] == storage_implementation.DRAFT_STORAGE_RECORD
    assert draft_record["lifecycle_status"] == "draft"
    assert finalized_record["record_type"] == (
        storage_implementation.FINALIZED_STORAGE_RECORD
    )
    assert finalized_record["lifecycle_status"] == "finalized"
    assert finalization_result == finalized_record
    assert invalidated_record["record_type"] == (
        storage_implementation.INVALIDATION_REFERENCE
    )
    assert invalidated_record["lifecycle_status"] == "invalidated"
    assert invalidated_record["invalidation_lineage"] is True
    assert superseded_record["record_type"] == (
        storage_implementation.SUPERSESSION_REFERENCE
    )
    assert superseded_record["lifecycle_status"] == "superseded"
    assert superseded_record["supersession_lineage"] is True

    for record in (
        draft_record,
        finalized_record,
        finalization_result,
        invalidated_record,
        superseded_record,
    ):
        assert record["canonical_run_id"] == "run_unit11"
        assert record["result_type"] == (
            storage_implementation.STORAGE_WRITER_METADATA_RESULT
        )
        assert record["storage_root"] == "replay_packages"
        assert record["package_path"] == "replay_packages/run_unit11"
        assert record["package_directory"] == "run_unit11"
        assert record["immutability_marker"] == storage_implementation.IMMUTABILITY_MARKER
        assert record["lineage_reference"] == storage_implementation.LINEAGE_REFERENCE
        assert record["no_overwrite_rule"] == (
            storage_implementation.NO_OVERWRITE_ENFORCEMENT_VOCABULARY
        )
        assert record["append_only_lineage"] is True
        assert record["correction_lineage"] is True
        assert record["derived_reports_distinct_from_immutable_evidence"] is True
        assert record["evidence_only"] is True
        assert record["non_authoritative"] is True
        assert record["actual_filesystem_reads"] is False
        assert record["actual_filesystem_writes"] is False
        assert record["package_directory_creation"] is False
        assert record["package_completeness"] is False
        assert record["runtime_capture"] is False
        assert record["evaluation_or_promotion"] is False
        assert record["broker_api_authority"] is False
        assert record["execution_authority"] is False
        assert record["live_trading_authority"] is False
        assert record["authority_boundary"] == (
            storage_implementation.STORAGE_IMPLEMENTATION_AUTHORITY_BOUNDARY
        )
        assert "no_actual_filesystem_reads" in record["authority_boundary"]
        assert "no_actual_filesystem_writes" in record["authority_boundary"]
        assert "no_package_directory_creation" in record["authority_boundary"]
        assert "no_package_completeness" in record["authority_boundary"]
        assert "no_runtime_capture" in record["authority_boundary"]
        assert "no_evaluation_or_promotion" in record["authority_boundary"]
        assert "no_broker_authority" in record["authority_boundary"]
        assert "no_execution_authority" in record["authority_boundary"]
        assert "no_live_trading_authority" in record["authority_boundary"]

    module_names = set(storage_implementation.__dict__)
    for relaxable_name in STORAGE_IMPLEMENTATION_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names
    for denied_name in (
        "ActualFilesystemRead",
        "ActualFilesystemWrite",
        "PackageDirectoryCreation",
        "PackageCompleteness",
        "RuntimeCapture",
        "EvaluationEngine",
        "PromotionGate",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name not in module_names


def test_storage_implementation_helper_fails_closed() -> None:
    base_input = _storage_writer_metadata_input()

    bad_cases = (
        ({**base_input, "filesystem_storage_authority_result": {}}, ValueError),
        (
            {
                **base_input,
                "filesystem_storage_authority_result": {
                    **base_input["filesystem_storage_authority_result"],
                    "evidence_only": False,
                },
            },
            ValueError,
        ),
        (
            {
                **base_input,
                "filesystem_storage_authority_result": {
                    **base_input["filesystem_storage_authority_result"],
                    "actual_filesystem_writes": True,
                },
            },
            ValueError,
        ),
        ({**base_input, "package_creation_result": {}}, ValueError),
        (
            {
                **base_input,
                "package_creation_result": {
                    **base_input["package_creation_result"],
                    "package_completeness": True,
                },
            },
            ValueError,
        ),
        ({**base_input, "package_identity": {}}, ValueError),
        ({**base_input, "canonical_run_id": ""}, ValueError),
        ({**base_input, "storage_root": ""}, ValueError),
        ({**base_input, "storage_root": "other"}, ValueError),
        ({**base_input, "package_path": ""}, ValueError),
        ({**base_input, "package_path": "other"}, ValueError),
        ({**base_input, "package_directory": ""}, ValueError),
        ({**base_input, "package_directory": "other"}, ValueError),
        ({**base_input, "lifecycle_status": "unknown"}, ValueError),
        ({**base_input, "overwrite_attempt": True}, ValueError),
        ({**base_input, "package_path": "../escape"}, ValueError),
        ({**base_input, "package_path": "/tmp/package"}, ValueError),
        ({**base_input, "symlink_status": "unknown"}, ValueError),
        ({**base_input, "repo_relative": False}, ValueError),
        (
            {
                **base_input,
                "input_run_ids": ("run_unit11", "other"),
            },
            ValueError,
        ),
        ({**base_input, "provenance": ""}, ValueError),
        ({**base_input, "provenance": object()}, ValueError),
        ({**base_input, "redaction_status": ""}, ValueError),
        ({**base_input, "redaction_status": "unknown"}, ValueError),
        ({**base_input, "source_reference": "unknown"}, ValueError),
        ({**base_input, "sensitive_data_status": "exposed"}, ValueError),
        ({**base_input, "runtime_dependent": True}, ValueError),
        ({**base_input, "evaluation_dependent": True}, ValueError),
        ({**base_input, "broker_dependent": True}, ValueError),
        ({**base_input, "package_completeness_authority": True}, ValueError),
        (
            {**base_input, "attempted_complete_replay_package_authority": True},
            ValueError,
        ),
        (object(), TypeError),
    )
    for bad_input, expected_error in bad_cases:
        with pytest.raises(expected_error):
            storage_implementation.build_draft_storage_record(bad_input)

    lifecycle_mismatch_cases = (
        (
            storage_implementation.build_draft_storage_record,
            {**base_input, "lifecycle_status": "finalized"},
        ),
        (
            storage_implementation.build_finalized_storage_record,
            {**base_input, "lifecycle_status": "draft"},
        ),
        (
            storage_implementation.invalidate_storage_record,
            {**base_input, "lifecycle_status": "draft"},
        ),
        (
            storage_implementation.supersede_storage_record,
            {**base_input, "lifecycle_status": "draft"},
        ),
    )
    for builder, bad_input in lifecycle_mismatch_cases:
        with pytest.raises(ValueError):
            builder(bad_input)

    module_text = STORAGE_IMPLEMENTATION_MODULE.read_text(encoding="utf-8")
    assert "from pathlib" not in module_text
    assert "import os" not in module_text
    assert "open(" not in module_text
    assert ".read(" not in module_text
    assert ".write(" not in module_text
    assert "write_text(" not in module_text
    assert "write_bytes(" not in module_text
    assert "mkdir(" not in module_text
    assert "PackageCompleteness" not in module_text
    assert "RuntimeCapture" not in module_text
    assert "EvaluationEngine" not in module_text
    assert "BrokerAuthority" not in module_text
    assert "ExecutionPermission" not in module_text
    assert "LiveTradingAuthority" not in module_text


def test_package_completeness_scope_guard_records_boundary_only() -> None:
    map_text = IMPLEMENTATION_PREREQUISITE_MAP.read_text(encoding="utf-8")
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    architecture_text = EVALUATION_INFRASTRUCTURE_ARCHITECTURE.read_text(
        encoding="utf-8"
    )

    assert "Mapper completeness is not equivalent to a complete replay package" in (
        spec_text
    )
    assert "Future complete replay packages still require implemented section schemas" in (
        spec_text
    )
    assert "remain separate from mapper completeness" in spec_text
    assert "cannot\nbe treated as complete replay package authority" in spec_text
    assert "Package hash must not imply package completeness unless package completeness" in (
        spec_text
    )
    assert "storage output cannot create package completeness" in map_text
    assert "Trusted scoring requires complete replay package authority" in (
        architecture_text
    )
    assert "Missing complete replay package authority for trusted scoring" in (
        architecture_text
    )

    assert PACKAGE_COMPLETENESS_SCOPE_RELAXABLE_NAMES == (
        "PACKAGE_COMPLETENESS",
        "COMPLETE_REPLAY_PACKAGE",
        "PACKAGE_COMPLETENESS_AUTHORITY",
        "PACKAGE_COMPLETENESS_RESULT",
        "PACKAGE_COMPLETENESS_VALIDATION",
        "COMPLETE_PACKAGE_EVIDENCE",
        "COMPLETE_PACKAGE_ELIGIBILITY",
        "COMPLETE_REPLAY_PACKAGE_AUTHORITY",
        "COMPLETENESS_MANIFEST_CHECK",
        "COMPLETENESS_HASH_CHECK",
        "COMPLETENESS_INTEGRITY_CHECK",
        "COMPLETENESS_STORAGE_CHECK",
        "COMPLETENESS_PROVENANCE_CHECK",
        "COMPLETENESS_REDACTION_CHECK",
        "COMPLETENESS_SOURCE_REFERENCE_CHECK",
        "PackageCompleteness",
        "CompleteReplayPackage",
        "PackageCompletenessAuthority",
        "PackageCompletenessResult",
        "PackageCompletenessValidation",
        "CompletePackageEvidence",
        "CompletePackageEligibility",
        "CompleteReplayPackageAuthority",
        "CompletenessManifestCheck",
        "CompletenessHashCheck",
        "CompletenessIntegrityCheck",
        "CompletenessStorageCheck",
        "CompletenessProvenanceCheck",
        "CompletenessRedactionCheck",
        "CompletenessSourceReferenceCheck",
    )
    assert not (
        set(PACKAGE_COMPLETENESS_SCOPE_RELAXABLE_NAMES)
        & set(PACKAGE_COMPLETENESS_SCOPE_DOWNSTREAM_DENIED_NAMES)
    )

    completeness_scope_boundaries = (
        "package_completeness_after_package_creation_storage_authority_and_storage",
        "code_and_test_lane_required_before_behavior_exists",
        "mapper_scaffold_completeness_is_not_complete_replay_package_authority",
        "draft_package_creation_is_not_package_completeness",
        "storage_finalization_metadata_is_not_package_completeness",
        "package_completeness_is_not_actual_filesystem_writer_authority",
        "package_completeness_is_not_runtime_capture",
        "package_completeness_is_not_evaluation_or_promotion",
        "complete_replay_package_authority_is_not_runtime_broker_or_live_authority",
    )
    assert completeness_scope_boundaries == (
        "package_completeness_after_package_creation_storage_authority_and_storage",
        "code_and_test_lane_required_before_behavior_exists",
        "mapper_scaffold_completeness_is_not_complete_replay_package_authority",
        "draft_package_creation_is_not_package_completeness",
        "storage_finalization_metadata_is_not_package_completeness",
        "package_completeness_is_not_actual_filesystem_writer_authority",
        "package_completeness_is_not_runtime_capture",
        "package_completeness_is_not_evaluation_or_promotion",
        "complete_replay_package_authority_is_not_runtime_broker_or_live_authority",
    )

    completeness_prerequisites = (
        "canonical_run_id_alignment",
        "package_identity_present",
        "draft_package_creation_result_present",
        "manifest_present",
        "canonical_bytes_present",
        "hash_records_present",
        "integrity_validation_result_present_and_valid",
        "storage_implementation_result_present",
        "storage_lifecycle_state_acceptable_for_completeness_review",
        "provenance_present_and_valid",
        "redaction_status_present_and_valid",
        "source_references_present_and_known",
        "no_sensitive_data_exposure",
        "no_stale_inputs",
        "no_mixed_run_id_evidence",
        "no_malformed_package_evidence",
    )
    assert completeness_prerequisites == (
        "canonical_run_id_alignment",
        "package_identity_present",
        "draft_package_creation_result_present",
        "manifest_present",
        "canonical_bytes_present",
        "hash_records_present",
        "integrity_validation_result_present_and_valid",
        "storage_implementation_result_present",
        "storage_lifecycle_state_acceptable_for_completeness_review",
        "provenance_present_and_valid",
        "redaction_status_present_and_valid",
        "source_references_present_and_known",
        "no_sensitive_data_exposure",
        "no_stale_inputs",
        "no_mixed_run_id_evidence",
        "no_malformed_package_evidence",
    )

    completeness_stop_conditions = (
        "missing_package_identity",
        "missing_package_creation_result",
        "missing_manifest",
        "missing_canonical_bytes",
        "missing_hash_records",
        "missing_integrity_validation_result",
        "failed_integrity_validation_result",
        "missing_storage_implementation_result",
        "failed_storage_implementation_result",
        "missing_storage_lifecycle_state",
        "invalid_storage_lifecycle_state",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "missing_source_references",
        "unknown_source_references",
        "sensitive_data_exposure",
        "stale_inputs",
        "malformed_inputs",
        "mixed_run_id",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
        "broker_dependent_inputs",
        "actual_filesystem_writer_dependency_before_explicit_writer_authority",
        "package_completeness_as_evaluation_approval",
        "package_completeness_as_execution_permission",
        "package_completeness_as_live_trading_authority",
    )
    assert completeness_stop_conditions == (
        "missing_package_identity",
        "missing_package_creation_result",
        "missing_manifest",
        "missing_canonical_bytes",
        "missing_hash_records",
        "missing_integrity_validation_result",
        "failed_integrity_validation_result",
        "missing_storage_implementation_result",
        "failed_storage_implementation_result",
        "missing_storage_lifecycle_state",
        "invalid_storage_lifecycle_state",
        "missing_provenance",
        "malformed_provenance",
        "missing_redaction_status",
        "invalid_redaction_status",
        "missing_source_references",
        "unknown_source_references",
        "sensitive_data_exposure",
        "stale_inputs",
        "malformed_inputs",
        "mixed_run_id",
        "runtime_dependent_inputs",
        "evaluation_dependent_inputs",
        "broker_dependent_inputs",
        "actual_filesystem_writer_dependency_before_explicit_writer_authority",
        "package_completeness_as_evaluation_approval",
        "package_completeness_as_execution_permission",
        "package_completeness_as_live_trading_authority",
    )

    assert PACKAGE_COMPLETENESS_MODULE.exists()

    complete_inputs_envelope = build_draft_replay_envelope(
        ReplayInputBundle(**_complete_replay_inputs())
    )
    mapper_package = complete_inputs_envelope["mapper_package"]

    assert mapper_package["package_status"]["status"] == "complete"
    assert complete_inputs_envelope["complete_replay_package_authority"] is False
    assert complete_inputs_envelope["filesystem_writes"] is False
    assert complete_inputs_envelope["package_directory_creation"] is False
    assert complete_inputs_envelope["runtime_capture"] is False
    assert complete_inputs_envelope["evaluation_or_promotion"] is False
    assert complete_inputs_envelope["broker_api_authority"] is False
    assert mapper_package["authority_boundary"]["evidence_only"] is True
    assert mapper_package["authority_boundary"]["non_authoritative"] is True
    assert mapper_package["authority_boundary"]["no_runtime_mutation"] is True
    assert mapper_package["authority_boundary"]["no_execution_authority"] is True
    assert mapper_package["authority_boundary"]["no_broker_authority"] is True
    assert mapper_package["out_of_scope"]["artifact_writer"] is True
    assert mapper_package["out_of_scope"]["runtime_capture"] is True
    assert mapper_package["out_of_scope"]["storage"] is True
    assert mapper_package["out_of_scope"]["broker_live_api_work"] is True
    assert mapper_package["out_of_scope"]["replay_based_promotion_decisions"] is True

    for denied_name in (
        "PACKAGE_COMPLETENESS_IMPLEMENTATION",
        "ACTUAL_FILESYSTEM_READ",
        "ACTUAL_FILESYSTEM_WRITE",
        "PACKAGE_DIRECTORY_CREATION",
        "RUNTIME_CAPTURE",
        "EVALUATION_PROMOTION",
        "BROKER_API_AUTHORITY",
        "EXECUTION_PERMISSION",
        "LIVE_TRADING_AUTHORITY",
    ):
        assert denied_name in PACKAGE_COMPLETENESS_SCOPE_DOWNSTREAM_DENIED_NAMES
        assert denied_name not in PACKAGE_COMPLETENESS_SCOPE_RELAXABLE_NAMES


def test_package_completeness_helper_validates_in_memory_evidence_only() -> None:
    assert package_completeness.PackageCompleteness().authority_boundary == (
        package_completeness.PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY
    )
    assert package_completeness.PackageCompletenessResult().result_type == (
        package_completeness.PACKAGE_COMPLETENESS_RESULT
    )
    assert package_completeness.CompletePackageEligibility().prerequisites == (
        package_completeness.PACKAGE_COMPLETENESS_PREREQUISITES
    )
    assert package_completeness.ACCEPTABLE_COMPLETENESS_LIFECYCLE_STATES == (
        "finalized",
    )

    evidence = _package_completeness_evidence()
    result = package_completeness.validate_package_completeness(evidence)

    assert result == package_completeness.build_package_completeness_result(evidence)
    assert result == package_completeness.assert_package_complete(evidence)
    assert result["result_type"] == package_completeness.PACKAGE_COMPLETENESS_RESULT
    assert result["validation_type"] == (
        package_completeness.PACKAGE_COMPLETENESS_VALIDATION
    )
    assert result["canonical_run_id"] == "run_unit11"
    assert result["package_identity"]["package_id"] == "package_run_unit11"
    assert result["package_creation_result"]["package_completeness"] is False
    assert result["storage_implementation_result"]["package_completeness"] is False
    assert result["storage_lifecycle_state"] == "finalized"
    assert result["package_completeness"] is True
    assert result["package_completeness_authority"] is True
    assert result["complete_replay_package_authority"] is True
    assert result["evidence_only"] is True
    assert (
        result["non_authoritative_beyond_package_completeness_metadata"] is True
    )
    assert result["actual_filesystem_reads"] is False
    assert result["actual_filesystem_writes"] is False
    assert result["package_directory_creation"] is False
    assert result["runtime_capture"] is False
    assert result["evaluation_or_promotion"] is False
    assert result["broker_api_authority"] is False
    assert result["execution_authority"] is False
    assert result["live_trading_authority"] is False
    assert result["prerequisites"] == (
        package_completeness.PACKAGE_COMPLETENESS_PREREQUISITES
    )
    assert result["fail_closed_boundaries"] == (
        package_completeness.PACKAGE_COMPLETENESS_FAIL_CLOSED_BOUNDARIES
    )
    assert result["authority_boundary"] == (
        package_completeness.PACKAGE_COMPLETENESS_AUTHORITY_BOUNDARY
    )
    assert "no_actual_filesystem_reads" in result["authority_boundary"]
    assert "no_actual_filesystem_writes" in result["authority_boundary"]
    assert "no_package_directory_creation" in result["authority_boundary"]
    assert "no_runtime_capture" in result["authority_boundary"]
    assert "no_evaluation_or_promotion" in result["authority_boundary"]
    assert "no_broker_api_authority" in result["authority_boundary"]
    assert "no_execution_authority" in result["authority_boundary"]
    assert "no_live_trading_authority" in result["authority_boundary"]

    module_names = set(package_completeness.__dict__)
    for relaxable_name in PACKAGE_COMPLETENESS_SCOPE_RELAXABLE_NAMES:
        assert relaxable_name in module_names
    for denied_name in (
        "ActualFilesystemRead",
        "ActualFilesystemWrite",
        "PackageDirectoryCreation",
        "RuntimeCapture",
        "EvaluationEngine",
        "PromotionGate",
        "BrokerAuthority",
        "ExecutionPermission",
        "LiveTradingAuthority",
    ):
        assert denied_name not in module_names


def test_package_completeness_helper_fails_closed() -> None:
    base_evidence = _package_completeness_evidence()

    bad_cases = (
        ({**base_evidence, "package_identity": {}}, ValueError),
        ({**base_evidence, "package_creation_result": {}}, ValueError),
        ({**base_evidence, "manifest": {}}, ValueError),
        ({**base_evidence, "canonical_bytes": b""}, ValueError),
        ({**base_evidence, "hash_records": ()}, ValueError),
        ({**base_evidence, "integrity_validation_result": {}}, ValueError),
        (
            {
                **base_evidence,
                "integrity_validation_result": {
                    **base_evidence["integrity_validation_result"],
                    "integrity_status": "mismatch",
                },
            },
            ValueError,
        ),
        ({**base_evidence, "storage_implementation_result": {}}, ValueError),
        (
            {
                **base_evidence,
                "storage_implementation_result": {
                    **base_evidence["storage_implementation_result"],
                    "evidence_only": False,
                },
            },
            ValueError,
        ),
        ({**base_evidence, "storage_lifecycle_state": ""}, ValueError),
        ({**base_evidence, "storage_lifecycle_state": "unknown"}, ValueError),
        ({**base_evidence, "storage_lifecycle_state": "draft"}, ValueError),
        ({**base_evidence, "provenance": ""}, ValueError),
        ({**base_evidence, "provenance": object()}, ValueError),
        ({**base_evidence, "redaction_status": ""}, ValueError),
        ({**base_evidence, "redaction_status": "unknown"}, ValueError),
        ({**base_evidence, "source_references": ()}, ValueError),
        ({**base_evidence, "source_references": ("unknown",)}, ValueError),
        ({**base_evidence, "sensitive_data_status": "exposed"}, ValueError),
        ({**base_evidence, "stale_input": True}, ValueError),
        ({**base_evidence, "malformed_input": True}, ValueError),
        ({**base_evidence, "input_run_ids": ("run_unit11", "other")}, ValueError),
        ({**base_evidence, "runtime_dependent": True}, ValueError),
        ({**base_evidence, "evaluation_dependent": True}, ValueError),
        ({**base_evidence, "broker_dependent": True}, ValueError),
        ({**base_evidence, "filesystem_writer_dependent": True}, ValueError),
        ({**base_evidence, "attempted_evaluation_approval": True}, ValueError),
        ({**base_evidence, "attempted_execution_permission": True}, ValueError),
        ({**base_evidence, "attempted_live_trading_authority": True}, ValueError),
        (object(), TypeError),
    )
    for bad_evidence, expected_error in bad_cases:
        with pytest.raises(expected_error):
            package_completeness.validate_package_completeness(bad_evidence)

    module_text = PACKAGE_COMPLETENESS_MODULE.read_text(encoding="utf-8")
    assert "from pathlib" not in module_text
    assert "import os" not in module_text
    assert "open(" not in module_text
    assert ".read(" not in module_text
    assert ".write(" not in module_text
    assert "write_text(" not in module_text
    assert "write_bytes(" not in module_text
    assert "mkdir(" not in module_text
    assert "RuntimeCapture" not in module_text
    assert "EvaluationEngine" not in module_text
    assert "BrokerAuthority" not in module_text
    assert "ExecutionPermission" not in module_text
    assert "LiveTradingAuthority" not in module_text

    for module_path in (
        *REPLAY_SOURCE_MODULES,
        CANONICAL_JSON_MODULE,
        CANONICAL_BYTES_MODULE,
        *FUTURE_HASHING_INTEGRITY_MODULES,
        *FUTURE_MANIFEST_GENERATION_MODULES,
        *FUTURE_HASH_COMPUTATION_MODULES,
        *FUTURE_INTEGRITY_VALIDATION_MODULES,
        PACKAGE_CREATION_MODULE,
        FILESYSTEM_STORAGE_AUTHORITY_MODULE,
        STORAGE_IMPLEMENTATION_MODULE,
    ):
        module_text = module_path.read_text(encoding="utf-8")
        for denied_name in (
            "PACKAGE_COMPLETENESS_IMPLEMENTATION",
            "validate_package_completeness",
            "assert_package_complete",
            "RuntimeCapture",
            "EvaluationEngine",
            "PromotionGate",
            "BrokerAuthority",
            "ExecutionPermission",
            "LiveTradingAuthority",
        ):
            assert denied_name not in module_text


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
