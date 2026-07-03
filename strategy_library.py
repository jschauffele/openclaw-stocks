from __future__ import annotations

from dataclasses import dataclass


ALLOWED_VALIDATION_STATUSES = frozenset(
    {
        "scaffolded",
        "active_metadata",
        "deprecated_metadata",
    }
)


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

    def __post_init__(self) -> None:
        _validate_non_blank("strategy_id", self.strategy_id)
        _validate_non_blank("version", self.version)
        _validate_non_blank("name", self.name)
        _validate_non_blank("family", self.family)
        if not isinstance(self.execution_authority, bool):
            raise ValueError("execution_authority must be a bool")
        _validate_unique_values("required_inputs", self.required_inputs)
        _validate_unique_values("output_schema", self.output_schema)
        _validate_unique_values("observability_fields", self.observability_fields)
        if self.validation_status not in ALLOWED_VALIDATION_STATUSES:
            raise ValueError(f"Unsupported validation_status: {self.validation_status}")
        if self.broker_compatibility:
            raise ValueError("broker_compatibility must remain empty")


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
                allowed_regimes=("uptrend",),
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


def _validate_non_blank(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _validate_unique_values(field_name: str, values: tuple[str, ...]) -> None:
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            raise ValueError(f"{field_name} contains duplicate value: {value}")
        seen_values.add(value)
