"""Tests for warbler.inspector."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.inspector import (
    FileInspection,
    InspectionReport,
    inspect_file,
    inspect_files,
)
from warbler.metadata import FileMetadata


_FAKE_FP = "ab" * 32  # 64-char hex string


def _meta(title="Title", artist="Artist", album="Album") -> FileMetadata:
    return FileMetadata(title=title, artist=artist, album=album)


# ---------------------------------------------------------------------------
# FileInspection properties
# ---------------------------------------------------------------------------

class TestFileInspection:
    def test_is_tagged_true_when_fingerprint_present(self):
        insp = FileInspection(Path("a.mp3"), _FAKE_FP, True, True, True)
        assert insp.is_tagged is True

    def test_is_tagged_false_when_no_fingerprint(self):
        insp = FileInspection(Path("a.mp3"), None, True, True, True)
        assert insp.is_tagged is False

    def test_is_complete_requires_all_fields(self):
        insp = FileInspection(Path("a.mp3"), _FAKE_FP, True, True, True)
        assert insp.is_complete is True

    def test_is_complete_false_when_missing_artist(self):
        insp = FileInspection(Path("a.mp3"), _FAKE_FP, True, False, True)
        assert insp.is_complete is False

    def test_is_complete_false_when_no_fingerprint(self):
        insp = FileInspection(Path("a.mp3"), None, True, True, True)
        assert insp.is_complete is False


# ---------------------------------------------------------------------------
# InspectionReport aggregates
# ---------------------------------------------------------------------------

class TestInspectionReport:
    def _report(self):
        return InspectionReport(inspections=[
            FileInspection(Path("a.mp3"), _FAKE_FP, True, True, True),
            FileInspection(Path("b.mp3"), None, False, False, False),
            FileInspection(Path("c.mp3"), None, False, False, False, error="boom"),
        ])

    def test_total(self):
        assert self._report().total == 3

    def test_tagged_count(self):
        assert self._report().tagged_count == 1

    def test_complete_count(self):
        assert self._report().complete_count == 1

    def test_error_count(self):
        assert self._report().error_count == 1


# ---------------------------------------------------------------------------
# inspect_file
# ---------------------------------------------------------------------------

@patch("warbler.inspector.read_metadata")
@patch("warbler.inspector.read_fingerprint")
def test_inspect_file_fully_tagged(mock_fp, mock_meta):
    mock_fp.return_value = _FAKE_FP
    mock_meta.return_value = _meta()
    result = inspect_file(Path("song.mp3"))
    assert result.is_complete
    assert result.error is None


@patch("warbler.inspector.read_metadata")
@patch("warbler.inspector.read_fingerprint")
def test_inspect_file_untagged(mock_fp, mock_meta):
    mock_fp.return_value = None
    mock_meta.return_value = _meta(title="", artist="", album="")
    result = inspect_file(Path("song.flac"))
    assert not result.is_tagged
    assert not result.is_complete


@patch("warbler.inspector.read_fingerprint", side_effect=RuntimeError("bad file"))
def test_inspect_file_captures_error(mock_fp):
    result = inspect_file(Path("broken.mp3"))
    assert result.error == "bad file"
    assert not result.is_tagged


# ---------------------------------------------------------------------------
# inspect_files
# ---------------------------------------------------------------------------

@patch("warbler.inspector.read_metadata")
@patch("warbler.inspector.read_fingerprint")
def test_inspect_files_returns_report(mock_fp, mock_meta):
    mock_fp.return_value = _FAKE_FP
    mock_meta.return_value = _meta()
    paths = [Path("a.mp3"), Path("b.flac")]
    report = inspect_files(paths)
    assert report.total == 2
    assert report.tagged_count == 2
    assert report.complete_count == 2
