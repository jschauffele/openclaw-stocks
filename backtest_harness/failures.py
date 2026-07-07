"""Structured fail-closed errors for the Phase 1B harness."""

from __future__ import annotations

from enum import Enum


class HarnessFailureCode(str, Enum):
    MISSING_DERIVED_DATA = "missing_derived_data"
    VENDOR_ADJCLOSE_FORBIDDEN = "vendor_adjclose_forbidden"
    DUPLICATE_TICKER_DATE = "duplicate_ticker_date"
    MISSING_MANIFEST_LINEAGE = "missing_manifest_lineage"
    NON_DETERMINISTIC_OUTPUT = "non_deterministic_output"
    MISSING_UNIVERSE_LABEL = "missing_universe_label"
    TRAIN_TEST_OVERLAP = "train_test_overlap"
    DATA_ROOT_INSIDE_REPOSITORY = "data_root_inside_repository"
    DISALLOWED_RUNTIME_MODE = "disallowed_runtime_mode"
    SCHEMA_MISMATCH = "schema_mismatch"
    UNPARSEABLE_DATE = "unparseable_date"
    MANIFEST_CONFLICT = "manifest_conflict"
    INVALID_TICKER = "invalid_ticker"
    INVALID_PRICE = "invalid_price"


class BacktestHarnessError(RuntimeError):
    """Fail-closed harness exception carrying a stable failure code."""

    def __init__(self, code: HarnessFailureCode, message: str):
        self.code = code
        super().__init__(f"{code.value}: {message}")
