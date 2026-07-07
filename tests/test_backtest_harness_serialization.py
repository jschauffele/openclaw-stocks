import pytest

from backtest_harness.serialization import canonical_json_bytes, canonical_json_text, stable_sha256


def test_canonical_json_and_hash_are_stable_across_key_order() -> None:
    left = {"b": 2, "a": [{"d": 4, "c": 3}]}
    right = {"a": [{"c": 3, "d": 4}], "b": 2}

    assert canonical_json_text(left) == canonical_json_text(right)
    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert stable_sha256(left) == stable_sha256(right)


def test_canonical_json_rejects_nan() -> None:
    with pytest.raises(ValueError):
        canonical_json_text({"bad": float("nan")})
