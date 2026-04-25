"""Tests for warbler.splitter."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from warbler.splitter import (
    SplitReport,
    SplitResult,
    _build_split_cmd,
    batch_split,
    split_file,
)


def _proc(returncode: int = 0, stderr: bytes = b"") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stderr=stderr)


class TestSplitResult:
    def test_success_true_when_no_error(self):
        r = SplitResult(source=Path("a.mp3"), segments=[Path("a_000.mp3")])
        assert r.success is True

    def test_success_false_when_error(self):
        r = SplitResult(source=Path("a.mp3"), error="oops")
        assert r.success is False

    def test_segment_count(self):
        segs = [Path(f"a_{i:03d}.mp3") for i in range(5)]
        r = SplitResult(source=Path("a.mp3"), segments=segs)
        assert r.segment_count == 5


class TestSplitReport:
    def _report(self) -> SplitReport:
        r = SplitReport()
        r.results.append(SplitResult(source=Path("a.mp3"), segments=[Path("x"), Path("y")]))
        r.results.append(SplitResult(source=Path("b.mp3"), error="bad"))
        return r

    def test_success_count(self):
        assert self._report().success_count == 1

    def test_error_count(self):
        assert self._report().error_count == 1

    def test_total_segments(self):
        assert self._report().total_segments == 2


def test_build_split_cmd_contains_segment_time():
    cmd = _build_split_cmd(Path("/audio/track.mp3"), Path("/out"), 60)
    assert "-segment_time" in cmd
    assert "60" in cmd


def test_build_split_cmd_output_pattern_uses_stem():
    cmd = _build_split_cmd(Path("/audio/track.mp3"), Path("/out"), 30)
    pattern = cmd[-1]
    assert "track_" in pattern
    assert pattern.endswith(".mp3")


class TestSplitFile:
    def test_returns_error_for_unsupported_format(self, tmp_path):
        src = tmp_path / "audio.xyz"
        src.touch()
        result = split_file(src, tmp_path / "out")
        assert not result.success
        assert "Unsupported" in result.error

    def test_returns_error_when_ffmpeg_missing(self, tmp_path):
        src = tmp_path / "audio.mp3"
        src.touch()

        def _raise(*_a, **_kw):
            raise FileNotFoundError

        result = split_file(src, tmp_path / "out", run=_raise)
        assert not result.success
        assert "ffmpeg" in result.error

    def test_returns_error_on_nonzero_exit(self, tmp_path):
        src = tmp_path / "audio.mp3"
        src.touch()
        result = split_file(src, tmp_path / "out", run=lambda *a, **k: _proc(1, b"err"))
        assert not result.success
        assert "err" in result.error

    def test_returns_segments_on_success(self, tmp_path):
        src = tmp_path / "track.mp3"
        src.touch()
        out_dir = tmp_path / "out" / "track"
        out_dir.mkdir(parents=True)
        seg = out_dir / "track_000.mp3"
        seg.touch()

        result = split_file(src, tmp_path / "out", run=lambda *a, **k: _proc(0))
        assert result.success
        assert seg in result.segments


def test_batch_split_aggregates_results(tmp_path):
    sources = [tmp_path / f"t{i}.mp3" for i in range(3)]
    for s in sources:
        s.touch()

    report = batch_split(sources, tmp_path / "out", run=lambda *a, **k: _proc(0))
    assert len(report.results) == 3
