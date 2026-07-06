import pandas as pd

from data_layer.schema import (
    CANONICAL_FIELDS,
    detect_data_value_rewrites,
    normalize_tiingo_payload,
    validate_tiingo_payload,
)


def _payload(close=100.0):
    return [
        {
            "date": "2024-01-02T00:00:00.000Z",
            "open": 99.0,
            "high": 101.0,
            "low": 98.0,
            "close": close,
            "volume": 123,
            "adjClose": close,
            "divCash": 0.0,
            "splitFactor": 1.0,
        }
    ]


def test_canonical_rows_are_append_stable_only():
    frame = normalize_tiingo_payload(
        _payload(),
        ticker="AAPL",
        source_symbol="AAPL",
        ingest_run_id="run-1",
        payload_hash="hash-1",
    )
    assert list(frame.columns) == CANONICAL_FIELDS
    assert "vendor_adjClose" not in frame.columns
    assert "computed_adjClose" not in frame.columns
    assert "adjustment_method" not in frame.columns


def test_schema_hard_fails_required_tiingo_fields():
    payload = _payload()
    del payload[0]["adjClose"]
    result = validate_tiingo_payload(payload)
    assert not result.passed
    assert "missing_required_field:adjClose" in result.errors


def test_rewrite_detection_ignores_provenance_changes():
    existing = normalize_tiingo_payload(
        _payload(),
        ticker="AAPL",
        source_symbol="AAPL",
        ingest_run_id="run-1",
        payload_hash="hash-1",
    )
    incoming = normalize_tiingo_payload(
        _payload(),
        ticker="AAPL",
        source_symbol="AAPL",
        ingest_run_id="run-2",
        payload_hash="hash-2",
    )
    assert detect_data_value_rewrites(existing, incoming) == []


def test_rewrite_detection_reports_data_value_change():
    existing = normalize_tiingo_payload(
        _payload(close=100.0),
        ticker="AAPL",
        source_symbol="AAPL",
        ingest_run_id="run-1",
        payload_hash="hash-1",
    )
    incoming = normalize_tiingo_payload(
        _payload(close=101.0),
        ticker="AAPL",
        source_symbol="AAPL",
        ingest_run_id="run-2",
        payload_hash="hash-2",
    )
    rewrites = detect_data_value_rewrites(existing, incoming)
    assert rewrites == [{"date": "2024-01-02", "ticker": "AAPL", "field": "close", "stored": 100.0, "incoming": 101.0}]

