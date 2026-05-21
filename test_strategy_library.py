from __future__ import annotations

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

    assert [definition.strategy_id for definition in catalog] == ["close_momentum_v1"]
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


def test_default_strategy_has_no_broker_compatibility_enabled() -> None:
    definition = get_strategy_definition("close_momentum_v1")

    assert definition.broker_compatibility == ()


def test_import_does_not_load_forbidden_modules() -> None:
    loaded_modules = set(sys.modules)

    assert not loaded_modules.intersection(FORBIDDEN_MODULES)
    assert not any(module_name.startswith("ibkr_") for module_name in loaded_modules)
    assert not any(
        module_name.startswith("manual_ibkr_") for module_name in loaded_modules
    )


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
    assert definition.broker_compatibility == ()
