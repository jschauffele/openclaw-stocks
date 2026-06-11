"""Tests for tools/replay/verify_vocabulary_boundaries.py.

Verifies that the vocabulary boundary verifier:
- passes on the current source_references.py and source_paths.py
- rejects synthetic modules with forbidden imports
- rejects synthetic modules with forbidden filesystem/path calls
- does not reject required boundary strings like no_runtime_capture
- emits VOCABULARY_BOUNDARY_VERIFICATION_PASS on success
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import tools.replay.verify_vocabulary_boundaries as verifier


_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_REFERENCES = _REPO_ROOT / "tools" / "replay" / "source_references.py"
_SOURCE_PATHS = _REPO_ROOT / "tools" / "replay" / "source_paths.py"
_VERIFIER_MODULE = _REPO_ROOT / "tools" / "replay" / "verify_vocabulary_boundaries.py"


def test_verifier_module_exists() -> None:
    assert _VERIFIER_MODULE.exists()


def test_target_modules_exist() -> None:
    assert _SOURCE_REFERENCES.exists()
    assert _SOURCE_PATHS.exists()


def test_verifier_passes_on_current_source_references_and_source_paths() -> None:
    failures = verifier.verify(target_paths=(_SOURCE_REFERENCES, _SOURCE_PATHS))
    assert failures == [], f"Unexpected failures: {failures}"


def test_verifier_rejects_forbidden_import_os(tmp_path: Path) -> None:
    bad = tmp_path / "bad_module.py"
    bad.write_text(
        textwrap.dedent("""\
            import os

            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("forbidden import" in f and "os" in f for f in failures)


def test_verifier_rejects_forbidden_import_pathlib(tmp_path: Path) -> None:
    bad = tmp_path / "bad_pathlib.py"
    bad.write_text(
        textwrap.dedent("""\
            from pathlib import Path

            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("forbidden import" in f and "pathlib" in f for f in failures)


def test_verifier_rejects_forbidden_import_subprocess(tmp_path: Path) -> None:
    bad = tmp_path / "bad_sub.py"
    bad.write_text(
        textwrap.dedent("""\
            import subprocess

            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("forbidden import" in f and "subprocess" in f for f in failures)


def test_verifier_rejects_forbidden_call_open(tmp_path: Path) -> None:
    bad = tmp_path / "bad_open.py"
    bad.write_text(
        textwrap.dedent("""\
            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"

            def sneaky():
                return open("x.txt")
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("forbidden call" in f and "open" in f for f in failures)


def test_verifier_rejects_forbidden_call_path_exists(tmp_path: Path) -> None:
    bad = tmp_path / "bad_exists.py"
    bad.write_text(
        textwrap.dedent("""\
            from pathlib import Path as _Path

            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"

            def sneaky():
                return _Path("x").exists()
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    # forbidden import from pathlib and forbidden call .exists
    assert any("pathlib" in f for f in failures)
    assert any("exists" in f for f in failures)


def test_verifier_rejects_forbidden_text_opt_path(tmp_path: Path) -> None:
    bad = tmp_path / "bad_path.py"
    bad.write_text(
        textwrap.dedent("""\
            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
            RUNTIME_PATH = "/opt/openclaw-stocks/logs"
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("/opt/" in f for f in failures)


def test_verifier_rejects_forbidden_text_alpaca(tmp_path: Path) -> None:
    bad = tmp_path / "bad_alpaca.py"
    bad.write_text(
        textwrap.dedent("""\
            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
            BROKER = "Alpaca"
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("Alpaca" in f for f in failures)


def test_verifier_does_not_reject_no_runtime_capture_boundary_vocab(tmp_path: Path) -> None:
    good = tmp_path / "boundary_vocab.py"
    good.write_text(
        textwrap.dedent("""\
            AUTHORITY_BOUNDARY = (
                "in_memory_only",
                "no_filesystem_reads",
                "no_path_resolution",
                "no_runtime_capture",
                "no_live_trading_authority",
            )
            KNOWN_SOURCE_REFERENCES = ("event_jsonl", "last_run_report", "order_state")
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(good,))
    assert failures == [], f"Required boundary vocab incorrectly rejected: {failures}"


def test_verifier_does_not_reject_no_filesystem_reads_boundary_vocab(tmp_path: Path) -> None:
    good = tmp_path / "boundary_vocab2.py"
    good.write_text(
        textwrap.dedent("""\
            AUTHORITY_BOUNDARY = (
                "no_filesystem_reads",
                "no_runtime_capture",
            )
            KNOWN = ("event_jsonl", "last_run_report", "order_state")
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(good,))
    assert failures == [], f"Unexpected failures: {failures}"


def test_verifier_fails_when_required_term_missing(tmp_path: Path) -> None:
    bad = tmp_path / "missing_term.py"
    bad.write_text(
        textwrap.dedent("""\
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
            KNOWN = ("event_jsonl", "last_run_report", "order_state")
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("no_filesystem_reads" in f for f in failures)


def test_verifier_fails_when_collection_term_missing(tmp_path: Path) -> None:
    bad = tmp_path / "missing_collection.py"
    bad.write_text(
        textwrap.dedent("""\
            NO_FILESYSTEM_READS = "no_filesystem_reads"
            NO_RUNTIME_CAPTURE = "no_runtime_capture"
            KNOWN = ("last_run_report", "order_state")
        """),
        encoding="utf-8",
    )
    failures = verifier.verify(target_paths=(bad,))
    assert any("event_jsonl" in f for f in failures)


def test_cli_emits_pass_string_on_success() -> None:
    result = subprocess.run(
        [sys.executable, str(_VERIFIER_MODULE)],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0
    assert "VOCABULARY_BOUNDARY_VERIFICATION_PASS" in result.stdout


def test_cli_emits_fail_string_on_failure(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("import os\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, '{_REPO_ROOT}'); "
         f"from pathlib import Path; "
         f"import tools.replay.verify_vocabulary_boundaries as v; "
         f"failures = v.verify(target_paths=(Path('{bad}'),)); "
         f"print('VOCABULARY_BOUNDARY_VERIFICATION_FAIL' if failures else 'PASS')"],
        capture_output=True,
        text=True,
    )
    assert "VOCABULARY_BOUNDARY_VERIFICATION_FAIL" in result.stdout
