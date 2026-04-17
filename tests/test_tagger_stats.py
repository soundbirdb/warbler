"""Tests for warbler.tagger_stats."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.tagger_stats import TagStats, collect_stats, format_stats


def _paths(*names: str) -> list[Path]:
    return [Path(n) for n in names]


class TestTagStats:
    def test_tagged_ratio_zero_when_empty(self):
        s = TagStats()
        assert s.tagged_ratio == 0.0

    def test_tagged_ratio_half(self):
        s = TagStats(total=4, tagged=2, untagged=2)
        assert s.tagged_ratio == 0.5

    def test_tagged_ratio_full(self):
        s = TagStats(total=3, tagged=3, untagged=0)
        assert s.tagged_ratio == 1.0


class TestCollectStats:
    def _mock_read(self, tagged_names: set[str]):
        def _read(path: Path):
            if path.name in tagged_names:
                return "abc123"
            return None
        return _read

    def test_counts_total(self):
        paths = _paths("a.mp3", "b.mp3", "c.flac")
        with patch("warbler.tagger_stats.read_fingerprint", side_effect=self._mock_read({"a.mp3"})):
            stats = collect_stats(paths)
        assert stats.total == 3

    def test_counts_tagged_and_untagged(self):
        paths = _paths("a.mp3", "b.mp3")
        with patch("warbler.tagger_stats.read_fingerprint", side_effect=self._mock_read({"a.mp3"})):
            stats = collect_stats(paths)
        assert stats.tagged == 1
        assert stats.untagged == 1

    def test_by_extension(self):
        paths = _paths("a.mp3", "b.mp3", "c.flac")
        with patch("warbler.tagger_stats.read_fingerprint", return_value=None):
            stats = collect_stats(paths)
        assert stats.by_extension["mp3"] == 2
        assert stats.by_extension["flac"] == 1

    def test_exception_in_read_counts_as_untagged(self):
        paths = _paths("bad.mp3")
        with patch("warbler.tagger_stats.read_fingerprint", side_effect=RuntimeError("boom")):
            stats = collect_stats(paths)
        assert stats.untagged == 1
        assert stats.tagged == 0


class TestFormatStats:
    def test_contains_totals(self):
        s = TagStats(total=10, tagged=7, untagged=3, by_extension={"mp3": 10})
        text = format_stats(s)
        assert "10" in text
        assert "70.0%" in text

    def test_lists_extensions(self):
        s = TagStats(total=2, tagged=0, untagged=2, by_extension={"flac": 2})
        text = format_stats(s)
        assert ".flac" in text
