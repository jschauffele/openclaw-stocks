# Phase 1B Authorization Addendum

Phase 1B implementation is AUTHORIZED as of 2026-07-07, per operator
decision. Source plan: docs/phase_1b_backtest_harness_implementation_plan.md.
Scope of this authorization: implementation units in the 1B plan, staged;
this session covers units 1-2 (skeleton, derived reader).

Amendment 1 — acceptance tests are signal-domain analogues:
- Known-answer: a toy strategy with analytically predictable signal counts
  must reproduce the independently computed count exactly.
- Null strategy: always-hold emits zero buy signals, zero exceptions.
- Look-ahead canary: a probe strategy attempting to observe data beyond the
  decision date must find it structurally absent, or the harness fails loudly.
- Determinism: identical inputs produce byte-identical hashed report outputs.
No execution simulation and no P&L accounting in Phase 1B.

Amendment 2 — derived reader selection rule: among multiple
tiingo-*.parquet files per ticker, select by latest source_manifest_id;
fail closed on manifest conflict, duplicate dates, unparseable dates, or
schema mismatch.
