"""Tests for warbler.cli_stats."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.cli_stats import add_stats_subcommand, _run_stats
from warbler.tagger_stats import TagStats


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_stats_subcommand(sub)
    return p


class TestAddStatsSubcommand:
    def test_registers_stats_parser(self):
        p = _parser()
        ns = p.parse_args(["stats", "/tmp"])
        assert ns.func is _run_stats

    def test_default_recursive_false(self):
        p = _parser()
        ns = p.parse_args(["stats", "/tmp"])
        assert ns.recursive is False

    def test_recursive_flag(self):
        p = _parser()
        ns = p.parse_args(["stats", "/tmp", "--recursive"])
        assert ns.recursive is True

    def test_default_json_false(self):
        p = _parser()
        ns = p.parse_args(["stats", "/tmp"])
        assert ns.json is False

    def test_json_flag(self):
        p = _parser()
        ns = p.parse_args(["stats", "/tmp", "--json"])
        assert ns.json is True


class TestRunStats:
    def _namespace(self, directory="/tmp", recursive=False, json_out=False):
        ns = argparse.Namespace(directory=Path(directory), recursive=recursive, json=json_out)
        return ns

    def test_prints_formatted_stats(self, capsys):
        stats = TagStats(total=5, tagged=3, untagged=2, by_extension={"mp3": 5})
        with patch("warbler.cli_stats._collect_audio_files", return_value=[]), \
             patch("warbler.cli_stats.collect_stats", return_value=stats):
            _run_stats(self._namespace())
        out = capsys.readouterr().out
        assert "5" in out

    def test_json_output(self, capsys):
        stats = TagStats(total=2, tagged=1, untagged=1, by_extension={"flac": 2})
        with patch("warbler.cli_stats._collect_audio_files", return_value=[]), \
             patch("warbler.cli_stats.collect_stats", return_value=stats):
            _run_stats(self._namespace(json_out=True))
        data = json.loads(capsys.readouterr().out)
        assert data["total"] == 2
        assert data["tagged"] == 1
        assert "by_extension" in data
