"""Tests for warbler.archiver."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.archiver import (
    ArchiveReport,
    ArchiveResult,
    archive_file,
    batch_archive,
)


def _fake_read(fp: str):
    def _read(path: Path):
        return fp
    return _read


class TestArchiveFile:
    def test_moves_file_into_bucket_subdir(self, tmp_path):
        src = tmp_path / "song.mp3"
        src.write_bytes(b"data")
        archive_root = tmp_path / "archive"
        result = archive_file(src, archive_root, copy=True, _read=_fake_read("abcdef"))
        assert result.success
        assert result.destination == archive_root / "ab" / "song.mp3"
        assert result.destination.exists()

    def test_untagged_files_go_to_untagged_bucket(self, tmp_path):
        src = tmp_path / "unknown.mp3"
        src.write_bytes(b"data")
        archive_root = tmp_path / "archive"
        result = archive_file(src, archive_root, copy=True, _read=_fake_read(None))
        assert result.success
        assert result.destination == archive_root / "untagged" / "unknown.mp3"

    def test_skips_when_destination_exists_and_no_overwrite(self, tmp_path):
        src = tmp_path / "song.mp3"
        src.write_bytes(b"data")
        archive_root = tmp_path / "archive"
        dest = archive_root / "ab" / "song.mp3"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"existing")
        result = archive_file(src, archive_root, copy=True, _read=_fake_read("abcdef"))
        assert result.skipped
        assert not result.success

    def test_overwrites_when_flag_set(self, tmp_path):
        src = tmp_path / "song.mp3"
        src.write_bytes(b"new")
        archive_root = tmp_path / "archive"
        dest = archive_root / "ab" / "song.mp3"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"old")
        result = archive_file(src, archive_root, copy=True, overwrite=True, _read=_fake_read("abcdef"))
        assert result.success
        assert dest.read_bytes() == b"new"

    def test_returns_error_result_on_exception(self, tmp_path):
        src = tmp_path / "missing.mp3"
        archive_root = tmp_path / "archive"
        result = archive_file(src, archive_root, _read=_fake_read("abcdef"))
        assert result.error is not None
        assert not result.success


class TestBatchArchive:
    def test_report_counts(self, tmp_path):
        files = []
        for i in range(3):
            p = tmp_path / f"track{i}.mp3"
            p.write_bytes(b"x")
            files.append(p)
        archive_root = tmp_path / "archive"
        with patch("warbler.archiver.read_fingerprint", return_value="ff1234"):
            report = batch_archive(files, archive_root, copy=True)
        assert report.moved_count == 3
        assert report.skipped_count == 0
        assert report.error_count == 0

    def test_mixed_report(self, tmp_path):
        good = tmp_path / "good.mp3"
        good.write_bytes(b"x")
        bad = tmp_path / "bad.mp3"  # does not exist -> error on move
        archive_root = tmp_path / "archive"
        with patch("warbler.archiver.read_fingerprint", return_value="aa0000"):
            report = batch_archive([good, bad], archive_root)
        assert report.moved_count + report.error_count == 2
