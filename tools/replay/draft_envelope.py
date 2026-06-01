"""Pure in-memory draft replay envelope builder."""

from __future__ import annotations

from typing import Any

from tools.replay.offline_mapper import build_replay_package
from tools.replay.package_schema import ReplayInputBundle


def build_draft_replay_envelope(
    source: dict[str, Any] | ReplayInputBundle,
) -> dict[str, Any]:
    """Build a non-authoritative draft envelope from already-loaded inputs."""

    if isinstance(source, ReplayInputBundle):
        loaded_inputs = {
            "events": source.events,
            "run_report": source.run_report,
            "observations": source.observations,
            "order_state": source.order_state,
            "runtime_visibility": source.runtime_visibility,
        }
    elif isinstance(source, dict):
        loaded_inputs = source
    else:
        raise TypeError("draft envelope scaffold accepts loaded replay inputs only")

    package = build_replay_package(**loaded_inputs)
    return {
        "lifecycle_status": "draft",
        "evidence_only": True,
        "non_authoritative": True,
        "complete_replay_package_authority": False,
        "writer_authority": False,
        "filesystem_writes": False,
        "package_directory_creation": False,
        "file_path_ingestion": False,
        "manifest_creation": False,
        "hashing_integrity_enforcement": False,
        "runtime_capture": False,
        "storage_finalization_immutability": False,
        "evaluation_or_promotion": False,
        "broker_api_authority": False,
        "canonical_chronology": "event_jsonl",
        "mapper_package": package,
    }
