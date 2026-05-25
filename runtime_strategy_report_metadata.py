from __future__ import annotations

from runtime_strategy_metadata_adapter import StrategyArchitectureMetadata


def build_orchestration_strategy_architecture_payload(
    metadata: StrategyArchitectureMetadata,
) -> dict[str, object]:
    if not isinstance(metadata, StrategyArchitectureMetadata):
        raise ValueError("metadata must be StrategyArchitectureMetadata")

    return {
        "strategy_architecture": {
            "metadata_schema_version": metadata.metadata_schema_version,
            "regime_id": metadata.regime_id,
            "selected_strategy_id": metadata.selected_strategy_id,
            "routing_reason": metadata.routing_reason,
            "eligible_strategy_ids": metadata.eligible_strategy_ids,
            "rejected_strategy_ids": metadata.rejected_strategy_ids,
            "source": metadata.source,
        }
    }
