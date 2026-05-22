from __future__ import annotations

from dataclasses import dataclass

from strategy_integration import StrategyIntegrationInput, evaluate_strategy_integration


@dataclass(frozen=True, slots=True)
class RuntimeStrategySeamInput:
    closes: tuple[float, ...]
    lookback: int = 5
    min_trend_percent: float = 1.0
    volatility_percent: float = 2.0


@dataclass(frozen=True, slots=True)
class RuntimeStrategySeamResult:
    regime_id: str
    selected_strategy_id: str | None
    routing_reason: str
    eligible_strategy_ids: tuple[str, ...]
    rejected_strategy_ids: tuple[str, ...]


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
