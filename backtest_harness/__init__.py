"""Phase 1B backtest harness foundation."""

from backtest_harness.config import (
    DEFAULT_DATA_ROOT,
    DEFAULT_PHASE_1_UNIVERSE,
    NON_GENERALIZABLE_RESEARCH_RESULT,
    BacktestHarnessConfig,
)
from backtest_harness.derived_reader import read_derived_adjusted_series
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode
from backtest_harness.serialization import canonical_json_bytes, canonical_json_text, stable_sha256

__all__ = [
    "BacktestHarnessConfig",
    "BacktestHarnessError",
    "DEFAULT_DATA_ROOT",
    "DEFAULT_PHASE_1_UNIVERSE",
    "HarnessFailureCode",
    "NON_GENERALIZABLE_RESEARCH_RESULT",
    "canonical_json_bytes",
    "canonical_json_text",
    "read_derived_adjusted_series",
    "stable_sha256",
]
