"""Tests for warbler.cli_filter."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

from warbler.cli_filter import add_filter_subcommand, _run_filter


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_filter_subcommand(sub)
    return p


class TestAddFilterSubcommand:
    def test_registers_filter_parser(self):
        p = _parser()
        ns = p.parse_args(["filter", "/tmp"])
        assert hasattr(ns, "func")

    def test_default_recursive_false(self):
        ns = _parser().parse_args(["filter", "/tmp"])
        assert ns.recursive is False

    def test_tagged_flag(self):
        ns = _parser().parse_args(["filter", "/tmp", "--tagged"])
        assert ns.tagged is True

    def test_untagged_flag(self):
        ns = _parser().parse_args(["filter", "/tmp", "--untagged"])
        assert ns.untagged is True

    def test_extension_accepted(self):
        ns = _parser().parse_args(["filter", "/tmp", "--extension", ".flac"])
        assert ns.extension == ".flac"


class TestRunFilter:
    def _make_ns(self, **kwargs):
        defaults = dict(directory=Path("/tmp"), recursive=False, tagged=False, untagged=False, extension=None)
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_prints_results(self, capsys):
        fake_result = MagicMock()
        fake_result.path = Path("a.mp3")
        fake_result.is_tagged = True
        fake_result.fingerprint = "abc"

        with patch("warbler.cli_filter._collect_audio_files", return_value=[Path("a.mp3")]):
            with patch("warbler.cli_filter.apply_filter", return_value=[fake_result]):
                _run_filter(self._make_ns())

        out = capsys.readouterr().out
        assert "a.mp3" in out
        assert "1 file(s) matched" in out

    def test_empty_results(self, capsys):
        with patch("warbler.cli_filter._collect_audio_files", return_value=[]):
            with patch("warbler.cli_filter.apply_filter", return_value=[]):
                _run_filter(self._make_ns())
        out = capsys.readouterr().out
        assert "0 file(s) matched" in out
