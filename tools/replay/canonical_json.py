"""Deterministic canonical JSON text helper.

This module produces canonical JSON text only. It does not produce bytes,
serialize manifests or packages as authority, compute hashes, touch the
filesystem, capture runtime artifacts, evaluate strategies, or authorize
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


SERIALIZATION_VERSION = "0.1-canonical-json"
SERIALIZATION_SCHEMA = "canonical_json_text_only"
SERIALIZATION_CONSTANTS: tuple[str, ...] = (
    "sort_object_keys",
    "recursive_object_ordering",
    "preserve_list_order",
    "minimal_whitespace",
    "utf8_safe_text",
    "reject_unsupported_types",
    "reject_ambiguous_floats",
)
CANONICAL_JSON = "json"
CANONICAL_SERIALIZATION = "canonical_json_text"
CANONICAL_SERIALIZER = "canonicalize_json"
SERIALIZATION_TYPES: tuple[str, ...] = (
    "null",
    "boolean",
    "integer",
    "string",
    "array",
    "object",
)
SERIALIZER_INPUT = "json_compatible_in_memory_value"
SERIALIZER_OUTPUT = "canonical_json_text"


@dataclass(frozen=True, slots=True)
class SerializationInput:
    """An in-memory value eligible for canonical JSON text serialization."""

    value: Any


@dataclass(frozen=True, slots=True)
class SerializationOutput:
    """Canonical JSON text output."""

    text: str


@dataclass(frozen=True, slots=True)
class SerializationSchema:
    """Static canonical JSON text serialization rules."""

    version: str = SERIALIZATION_VERSION
    schema: str = SERIALIZATION_SCHEMA
    constants: tuple[str, ...] = SERIALIZATION_CONSTANTS
    supported_types: tuple[str, ...] = SERIALIZATION_TYPES
    input_model: str = SERIALIZER_INPUT
    output_model: str = SERIALIZER_OUTPUT


@dataclass(frozen=True, slots=True)
class SerializationVersion:
    """Static serialization version vocabulary."""

    value: str = SERIALIZATION_VERSION


@dataclass(frozen=True, slots=True)
class CanonicalJson:
    """Canonical JSON text vocabulary."""

    format_name: str = CANONICAL_JSON
    serializer_name: str = CANONICAL_SERIALIZER


@dataclass(frozen=True, slots=True)
class CanonicalSerializer:
    """Canonical JSON text serializer vocabulary."""

    name: str = CANONICAL_SERIALIZER
    output_model: str = SERIALIZER_OUTPUT


def validate_serialization(value: Any) -> None:
    """Fail closed unless the value is eligible for canonical JSON text."""

    _validate_value(value)


def canonicalize_json(value: Any) -> str:
    """Return deterministic canonical JSON text for an in-memory value."""

    validate_serialization(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _validate_value(value: Any) -> None:
    if value is None or isinstance(value, str):
        return
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise TypeError("ambiguous float values are not canonical JSON eligible")
    if isinstance(value, list):
        for item in value:
            _validate_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            _validate_value(item)
        return
    raise TypeError(f"unsupported canonical JSON value type: {type(value).__name__}")
