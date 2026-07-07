from pathlib import Path

import pytest

from backtest_harness import BacktestHarnessConfig
from backtest_harness.config import DEFAULT_PHASE_1_UNIVERSE, NON_GENERALIZABLE_RESEARCH_RESULT
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode


def test_config_defaults_include_phase_1_universe_and_label() -> None:
    config = BacktestHarnessConfig()

    assert config.universe == DEFAULT_PHASE_1_UNIVERSE
    assert config.universe_label == NON_GENERALIZABLE_RESEARCH_RESULT
    assert str(config.data_root) == "/Users/openclawcontrol/openclaw-market-data"
    assert str(config.derived_root).endswith("/tiingo/derived")


def test_config_rejects_repo_data_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with pytest.raises(BacktestHarnessError) as excinfo:
        BacktestHarnessConfig(data_root=repo_root)

    assert excinfo.value.code == HarnessFailureCode.DATA_ROOT_INSIDE_REPOSITORY


def test_config_rejects_missing_universe_label(tmp_path) -> None:
    with pytest.raises(BacktestHarnessError) as excinfo:
        BacktestHarnessConfig(data_root=tmp_path, universe_label="")

    assert excinfo.value.code == HarnessFailureCode.MISSING_UNIVERSE_LABEL


def test_config_rejects_disallowed_modes(tmp_path) -> None:
    with pytest.raises(BacktestHarnessError) as excinfo:
        BacktestHarnessConfig(data_root=tmp_path, allow_broker_access=True)

    assert excinfo.value.code == HarnessFailureCode.DISALLOWED_RUNTIME_MODE
