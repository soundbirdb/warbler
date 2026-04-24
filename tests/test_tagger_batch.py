"""Tests for warbler.tagger_batch."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pytest

from warbler.tagger_batch import (
    BatchWriteReport,
    BatchWriteResult,
    batch_write_fingerprints,
    write_fingerprint_to_file,
)


def _noop_write(path: Path, fp: str) -> None:
    """Write stub that records calls without touching the filesystem."""
    _noop_write.calls[path] = fp  # type: ignore[attr-defined]


_noop_write.calls: Dict[Path, str] = {}  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def _clear_calls():
    _noop_write.calls.clear()
    yield


class TestWriteFingerprintToFile:
    def test_returns_success_result_on_ok(self):
        path = Path("/tmp/a.mp3")
        result = write_fingerprint_to_file(path, "abc123", _write=_noop_write)
        assert result.ok is True
        assert result.success is True
        assert result.error is None

    def test_calls_write_function(self):
        path = Path("/tmp/b.mp3")
        write_fingerprint_to_file(path, "deadbeef", _write=_noop_write)
        assert _noop_write.calls[path] == "deadbeef"

    def test_dry_run_skips_write(self):
        path = Path("/tmp/c.mp3")
        write_fingerprint_to_file(path, "aabbcc", dry_run=True, _write=_noop_write)
        assert path not in _noop_write.calls

    def test_dry_run_still_returns_success(self):
        path = Path("/tmp/d.mp3")
        result = write_fingerprint_to_file(path, "fp", dry_run=True, _write=_noop_write)
        assert result.ok is True

    def test_returns_error_result_on_exception(self):
        def _bad_write(p: Path, fp: str) -> None:
            raise OSError("disk full")

        path = Path("/tmp/e.mp3")
        result = write_fingerprint_to_file(path, "fp", _write=_bad_write)
        assert result.ok is False
        assert "disk full" in (result.error or "")


class TestBatchWriteFingerprints:
    def test_writes_all_entries(self):
        mapping = {Path("/a.mp3"): "fp1", Path("/b.flac"): "fp2"}
        report = batch_write_fingerprints(mapping, _write=_noop_write)
        assert report.written_count == 2
        assert report.error_count == 0

    def test_empty_mapping_gives_empty_report(self):
        report = batch_write_fingerprints({}, _write=_noop_write)
        assert report.written_count == 0
        assert report.error_count == 0

    def test_failed_paths_lists_errors(self):
        def _fail_second(p: Path, fp: str) -> None:
            if p.name == "bad.mp3":
                raise ValueError("bad file")

        mapping = {Path("/ok.mp3"): "fp1", Path("/bad.mp3"): "fp2"}
        report = batch_write_fingerprints(mapping, _write=_fail_second)
        assert report.error_count == 1
        assert Path("/bad.mp3") in report.failed_paths

    def test_dry_run_writes_nothing(self):
        mapping = {Path("/x.mp3"): "fp"}
        batch_write_fingerprints(mapping, dry_run=True, _write=_noop_write)
        assert len(_noop_write.calls) == 0
