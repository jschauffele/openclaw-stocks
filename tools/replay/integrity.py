"""Inert integrity status vocabulary for replay prerequisites.

This module defines integrity status labels only. It does not validate
integrity, compute or compare hashes, serialize manifests or packages, create
packages, touch the filesystem, capture runtime artifacts, evaluate
strategies, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass


INTEGRITY_STATUS: tuple[str, ...] = (
    "missing",
    "present",
    "unavailable",
    "not_validated",
)


@dataclass(frozen=True, slots=True)
class IntegrityStatus:
    """Static integrity status vocabulary."""

    values: tuple[str, ...] = INTEGRITY_STATUS
