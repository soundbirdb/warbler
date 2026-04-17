"""Tests for warbler.converter."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.converter import (
    ConversionResult,
    batch_convert,
    convert_file,
)


def _completed(returncode: int = 0, stderr: bytes = b"") -> MagicMock:
    mock = MagicMock()
    mock.returncode = returncode
    mock.stderr = stderr
    return mock


class TestConvertFile:
    def test_returns_success_result(self, tmp_path):
        src = tmp_path / "track.wav"
        dest = tmp_path / "track.mp3"
        with patch("subprocess.run", return_value=_completed()) as mock_run:
            result = convert_file(src, dest)
        mock_run.assert_called_once()
        assert result.success is True
        assert result.source == src
        assert result.destination == dest
        assert result.error is None

    def test_returns_failure_result_on_nonzero_exit(self, tmp_path):
        src = tmp_path / "track.wav"
        dest = tmp_path / "track.mp3"
        exc = subprocess.CalledProcessError(1, "ffmpeg", stderr=b"codec error")
        with patch("subprocess.run", side_effect=exc):
            result = convert_file(src, dest)
        assert result.success is False
        assert "codec error" in (result.error or "")

    def test_raises_on_unsupported_target_format(self, tmp_path):
        src = tmp_path / "track.wav"
        dest = tmp_path / "track.xyz"
        with pytest.raises(ValueError, match="Unsupported target format"):
            convert_file(src, dest)

    def test_ffmpeg_command_contains_source_and_dest(self, tmp_path):
        src = tmp_path / "a.wav"
        dest = tmp_path / "a.flac"
        with patch("subprocess.run", return_value=_completed()) as mock_run:
            convert_file(src, dest)
        cmd = mock_run.call_args[0][0]
        assert str(src) in cmd
        assert str(dest) in cmd


class TestBatchConvert:
    def test_creates_output_dir(self, tmp_path):
        sources = [tmp_path / "a.wav", tmp_path / "b.wav"]
        out = tmp_path / "converted"
        with patch("subprocess.run", return_value=_completed()):
            batch_convert(sources, out, "mp3")
        assert out.is_dir()

    def test_returns_one_result_per_source(self, tmp_path):
        sources = [tmp_path / f"track{i}.wav" for i in range(3)]
        out = tmp_path / "out"
        with patch("subprocess.run", return_value=_completed()):
            results = batch_convert(sources, out, "flac")
        assert len(results) == 3

    def test_destination_uses_target_extension(self, tmp_path):
        sources = [tmp_path / "song.wav"]
        out = tmp_path / "out"
        with patch("subprocess.run", return_value=_completed()):
            results = batch_convert(sources, out, "ogg")
        assert results[0].destination.suffix == ".ogg"

    def test_partial_failure_included_in_results(self, tmp_path):
        sources = [tmp_path / "good.wav", tmp_path / "bad.wav"]
        out = tmp_path / "out"
        exc = subprocess.CalledProcessError(1, "ffmpeg", stderr=b"err")
        with patch("subprocess.run", side_effect=[_completed(), exc]):
            results = batch_convert(sources, out, "mp3")
        assert results[0].success is True
        assert results[1].success is False
