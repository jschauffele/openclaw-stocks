from __future__ import annotations

import json
import subprocess
import sys

import pytest

from strategy_library import (
    StrategyDefinition,
    _build_strategy_catalog,
    build_default_strategy_catalog,
    get_strategy_definition,
    list_strategy_definitions,
)


FORBIDDEN_MODULES = (
    "main",
    "config",
    "broker_factory",
    "risk_engine",
    "execution_engine",
    "execution_use_case",
    "reporting",
    "observation_logger",
    "state_manager",
)


def test_default_catalog_contains_close_momentum_strategy() -> None:
    catalog = build_default_strategy_catalog()

    assert [definition.strategy_id for definition in catalog] == [
        "close_momentum_v1",
        "equity_momentum_continuation_v1",
    ]
    assert get_strategy_definition("close_momentum_v1") == catalog[0]


def test_strategy_id_and_version_are_stable() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert definition.strategy_id == "close_momentum_v1"
    assert definition.version == "1.0.0"


def test_duplicate_strategy_ids_are_rejected() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    with pytest.raises(ValueError, match="Duplicate strategy_id"):
        _build_strategy_catalog((definition, definition))


def test_returned_catalog_and_metadata_collections_are_immutable() -> None:
    catalog = list_strategy_definitions()
    definition = catalog[0]

    assert isinstance(catalog, tuple)
    assert isinstance(definition.required_inputs, tuple)
    assert isinstance(definition.output_schema, tuple)
    assert isinstance(definition.allowed_symbols, tuple)
    assert isinstance(definition.allowed_regimes, tuple)
    assert isinstance(definition.allowed_actions, tuple)
    assert isinstance(definition.broker_compatibility, tuple)
    assert isinstance(definition.risk_profile, tuple)
    assert isinstance(definition.observability_fields, tuple)

    with pytest.raises(AttributeError):
        definition.strategy_id = "mutated"  # type: ignore[misc]

    with pytest.raises(TypeError):
        catalog[0] = definition  # type: ignore[index]


def test_default_strategy_advertises_current_output_schema() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert set(
        (
            "signal",
            "decision",
            "reason",
            "previous_close",
            "latest_close",
            "price_delta",
            "percent_change",
            "three_close_percent_change",
        )
    ).issubset(definition.output_schema)


def test_default_strategy_advertises_current_observability_fields() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert set(
        (
            "signal",
            "decision",
            "action",
            "reason",
            "signal_timeframe",
            "signal_limit",
            "latest_candle_timestamp",
        )
    ).issubset(definition.observability_fields)


def test_default_strategy_has_no_execution_authority() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert definition.execution_authority is False


def test_default_strategy_is_only_allowed_for_uptrend_regime() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert definition.allowed_regimes == ("uptrend",)


def test_default_strategy_advertises_long_only_allowed_actions() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert definition.allowed_actions == ("buy", "hold")


def test_default_strategy_has_no_broker_compatibility_enabled() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert definition.broker_compatibility == ()


def test_catalog_includes_candidate_with_report_only_uptrend_buy_hold_metadata() -> None:
    definition = get_strategy_definition("equity_momentum_continuation_v1")

    assert definition.strategy_id == "equity_momentum_continuation_v1"
    assert definition.version == "1.0.0"
    assert definition.family == "momentum"
    assert definition.required_inputs == ("closes",)
    assert definition.allowed_regimes == ("uptrend",)
    assert definition.allowed_actions == ("buy", "hold")
    assert definition.validation_status == "active_metadata"
    assert definition.execution_authority is False
    assert definition.broker_compatibility == ()
    assert definition.risk_profile == (
        "pure_signal",
        "non_executing",
        "report_only_candidate",
    )


def test_import_does_not_load_forbidden_modules() -> None:
    _assert_clean_import_does_not_load_forbidden_modules("strategy_library")


def test_strategy_definition_requires_dependency_free_tuple_metadata() -> None:
    definition = StrategyDefinition(
        strategy_id="example",
        version="1.0.0",
        name="Example",
        description="Example metadata.",
        family="example",
        required_inputs=("closes",),
        output_schema=("signal",),
    )

    assert definition.execution_authority is False
    assert definition.allowed_actions == ()
    assert definition.broker_compatibility == ()


def test_blank_strategy_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="strategy_id must be non-empty"):
        StrategyDefinition(
            strategy_id=" ",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
        )


def test_blank_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="version must be non-empty"):
        StrategyDefinition(
            strategy_id="example",
            version=" ",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
        )


def test_blank_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="name must be non-empty"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name=" ",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
        )


def test_blank_family_is_rejected() -> None:
    with pytest.raises(ValueError, match="family must be non-empty"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family=" ",
            required_inputs=("closes",),
            output_schema=("signal",),
        )


def test_non_bool_execution_authority_is_rejected() -> None:
    with pytest.raises(ValueError, match="execution_authority must be a bool"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
            execution_authority="false",  # type: ignore[arg-type]
        )


def test_duplicate_required_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="required_inputs contains duplicate value"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes", "closes"),
            output_schema=("signal",),
        )


def test_duplicate_output_schema_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="output_schema contains duplicate value"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal", "signal"),
        )


def test_duplicate_observability_fields_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="observability_fields contains duplicate value",
    ):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
            observability_fields=("signal", "signal"),
        )


def test_duplicate_allowed_actions_are_rejected() -> None:
    with pytest.raises(ValueError, match="allowed_actions contains duplicate value"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
            allowed_actions=("buy", "buy"),
        )


def test_unsupported_allowed_actions_are_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported allowed_action"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
            allowed_actions=("short",),
        )


def test_unknown_validation_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported validation_status"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
            validation_status="runtime_approved",
        )


def test_non_empty_broker_compatibility_is_rejected() -> None:
    with pytest.raises(ValueError, match="broker_compatibility must remain empty"):
        StrategyDefinition(
            strategy_id="example",
            version="1.0.0",
            name="Example",
            description="Example metadata.",
            family="example",
            required_inputs=("closes",),
            output_schema=("signal",),
            broker_compatibility=("alpaca",),
        )


def test_lookup_normalizes_leading_and_trailing_whitespace() -> None:
    assert get_strategy_definition(" close_momentum_v1 ").strategy_id == (
        "close_momentum_v1"
    )


def test_lookup_remains_case_sensitive() -> None:
    with pytest.raises(KeyError):
        get_strategy_definition("CLOSE_MOMENTUM_V1")


def test_repeated_list_and_get_calls_are_deterministic_and_read_only() -> None:
    first_catalog = list_strategy_definitions()
    second_catalog = list_strategy_definitions()
    first_definition = get_strategy_definition("close_momentum_v1")
    second_definition = get_strategy_definition("close_momentum_v1")

    assert first_catalog == second_catalog
    assert first_catalog is not second_catalog
    assert first_definition == second_definition
    assert first_definition is not second_definition


def _assert_clean_import_does_not_load_forbidden_modules(module_name: str) -> None:
    code = f"""
import json
import sys
import {module_name}

forbidden = set({FORBIDDEN_MODULES!r})
loaded = set(sys.modules)
violations = sorted(
    forbidden.intersection(loaded)
    | {{name for name in loaded if name.startswith("ibkr_")}}
    | {{name for name in loaded if name.startswith("manual_ibkr_")}}
)
print(json.dumps(violations))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []
