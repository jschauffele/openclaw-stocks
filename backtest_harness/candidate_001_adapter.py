"""Candidate 001 replay adapter for Phase 1B dispatch."""

from __future__ import annotations

from equity_momentum_continuation_strategy import generate_equity_momentum_continuation_signal_from_closes


def candidate_001_replay_adapter(closes: tuple[float, ...]) -> dict:
    return dict(generate_equity_momentum_continuation_signal_from_closes(closes))
