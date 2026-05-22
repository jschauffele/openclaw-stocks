from __future__ import annotations

from dataclasses import dataclass

from regime_classifier import RegimeClassificationInput, classify_regime
from strategy_library import build_default_strategy_catalog
from strategy_router import StrategyRoutingInput, route_strategy


@dataclass(frozen=True, slots=True)
class StrategyIntegrationInput:
    closes: tuple[float, ...]
    lookback: int = 5
    min_trend_percent: float = 1.0
    volatility_percent: float = 2.0


@dataclass(frozen=True, slots=True)
class StrategyIntegrationResult:
    regime_id: str
    selected_strategy_id: str | None
    routing_reason: str
    eligible_strategy_ids: tuple[str, ...]
    rejected_strategy_ids: tuple[str, ...]


def evaluate_strategy_integration(
    input_model: StrategyIntegrationInput,
) -> StrategyIntegrationResult:
    if not isinstance(input_model, StrategyIntegrationInput):
        raise ValueError("input_model must be StrategyIntegrationInput")

    strategy_catalog = build_default_strategy_catalog()
    regime_result = classify_regime(
        RegimeClassificationInput(
            closes=input_model.closes,
            lookback=input_model.lookback,
            min_trend_percent=input_model.min_trend_percent,
            volatility_percent=input_model.volatility_percent,
        )
    )
    routing_result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=strategy_catalog,
            regime_result=regime_result,
        )
    )

    return StrategyIntegrationResult(
        regime_id=regime_result.regime_id,
        selected_strategy_id=routing_result.selected_strategy_id,
        routing_reason=routing_result.reason,
        eligible_strategy_ids=routing_result.eligible_strategy_ids,
        rejected_strategy_ids=routing_result.rejected_strategy_ids,
    )
