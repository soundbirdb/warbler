"""Tests for warbler.tagger_cleaner."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from warbler.tagger_cleaner import (
    TagCleanResult,
    TagCleanReport,
    batch_clean,
    clean_tag,
)

_FAKE_FP = "ab" * 32  # 64-char hex string


def _read_with(value: Optional[str]):
    return lambda _path: value


class TestCleanTag:
    def test_skips_unsupported_extension(self, tmp_path):
        p = tmp_path / "track.wav"
        p.touch()
        result = clean_tag(p, read_fn=_read_with(_FAKE_FP))
        assert not result.removed
        assert result.error is not None
        assert "Unsupported" in result.error

    def test_skips_when_no_fingerprint(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()
        result = clean_tag(p, read_fn=_read_with(None))
        assert not result.removed
        assert result.error is None
        assert result.success

    def test_dry_run_does_not_call_remover(self, tmp_path):
        p = tmp_path / "track.flac"
        p.touch()
        with patch("warbler.tagger_cleaner._remove_tag_flac") as mock_rm:
            result = clean_tag(p, dry_run=True, read_fn=_read_with(_FAKE_FP))
        mock_rm.assert_not_called()
        assert result.removed is True
        assert result.dry_run is True

    def test_removes_mp3_tag(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()
        with patch("warbler.tagger_cleaner._remove_tag_mp3") as mock_rm:
            result = clean_tag(p, dry_run=False, read_fn=_read_with(_FAKE_FP))
        mock_rm.assert_called_once_with(p)
        assert result.removed is True
        assert result.success

    def test_removes_flac_tag(self, tmp_path):
        p = tmp_path / "track.flac"
        p.touch()
        with patch("warbler.tagger_cleaner._remove_tag_flac") as mock_rm:
            result = clean_tag(p, dry_run=False, read_fn=_read_with(_FAKE_FP))
        mock_rm.assert_called_once_with(p)
        assert result.removed is True

    def test_returns_error_result_on_exception(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()

        def bad_read(_p):
            raise RuntimeError("disk error")

        result = clean_tag(p, read_fn=bad_read)
        assert not result.success
        assert "disk error" in result.error


class TestTagCleanReport:
    def _make_report(self) -> TagCleanReport:
        return TagCleanReport(results=[
            TagCleanResult(path=Path("a.mp3"), removed=True, dry_run=False),
            TagCleanResult(path=Path("b.mp3"), removed=True, dry_run=False),
            TagCleanResult(path=Path("c.flac"), removed=False, dry_run=False),
            TagCleanResult(path=Path("d.mp3"), removed=False, dry_run=False,
                           error="oops"),
        ])

    def test_removed_count(self):
        assert self._make_report().removed_count == 2

    def test_skipped_count(self):
        assert self._make_report().skipped_count == 1

    def test_error_count(self):
        assert self._make_report().error_count == 1


class TestBatchClean:
    def test_processes_all_paths(self, tmp_path):
        paths = [tmp_path / "a.mp3", tmp_path / "b.flac"]
        for p in paths:
            p.touch()
        with patch("warbler.tagger_cleaner._remove_tag_mp3"), \
             patch("warbler.tagger_cleaner._remove_tag_flac"):
            report = batch_clean(paths, read_fn=_read_with(_FAKE_FP))
        assert len(report.results) == 2
        assert report.removed_count == 2

    def test_empty_paths_gives_empty_report(self):
        report = batch_clean([], read_fn=_read_with(None))
        assert report.removed_count == 0
        assert report.error_count == 0
