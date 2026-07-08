"""Phase 1B backtest harness foundation."""

from backtest_harness.config import (
    DEFAULT_DATA_ROOT,
    DEFAULT_PHASE_1_UNIVERSE,
    NON_GENERALIZABLE_RESEARCH_RESULT,
    BacktestHarnessConfig,
)
from backtest_harness.candidate_001_adapter import candidate_001_replay_adapter
from backtest_harness.derived_reader import read_derived_adjusted_series
from backtest_harness.dispatch import replay_signal_dispatch
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode
from backtest_harness.report import build_replay_report, write_replay_report
from backtest_harness.serialization import canonical_json_bytes, canonical_json_text, stable_sha256
from backtest_harness.walk_forward import WalkForwardFold, generate_walk_forward_folds

__all__ = [
    "BacktestHarnessConfig",
    "BacktestHarnessError",
    "DEFAULT_DATA_ROOT",
    "DEFAULT_PHASE_1_UNIVERSE",
    "HarnessFailureCode",
    "NON_GENERALIZABLE_RESEARCH_RESULT",
    "WalkForwardFold",
    "build_replay_report",
    "candidate_001_replay_adapter",
    "canonical_json_bytes",
    "canonical_json_text",
    "generate_walk_forward_folds",
    "read_derived_adjusted_series",
    "replay_signal_dispatch",
    "stable_sha256",
    "write_replay_report",
]
