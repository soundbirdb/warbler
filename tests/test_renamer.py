"""Tests for warbler.renamer."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.renamer import (
    RenameResult,
    RenameReport,
    _build_destination,
    rename_file,
    batch_rename,
)

_FP = "abcdef123456" + "0" * 52  # 64-char hex


def test_build_destination_includes_fingerprint_prefix(tmp_path):
    src = tmp_path / "song.mp3"
    dest = _build_destination(src, _FP, "{stem}_{fingerprint}")
    assert dest.name == "song_abcdef123456.mp3"


def test_build_destination_custom_template(tmp_path):
    src = tmp_path / "track.flac"
    dest = _build_destination(src, _FP, "fp_{fingerprint}")
    assert dest.name == "fp_abcdef123456.flac"


class TestRenameFile:
    def test_skips_when_no_fingerprint(self, tmp_path):
        src = tmp_path / "a.mp3"
        src.touch()
        with patch("warbler.renamer.read_fingerprint", return_value=None):
            result = rename_file(src)
        assert not result.renamed
        assert result.error is None

    def test_returns_error_on_read_exception(self, tmp_path):
        src = tmp_path / "b.mp3"
        src.touch()
        with patch("warbler.renamer.read_fingerprint", side_effect=RuntimeError("bad")):
            result = rename_file(src)
        assert result.error == "bad"
        assert not result.renamed

    def test_renames_file(self, tmp_path):
        src = tmp_path / "song.mp3"
        src.touch()
        with patch("warbler.renamer.read_fingerprint", return_value=_FP):
            result = rename_file(src)
        assert result.renamed
        expected = tmp_path / "song_abcdef123456.mp3"
        assert result.destination == expected
        assert expected.exists()

    def test_dry_run_does_not_rename(self, tmp_path):
        src = tmp_path / "song.mp3"
        src.touch()
        with patch("warbler.renamer.read_fingerprint", return_value=_FP):
            result = rename_file(src, dry_run=True)
        assert result.renamed
        assert src.exists()  # original untouched


class TestBatchRename:
    def test_report_counts(self, tmp_path):
        paths = [tmp_path / f"f{i}.mp3" for i in range(3)]
        for p in paths:
            p.touch()
        returns = [_FP, None, RuntimeError("oops")]

        def fake_read(p):
            v = returns.pop(0)
            if isinstance(v, Exception):
                raise v
            return v

        with patch("warbler.renamer.read_fingerprint", side_effect=fake_read):
            report = batch_rename(paths)

        assert report.renamed_count == 1
        assert report.skipped_count == 1
        assert report.error_count == 1
