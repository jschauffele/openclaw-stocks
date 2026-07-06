"""Configuration template for Phase 1 Tiingo ingestion.

No secrets belong in this module. TIINGO_API_TOKEN must be supplied by the
process environment only.
"""

from pathlib import Path

DEFAULT_DATA_ROOT = Path("/Users/openclawcontrol/openclaw-market-data")
TIINGO_SUBDIR = "tiingo"


def resolve_data_root(override: str | None = None) -> Path:
    """Return the data root, allowing a documented caller override."""
    return Path(override).expanduser().resolve() if override else DEFAULT_DATA_ROOT

