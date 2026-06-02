from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType

import tools.replay.draft_envelope as draft_envelope
import tools.replay.offline_mapper as offline_mapper
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
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "manifest_schema.py",
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
FUTURE_DETERMINISTIC_SERIALIZATION_MODULES = (
    (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "replay"
        / "serialization_constants.py"
    ),
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "canonical_json.py",
    Path(__file__).resolve().parents[1] / "tools" / "replay" / "canonical_bytes.py",
)
REPLAY_PACKAGE_SPECIFICATION = (
    Path(__file__).resolve().parents[1] / "docs" / "replay_package_specification.md"
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
    "PACKAGE_ROOT",
    "PACKAGE_DIR",
    "PACKAGE_DIRECTORY",
    "FINALIZATION_STATE",
    "IMMUTABILITY_MARKER",
    "RETENTION_INDEX",
    "DISCOVERY_INDEX",
    "build_storage_path",
    "build_package_directory",
    "write_replay_package",
    "write_package_file",
    "finalize_replay_package",
    "mark_package_finalized",
    "enforce_immutability",
    "validate_storage_integrity",
    "build_retention_index",
    "build_discovery_index",
    "StorageWriter",
    "ReplayPackageWriter",
    "FinalizationState",
    "ImmutabilityEnforcer",
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
    "RUNTIME_CAPTURE_ROOT",
    "RUNTIME_CAPTURE_PATH",
    "RUNTIME_ARTIFACT_PATH",
    "SOURCE_ARTIFACT_PATH",
    "SOURCE_REFERENCE",
    "CAPTURE_SOURCE",
    "CAPTURED_ARTIFACT",
    "JSONL_CAPTURE",
    "LAST_RUN_REPORT_CAPTURE",
    "OBSERVATION_CAPTURE",
    "RUNTIME_VISIBILITY_CAPTURE",
    "build_runtime_capture",
    "capture_runtime_artifacts",
    "capture_jsonl_event_stream",
    "capture_last_run_report",
    "capture_observations",
    "capture_runtime_visibility",
    "ingest_runtime_file",
    "ingest_source_path",
    "read_runtime_artifact",
    "read_runtime_file",
    "build_capture_manifest",
    "RuntimeCapture",
    "RuntimeCaptureResult",
    "RuntimeArtifactCapture",
    "RuntimeCaptureSource",
    "RuntimeCaptureWriter",
    "SourcePathIngestion",
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


def test_manifest_schema_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert "## Manifest Schema Authority Contract" in spec_text
    assert "governance-only and is not implemented yet" in spec_text
    assert "does not approve tests, code, manifest constants" in spec_text
    assert "must remain separate from manifest generation" in spec_text
    assert "remain separate from mapper completeness" in spec_text
    assert "package_status == \"complete\"" in spec_text
    assert "only in-memory bucket completeness" in spec_text

    for module_path in FUTURE_MANIFEST_SCHEMA_MODULES:
        assert not module_path.exists()

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


def test_storage_immutability_boundary_remains_unimplemented() -> None:
    spec_text = REPLAY_PACKAGE_SPECIFICATION.read_text(encoding="utf-8")
    assert (
        "## Storage, Finalization, and Immutability Authority Contract"
        in spec_text
    )
    assert "governance-only and\nis not implemented yet" in spec_text

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
        "package_root",
        "package_dir",
        "package_directory",
        "finalization_state",
        "immutability_marker",
        "retention_index",
        "discovery_index",
        "storage_authority",
        "finalization_authority",
        "immutability_authority",
        "retention_authority",
        "discovery_authority",
        "index_authority",
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
        "runtime_artifact_ingestion",
        "source_path_ingestion",
        "source_artifact_path",
        "runtime_artifact_path",
        "capture_manifest",
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
