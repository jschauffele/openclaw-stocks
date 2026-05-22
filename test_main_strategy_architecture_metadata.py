from __future__ import annotations

import inspect

import pytest

import main
import reporting


pytestmark = pytest.mark.xfail(
    reason="Future report-only strategy_architecture metadata integration is not implemented yet.",
    strict=False,
)


def _main_source() -> str:
    return inspect.getsource(main)


def _reporting_source() -> str:
    return inspect.getsource(reporting)


def test_main_success_path_assembles_strategy_architecture_before_persist_report() -> None:
    source = _main_source()

    assert "build_orchestration_strategy_architecture_payload" in source
    assert '"strategy_architecture"' in source
    assert source.index("build_orchestration_strategy_architecture_payload") < source.index(
        "persist_report("
    )


def test_metadata_assembly_failure_omits_strategy_architecture_and_still_persists_report() -> None:
    source = _main_source()

    assert "except ValueError" in source
    assert '"strategy_architecture"' in source
    assert "persist_report(" in source
    assert "strategy_architecture_metadata_failed" not in source


def test_metadata_assembly_failure_does_not_change_runtime_decision_fields() -> None:
    source = _main_source()

    assert "metadata assembly" in source
    assert "action_proposal" in source
    assert "risk_check(" in source
    assert "submit_market_order(" in source
    assert "result=" in source
    assert "reason=" in source


def test_metadata_assembly_does_not_alter_append_observation_behavior() -> None:
    source = _main_source()

    assert "build_orchestration_strategy_architecture_payload" in source
    assert "append_observation(" in source
    assert "strategy_architecture" not in source[
        source.index("def log_observation") : source.index("if not action_proposal")
    ]


def test_metadata_success_does_not_emit_strategy_architecture_to_jsonl_events() -> None:
    source = _main_source()

    assert "build_orchestration_strategy_architecture_payload" in source
    assert "log_event(" in source
    assert "strategy_architecture" not in source[
        source.index("log_event(") : source.rindex("logging.info")
    ]


def test_reporting_remains_passthrough_only_and_does_not_import_metadata_builders() -> None:
    source = _reporting_source()

    assert "orchestration" in source
    assert "runtime_strategy_seam" not in source
    assert "runtime_strategy_metadata_adapter" not in source
    assert "runtime_strategy_report_metadata" not in source
    assert "build_runtime_strategy_metadata" not in source
    assert "build_strategy_architecture_metadata" not in source
    assert "build_orchestration_strategy_architecture_payload" not in source


def test_metadata_chain_is_called_outside_reporting_in_required_order() -> None:
    main_source = _main_source()
    reporting_source = _reporting_source()

    assert "build_runtime_strategy_metadata" not in reporting_source
    assert "build_strategy_architecture_metadata" not in reporting_source
    assert "build_orchestration_strategy_architecture_payload" not in reporting_source
    assert main_source.index("build_runtime_strategy_metadata") < main_source.index(
        "build_strategy_architecture_metadata"
    )
    assert main_source.index("build_strategy_architecture_metadata") < main_source.index(
        "build_orchestration_strategy_architecture_payload"
    )


def test_metadata_assembly_uses_already_fetched_closes_without_fetching_market_data_again() -> None:
    source = _main_source()

    assert "build_runtime_strategy_metadata" in source
    assert "RuntimeStrategySeamInput(closes=tuple(closes)" in source
    assert source.count("get_historical_bars(") == 1
