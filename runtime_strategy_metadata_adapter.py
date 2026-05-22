from __future__ import annotations

from dataclasses import dataclass

from runtime_strategy_seam import RuntimeStrategySeamResult


STRATEGY_ARCHITECTURE_SOURCE = "runtime_strategy_seam"


@dataclass(frozen=True, slots=True)
class StrategyArchitectureMetadata:
    regime_id: str
    selected_strategy_id: str | None
    routing_reason: str
    eligible_strategy_ids: tuple[str, ...]
    rejected_strategy_ids: tuple[str, ...]
    source: str = STRATEGY_ARCHITECTURE_SOURCE

    def __post_init__(self) -> None:
        if not self.regime_id.strip():
            raise ValueError("regime_id must be non-empty")
        if self.selected_strategy_id is not None and not self.selected_strategy_id.strip():
            raise ValueError("selected_strategy_id must be non-empty when present")
        if not self.routing_reason.strip():
            raise ValueError("routing_reason must be non-empty")
        if self.source != STRATEGY_ARCHITECTURE_SOURCE:
            raise ValueError("source must be runtime_strategy_seam")
        _validate_strategy_id_tuple("eligible_strategy_ids", self.eligible_strategy_ids)
        _validate_strategy_id_tuple("rejected_strategy_ids", self.rejected_strategy_ids)
        overlap = set(self.eligible_strategy_ids).intersection(self.rejected_strategy_ids)
        if overlap:
            overlap_list = ", ".join(sorted(overlap))
            raise ValueError(f"strategy ID appears in both eligible and rejected: {overlap_list}")
        if (
            self.selected_strategy_id is not None
            and self.selected_strategy_id not in self.eligible_strategy_ids
        ):
            raise ValueError("selected_strategy_id must be present in eligible_strategy_ids")


def build_strategy_architecture_metadata(
    seam_result: RuntimeStrategySeamResult,
) -> StrategyArchitectureMetadata:
    if not isinstance(seam_result, RuntimeStrategySeamResult):
        raise ValueError("seam_result must be RuntimeStrategySeamResult")

    return StrategyArchitectureMetadata(
        regime_id=seam_result.regime_id,
        selected_strategy_id=seam_result.selected_strategy_id,
        routing_reason=seam_result.routing_reason,
        eligible_strategy_ids=seam_result.eligible_strategy_ids,
        rejected_strategy_ids=seam_result.rejected_strategy_ids,
        source=STRATEGY_ARCHITECTURE_SOURCE,
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
