from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    strategy_id: str
    version: str
    name: str
    description: str
    family: str
    required_inputs: tuple[str, ...]
    output_schema: tuple[str, ...]
    allowed_symbols: tuple[str, ...] = ()
    allowed_regimes: tuple[str, ...] = ()
    validation_status: str = "scaffolded"
    execution_authority: bool = False
    broker_compatibility: tuple[str, ...] = ()
    risk_profile: tuple[str, ...] = ()
    observability_fields: tuple[str, ...] = ()


def build_default_strategy_catalog() -> tuple[StrategyDefinition, ...]:
    return _build_strategy_catalog(
        (
            StrategyDefinition(
                strategy_id="close_momentum_v1",
                version="1.0.0",
                name="Close Momentum",
                description=(
                    "Deterministic close-based momentum strategy metadata for "
                    "the existing close sequence signal."
                ),
                family="momentum",
                required_inputs=("closes",),
                output_schema=(
                    "signal",
                    "decision",
                    "reason",
                    "previous_close",
                    "latest_close",
                    "price_delta",
                    "percent_change",
                    "three_close_percent_change",
                ),
                validation_status="active_metadata",
                risk_profile=("pure_signal", "non_executing"),
                observability_fields=(
                    "signal",
                    "decision",
                    "action",
                    "reason",
                    "signal_timeframe",
                    "signal_limit",
                    "latest_candle_timestamp",
                ),
            ),
        )
    )


def get_strategy_definition(strategy_id: str) -> StrategyDefinition:
    normalized_strategy_id = str(strategy_id).strip()
    for definition in build_default_strategy_catalog():
        if definition.strategy_id == normalized_strategy_id:
            return definition
    raise KeyError(f"Unknown strategy_id: {strategy_id}")


def list_strategy_definitions() -> tuple[StrategyDefinition, ...]:
    return build_default_strategy_catalog()


def _build_strategy_catalog(
    definitions: tuple[StrategyDefinition, ...],
) -> tuple[StrategyDefinition, ...]:
    seen_strategy_ids: set[str] = set()
    for definition in definitions:
        if definition.strategy_id in seen_strategy_ids:
            raise ValueError(f"Duplicate strategy_id: {definition.strategy_id}")
        seen_strategy_ids.add(definition.strategy_id)
    return tuple(definitions)
