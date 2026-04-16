"""Tests for warbler.exporter."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.exporter import (
    collect_fingerprint_records,
    export,
    export_to_csv,
    export_to_json,
)

_FP = "a" * 64


def _fake_read(path: Path):
    """Return a fingerprint only for paths whose name contains 'tagged'."""
    return _FP if "tagged" in path.name else None


class TestCollectFingerprintRecords:
    def test_includes_tagged_files(self, tmp_path):
        tagged = tmp_path / "tagged_song.mp3"
        tagged.touch()
        with patch("warbler.exporter.read_fingerprint", side_effect=_fake_read):
            records = collect_fingerprint_records([tagged])
        assert len(records) == 1
        assert records[0]["fingerprint"] == _FP

    def test_skips_untagged_files(self, tmp_path):
        untagged = tmp_path / "bare_song.mp3"
        untagged.touch()
        with patch("warbler.exporter.read_fingerprint", return_value=None):
            records = collect_fingerprint_records([untagged])
        assert records == []

    def test_mixed_files(self, tmp_path):
        files = [tmp_path / "tagged_a.mp3", tmp_path / "bare_b.mp3"]
        for f in files:
            f.touch()
        with patch("warbler.exporter.read_fingerprint", side_effect=_fake_read):
            records = collect_fingerprint_records(files)
        assert len(records) == 1


class TestExportToJson:
    def test_creates_valid_json(self, tmp_path):
        records = [{"file": "a.mp3", "fingerprint": _FP}]
        dest = tmp_path / "out.json"
        export_to_json(records, dest)
        data = json.loads(dest.read_text())
        assert data == records

    def test_creates_parent_dirs(self, tmp_path):
        dest = tmp_path / "nested" / "deep" / "out.json"
        export_to_json([], dest)
        assert dest.exists()


class TestExportToCsv:
    def test_creates_valid_csv(self, tmp_path):
        records = [{"file": "a.mp3", "fingerprint": _FP}]
        dest = tmp_path / "out.csv"
        export_to_csv(records, dest)
        with dest.open() as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["fingerprint"] == _FP

    def test_header_row_present(self, tmp_path):
        dest = tmp_path / "out.csv"
        export_to_csv([], dest)
        text = dest.read_text()
        assert "file" in text and "fingerprint" in text


class TestExport:
    def test_returns_record_count(self, tmp_path):
        files = [tmp_path / "tagged_x.mp3"]
        files[0].touch()
        with patch("warbler.exporter.read_fingerprint", side_effect=_fake_read):
            count = export(files, tmp_path / "out.json", fmt="json")
        assert count == 1

    def test_unsupported_format_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unsupported export format"):
            export([], tmp_path / "out.xml", fmt="xml")

    def test_csv_format_writes_csv(self, tmp_path):
        dest = tmp_path / "out.csv"
        with patch("warbler.exporter.read_fingerprint", return_value=None):
            export([], dest, fmt="csv")
        assert dest.exists()
