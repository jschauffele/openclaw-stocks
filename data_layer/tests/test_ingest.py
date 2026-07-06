from pathlib import Path

import pytest

from data_layer.ingest import (
    IngestBlocked,
    read_existing_canonical,
    run_ingest,
    tiingo_layout,
    write_partitioned_parquet,
)
from data_layer.schema import detect_data_value_rewrites, normalize_tiingo_payload


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


def _canonical(close=100.0, *, run_id="tiingo-20260101T000000Z-aaaaaaaaaaaa", payload_hash="hash-1"):
    return normalize_tiingo_payload(
        _payload(close=close),
        ticker="AAPL",
        source_symbol="AAPL",
        ingest_run_id=run_id,
        payload_hash=payload_hash,
    )


def _assert_no_layout_created(data_root: Path):
    paths = tiingo_layout(data_root)
    assert not paths["base"].exists()
    for key, path in paths.items():
        if key != "base":
            assert not path.exists()


def test_run_ingest_rejects_documents_data_root_before_layout_creation(monkeypatch):
    monkeypatch.setenv("TIINGO_API_TOKEN", "test-token")
    rejected = Path.home() / "Documents" / "openclaw-forbidden-data-root"

    with pytest.raises(IngestBlocked, match="iCloud-synced|~/Documents"):
        run_ingest(["AAPL"], rejected)

    _assert_no_layout_created(rejected)


def test_run_ingest_rejects_repo_data_root_before_layout_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("TIINGO_API_TOKEN", "test-token")
    fake_repo = tmp_path / "repo"
    (fake_repo / ".git").mkdir(parents=True)
    rejected = fake_repo / "market-data"

    with pytest.raises(IngestBlocked, match="inside tracked repo"):
        run_ingest(["AAPL"], rejected)

    _assert_no_layout_created(rejected)


def test_read_existing_canonical_uses_latest_ticker_baseline(tmp_path):
    root = tmp_path / "canonical"
    write_partitioned_parquet(
        _canonical(close=100.0, run_id="tiingo-20260101T000000Z-aaaaaaaaaaaa", payload_hash="old-hash"),
        root,
        "tiingo-20260101T000000Z-aaaaaaaaaaaa",
    )
    write_partitioned_parquet(
        _canonical(close=101.0, run_id="tiingo-20260102T000000Z-bbbbbbbbbbbb", payload_hash="latest-hash"),
        root,
        "tiingo-20260102T000000Z-bbbbbbbbbbbb",
    )

    existing = read_existing_canonical(root, ["AAPL"])

    assert len(existing) == 1
    assert existing.iloc[0]["close"] == 101.0
    incoming_same_values_new_provenance = _canonical(
        close=101.0,
        run_id="tiingo-20260103T000000Z-cccccccccccc",
        payload_hash="new-hash",
    )
    assert detect_data_value_rewrites(existing, incoming_same_values_new_provenance) == []

    incoming_changed_value = _canonical(
        close=102.0,
        run_id="tiingo-20260103T000000Z-cccccccccccc",
        payload_hash="new-hash",
    )
    rewrites = detect_data_value_rewrites(existing, incoming_changed_value)
    assert rewrites == [{"date": "2024-01-02", "ticker": "AAPL", "field": "close", "stored": 101.0, "incoming": 102.0}]
