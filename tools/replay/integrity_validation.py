"""Pure in-memory integrity validation helper for replay prerequisites.

This module compares already-built hash records only. It does not assert
package completeness, create packages, touch the filesystem, store artifacts,
capture runtime data, evaluate strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.replay.hashing import HASH_ALGORITHM, HASH_VERSION


INTEGRITY_VALIDATION = "in_memory_hash_record_integrity_validation"
INTEGRITY_VALIDATOR = "hash_record_integrity_validator"
EXPECTED_HASH_RECORD = "expected_hash_record"
OBSERVED_HASH_RECORD = "observed_hash_record"
INTEGRITY_VALIDATION_RESULT = "integrity_validation_result"
VALID_REDACTION_STATUS: tuple[str, ...] = (
    "not_required",
    "clear",
    "redacted",
)

INTEGRITY_VALIDATION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "in_memory_only",
    "evidence_only",
    "non_authoritative",
    "no_package_completeness",
    "no_package_creation",
    "no_filesystem_access",
    "no_storage_finalization",
    "no_runtime_capture",
    "no_evaluation_or_promotion",
    "no_broker_authority",
    "no_execution_authority",
    "no_live_trading_authority",
)


@dataclass(frozen=True, slots=True)
class ExpectedHashRecord:
    """Expected non-authoritative hash record."""

    record: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ObservedHashRecord:
    """Observed non-authoritative hash record."""

    record: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class IntegrityValidationInput:
    """Already-loaded expected and observed hash records."""

    expected: Mapping[str, Any]
    observed: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class IntegrityValidationResult:
    """Static integrity validation result vocabulary."""

    result_type: str = INTEGRITY_VALIDATION_RESULT
    authority_boundary: tuple[str, ...] = INTEGRITY_VALIDATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class IntegrityValidation:
    """Static integrity validation vocabulary."""

    name: str = INTEGRITY_VALIDATION
    authority_boundary: tuple[str, ...] = INTEGRITY_VALIDATION_AUTHORITY_BOUNDARY


@dataclass(frozen=True, slots=True)
class IntegrityValidator:
    """Static integrity validator vocabulary."""

    name: str = INTEGRITY_VALIDATOR
    input_model: str = f"{EXPECTED_HASH_RECORD}:{OBSERVED_HASH_RECORD}"


def validate_hash(
    expected_hash_record: Mapping[str, Any],
    observed_hash_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare expected and observed hash records without package authority."""

    return validate_integrity(expected_hash_record, observed_hash_record)


def verify_integrity(
    expected_hash_record: Mapping[str, Any],
    observed_hash_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Alias for integrity validation over already-built hash records."""

    return validate_integrity(expected_hash_record, observed_hash_record)


def validate_integrity(
    expected_hash_record: Mapping[str, Any],
    observed_hash_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a non-authoritative integrity result for hash records."""

    _check_record(expected_hash_record, "expected")
    _check_record(observed_hash_record, "observed")
    _validate_record_pair(expected_hash_record, observed_hash_record)

    status = "valid"
    reason = "hash_match"
    if expected_hash_record["digest"] != observed_hash_record["digest"]:
        status = "mismatch"
        reason = "hash_mismatch"

    return {
        "result_type": INTEGRITY_VALIDATION_RESULT,
        "integrity_status": status,
        "reason": reason,
        "hash_match": status == "valid",
        "expected_hash_type": expected_hash_record["hash_type"],
        "observed_hash_type": observed_hash_record["hash_type"],
        "hash_algorithm": HASH_ALGORITHM,
        "hash_version": HASH_VERSION,
        "evidence_only": True,
        "non_authoritative": True,
        "package_completeness": False,
        "authority_boundary": INTEGRITY_VALIDATION_AUTHORITY_BOUNDARY,
    }


def _check_record(record: Mapping[str, Any], label: str) -> None:
    if not isinstance(record, Mapping):
        raise TypeError(f"{label} hash record must be already-loaded metadata")
    if not record.get("digest"):
        raise ValueError(f"missing {label} hash")
    if record.get("hash_algorithm") != HASH_ALGORITHM:
        raise ValueError("missing or unsupported hash algorithm metadata")
    if record.get("hash_version") != HASH_VERSION:
        raise ValueError("missing or unsupported hash version metadata")
    if not record.get("hash_type"):
        raise ValueError(f"missing {label} hash type")

    metadata = record.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("malformed provenance")
    _check_metadata(metadata)


def _check_metadata(metadata: Mapping[str, Any]) -> None:
    provenance = metadata.get("provenance")
    if not isinstance(provenance, str):
        raise ValueError("malformed provenance")
    if not provenance:
        raise ValueError("missing provenance")

    redaction_status = metadata.get("redaction_status")
    if not redaction_status:
        raise ValueError("missing redaction status")
    if redaction_status not in VALID_REDACTION_STATUS:
        raise ValueError("invalid redaction status")

    if metadata.get("sensitive_data_status") != "clear":
        raise ValueError("sensitive data exposure")

    _validate_source_reference(metadata)
    _validate_run_id_alignment(metadata)


def _validate_record_pair(
    expected_hash_record: Mapping[str, Any],
    observed_hash_record: Mapping[str, Any],
) -> None:
    if expected_hash_record["hash_type"] != observed_hash_record["hash_type"]:
        raise ValueError("hash type mismatch")

    expected_metadata = expected_hash_record["metadata"]
    observed_metadata = observed_hash_record["metadata"]
    if expected_metadata.get("canonical_run_id") != observed_metadata.get(
        "canonical_run_id"
    ):
        raise ValueError("mixed run_id integrity input")


def _validate_source_reference(metadata: Mapping[str, Any]) -> None:
    known_references = metadata.get("known_source_references")
    source_reference = metadata.get("source_reference")
    if not isinstance(known_references, tuple) or not known_references:
        raise ValueError("unknown source references")
    if source_reference not in known_references:
        raise ValueError("unknown source references")


def _validate_run_id_alignment(metadata: Mapping[str, Any]) -> None:
    canonical_run_id = metadata.get("canonical_run_id")
    if not canonical_run_id:
        raise ValueError("mixed run_id integrity input")
    for run_id in metadata.get("run_ids", (canonical_run_id,)):
        if run_id != canonical_run_id:
            raise ValueError("mixed run_id integrity input")
