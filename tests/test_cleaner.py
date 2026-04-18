"""Tests for warbler.cleaner."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.cleaner import (
    CleanReport,
    CleanResult,
    batch_clean,
    clean_file,
)


FAKE_FP = "abcd1234" * 8  # 64-char hex


class TestCleanFile:
    def test_skips_unsupported_format(self, tmp_path):
        p = tmp_path / "track.wav"
        p.touch()
        result = clean_file(p)
        assert not result.cleaned
        assert result.success
        assert "unsupported" in result.reason

    def test_skips_when_no_fingerprint(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()
        with patch("warbler.cleaner.read_fingerprint", return_value=None):
            result = clean_file(p)
        assert not result.cleaned
        assert "no fingerprint" in result.reason

    def test_cleans_file_with_fingerprint(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()
        with (
            patch("warbler.cleaner.read_fingerprint", return_value=FAKE_FP),
            patch("warbler.cleaner._remove_fingerprint") as mock_rm,
        ):
            result = clean_file(p)
        mock_rm.assert_called_once_with(p)
        assert result.cleaned
        assert result.success

    def test_dry_run_does_not_call_remove(self, tmp_path):
        p = tmp_path / "track.flac"
        p.touch()
        with (
            patch("warbler.cleaner.read_fingerprint", return_value=FAKE_FP),
            patch("warbler.cleaner._remove_fingerprint") as mock_rm,
        ):
            result = clean_file(p, dry_run=True)
        mock_rm.assert_not_called()
        assert result.cleaned
        assert "dry-run" in result.reason

    def test_returns_error_on_read_exception(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()
        with patch("warbler.cleaner.read_fingerprint", side_effect=RuntimeError("boom")):
            result = clean_file(p)
        assert not result.success
        assert "boom" in result.error

    def test_returns_error_on_remove_exception(self, tmp_path):
        p = tmp_path / "track.mp3"
        p.touch()
        with (
            patch("warbler.cleaner.read_fingerprint", return_value=FAKE_FP),
            patch("warbler.cleaner._remove_fingerprint", side_effect=OSError("disk full")),
        ):
            result = clean_file(p)
        assert not result.success
        assert "disk full" in result.error


class TestCleanReport:
    def _report(self):
        return CleanReport(
            results=[
                CleanResult(path=Path("a.mp3"), cleaned=True),
                CleanResult(path=Path("b.mp3"), cleaned=False, reason="no fingerprint present"),
                CleanResult(path=Path("c.mp3"), cleaned=False, error="oops"),
            ]
        )

    def test_cleaned_count(self):
        assert self._report().cleaned_count == 1

    def test_skipped_count(self):
        assert self._report().skipped_count == 1

    def test_error_count(self):
        assert self._report().error_count == 1


def test_batch_clean_aggregates_results(tmp_path):
    paths = [tmp_path / "a.mp3", tmp_path / "b.mp3"]
    for p in paths:
        p.touch()
    with (
        patch("warbler.cleaner.read_fingerprint", return_value=FAKE_FP),
        patch("warbler.cleaner._remove_fingerprint"),
    ):
        report = batch_clean(paths)
    assert report.cleaned_count == 2
    assert report.error_count == 0
