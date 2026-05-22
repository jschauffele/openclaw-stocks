from __future__ import annotations

from dataclasses import dataclass

from strategy_integration import StrategyIntegrationInput, evaluate_strategy_integration


@dataclass(frozen=True, slots=True)
class RuntimeStrategySeamInput:
    closes: tuple[float, ...]
    lookback: int = 5
    min_trend_percent: float = 1.0
    volatility_percent: float = 2.0

    def __post_init__(self) -> None:
        if not isinstance(self.closes, tuple):
            raise ValueError("closes must be a tuple")


@dataclass(frozen=True, slots=True)
class RuntimeStrategySeamResult:
    regime_id: str
    selected_strategy_id: str | None
    routing_reason: str
    eligible_strategy_ids: tuple[str, ...]
    rejected_strategy_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.regime_id.strip():
            raise ValueError("regime_id must be non-empty")
        if self.selected_strategy_id is not None and not self.selected_strategy_id.strip():
            raise ValueError("selected_strategy_id must be non-empty when present")
        if not self.routing_reason.strip():
            raise ValueError("routing_reason must be non-empty")
        _validate_strategy_id_tuple("eligible_strategy_ids", self.eligible_strategy_ids)
        _validate_strategy_id_tuple("rejected_strategy_ids", self.rejected_strategy_ids)
        overlap = set(self.eligible_strategy_ids).intersection(self.rejected_strategy_ids)
        if overlap:
            overlap_list = ", ".join(sorted(overlap))
            raise ValueError(f"strategy ID appears in both eligible and rejected: {overlap_list}")
        if self.selected_strategy_id is not None:
            if not self.eligible_strategy_ids:
                raise ValueError(
                    "selected_strategy_id requires non-empty eligible_strategy_ids"
                )
            if self.selected_strategy_id not in self.eligible_strategy_ids:
                raise ValueError(
                    "selected_strategy_id must be present in eligible_strategy_ids"
                )


def build_runtime_strategy_metadata(
    input_model: RuntimeStrategySeamInput,
) -> RuntimeStrategySeamResult:
    if not isinstance(input_model, RuntimeStrategySeamInput):
        raise ValueError("input_model must be RuntimeStrategySeamInput")

    integration_result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=input_model.closes,
            lookback=input_model.lookback,
            min_trend_percent=input_model.min_trend_percent,
            volatility_percent=input_model.volatility_percent,
        )
    )

    return RuntimeStrategySeamResult(
        regime_id=integration_result.regime_id,
        selected_strategy_id=integration_result.selected_strategy_id,
        routing_reason=integration_result.routing_reason,
        eligible_strategy_ids=integration_result.eligible_strategy_ids,
        rejected_strategy_ids=integration_result.rejected_strategy_ids,
    )


def _validate_strategy_id_tuple(field_name: str, strategy_ids: tuple[str, ...]) -> None:
    if not isinstance(strategy_ids, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    seen_strategy_ids: set[str] = set()
    for strategy_id in strategy_ids:
        if not isinstance(strategy_id, str):
            raise ValueError(f"{field_name} must contain strings")
        if not strategy_id.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        if strategy_id in seen_strategy_ids:
            raise ValueError(f"{field_name} contains duplicate strategy_id: {strategy_id}")
        seen_strategy_ids.add(strategy_id)
