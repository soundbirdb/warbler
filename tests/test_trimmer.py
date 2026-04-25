"""Tests for warbler.trimmer."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.trimmer import (
    TrimReport,
    TrimResult,
    _build_ffmpeg_trim_cmd,
    batch_trim,
    trim_file,
)


class TestTrimResult:
    def test_success_true_when_no_error(self):
        r = TrimResult(path=Path("a.mp3"), output_path=Path("a_trimmed.mp3"))
        assert r.success is True

    def test_success_false_when_error_present(self):
        r = TrimResult(path=Path("a.mp3"), output_path=None, error="oops")
        assert r.success is False


class TestTrimReport:
    def _report(self, results):
        r = TrimReport()
        r.results = results
        return r

    def test_trimmed_count(self):
        results = [
            TrimResult(Path("a.mp3"), Path("a_t.mp3")),
            TrimResult(Path("b.mp3"), None, error="bad"),
        ]
        assert self._report(results).trimmed_count == 1

    def test_error_count(self):
        results = [
            TrimResult(Path("a.mp3"), None, error="fail"),
            TrimResult(Path("b.mp3"), None, error="fail"),
        ]
        assert self._report(results).error_count == 2

    def test_empty_report_all_zero(self):
        r = TrimReport()
        assert r.trimmed_count == 0
        assert r.error_count == 0


class TestBuildFfmpegTrimCmd:
    def test_contains_input_and_output(self):
        cmd = _build_ffmpeg_trim_cmd(Path("in.mp3"), Path("out.mp3"))
        assert "in.mp3" in cmd
        assert "out.mp3" in cmd

    def test_contains_silenceremove_filter(self):
        cmd = _build_ffmpeg_trim_cmd(Path("in.mp3"), Path("out.mp3"))
        af = cmd[cmd.index("-af") + 1]
        assert "silenceremove" in af

    def test_threshold_reflected_in_filter(self):
        cmd = _build_ffmpeg_trim_cmd(Path("in.mp3"), Path("out.mp3"), silence_threshold=-40.0)
        af = cmd[cmd.index("-af") + 1]
        assert "-40.0dB" in af


class TestTrimFile:
    def test_unsupported_extension_returns_error(self):
        result = trim_file(Path("song.xyz"))
        assert result.success is False
        assert "Unsupported" in result.error

    def test_dry_run_returns_success_without_subprocess(self):
        result = trim_file(Path("song.mp3"), dry_run=True)
        assert result.success is True
        assert result.output_path is not None

    def test_dry_run_uses_custom_output_path(self, tmp_path):
        dest = tmp_path / "out.mp3"
        result = trim_file(Path("song.mp3"), output_path=dest, dry_run=True)
        assert result.output_path == dest

    def test_returns_success_on_zero_exit(self):
        completed = MagicMock(spec=subprocess.CompletedProcess)
        completed.returncode = 0
        with patch("warbler.trimmer.subprocess.run", return_value=completed):
            result = trim_file(Path("song.flac"))
        assert result.success is True

    def test_returns_error_on_nonzero_exit(self):
        completed = MagicMock(spec=subprocess.CompletedProcess)
        completed.returncode = 1
        completed.stderr = b"ffmpeg error"
        with patch("warbler.trimmer.subprocess.run", return_value=completed):
            result = trim_file(Path("song.mp3"))
        assert result.success is False
        assert "ffmpeg error" in result.error

    def test_returns_error_on_exception(self):
        with patch("warbler.trimmer.subprocess.run", side_effect=OSError("not found")):
            result = trim_file(Path("song.mp3"))
        assert result.success is False
        assert "not found" in result.error


class TestBatchTrim:
    def test_processes_all_paths(self):
        paths = [Path("a.mp3"), Path("b.flac")]
        with patch("warbler.trimmer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            report = batch_trim(paths)
        assert len(report.results) == 2

    def test_skips_unsupported_files(self):
        paths = [Path("a.txt"), Path("b.mp3")]
        with patch("warbler.trimmer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            report = batch_trim(paths)
        assert report.error_count == 1
        assert report.trimmed_count == 1
