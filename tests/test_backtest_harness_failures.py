from backtest_harness.failures import HarnessFailureCode


def test_failure_enum_includes_phase_1b_blockers() -> None:
    assert HarnessFailureCode.MISSING_DERIVED_DATA.value == "missing_derived_data"
    assert HarnessFailureCode.VENDOR_ADJCLOSE_FORBIDDEN.value == "vendor_adjclose_forbidden"
    assert HarnessFailureCode.DUPLICATE_TICKER_DATE.value == "duplicate_ticker_date"
    assert HarnessFailureCode.MISSING_MANIFEST_LINEAGE.value == "missing_manifest_lineage"
    assert HarnessFailureCode.NON_DETERMINISTIC_OUTPUT.value == "non_deterministic_output"
    assert HarnessFailureCode.MISSING_UNIVERSE_LABEL.value == "missing_universe_label"
    assert HarnessFailureCode.TRAIN_TEST_OVERLAP.value == "train_test_overlap"
