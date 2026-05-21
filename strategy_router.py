from __future__ import annotations

from dataclasses import dataclass

from regime_classifier import RegimeClassificationResult
from strategy_library import StrategyDefinition


@dataclass(frozen=True, slots=True)
class StrategyRoutingInput:
    strategy_catalog: tuple[StrategyDefinition, ...]
    regime_result: RegimeClassificationResult

    def __post_init__(self) -> None:
        if not self.strategy_catalog:
            raise ValueError("strategy_catalog must be non-empty")
        if not isinstance(self.regime_result, RegimeClassificationResult):
            raise ValueError("regime_result must be RegimeClassificationResult")
        seen_strategy_ids: set[str] = set()
        for strategy in self.strategy_catalog:
            if not isinstance(strategy, StrategyDefinition):
                raise ValueError("strategy_catalog must contain StrategyDefinition")
            if strategy.strategy_id in seen_strategy_ids:
                raise ValueError(f"Duplicate strategy_id: {strategy.strategy_id}")
            seen_strategy_ids.add(strategy.strategy_id)


@dataclass(frozen=True, slots=True)
class StrategyRoutingResult:
    selected_strategy_id: str | None
    regime_id: str
    reason: str
    eligible_strategy_ids: tuple[str, ...]
    rejected_strategy_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.selected_strategy_id is not None and not self.selected_strategy_id.strip():
            raise ValueError("selected_strategy_id must be non-empty when present")
        if not self.regime_id.strip():
            raise ValueError("regime_id must be non-empty")
        if not self.reason.strip():
            raise ValueError("reason must be non-empty")


def route_strategy(input_model: StrategyRoutingInput) -> StrategyRoutingResult:
    if not isinstance(input_model, StrategyRoutingInput):
        raise ValueError("input_model must be StrategyRoutingInput")

    eligible_strategy_ids: list[str] = []
    rejected_strategy_ids: list[str] = []
    regime_id = input_model.regime_result.regime_id

    for strategy in input_model.strategy_catalog:
        if _strategy_is_eligible(strategy, regime_id):
            eligible_strategy_ids.append(strategy.strategy_id)
        else:
            rejected_strategy_ids.append(strategy.strategy_id)

    selected_strategy_id = eligible_strategy_ids[0] if eligible_strategy_ids else None
    reason = (
        "selected_first_eligible_strategy"
        if selected_strategy_id is not None
        else "no_eligible_strategy"
    )

    return StrategyRoutingResult(
        selected_strategy_id=selected_strategy_id,
        regime_id=regime_id,
        reason=reason,
        eligible_strategy_ids=tuple(eligible_strategy_ids),
        rejected_strategy_ids=tuple(rejected_strategy_ids),
    )


def _strategy_is_eligible(strategy: StrategyDefinition, regime_id: str) -> bool:
    if strategy.execution_authority:
        return False
    if strategy.broker_compatibility:
        return False
    if strategy.validation_status != "active_metadata":
        return False
    if strategy.allowed_regimes and regime_id not in strategy.allowed_regimes:
        return False
    return True
