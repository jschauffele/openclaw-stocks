"""Canonical bytes helper for canonical JSON text.

This module converts already-canonical JSON text to UTF-8 bytes only. It does
not create JSON text, serialize manifests or packages as authority, compute
digests, touch the filesystem, capture runtime artifacts, evaluate strategies,
or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass


CANONICAL_BYTES = "utf8_canonical_json_bytes"
CANONICAL_BYTES_ENCODING = "utf-8"
CANONICAL_BYTES_INPUT = "canonical_json_text"
CANONICAL_BYTES_OUTPUT = "canonical_json_utf8_bytes"


@dataclass(frozen=True, slots=True)
class CanonicalBytes:
    """Static canonical bytes vocabulary."""

    input_model: str = CANONICAL_BYTES_INPUT
    output_model: str = CANONICAL_BYTES_OUTPUT
    encoding: str = CANONICAL_BYTES_ENCODING


def validate_canonical_bytes(canonical_json_text: str) -> None:
    """Fail closed unless input is canonical JSON text."""

    if not isinstance(canonical_json_text, str):
        raise TypeError("canonical bytes input must be canonical JSON text")


def build_canonical_bytes(canonical_json_text: str) -> bytes:
    """Return UTF-8 bytes for already-canonical JSON text."""

    validate_canonical_bytes(canonical_json_text)
    return canonical_json_text.encode(CANONICAL_BYTES_ENCODING)
