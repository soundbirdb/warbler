"""Integration tests: exporter round-trips through real temp files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import patch

from warbler.exporter import export

_FP_A = "a" * 64
_FP_B = "b" * 64


def _fake_read_factory(mapping: dict):
    def _read(path: Path):
        return mapping.get(str(path))
    return _read


class TestExporterRoundTrip:
    def test_json_round_trip(self, tmp_path):
        f1 = tmp_path / "song1.mp3"
        f2 = tmp_path / "song2.flac"
        f1.touch()
        f2.touch()
        mapping = {str(f1): _FP_A, str(f2): _FP_B}
        dest = tmp_path / "export.json"

        with patch("warbler.exporter.read_fingerprint", side_effect=_fake_read_factory(mapping)):
            count = export([f1, f2], dest, fmt="json")

        assert count == 2
        data = json.loads(dest.read_text())
        fingerprints = {r["file"]: r["fingerprint"] for r in data}
        assert fingerprints[str(f1)] == _FP_A
        assert fingerprints[str(f2)] == _FP_B

    def test_csv_round_trip(self, tmp_path):
        f1 = tmp_path / "song1.mp3"
        f1.touch()
        mapping = {str(f1): _FP_A}
        dest = tmp_path / "export.csv"

        with patch("warbler.exporter.read_fingerprint", side_effect=_fake_read_factory(mapping)):
            count = export([f1], dest, fmt="csv")

        assert count == 1
        with dest.open() as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["fingerprint"] == _FP_A

    def test_empty_export_produces_empty_json_array(self, tmp_path):
        dest = tmp_path / "empty.json"
        with patch("warbler.exporter.read_fingerprint", return_value=None):
            count = export([tmp_path / "x.mp3"], dest, fmt="json")
        assert count == 0
        assert json.loads(dest.read_text()) == []

    def test_output_directory_created_automatically(self, tmp_path):
        dest = tmp_path / "subdir" / "nested" / "out.json"
        with patch("warbler.exporter.read_fingerprint", return_value=None):
            export([], dest, fmt="json")
        assert dest.exists()
