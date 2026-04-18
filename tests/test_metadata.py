"""Tests for warbler.metadata."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.metadata import (
    FileMetadata,
    _COMMON_FIELDS,
    batch_read_metadata,
    format_metadata_report,
    read_metadata,
)


def _full_fields() -> dict:
    return {f: f"value_{f}" for f in _COMMON_FIELDS}


# ---------------------------------------------------------------------------
# FileMetadata
# ---------------------------------------------------------------------------

class TestFileMetadata:
    def test_is_complete_true_when_all_fields_present(self):
        fm = FileMetadata(path=Path("a.mp3"), fields=_full_fields())
        assert fm.is_complete is True

    def test_is_complete_false_when_field_missing(self):
        fields = _full_fields()
        del fields["artist"]
        fm = FileMetadata(path=Path("a.mp3"), fields=fields)
        assert fm.is_complete is False

    def test_missing_fields_lists_absent_keys(self):
        fields = _full_fields()
        del fields["title"]
        del fields["genre"]
        fm = FileMetadata(path=Path("a.mp3"), fields=fields)
        assert set(fm.missing_fields) == {"title", "genre"}

    def test_missing_fields_empty_when_complete(self):
        fm = FileMetadata(path=Path("a.flac"), fields=_full_fields())
        assert fm.missing_fields == []


# ---------------------------------------------------------------------------
# read_metadata
# ---------------------------------------------------------------------------

class TestReadMetadata:
    def test_unsupported_extension_returns_error(self):
        result = read_metadata(Path("track.ogg"))
        assert result.error is not None
        assert "Unsupported" in result.error

    def test_mp3_reads_fields(self):
        fake_audio = {"title": ["My Song"], "artist": ["Band"]}
        with patch("warbler.metadata.EasyID3", return_value=fake_audio):
            result = read_metadata(Path("track.mp3"))
        assert result.fields["title"] == "My Song"
        assert result.fields["artist"] == "Band"
        assert result.error is None

    def test_flac_reads_fields(self):
        fake_audio = {"album": ["Greatest Hits"], "date": ["2024"]}
        with patch("warbler.metadata.FLAC", return_value=fake_audio):
            result = read_metadata(Path("track.flac"))
        assert result.fields["album"] == "Greatest Hits"

    def test_exception_captured_as_error(self):
        with patch("warbler.metadata.EasyID3", side_effect=Exception("bad file")):
            result = read_metadata(Path("broken.mp3"))
        assert result.error == "bad file"
        assert result.fields == {}


# ---------------------------------------------------------------------------
# format_metadata_report
# ---------------------------------------------------------------------------

class TestFormatMetadataReport:
    def test_counts_appear_in_output(self):
        records = [
            FileMetadata(path=Path("a.mp3"), fields=_full_fields()),
            FileMetadata(path=Path("b.mp3"), fields={"title": "T"}),
        ]
        report = format_metadata_report(records)
        assert "Files scanned : 2" in report
        assert "Complete      : 1" in report

    def test_incomplete_files_listed(self):
        records = [
            FileMetadata(path=Path("b.mp3"), fields={"title": "T"}),
        ]
        report = format_metadata_report(records)
        assert "b.mp3" in report
        assert "missing:" in report

    def test_no_incomplete_section_when_all_complete(self):
        records = [FileMetadata(path=Path("a.flac"), fields=_full_fields())]
        report = format_metadata_report(records)
        assert "Incomplete files" not in report

    def test_batch_read_delegates_to_read_metadata(self):
        paths = [Path("x.ogg"), Path("y.ogg")]
        results = batch_read_metadata(paths)
        assert len(results) == 2
        assert all(r.error for r in results)
