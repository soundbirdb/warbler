"""Tests for warbler.cli_export."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.cli_export import _run_export, add_export_subcommand


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "directory": Path("/audio"),
        "output": Path("fingerprints.json"),
        "fmt": "json",
        "recursive": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddExportSubcommand:
    def test_registers_export_parser(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers()
        add_export_subcommand(subs)
        ns = root.parse_args(["export", "/some/dir"])
        assert ns.func is _run_export

    def test_default_format_is_json(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers()
        add_export_subcommand(subs)
        ns = root.parse_args(["export", "/some/dir"])
        assert ns.fmt == "json"

    def test_csv_format_accepted(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers()
        add_export_subcommand(subs)
        ns = root.parse_args(["export", "/some/dir", "--format", "csv"])
        assert ns.fmt == "csv"


class TestRunExport:
    def test_prints_no_files_when_empty(self, capsys):
        args = _make_namespace()
        with patch("warbler.cli_export._collect_audio_files", return_value=[]):
            code = _run_export(args)
        out = capsys.readouterr().out
        assert "No audio files found" in out
        assert code == 0

    def test_calls_export_with_correct_args(self, tmp_path):
        dest = tmp_path / "out.csv"
        args = _make_namespace(output=dest, fmt="csv")
        fake_files = [Path("/audio/a.mp3")]
        with patch("warbler.cli_export._collect_audio_files", return_value=fake_files), \
             patch("warbler.cli_export.export", return_value=1) as mock_export:
            _run_export(args)
        mock_export.assert_called_once_with(fake_files, dest, fmt="csv")

    def test_reports_count_in_output(self, tmp_path, capsys):
        dest = tmp_path / "out.json"
        args = _make_namespace(output=dest)
        fake_files = [Path("/audio/a.mp3"), Path("/audio/b.mp3")]
        with patch("warbler.cli_export._collect_audio_files", return_value=fake_files), \
             patch("warbler.cli_export.export", return_value=2):
            _run_export(args)
        out = capsys.readouterr().out
        assert "2" in out

    def test_returns_zero_exit_code(self, tmp_path):
        args = _make_namespace(output=tmp_path / "out.json")
        with patch("warbler.cli_export._collect_audio_files", return_value=[Path("x.mp3")]), \
             patch("warbler.cli_export.export", return_value=1):
            assert _run_export(args) == 0
