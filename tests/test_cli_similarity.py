"""Tests for warbler.cli_similarity."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.cli_similarity import add_similarity_subcommand, _run_similarity
from warbler.similarity import SimilarityMatch

FP = "a" * 64


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_similarity_subcommand(sub)
    return p


class TestAddSimilaritySubcommand:
    def test_registers_similarity_parser(self):
        p = _parser()
        ns = p.parse_args(["similarity", FP, "/music"])
        assert ns.fingerprint == FP

    def test_default_threshold_is_085(self):
        p = _parser()
        ns = p.parse_args(["similarity", FP, "/music"])
        assert ns.threshold == pytest.approx(0.85)

    def test_custom_threshold_accepted(self):
        p = _parser()
        ns = p.parse_args(["similarity", FP, "/music", "--threshold", "0.5"])
        assert ns.threshold == pytest.approx(0.5)

    def test_no_recurse_flag(self):
        p = _parser()
        ns = p.parse_args(["similarity", FP, "/music", "--no-recurse"])
        assert ns.no_recurse is True


class TestRunSimilarity:
    def _ns(self, **kwargs):
        defaults = dict(
            fingerprint=FP,
            paths=[Path("/music")],
            threshold=0.85,
            no_recurse=False,
        )
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    @patch("warbler.cli_similarity.find_similar")
    def test_prints_no_results_message(self, mock_find, capsys):
        mock_find.return_value = []
        _run_similarity(self._ns())
        out = capsys.readouterr().out
        assert "No similar" in out

    @patch("warbler.cli_similarity.find_similar")
    def test_prints_match_details(self, mock_find, capsys):
        mock_find.return_value = [
            SimilarityMatch(path=Path("/music/a.mp3"), fingerprint=FP, distance=0)
        ]
        _run_similarity(self._ns())
        out = capsys.readouterr().out
        assert "a.mp3" in out
        assert "score=1.000" in out

    @patch("warbler.cli_similarity.find_similar")
    def test_passes_recursive_flag(self, mock_find):
        mock_find.return_value = []
        _run_similarity(self._ns(no_recurse=True))
        _, kwargs = mock_find.call_args
        assert kwargs["recursive"] is False
