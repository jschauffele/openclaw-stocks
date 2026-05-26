from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


POSITIVE_CONTROL_3 = "Positive Control 3"
FALSE_POSITIVE_REVIEW_1 = "False-Positive Review 1"
FALSE_POSITIVE_REVIEW_3 = "False-Positive Review 3"
ARTIFACT_TYPE = "review_input_not_test"
REVIEWER_DECISION_PENDING_REVIEW = "PENDING_REVIEW"
REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED = "GENERATED_CANDIDATE_NOT_ACCEPTED"
SCANNER_VERSION = "3_close_evidence_scanner_v1"


@dataclass(frozen=True)
class ScannerSettings:
    """
    Candidate-generation heuristics only.

    These values are not strategy thresholds, do not approve strategy behavior, and
    do not finalize stronger confirmation logic.
    """

    shallow_drift_max_delta: float = 0.10
    steady_continuation_min_delta: float = 0.50
    steady_continuation_max_to_min_delta_ratio: float = 2.0


DEFAULT_SCANNER_SETTINGS = ScannerSettings()


@dataclass(frozen=True)
class CloseBar:
    timestamp: str
    close: float

    def __post_init__(self) -> None:
        if not str(self.timestamp).strip():
            raise ValueError("timestamp must be non-empty")
        object.__setattr__(self, "timestamp", str(self.timestamp).strip())
        object.__setattr__(self, "close", float(self.close))


@dataclass(frozen=True)
class EvidenceCandidate:
    fixture_name: str
    symbol: str
    timeframe: str
    date_time_range: str
    close_sequence: tuple[float, ...]
    signal_window_closes: tuple[float, ...]
    follow_through_closes: tuple[float, ...]
    source_provider: str
    evidence_type: str
    fixture_effect: str
    ambiguity_notes: str
    uses_close_only_data: bool
    non_close_data_present_but_out_of_scope: bool
    reviewer_decision: str
    review_status: str
    generated_at: str


def scan_three_close_evidence_candidates(
    *,
    symbol: str,
    timeframe: str,
    bars: Sequence[CloseBar],
    source_provider: str,
    evidence_type: str,
    generated_at: str | None = None,
    max_examples: int | None = None,
    scanner_settings: ScannerSettings = DEFAULT_SCANNER_SETTINGS,
) -> tuple[EvidenceCandidate, ...]:
    normalized_symbol = _normalize_required_text("symbol", symbol).upper()
    normalized_timeframe = _normalize_required_text("timeframe", timeframe)
    normalized_source = _normalize_required_text("source_provider", source_provider)
    normalized_evidence_type = _normalize_required_text("evidence_type", evidence_type)
    generated = generated_at or datetime.now(timezone.utc).isoformat()

    candidates: list[EvidenceCandidate] = []
    close_bars = tuple(bars)

    for start_index in range(len(close_bars)):
        candidates.extend(
            _scan_positive_control_3(
                normalized_symbol,
                normalized_timeframe,
                close_bars,
                start_index,
                normalized_source,
                normalized_evidence_type,
                generated,
                scanner_settings,
            )
        )
        candidates.extend(
            _scan_false_positive_review_1(
                normalized_symbol,
                normalized_timeframe,
                close_bars,
                start_index,
                normalized_source,
                normalized_evidence_type,
                generated,
                scanner_settings,
            )
        )
        candidates.extend(
            _scan_false_positive_review_3(
                normalized_symbol,
                normalized_timeframe,
                close_bars,
                start_index,
                normalized_source,
                normalized_evidence_type,
                generated,
                scanner_settings,
            )
        )
        if max_examples is not None and len(candidates) >= max_examples:
            return tuple(candidates[:max_examples])

    return tuple(candidates)


def write_evidence_candidates_json(
    candidates: Iterable[EvidenceCandidate],
    output_path: str | Path,
    scanner_settings: ScannerSettings = DEFAULT_SCANNER_SETTINGS,
) -> Path:
    path = Path(output_path)
    if str(path).strip() == "":
        raise ValueError("output_path must be provided")
    if path.exists() and path.is_dir():
        raise ValueError("output_path must be a file path, not a directory")

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "openclaw_3_close_evidence_candidates_v1",
        "artifact_type": ARTIFACT_TYPE,
        "scanner_version": SCANNER_VERSION,
        "scanner_settings": _scanner_settings_to_json(scanner_settings),
        "candidates": [_candidate_to_json(candidate) for candidate in candidates],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def _scan_positive_control_3(
    symbol: str,
    timeframe: str,
    bars: tuple[CloseBar, ...],
    start_index: int,
    source_provider: str,
    evidence_type: str,
    generated_at: str,
    scanner_settings: ScannerSettings,
) -> tuple[EvidenceCandidate, ...]:
    signal = bars[start_index : start_index + 4]
    follow = bars[start_index + 4 : start_index + 7]
    if len(signal) < 4 or not follow:
        return ()

    closes = tuple(bar.close for bar in signal)
    deltas = _deltas(closes)
    if not all(delta > 0 for delta in deltas):
        return ()
    if _is_shallow_drift(deltas, scanner_settings):
        return ()
    if not _is_steady_continuation(deltas, scanner_settings):
        return ()

    effect = "supports_fixture" if follow[0].close >= closes[-1] else "weakens_fixture"
    notes = (
        "steady close-only continuation with constructive follow-through"
        if effect == "supports_fixture"
        else "steady close-only continuation but first follow-through close is below signal window"
    )
    return (
        _candidate(
            fixture_name=POSITIVE_CONTROL_3,
            symbol=symbol,
            timeframe=timeframe,
            signal=signal,
            follow=follow,
            source_provider=source_provider,
            evidence_type=evidence_type,
            fixture_effect=effect,
            ambiguity_notes=notes,
            generated_at=generated_at,
        ),
    )


def _scan_false_positive_review_1(
    symbol: str,
    timeframe: str,
    bars: tuple[CloseBar, ...],
    start_index: int,
    source_provider: str,
    evidence_type: str,
    generated_at: str,
    scanner_settings: ScannerSettings,
) -> tuple[EvidenceCandidate, ...]:
    signal = bars[start_index : start_index + 4]
    follow = bars[start_index + 4 : start_index + 7]
    if len(signal) < 4 or not follow:
        return ()

    closes = tuple(bar.close for bar in signal)
    deltas = _deltas(closes)
    if not all(delta > 0 for delta in deltas):
        return ()
    if not _is_shallow_drift(deltas, scanner_settings):
        return ()

    failed_follow = follow[0].close <= closes[-1]
    effect = "supports_fixture" if failed_follow else "weakens_fixture"
    notes = (
        "tiny close-only upward drift with weak or failed first follow-through close"
        if failed_follow
        else "tiny close-only upward drift but first follow-through close continued higher"
    )
    return (
        _candidate(
            fixture_name=FALSE_POSITIVE_REVIEW_1,
            symbol=symbol,
            timeframe=timeframe,
            signal=signal,
            follow=follow,
            source_provider=source_provider,
            evidence_type=evidence_type,
            fixture_effect=effect,
            ambiguity_notes=notes,
            generated_at=generated_at,
        ),
    )


def _scan_false_positive_review_3(
    symbol: str,
    timeframe: str,
    bars: tuple[CloseBar, ...],
    start_index: int,
    source_provider: str,
    evidence_type: str,
    generated_at: str,
    scanner_settings: ScannerSettings,
) -> tuple[EvidenceCandidate, ...]:
    signal = bars[start_index : start_index + 5]
    follow = bars[start_index + 5 : start_index + 8]
    if len(signal) < 5 or not follow:
        return ()

    closes = tuple(bar.close for bar in signal)
    has_choppy_recovery = closes[1] < closes[0] and closes[2] > closes[1]
    has_short_upward_run = closes[2] < closes[3] < closes[4]
    if not (has_choppy_recovery and has_short_upward_run):
        return ()

    failed_follow = follow[0].close <= closes[-1]
    effect = "supports_fixture" if failed_follow else "weakens_fixture"
    notes = (
        "choppy close-only recovery followed by short upward run and weak first follow-through close"
        if failed_follow
        else "choppy close-only recovery followed by short upward run but first follow-through close continued higher"
    )
    return (
        _candidate(
            fixture_name=FALSE_POSITIVE_REVIEW_3,
            symbol=symbol,
            timeframe=timeframe,
            signal=signal,
            follow=follow,
            source_provider=source_provider,
            evidence_type=evidence_type,
            fixture_effect=effect,
            ambiguity_notes=notes,
            generated_at=generated_at,
        ),
    )


def _candidate(
    *,
    fixture_name: str,
    symbol: str,
    timeframe: str,
    signal: Sequence[CloseBar],
    follow: Sequence[CloseBar],
    source_provider: str,
    evidence_type: str,
    fixture_effect: str,
    ambiguity_notes: str,
    generated_at: str,
) -> EvidenceCandidate:
    signal_closes = tuple(bar.close for bar in signal)
    follow_closes = tuple(bar.close for bar in follow)
    return EvidenceCandidate(
        fixture_name=fixture_name,
        symbol=symbol,
        timeframe=timeframe,
        date_time_range=f"{signal[0].timestamp} to {follow[-1].timestamp}",
        close_sequence=signal_closes + follow_closes,
        signal_window_closes=signal_closes,
        follow_through_closes=follow_closes,
        source_provider=source_provider,
        evidence_type=evidence_type,
        fixture_effect=fixture_effect,
        ambiguity_notes=ambiguity_notes,
        uses_close_only_data=True,
        non_close_data_present_but_out_of_scope=False,
        reviewer_decision=REVIEWER_DECISION_PENDING_REVIEW,
        review_status=REVIEW_STATUS_GENERATED_CANDIDATE_NOT_ACCEPTED,
        generated_at=generated_at,
    )


def _candidate_to_json(candidate: EvidenceCandidate) -> dict:
    payload = asdict(candidate)
    payload["close_sequence"] = list(candidate.close_sequence)
    payload["signal_window_closes"] = list(candidate.signal_window_closes)
    payload["follow_through_closes"] = list(candidate.follow_through_closes)
    return payload


def _scanner_settings_to_json(scanner_settings: ScannerSettings) -> dict:
    return {
        "meaning": (
            "scanner candidate-generation heuristics only; not strategy thresholds, "
            "not strategy behavior approval, and not finalized stronger confirmation logic"
        ),
        "shallow_drift_max_delta": scanner_settings.shallow_drift_max_delta,
        "steady_continuation_min_delta": scanner_settings.steady_continuation_min_delta,
        "steady_continuation_max_to_min_delta_ratio": (
            scanner_settings.steady_continuation_max_to_min_delta_ratio
        ),
    }


def _deltas(closes: Sequence[float]) -> tuple[float, ...]:
    return tuple(closes[index] - closes[index - 1] for index in range(1, len(closes)))


def _is_shallow_drift(
    deltas: Sequence[float],
    scanner_settings: ScannerSettings,
) -> bool:
    return max(deltas) <= scanner_settings.shallow_drift_max_delta


def _is_steady_continuation(
    deltas: Sequence[float],
    scanner_settings: ScannerSettings,
) -> bool:
    if not deltas:
        return False
    min_delta = min(deltas)
    max_delta = max(deltas)
    return (
        min_delta >= scanner_settings.steady_continuation_min_delta
        and max_delta / min_delta
        <= scanner_settings.steady_continuation_max_to_min_delta_ratio
    )


def _normalize_required_text(field_name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized
