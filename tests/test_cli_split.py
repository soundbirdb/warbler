"""Tests for warbler.cli_split."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.cli_split import add_split_subcommand, _run_split
from warbler.splitter import SplitReport, SplitResult


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_split_subcommand(sub)
    return p


class TestAddSplitSubcommand:
    def test_registers_split_parser(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio"])
        assert ns.command == "split"

    def test_default_duration_is_30(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio"])
        assert ns.duration == 30

    def test_custom_duration_accepted(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio", "--duration", "60"])
        assert ns.duration == 60

    def test_default_recursive_false(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio"])
        assert ns.recursive is False

    def test_recursive_flag(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio", "--recursive"])
        assert ns.recursive is True

    def test_default_output_is_none(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio"])
        assert ns.output is None

    def test_custom_output_accepted(self):
        p = _parser()
        ns = p.parse_args(["split", "/audio", "--output", "/out"])
        assert ns.output == Path("/out")


class TestRunSplit:
    def _make_namespace(self, tmp_path: Path, **kwargs) -> argparse.Namespace:
        defaults = dict(
            directory=tmp_path,
            output=None,
            duration=30,
            recursive=False,
        )
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_prints_no_files_when_directory_empty(self, tmp_path, capsys):
        ns = self._make_namespace(tmp_path)
        with patch("warbler.cli_split._collect_audio_files", return_value=[]):
            _run_split(ns)
        out = capsys.readouterr().out
        assert "No audio files found" in out

    def test_prints_ok_for_successful_result(self, tmp_path, capsys):
        src = tmp_path / "song.mp3"
        src.touch()
        report = SplitReport()
        report.results.append(
            SplitResult(source=src, segments=[tmp_path / "song_000.mp3"])
        )
        ns = self._make_namespace(tmp_path)
        with patch("warbler.cli_split._collect_audio_files", return_value=[src]), \
             patch("warbler.cli_split.batch_split", return_value=report):
            _run_split(ns)
        out = capsys.readouterr().out
        assert "[OK]" in out
        assert "song.mp3" in out

    def test_prints_error_for_failed_result(self, tmp_path, capsys):
        src = tmp_path / "bad.mp3"
        src.touch()
        report = SplitReport()
        report.results.append(SplitResult(source=src, error="ffmpeg error"))
        ns = self._make_namespace(tmp_path)
        with patch("warbler.cli_split._collect_audio_files", return_value=[src]), \
             patch("warbler.cli_split.batch_split", return_value=report):
            _run_split(ns)
        out = capsys.readouterr().out
        assert "[ERROR]" in out

    def test_default_output_falls_back_to_splits_subdir(self, tmp_path):
        src = tmp_path / "track.mp3"
        src.touch()
        report = SplitReport()
        report.results.append(SplitResult(source=src, segments=[]))
        ns = self._make_namespace(tmp_path)
        captured = {}
        def _fake_batch(sources, output_root, segment_duration):
            captured["output_root"] = output_root
            return report
        with patch("warbler.cli_split._collect_audio_files", return_value=[src]), \
             patch("warbler.cli_split.batch_split", side_effect=_fake_batch):
            _run_split(ns)
        assert captured["output_root"] == tmp_path / "splits"
