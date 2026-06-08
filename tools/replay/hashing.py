"""Inert hashing vocabulary for replay prerequisites.

This module defines hash algorithm and version identity only. It does not
compute digests, validate hashes, serialize manifests or packages, create
packages, touch the filesystem, capture runtime artifacts, evaluate
strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


HASH_ALGORITHM = "sha256"
HASH_VERSION = "v1"
HASH_DIGEST_ENCODING = "hex"
HASH_DIGEST_FIELD_LABELS: tuple[str, ...] = (
    "hash_algorithm",
    "hash_version",
    "digest",
)

HashAlgorithmName: TypeAlias = str
HashVersionName: TypeAlias = str
HashDigestEncodingName: TypeAlias = str
HashDigestFieldLabel: TypeAlias = str


@dataclass(frozen=True, slots=True)
class HashAlgorithm:
    """Static hash algorithm identity."""

    name: str = HASH_ALGORITHM


@dataclass(frozen=True, slots=True)
class HashVersion:
    """Static hash vocabulary version identity."""

    value: str = HASH_VERSION


@dataclass(frozen=True, slots=True)
class HashDigestEncoding:
    """Static digest encoding vocabulary."""

    value: HashDigestEncodingName = HASH_DIGEST_ENCODING


@dataclass(frozen=True, slots=True)
class HashDigestFieldLabels:
    """Static digest field label vocabulary."""

    values: tuple[HashDigestFieldLabel, ...] = HASH_DIGEST_FIELD_LABELS
