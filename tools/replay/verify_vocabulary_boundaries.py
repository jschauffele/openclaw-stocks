"""Deterministic vocabulary boundary verifier for replay source modules.

Checks only tools/replay/source_references.py and tools/replay/source_paths.py.
Uses AST parsing and fixed text checks. Does not import target modules, read
runtime artifacts, resolve paths, discover files dynamically, capture runtime
data, evaluate strategies, or authorize execution.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

TARGET_MODULES: tuple[Path, ...] = (
    _REPO_ROOT / "tools" / "replay" / "source_references.py",
    _REPO_ROOT / "tools" / "replay" / "source_paths.py",
)

FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    ("os", "pathlib", "glob", "shutil", "subprocess", "requests")
)

FORBIDDEN_NAMES: frozenset[str] = frozenset(
    ("open", "Path", "read_text", "write_text", "exists", "glob", "listdir", "stat")
)

FORBIDDEN_TEXT_MARKERS: tuple[str, ...] = (
    "/opt/",
    "/var/",
    "Alpaca",
    "IBKR",
    "TWS",
)

ALLOWED_BOUNDARY_VOCAB: frozenset[str] = frozenset(
    ("no_runtime_capture", "no_filesystem_reads", "no_path_resolution")
)

REQUIRED_IN_BOTH: tuple[str, ...] = (
    "no_filesystem_reads",
    "no_runtime_capture",
)

REQUIRED_IN_SOURCE_PATHS_ONLY: tuple[str, ...] = ("no_path_resolution",)

REQUIRED_ACROSS_COLLECTION: tuple[str, ...] = (
    "event_jsonl",
    "last_run_report",
    "order_state",
)


def _read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_forbidden_imports(source: str, path: Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"SyntaxError in {path.name}: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in FORBIDDEN_IMPORTS:
                    failures.append(f"{path.name}: forbidden import '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            top = module.split(".")[0]
            if top in FORBIDDEN_IMPORTS:
                failures.append(f"{path.name}: forbidden import from '{module}'")
    return failures


def _check_forbidden_calls(source: str, path: Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name and name in FORBIDDEN_NAMES and name not in ALLOWED_BOUNDARY_VOCAB:
                failures.append(f"{path.name}: forbidden call/attribute '{name}'")
    return failures


def _check_forbidden_text(source: str, path: Path) -> list[str]:
    failures: list[str] = []
    for marker in FORBIDDEN_TEXT_MARKERS:
        if marker in source:
            failures.append(f"{path.name}: forbidden text marker '{marker}'")
    return failures


def _check_required_in_both(sources: dict[Path, str]) -> list[str]:
    failures: list[str] = []
    for term in REQUIRED_IN_BOTH:
        for path, source in sources.items():
            if term not in source:
                failures.append(f"{path.name}: required term '{term}' is missing")
    return failures


def _check_required_in_source_paths(sources: dict[Path, str]) -> list[str]:
    failures: list[str] = []
    source_paths_entries = {p: s for p, s in sources.items() if p.name == "source_paths.py"}
    if not source_paths_entries:
        return failures
    combined = "\n".join(source_paths_entries.values())
    for term in REQUIRED_IN_SOURCE_PATHS_ONLY:
        if term not in combined:
            failures.append(f"source_paths.py: required term '{term}' is missing")
    return failures


def _check_required_across_collection(sources: dict[Path, str]) -> list[str]:
    combined = "\n".join(sources.values())
    failures: list[str] = []
    for term in REQUIRED_ACROSS_COLLECTION:
        if term not in combined:
            failures.append(f"collection: required term '{term}' not found in any target module")
    return failures


def verify(target_paths: tuple[Path, ...] = TARGET_MODULES) -> list[str]:
    """Return list of failure messages; empty list means PASS."""
    all_failures: list[str] = []
    sources: dict[Path, str] = {}

    for path in target_paths:
        if not path.exists():
            all_failures.append(f"target module not found: {path}")
            continue
        source = _read_source(path)
        sources[path] = source
        all_failures.extend(_check_forbidden_imports(source, path))
        all_failures.extend(_check_forbidden_calls(source, path))
        all_failures.extend(_check_forbidden_text(source, path))

    all_failures.extend(_check_required_in_both(sources))
    all_failures.extend(_check_required_in_source_paths(sources))
    all_failures.extend(_check_required_across_collection(sources))

    return all_failures


def main() -> int:
    failures = verify()
    if failures:
        for line in failures:
            print(f"FAIL: {line}")
        print("VOCABULARY_BOUNDARY_VERIFICATION_FAIL")
        return 1
    print("VOCABULARY_BOUNDARY_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
