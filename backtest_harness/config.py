"""Configuration model for Phase 1B harness units."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode


DEFAULT_DATA_ROOT = Path("/Users/openclawcontrol/openclaw-market-data")
DEFAULT_PHASE_1_UNIVERSE = ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR", "PTON")
NON_GENERALIZABLE_RESEARCH_RESULT = "NON_GENERALIZABLE_RESEARCH_RESULT"


@dataclass(frozen=True, slots=True)
class BacktestHarnessConfig:
    data_root: Path = DEFAULT_DATA_ROOT
    universe: tuple[str, ...] = DEFAULT_PHASE_1_UNIVERSE
    universe_label: str = NON_GENERALIZABLE_RESEARCH_RESULT
    allow_broker_access: bool = False
    allow_execution: bool = False
    allow_paper_trading: bool = False
    allow_live_trading: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_root", Path(self.data_root).expanduser().resolve())
        object.__setattr__(self, "universe", tuple(str(ticker).strip().upper() for ticker in self.universe))
        self._validate()

    @property
    def derived_root(self) -> Path:
        return self.data_root / "tiingo" / "derived"

    def _validate(self) -> None:
        if not self.universe:
            raise BacktestHarnessError(HarnessFailureCode.MISSING_UNIVERSE_LABEL, "universe must be non-empty")
        if any(not ticker for ticker in self.universe):
            raise BacktestHarnessError(HarnessFailureCode.INVALID_TICKER, "universe contains blank ticker")
        if len(set(self.universe)) != len(self.universe):
            raise BacktestHarnessError(HarnessFailureCode.INVALID_TICKER, "universe contains duplicate ticker")
        if self.universe_label != NON_GENERALIZABLE_RESEARCH_RESULT:
            raise BacktestHarnessError(
                HarnessFailureCode.MISSING_UNIVERSE_LABEL,
                "Phase 1 universe requires NON_GENERALIZABLE_RESEARCH_RESULT",
            )
        if self.allow_broker_access or self.allow_execution or self.allow_paper_trading or self.allow_live_trading:
            raise BacktestHarnessError(
                HarnessFailureCode.DISALLOWED_RUNTIME_MODE,
                "broker, execution, paper-trading, and live-trading modes are forbidden",
            )
        repo_root = Path(__file__).resolve().parents[1]
        if self.data_root == repo_root or repo_root in self.data_root.parents:
            raise BacktestHarnessError(
                HarnessFailureCode.DATA_ROOT_INSIDE_REPOSITORY,
                f"data_root must be external to repository: {self.data_root}",
            )
