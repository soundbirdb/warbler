"""Tests for warbler.cli."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.cli import run, _collect_audio_files
from warbler.pipeline import ProcessingResult


def _fake_result(path, status="success", fingerprint="aabbcc", error=None):
    return ProcessingResult(path=Path(path), status=status, fingerprint=fingerprint, error=error)


class TestCollectAudioFiles:
    def test_finds_supported_files(self, tmp_path):
        (tmp_path / "track.mp3").touch()
        (tmp_path / "song.flac").touch()
        (tmp_path / "notes.txt").touch()
        found = _collect_audio_files(tmp_path)
        names = {f.name for f in found}
        assert "track.mp3" in names
        assert "song.flac" in names
        assert "notes.txt" not in names

    def test_recurses_into_subdirectories(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "deep.ogg").touch()
        found = _collect_audio_files(tmp_path)
        assert any(f.name == "deep.ogg" for f in found)


class TestRun:
    def test_returns_2_for_missing_directory(self, tmp_path):
        code = run([str(tmp_path / "nonexistent")])
        assert code == 2

    def test_returns_0_when_no_files(self, tmp_path):
        code = run([str(tmp_path)])
        assert code == 0

    def test_returns_0_on_all_success(self, tmp_path):
        (tmp_path / "a.mp3").touch()
        with patch("warbler.cli.process_file", return_value=_fake_result("a.mp3")):
            code = run([str(tmp_path)])
        assert code == 0

    def test_returns_1_on_any_error(self, tmp_path):
        (tmp_path / "a.mp3").touch()
        bad = _fake_result("a.mp3", status="error", fingerprint=None, error=ValueError("x"))
        with patch("warbler.cli.process_file", return_value=bad):
            code = run([str(tmp_path)])
        assert code == 1

    def test_writes_json_report(self, tmp_path):
        (tmp_path / "a.mp3").touch()
        report_path = tmp_path / "out.json"
        with patch("warbler.cli.process_file", return_value=_fake_result("a.mp3")):
            run([str(tmp_path), "--report-json", str(report_path)])
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert "summary" in data

    def test_writes_csv_report(self, tmp_path):
        (tmp_path / "a.mp3").touch()
        report_path = tmp_path / "out.csv"
        with patch("warbler.cli.process_file", return_value=_fake_result("a.mp3")):
            run([str(tmp_path), "--report-csv", str(report_path)])
        assert report_path.exists()
        lines = report_path.read_text().splitlines()
        assert lines[0].startswith("path")

    def test_force_flag_passed_to_process_file(self, tmp_path):
        (tmp_path / "a.mp3").touch()
        with patch("warbler.cli.process_file", return_value=_fake_result("a.mp3")) as mock_pf:
            run([str(tmp_path), "--force"])
        mock_pf.assert_called_once()
        _, kwargs = mock_pf.call_args
        assert kwargs.get("force") is True
