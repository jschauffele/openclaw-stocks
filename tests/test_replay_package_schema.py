from __future__ import annotations

from dataclasses import is_dataclass

from tools.replay.package_schema import (
    AUTHORITY_BOUNDARY,
    ENVELOPE_SECTIONS,
    OUT_OF_SCOPE,
    ReplayInputBundle,
    absent_section,
    present_section,
)


def test_envelope_sections_match_documented_top_level_order() -> None:
    assert ENVELOPE_SECTIONS == (
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
        "out_of_scope",
    )


def test_authority_boundary_contains_required_non_authority_fields() -> None:
    assert AUTHORITY_BOUNDARY == {
        "evidence_only": True,
        "non_authoritative": True,
        "no_runtime_mutation": True,
        "no_execution_authority": True,
        "no_broker_authority": True,
        "no_strategy_behavior_change": True,
        "no_secret_material": True,
    }


def test_schema_records_out_of_scope_runtime_and_writer_work() -> None:
    assert OUT_OF_SCOPE["file_path_artifact_ingestion"] is True
    assert OUT_OF_SCOPE["artifact_writer"] is True
    assert OUT_OF_SCOPE["storage"] is True
    assert OUT_OF_SCOPE["hashing_integrity_enforcement"] is True
    assert OUT_OF_SCOPE["runtime_capture"] is True
    assert OUT_OF_SCOPE["runtime_integration"] is True
    assert OUT_OF_SCOPE["broker_live_api_work"] is True
    assert OUT_OF_SCOPE["alpaca_calls"] is True
    assert OUT_OF_SCOPE["ibkr_tws_work"] is True
    assert OUT_OF_SCOPE["credential_or_env_handling"] is True
    assert OUT_OF_SCOPE["replay_based_promotion_decisions"] is True


def test_replay_schema_remains_scaffold_only_and_non_authoritative() -> None:
    assert AUTHORITY_BOUNDARY["evidence_only"] is True
    assert AUTHORITY_BOUNDARY["non_authoritative"] is True
    assert AUTHORITY_BOUNDARY["no_runtime_mutation"] is True
    assert AUTHORITY_BOUNDARY["no_execution_authority"] is True
    assert AUTHORITY_BOUNDARY["no_broker_authority"] is True
    assert AUTHORITY_BOUNDARY["no_strategy_behavior_change"] is True
    assert OUT_OF_SCOPE["artifact_writer"] is True
    assert OUT_OF_SCOPE["runtime_capture"] is True
    assert OUT_OF_SCOPE["storage"] is True
    assert OUT_OF_SCOPE["hashing_integrity_enforcement"] is True
    assert OUT_OF_SCOPE["replay_based_promotion_decisions"] is True


def test_replay_input_bundle_is_plain_dataclass() -> None:
    assert is_dataclass(ReplayInputBundle)
    bundle = ReplayInputBundle(events=[{"run_id": "run_1"}])

    assert bundle.events == [{"run_id": "run_1"}]
    assert bundle.run_report is None
    assert bundle.observations is None
    assert bundle.order_state is None
    assert bundle.runtime_visibility is None


def test_section_helpers_mark_presence_without_generating_facts() -> None:
    assert absent_section() == {"status": "absent", "reason": "not_supplied"}
    assert present_section(reference={"run_id": "run_1"}) == {
        "status": "present",
        "reference": {"run_id": "run_1"},
    }
