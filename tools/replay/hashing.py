"""Inert hashing vocabulary for replay prerequisites.

This module defines hash algorithm and version identity only. It does not
compute digests, validate hashes, serialize manifests or packages, create
packages, touch the filesystem, capture runtime artifacts, evaluate
strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass


HASH_ALGORITHM = "sha256"
HASH_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class HashAlgorithm:
    """Static hash algorithm identity."""

    name: str = HASH_ALGORITHM


@dataclass(frozen=True, slots=True)
class HashVersion:
    """Static hash vocabulary version identity."""

    value: str = HASH_VERSION
