from __future__ import annotations

import importlib
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


PROJECT_ROOT = Path("/opt/openclaw-stocks")

REQUIRED_FILES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "data_models.py",
    PROJECT_ROOT / "market_data.py",
    PROJECT_ROOT / "alpaca_data_provider.py",
    PROJECT_ROOT / "test_market_data.py",
)

REQUIRED_ENV_GROUPS = (
    ("ALPACA_API_KEY", "APCA_API_KEY_ID"),
    ("ALPACA_SECRET_KEY", "APCA_API_SECRET_KEY"),
)

OPTIONAL_ENV_GROUPS = (
    ("ALPACA_BASE_URL", "APCA_API_BASE_URL"),
)


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _check_file(path: Path) -> tuple[bool, str]:
    exists = path.is_file()
    return exists, f"{path}: {'OK' if exists else 'MISSING'}"


def _check_env(group: tuple[str, ...], required: bool) -> tuple[bool, str]:
    value = _first_env(*group)
    label = " / ".join(group)
    if value:
        return True, f"{label}: OK"
    if required:
        return False, f"{label}: MISSING"
    return True, f"{label}: not set (optional)"


def _check_base_url() -> tuple[bool, str]:
    base_url = _first_env("ALPACA_BASE_URL", "APCA_API_BASE_URL")
    if not base_url:
        return True, "Base URL: not set, SDK default market data endpoint will be used"

    host = (urlparse(base_url).hostname or "").lower()
    if host in {"paper-api.alpaca.markets", "api.alpaca.markets"}:
        return True, (
            f"Base URL: {base_url} detected as trading endpoint; "
            "provider must ignore it for historical market data"
        )

    return True, f"Base URL: {base_url}"


def _check_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return False, f"import {module_name}: FAIL ({exc})"
    return True, f"import {module_name}: OK"


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    print("=== PRECHECK ===")

    checks: list[tuple[bool, str]] = []

    for path in REQUIRED_FILES:
        checks.append(_check_file(path))

    for group in REQUIRED_ENV_GROUPS:
        checks.append(_check_env(group, required=True))

    for group in OPTIONAL_ENV_GROUPS:
        checks.append(_check_env(group, required=False))

    checks.append(_check_base_url())
    checks.append(_check_import("data_models"))
    checks.append(_check_import("market_data"))
    checks.append(_check_import("alpaca_data_provider"))

    all_ok = True
    for ok, message in checks:
        print(message)
        if not ok:
            all_ok = False

    if all_ok:
        print("PRECHECK RESULT: PASS")
        return 0

    print("PRECHECK RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
