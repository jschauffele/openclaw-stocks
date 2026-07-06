from data_layer.manifest import budget_preflight, payload_hash, scrub_token, update_budget_ledger


def test_payload_hash_is_stable():
    assert payload_hash([{"b": 2, "a": 1}]) == payload_hash([{"a": 1, "b": 2}])


def test_scrub_token_handles_query_and_exception_text():
    token = "SECRET_TOKEN_VALUE"
    text = "failed https://example.test/path?token=SECRET_TOKEN_VALUE&format=json SECRET_TOKEN_VALUE"
    scrubbed = scrub_token(text, token)
    assert token not in scrubbed
    assert "[REDACTED_TOKEN]" in scrubbed


def test_budget_ledger_counts_unique_symbols_per_month(tmp_path):
    month = "2026-07"
    first = budget_preflight(tmp_path, ["AAPL", "MSFT"], month)
    assert first["new_unique_symbols_consumed"] == 2
    update_budget_ledger(tmp_path, ["AAPL", "MSFT"], month)
    second = budget_preflight(tmp_path, ["AAPL", "MSFT", "NVDA"], month)
    assert second["already_counted_symbols"] == ["AAPL", "MSFT"]
    assert second["new_unique_symbols"] == ["NVDA"]
    assert second["new_unique_symbols_consumed"] == 1

